"""Tests for core type definitions."""

from code_assist.types.command import (
    CommandBase,
    CommandType,
    SkipCommandResult,
    TextCommandResult,
)
from code_assist.types.hooks import (
    HookEvent,
    HookInput,
    HookOutcome,
    HookResult,
    PromptOption,
    PromptRequest,
)
from code_assist.types.ids import (
    generate_agent_id,
    generate_session_id,
    to_agent_id,
)
from code_assist.types.message import (
    AssistantMessage,
    SystemMessageSubtype,
    TextBlock,
    ToolUseBlock,
    Usage,
    create_api_error_message,
    create_assistant_message,
    create_system_message,
    create_user_message,
)
from code_assist.types.permissions import (
    PermissionAllowDecision,
    PermissionAskDecision,
    PermissionBehavior,
    PermissionDenyDecision,
    PermissionMode,
    PermissionRule,
    PermissionRuleSource,
    PermissionRuleValue,
    ToolPermissionContext,
    get_empty_tool_permission_context,
)
from code_assist.types.plugin import LoadedPlugin, PluginManifest
from code_assist.types.tools import (
    BashProgress,
    GenericToolProgress,
    MCPProgress,
    SpinnerMode,
    ToolProgress,
)


# ---------------------------------------------------------------------------
# ID Tests
# ---------------------------------------------------------------------------


class TestIds:
    def test_generate_session_id(self) -> None:
        sid = generate_session_id()
        assert isinstance(sid, str)
        assert len(sid) == 32  # hex uuid without dashes

    def test_generate_agent_id_no_label(self) -> None:
        aid = generate_agent_id()
        assert aid.startswith("a")
        assert len(aid) == 17  # 'a' + 16 hex chars

    def test_generate_agent_id_with_label(self) -> None:
        aid = generate_agent_id("test")
        assert aid.startswith("atest-")
        assert len(aid) == 22  # 'a' + 'test-' + 16 hex chars

    def test_to_agent_id_valid(self) -> None:
        result = to_agent_id("a1234567890abcdef")
        assert result is not None
        assert result == "a1234567890abcdef"

    def test_to_agent_id_with_label(self) -> None:
        result = to_agent_id("aexplore-1234567890abcdef")
        assert result is not None

    def test_to_agent_id_invalid(self) -> None:
        assert to_agent_id("invalid") is None
        assert to_agent_id("b1234567890abcdef") is None
        assert to_agent_id("a123") is None


# ---------------------------------------------------------------------------
# Message Tests
# ---------------------------------------------------------------------------


class TestMessages:
    def test_create_user_message(self) -> None:
        msg = create_user_message("hello")
        assert msg.type == "user"
        assert msg.content == "hello"
        assert msg.id.startswith("user_")
        assert msg.attachments == []
        assert msg.is_synthetic is False

    def test_create_user_message_synthetic(self) -> None:
        msg = create_user_message("test", is_synthetic=True, priority="now")
        assert msg.is_synthetic is True
        assert msg.priority == "now"

    def test_create_assistant_message(self) -> None:
        msg = create_assistant_message(
            [TextBlock(text="hello")], model="claude-sonnet-4-20250514"
        )
        assert msg.type == "assistant"
        assert len(msg.content) == 1
        assert msg.model == "claude-sonnet-4-20250514"

    def test_create_system_message(self) -> None:
        msg = create_system_message("compacting...", subtype=SystemMessageSubtype.STATUS)
        assert msg.type == "system"
        assert msg.subtype == SystemMessageSubtype.STATUS
        assert msg.content == "compacting..."

    def test_create_api_error_message(self) -> None:
        msg = create_api_error_message("Rate limited")
        assert msg.is_api_error_message is True
        assert msg.content[0].text == "Rate limited"  # type: ignore[union-attr]

    def test_content_blocks(self) -> None:
        text = TextBlock(text="hello")
        assert text.type == "text"

        tool_use = ToolUseBlock(id="t1", name="bash", input={"command": "ls"})
        assert tool_use.type == "tool_use"
        assert tool_use.name == "bash"

    def test_usage(self) -> None:
        usage = Usage(input_tokens=100, output_tokens=50)
        assert usage.input_tokens == 100
        assert usage.cache_read_input_tokens == 0

    def test_assistant_message_defaults(self) -> None:
        msg = AssistantMessage()
        assert msg.type == "assistant"
        assert msg.content == []
        assert msg.stop_reason is None


# ---------------------------------------------------------------------------
# Permission Tests
# ---------------------------------------------------------------------------


