"""ConfigTool - get or set configuration values at runtime.

Supports reading and writing settings from both global config
(~/.claude/config.json) and project settings (settings.json).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Union

from pydantic import BaseModel, Field

from code_assist.config.config import get_global_config, save_global_config
from code_assist.config.settings import (
    get_global_settings_path,
    load_settings_file,
    save_settings_file,
)
from code_assist.tools.base import (
    CanUseToolFn,
    DescriptionOptions,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
    ValidationResult,
)
from code_assist.types.message import AssistantMessage

logger = logging.getLogger(__name__)


# Settings that can be modified via the Config tool
SUPPORTED_SETTINGS: dict[str, dict[str, Any]] = {
    "theme": {
        "source": "global",
        "type": "string",
        "description": "Color theme for the UI",
        "options": ["dark", "light", "light-daltonize", "dark-daltonize"],
    },
    "verbose": {
        "source": "global",
        "type": "boolean",
        "description": "Show detailed debug output",
        "app_state_key": "verbose",
    },
    "autoCompactEnabled": {
        "source": "global",
        "type": "boolean",
        "description": "Auto-compact when context is full",
    },
    "showTurnDuration": {
        "source": "global",
        "type": "boolean",
        "description": "Show turn duration after responses",
    },
    "model": {
        "source": "settings",
        "type": "string",
        "description": "Override the default model",
        "app_state_key": "mainLoopModel",
    },
}


class ConfigToolInput(BaseModel):
    """Input schema for ConfigTool."""

    setting: str = Field(
        ...,
        description='The setting key (e.g. "theme", "model", "verbose")',
    )
    value: Union[str, bool, int, float] | None = Field(
        default=None,
        description="The new value. Omit to get current value.",
    )


class ConfigTool(ToolDef):
    """Get or set configuration values at runtime.

    Supports a curated set of settings that can be safely modified.
    Reading any setting is always allowed; writing requires confirmation.
    """

    name = "Config"
    search_hint = "get or set Claude Code settings (theme, model)"
    max_result_size_chars = 100_000
    should_defer = True

    @property
    def input_schema(self) -> type[BaseModel]:
        return ConfigToolInput

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        inp: ConfigToolInput = input  # type: ignore[assignment]
        if not inp.setting.strip():
            return ValidationResult(
                result=False, message="setting key is required", error_code=1
            )
        return ValidationResult(result=True)

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        inp: ConfigToolInput = args  # type: ignore[assignment]

        setting_key = inp.setting.strip()

        # Check if supported
        config_spec = SUPPORTED_SETTINGS.get(setting_key)
        if config_spec is None:
            return ToolResult(
                data={
                    "success": False,
                    "error": f'Unknown setting: "{setting_key}"',
                }
            )

        # GET operation
        if inp.value is None:
            current_value = self._get_value(config_spec, setting_key, context)
            return ToolResult(
                data={
                    "success": True,
                    "operation": "get",
                    "setting": setting_key,
                    "value": current_value,
                }
            )

        # SET operation
        final_value: Any = inp.value

        # Coerce booleans
        if config_spec["type"] == "boolean":
            if isinstance(final_value, str):
                lower = final_value.lower().strip()
                if lower == "true":
                    final_value = True
                elif lower == "false":
                    final_value = False
            if not isinstance(final_value, bool):
                return ToolResult(
                    data={
                        "success": False,
                        "operation": "set",
                        "setting": setting_key,
                        "error": f"{setting_key} requires true or false.",
                    }
                )

        # Validate options
        options = config_spec.get("options")
        if options and final_value not in options:
            return ToolResult(
                data={
                    "success": False,
                    "operation": "set",
                    "setting": setting_key,
                    "error": f"Invalid value. Options: {', '.join(str(o) for o in options)}",
                }
            )

        # Get previous value
        previous_value = self._get_value(config_spec, setting_key, context)

        # Write the value
        self._set_value(config_spec, setting_key, final_value, context)

        return ToolResult(
            data={
                "success": True,
                "operation": "set",
                "setting": setting_key,
                "previousValue": previous_value,
                "newValue": final_value,
            }
        )

    def _get_value(
        self,
        spec: dict[str, Any],
        key: str,
        context: ToolUseContext,
    ) -> Any:
        """Get the current value of a setting."""
        if spec["source"] == "global":
            config = get_global_config()
            return config.get(key)
        elif spec["source"] == "settings":
            from code_assist.config.constants import get_global_settings_path

            settings = load_settings_file(get_global_settings_path())
            return settings.get(key)
        return None

    def _set_value(
        self,
        spec: dict[str, Any],
        key: str,
        value: Any,
        context: ToolUseContext,
    ) -> None:
        """Write a setting value."""
        if spec["source"] == "global":
            save_global_config({key: value})

            # Sync to AppState if applicable
            app_state_key = spec.get("app_state_key")
            if app_state_key:
                def _sync(state: Any) -> Any:
                    if isinstance(state, dict):
                        return {**state, app_state_key: value}
                    return state
                context.set_app_state(_sync)

        elif spec["source"] == "settings":
            from code_assist.config.constants import get_global_settings_path

            path = get_global_settings_path()
            settings = load_settings_file(path)
            settings[key] = value
            save_settings_file(path, settings)

            # Sync to AppState
            app_state_key = spec.get("app_state_key")
            if app_state_key:
                def _sync(state: Any) -> Any:
                    if isinstance(state, dict):
                        return {**state, app_state_key: value}
                    return state
                context.set_app_state(_sync)

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        inp: ConfigToolInput = input  # type: ignore[assignment]
        if inp.value is not None:
            return f"Setting config: {inp.setting}"
        return f"Getting config: {inp.setting}"

    def is_read_only(self, input: BaseModel) -> bool:
        inp: ConfigToolInput = input  # type: ignore[assignment]
        return inp.value is None

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        inp: ConfigToolInput = input  # type: ignore[assignment]
        return inp.value is None
