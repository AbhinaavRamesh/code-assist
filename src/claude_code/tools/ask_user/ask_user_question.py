"""AskUserQuestion tool - presents structured questions to the user.

Mirrors the JS AskUserQuestionTool which supports structured multi-question
forms with options, multi-select, previews, and annotations. The actual
interactive rendering happens in the TUI layer; this tool collects the
question data and returns user answers from the permission component.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from claude_code.tools.base import (
    CanUseToolFn,
    DescriptionOptions,
    ToolCallProgress,
    ToolDef,
    ToolResult,
    ToolUseContext,
    ValidationResult,
)
from claude_code.types.message import AssistantMessage


class QuestionOption(BaseModel):
    """A single option in a structured question."""

    label: str = Field(
        ...,
        description="Display text for this option (1-5 words)",
    )
    description: str = Field(
        ...,
        description="Explanation of what this option means",
    )
    preview: str | None = Field(
        default=None,
        description="Optional preview content shown when focused",
    )


class Question(BaseModel):
    """A structured question to present to the user."""

    question: str = Field(
        ...,
        description="The complete question to ask. Should end with a question mark.",
    )
    header: str = Field(
        ...,
        description="Very short chip/tag label (max 20 chars)",
    )
    options: list[QuestionOption] = Field(
        ...,
        description="Available choices (2-4 options)",
        min_length=2,
        max_length=4,
    )
    multi_select: bool = Field(
        default=False,
        description="Allow multiple selections",
    )


class AskUserQuestionInput(BaseModel):
    """Input schema for AskUserQuestion."""

    questions: list[Question] = Field(
        ...,
        description="Questions to ask the user (1-4 questions)",
        min_length=1,
        max_length=4,
    )
    answers: dict[str, str] | None = Field(
        default=None,
        description="User answers collected by the permission component",
    )
    annotations: dict[str, Any] | None = Field(
        default=None,
        description="Per-question annotations from the user",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata for tracking",
    )


class AskUserQuestionTool(ToolDef):
    """Ask the user structured questions and collect their responses.

    The tool returns the questions and any pre-filled answers. In an
    interactive session, the TUI renders the question form and collects
    answers before returning the tool result to the model.
    """

    name = "AskUserQuestion"
    search_hint = "ask the user a question with structured options"
    max_result_size_chars = 10_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return AskUserQuestionInput

    async def validate_input(
        self, input: BaseModel, context: ToolUseContext
    ) -> ValidationResult:
        inp: AskUserQuestionInput = input  # type: ignore[assignment]

        # Uniqueness check: question texts must be unique
        texts = [q.question for q in inp.questions]
        if len(texts) != len(set(texts)):
            return ValidationResult(
                result=False,
                message="Question texts must be unique",
                error_code=1,
            )

        # Uniqueness check: option labels within each question
        for q in inp.questions:
            labels = [opt.label for opt in q.options]
            if len(labels) != len(set(labels)):
                return ValidationResult(
                    result=False,
                    message=f"Option labels must be unique within question: {q.question[:50]}",
                    error_code=2,
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
        inp: AskUserQuestionInput = args  # type: ignore[assignment]

        # If answers were already provided (e.g. by the permission component
        # or in non-interactive mode), return them directly.
        if inp.answers:
            return ToolResult(
                data={
                    "questions": [
                        {
                            "question": q.question,
                            "header": q.header,
                            "options": [
                                {"label": o.label, "description": o.description}
                                for o in q.options
                            ],
                            "multi_select": q.multi_select,
                        }
                        for q in inp.questions
                    ],
                    "answers": inp.answers,
                    "annotations": inp.annotations or {},
                }
            )

        # In non-interactive sessions, return the questions as-is
        # (the orchestration layer will handle user input collection)
        if context.is_non_interactive_session:
            return ToolResult(
                data={
                    "questions": [
                        {
                            "question": q.question,
                            "header": q.header,
                            "options": [
                                {"label": o.label, "description": o.description}
                                for o in q.options
                            ],
                        }
                        for q in inp.questions
                    ],
                    "answers": {},
                    "message": "Questions presented to user (non-interactive mode).",
                }
            )

        # Interactive mode: format the questions for the TUI layer to render.
        # The actual answer collection happens via the permission/approval flow.
        question_data = []
        for q in inp.questions:
            question_data.append({
                "question": q.question,
                "header": q.header,
                "options": [
                    {
                        "label": o.label,
                        "description": o.description,
                        "preview": o.preview,
                    }
                    for o in q.options
                ],
                "multi_select": q.multi_select,
            })

        return ToolResult(
            data={
                "questions": question_data,
                "answers": inp.answers or {},
                "annotations": inp.annotations or {},
            }
        )

    async def description(
        self, input: BaseModel, options: DescriptionOptions
    ) -> str:
        inp: AskUserQuestionInput = input  # type: ignore[assignment]
        first = inp.questions[0].question if inp.questions else "?"
        truncated = first[:60] + "..." if len(first) > 60 else first
        return f"Asking: {truncated}"

    def is_read_only(self, input: BaseModel) -> bool:
        return True

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return False