class TestPermissions:
    def test_permission_modes(self) -> None:
        assert PermissionMode.DEFAULT == "default"
        assert PermissionMode.BYPASS_PERMISSIONS == "bypassPermissions"
        assert PermissionMode.AUTO == "auto"
        assert PermissionMode.PLAN == "plan"

    def test_permission_behavior(self) -> None:
        assert PermissionBehavior.ALLOW == "allow"
        assert PermissionBehavior.DENY == "deny"
        assert PermissionBehavior.ASK == "ask"

    def test_permission_rule(self) -> None:
        rule = PermissionRule(
            source=PermissionRuleSource.USER_SETTINGS,
            rule_behavior=PermissionBehavior.ALLOW,
            rule_value=PermissionRuleValue(tool_name="bash", rule_content="ls *"),
        )
        assert rule.source == "userSettings"
        assert rule.rule_value.tool_name == "bash"

    def test_permission_decisions(self) -> None:
        allow = PermissionAllowDecision()
        assert allow.behavior == "allow"

        ask = PermissionAskDecision(message="Allow bash?")
        assert ask.behavior == "ask"
        assert ask.message == "Allow bash?"

        deny = PermissionDenyDecision(message="Blocked")
        assert deny.behavior == "deny"

    def test_empty_tool_permission_context(self) -> None:
        ctx = get_empty_tool_permission_context()
        assert ctx.mode == PermissionMode.DEFAULT
        assert ctx.always_allow_rules == {}
        assert ctx.is_bypass_permissions_mode_available is False

    def test_tool_permission_context(self) -> None:
        ctx = ToolPermissionContext(
            mode=PermissionMode.AUTO,
            is_bypass_permissions_mode_available=True,
        )
        assert ctx.mode == "auto"
        assert ctx.is_bypass_permissions_mode_available is True


# ---------------------------------------------------------------------------
# Hook Tests
# ---------------------------------------------------------------------------


class TestHooks:
    def test_hook_events(self) -> None:
        assert HookEvent.PRE_TOOL_USE == "PreToolUse"
        assert HookEvent.POST_TOOL_USE == "PostToolUse"
        assert HookEvent.SESSION_START == "SessionStart"

    def test_hook_input(self) -> None:
        inp = HookInput(
            hook_event=HookEvent.PRE_TOOL_USE,
            tool_name="bash",
            tool_input={"command": "rm -rf /"},
        )
        assert inp.hook_event == "PreToolUse"
        assert inp.tool_name == "bash"

    def test_hook_result(self) -> None:
        result = HookResult(outcome=HookOutcome.SUCCESS)
        assert result.outcome == "success"

        blocking = HookResult(
            outcome=HookOutcome.BLOCKING,
            prevent_continuation=True,
        )
        assert blocking.prevent_continuation is True

    def test_prompt_request(self) -> None:
        req = PromptRequest(
            prompt="perm-1",
            message="Allow this?",
            options=[
                PromptOption(key="y", label="Yes"),
                PromptOption(key="n", label="No"),
            ],
        )
        assert len(req.options) == 2
        assert req.options[0].key == "y"


# ---------------------------------------------------------------------------
# Tool Progress Tests
# ---------------------------------------------------------------------------


class TestToolProgress:
    def test_bash_progress(self) -> None:
        prog = BashProgress(
            command="ls -la",
            output="file1.txt\nfile2.txt",
            is_complete=True,
            exit_code=0,
        )
        assert prog.type == "bash_progress"
        assert prog.exit_code == 0

    def test_mcp_progress(self) -> None:
        prog = MCPProgress(
            server_name="sqlite",
            tool_name="query",
            progress=50.0,
            total=100.0,
        )
        assert prog.type == "mcp_progress"
        assert prog.progress == 50.0

    def test_tool_progress_wrapper(self) -> None:
        data = GenericToolProgress(message="Working...")
        prog = ToolProgress(tool_use_id="tu_123", data=data)
        assert prog.tool_use_id == "tu_123"
        assert prog.data.message == "Working..."

    def test_spinner_mode(self) -> None:
        assert SpinnerMode.THINKING == "thinking"
        assert SpinnerMode.TOOL_USE == "tool_use"


# ---------------------------------------------------------------------------
# Command Tests
# ---------------------------------------------------------------------------


class TestCommands:
    def test_command_base(self) -> None:
        cmd = CommandBase(
            name="commit",
            description="Create a git commit",
            command_type=CommandType.PROMPT,
        )
        assert cmd.name == "commit"
        assert cmd.is_enabled()
        assert cmd.user_facing_name() == "commit"

    def test_command_result_types(self) -> None:
        text = TextCommandResult(value="Done!")
        assert text.type == "text"

        skip = SkipCommandResult()
        assert skip.type == "skip"


# ---------------------------------------------------------------------------
# Plugin Tests
# ---------------------------------------------------------------------------


class TestPlugins:
    def test_plugin_manifest(self) -> None:
        manifest = PluginManifest(
            name="test-plugin",
            version="1.0.0",
            description="A test plugin",
        )
        assert manifest.name == "test-plugin"

    def test_loaded_plugin(self) -> None:
        plugin = LoadedPlugin(
            manifest=PluginManifest(name="test"),
            path="/path/to/plugin",
            source="bundled",
        )
        assert plugin.is_active is True
        assert plugin.error is None
