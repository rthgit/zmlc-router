from __future__ import annotations

from typing import Protocol

from zmlc.models import ProviderResult, Task


class Provider(Protocol):
    name: str

    def generate(self, task: Task) -> ProviderResult: ...
