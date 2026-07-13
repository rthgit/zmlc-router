from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field

from zmlc.models import ProviderResult, Task


@dataclass
class OpenAICompatibleProvider:
    base_url: str
    model: str
    api_key: str = ""
    name: str = "openai-compatible"
    timeout_s: float = 30.0
    max_tokens: int = 512
    system_prompt: str = field(
        default="Return only the complete final answer. Obey every requested format constraint."
    )

    def generate(self, task: Task) -> ProviderResult:
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": task.prompt},
                ],
                "temperature": 0,
                "max_tokens": self.max_tokens,
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            self.base_url.rstrip("/") + "/chat/completions",
            data=payload,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
            data = json.loads(response.read().decode("utf-8"))
        message = data["choices"][0]["message"]
        answer = str(message.get("content") or "").strip()
        usage = data.get("usage") or {}
        return ProviderResult(
            answer=answer,
            provider=self.name,
            model=self.model,
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
        )
