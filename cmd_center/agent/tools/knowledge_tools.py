"""Knowledge base tools for the agent."""

from pathlib import Path

from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"


class ReadKnowledgeParams(BaseModel):
    """Parameters for read_knowledge tool."""

    topic: str = Field(
        description="Knowledge topic to read. Use '_index' to see available topics."
    )


class ReadKnowledge(BaseTool):
    """Read company knowledge on a specific topic."""

    name = "read_knowledge"
    description = (
        "Read company knowledge on a specific topic. Use topic='_index' to see all "
        "available topics. Topics include: company_overview, company_structure, "
        "products_services, employees_rolecard, procedures, workflows, strategy."
    )
    parameters_model = ReadKnowledgeParams

    def execute(self, params: ReadKnowledgeParams) -> ToolResult:
        """Execute the tool.

        Args:
            params: Validated parameters with topic

        Returns:
            ToolResult with knowledge content or error
        """
        try:
            # Sanitize topic to prevent path traversal
            topic = params.topic.replace("/", "").replace("\\", "").replace("..", "")

            # Add .md extension if not present
            if not topic.endswith(".md"):
                topic = f"{topic}.md"

            file_path = KNOWLEDGE_DIR / topic

            if not file_path.exists():
                available = [f.stem for f in KNOWLEDGE_DIR.glob("*.md")]
                return ToolResult(
                    success=False,
                    error=f"Knowledge topic '{params.topic}' not found. Available: {available}",
                )

            content = file_path.read_text()

            return ToolResult(
                success=True,
                data={"topic": params.topic, "content": content},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
