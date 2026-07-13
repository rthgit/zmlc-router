from __future__ import annotations

from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
import asyncio
from time import perf_counter

from zmlc.models import Route, SolveResult, Task, TraceEvent
from zmlc.policy import RoutingPolicy
from zmlc.providers.base import Provider
from zmlc.registry import SolverRegistry
from zmlc.telemetry import TelemetrySink
from zmlc.verifiers import verify_answer, verify_solver_result


class Router:
    def __init__(
        self,
        *,
        registry: SolverRegistry | None = None,
        policy: RoutingPolicy | None = None,
        local_provider: Provider | None = None,
        remote_provider: Provider | None = None,
        telemetry: TelemetrySink | None = None,
    ) -> None:
        self.registry = registry or SolverRegistry()
        self.policy = policy or RoutingPolicy()
        self.local_provider = local_provider
        self.remote_provider = remote_provider
        self.telemetry = telemetry

    def _finish(self, task: Task, result: SolveResult, started: float) -> SolveResult:
        baseline_tokens = max(0, int(task.metadata.get("baseline_tokens") or 0))
        saved = baseline_tokens if result.route == Route.DETERMINISTIC else 0
        finished = replace(
            result,
            latency_ms=round((perf_counter() - started) * 1000, 3),
            estimated_tokens_saved=saved,
        )
        if self.telemetry is not None:
            self.telemetry.record(task, finished)
        return finished

    def solve(self, task: Task | str) -> SolveResult:
        started = perf_counter()
        if isinstance(task, str):
            task = Task(prompt=task)
        trace: list[TraceEvent] = []
        candidates = self.registry.candidates()[: self.policy.max_solver_candidates]
        for solver in candidates:
            if not solver.supports(task):
                continue
            result = solver.solve(task)
            if result is None:
                trace.append(TraceEvent(solver.name, "abstain"))
                continue
            verified = verify_solver_result(task, result)
            baseline_tokens = max(0, int(task.metadata.get("baseline_tokens") or 0))
            savings_worthwhile = (
                baseline_tokens == 0
                or baseline_tokens >= self.policy.minimum_estimated_savings
            )
            accepted = savings_worthwhile and result.confidence >= self.policy.solver_min_confidence and (
                verified or not self.policy.require_verification
            )
            trace.append(
                TraceEvent(
                    solver.name,
                    "accept" if accepted else "reject",
                    {
                        "confidence": result.confidence,
                        "verified": verified,
                        "savings_worthwhile": savings_worthwhile,
                    },
                )
            )
            if accepted:
                return self._finish(
                    task,
                    SolveResult(
                        task_id=task.task_id,
                        answer=result.answer,
                        route=Route.DETERMINISTIC,
                        confidence=result.confidence,
                        solver=result.solver,
                        trace=tuple(trace),
                    ),
                    started,
                )

        provider_chain: list[tuple[Route, Provider | None]] = []
        if self.policy.allow_local_model:
            provider_chain.append((Route.LOCAL_MODEL, self.local_provider))
        if self.policy.allow_remote_model:
            provider_chain.append((Route.REMOTE_MODEL, self.remote_provider))
        for route, provider in provider_chain:
            if provider is None:
                continue
            try:
                generated = provider.generate(task)
            except Exception as exc:
                trace.append(
                    TraceEvent(provider.name, "error", {"error_type": type(exc).__name__})
                )
                continue
            verified = verify_answer(task, generated.answer)
            trace.append(TraceEvent(provider.name, "accept" if verified else "reject"))
            if verified:
                return self._finish(
                    task,
                    SolveResult(
                        task_id=task.task_id,
                        answer=generated.answer,
                        route=route,
                        confidence=0.8,
                        provider=generated.provider,
                        model=generated.model,
                        input_tokens=generated.input_tokens,
                        output_tokens=generated.output_tokens,
                        trace=tuple(trace),
                    ),
                    started,
                )

        if self.policy.delegate_to_host:
            trace.append(
                TraceEvent(
                    "host_model",
                    "delegate",
                    {"reason": "no verified deterministic or configured provider route"},
                )
            )
            return self._finish(
                task,
                SolveResult(
                    task_id=task.task_id,
                    answer="",
                    route=Route.HOST_MODEL,
                    confidence=1.0,
                    trace=tuple(trace),
                ),
                started,
            )

        if self.policy.fail_closed:
            raise RuntimeError(f"no verified route for task {task.task_id}")
        return self._finish(
            task,
            SolveResult(
                task_id=task.task_id,
                answer="",
                route=Route.FAILED,
                confidence=0.0,
                trace=tuple(trace),
            ),
            started,
        )

    def solve_batch(
        self,
        tasks: list[Task | str],
        *,
        max_workers: int = 4,
    ) -> list[SolveResult]:
        if max_workers < 1:
            raise ValueError("max_workers must be positive")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(self.solve, tasks))

    async def solve_async(self, task: Task | str) -> SolveResult:
        return await asyncio.to_thread(self.solve, task)
