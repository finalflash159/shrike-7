from __future__ import annotations

from typing import Any

from shrike7.tools.base import SideEffectLevel, ToolResult, ToolSpec, object_schema


class DisabledWeatherTool:
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="weather.current",
            description="Return current weather. Disabled until network policy is configured.",
            input_schema=object_schema(
                properties={
                    "location": {
                        "type": "string",
                        "description": "Location name.",
                    }
                },
                required=["location"],
            ),
            side_effect=SideEffectLevel.NETWORK,
            enabled=False,
        )

    def run(self, arguments: dict[str, Any]) -> ToolResult:
        return ToolResult(
            name=self.spec.name,
            ok=False,
            content="",
            error="weather.current is disabled until network policy is configured.",
        )
