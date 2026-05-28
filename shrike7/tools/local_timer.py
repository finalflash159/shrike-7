from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from shrike7.tools.base import SideEffectLevel, ToolResult, ToolSpec, object_schema


@dataclass(frozen=True)
class TimerRecord:
    id: str
    label: str
    duration_seconds: int
    created_at: str
    due_at: str


class LocalTimerTool:
    def __init__(
        self,
        timezone: str = "Asia/Ho_Chi_Minh",
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        self.timezone = timezone
        self.now_fn = now_fn or (lambda: datetime.now(tz=ZoneInfo(self.timezone)))
        self._timers: list[TimerRecord] = []

    @property
    def timers(self) -> tuple[TimerRecord, ...]:
        return tuple(self._timers)

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="local_timer.set",
            description="Create an in-memory timer reminder for the current demo session.",
            input_schema=object_schema(
                properties={
                    "duration_seconds": {
                        "type": "integer",
                        "description": "Timer duration in seconds.",
                    },
                    "label": {
                        "type": "string",
                        "description": "Optional timer label.",
                    },
                },
                required=["duration_seconds"],
            ),
            side_effect=SideEffectLevel.LOCAL_STATE,
        )

    def run(self, arguments: dict[str, Any]) -> ToolResult:
        duration_seconds = int(arguments["duration_seconds"])
        if duration_seconds <= 0:
            raise ValueError("duration_seconds must be greater than 0")

        label = str(arguments.get("label") or "hẹn giờ")
        created_at = self.now_fn()
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=ZoneInfo(self.timezone))
        due_at = created_at + timedelta(seconds=duration_seconds)

        record = TimerRecord(
            id=f"timer-{len(self._timers) + 1:03d}",
            label=label,
            duration_seconds=duration_seconds,
            created_at=created_at.isoformat(),
            due_at=due_at.isoformat(),
        )
        self._timers.append(record)

        minutes, seconds = divmod(duration_seconds, 60)
        if minutes and seconds:
            duration_text = f"{minutes} phút {seconds} giây"
        elif minutes:
            duration_text = f"{minutes} phút"
        else:
            duration_text = f"{seconds} giây"

        return ToolResult(
            name=self.spec.name,
            ok=True,
            content=f"Đã đặt {label} trong {duration_text}.",
            data=asdict(record),
        )
