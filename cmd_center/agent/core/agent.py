"""OmniousAgent core implementation with ReAct loop, tool calling, streaming, and retry logic."""

import asyncio
import json
from dataclasses import dataclass, field
from typing import AsyncGenerator, Dict, List, Optional, Any

import httpx

from ...backend.integrations.config import get_config
from ..tools.registry import ToolRegistry
from ..tools.pipeline_tools import GetOverdueDeals, GetStuckDeals, GetDealDetails, GetDealNotes
from ..tools.task_tools import GetTasks, GetOverdueTasks, GetPendingReminders, GetNotes
from ..tools.employee_tools import GetEmployees, GetEmployeeDetails, GetEmployeeSkills, GetOwnerKPIs
from ..tools.financial_tools import GetCashflowProjection, GetCEODashboard
from ..tools.email_tools import SearchEmails, GetEmails
from ..tools.document_tools import GetExpiringDocuments
from ..tools.hr_tools import GetUnpaidBonuses
from ..observability.metrics import MetricsTracker, get_metrics_tracker
from .prompts import build_system_prompt


@dataclass
class StreamChunk:
    """Represents a chunk of streaming response.

    Types:
        - "text": Regular text content
        - "tool_call": Tool is being called
        - "tool_result": Tool execution result
        - "error": Error occurred
        - "done": Stream completed
    """
    type: str
    content: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[dict] = None
    tool_result: Optional[dict] = None
    error: Optional[str] = None


class OmniousAgent:
    """Main agent orchestrating conversation, tool calling, and streaming responses."""

    MAX_RETRIES = 3
    RETRY_DELAYS = [0.1, 0.5, 1.0]

    def __init__(self):
        """Initialize the agent with configuration, tools, and metrics."""
        self.config = get_config()
        self.tools = ToolRegistry()
        self.metrics = get_metrics_tracker()
        self.conversation_history: List[Dict[str, Any]] = []

        self._register_tools()

    def _register_tools(self) -> None:
        """Register all available tools."""
        # Pipeline tools
        self.tools.register(GetOverdueDeals())
        self.tools.register(GetStuckDeals())
        self.tools.register(GetDealDetails())
        self.tools.register(GetDealNotes())

        # Task tools
        self.tools.register(GetTasks())
        self.tools.register(GetOverdueTasks())
        self.tools.register(GetPendingReminders())
        self.tools.register(GetNotes())

        # Employee tools
        self.tools.register(GetEmployees())
        self.tools.register(GetEmployeeDetails())
        self.tools.register(GetEmployeeSkills())
        self.tools.register(GetOwnerKPIs())

        # Financial tools
        self.tools.register(GetCashflowProjection())
        self.tools.register(GetCEODashboard())

        # Email tools
        self.tools.register(SearchEmails())
        self.tools.register(GetEmails())

        # Document tools
        self.tools.register(GetExpiringDocuments())

        # HR tools
        self.tools.register(GetUnpaidBonuses())

    def _build_messages(self, user_message: str) -> List[Dict[str, Any]]:
        """Build messages array for API call.

        Args:
            user_message: The user's message

        Returns:
            List of message dicts including system prompt, history, and user message
        """
        messages = [
            {"role": "system", "content": build_system_prompt()}
        ]

        # Add conversation history
        messages.extend(self.conversation_history)

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    def _add_to_history(self, role: str, content: str) -> None:
        """Add a message to conversation history.

        Args:
            role: Message role (user, assistant)
            content: Message content
        """
        self.conversation_history.append({
            "role": role,
            "content": content
        })

    def clear_conversation(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []

    async def _call_api_with_retry(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[dict]] = None,
        stream: bool = False
    ) -> httpx.Response:
        """Call the LLM API with retry logic.

        Args:
            messages: Messages to send
            tools: Optional tool schemas
            stream: Whether to stream the response

        Returns:
            API response

        Raises:
            httpx.HTTPError: If all retries fail
        """
        headers = {
            "Authorization": f"Bearer {self.config.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://gyptech.com",
            "X-Title": "GypTech Command Center"
        }

        payload = {
            "model": self.config.llm_model,
            "messages": messages,
            "stream": stream
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        last_error = None

        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt in range(self.MAX_RETRIES):
                try:
                    response = await client.post(
                        f"{self.config.openrouter_api_url}/chat/completions",
                        headers=headers,
                        json=payload
                    )

                    # Handle rate limiting
                    if response.status_code == 429:
                        if attempt < self.MAX_RETRIES - 1:
                            await asyncio.sleep(self.RETRY_DELAYS[attempt])
                            continue
                        response.raise_for_status()

                    response.raise_for_status()
                    return response

                except httpx.HTTPError as e:
                    last_error = e
                    if attempt < self.MAX_RETRIES - 1:
                        await asyncio.sleep(self.RETRY_DELAYS[attempt])
                    else:
                        raise

        raise last_error  # type: ignore

    async def _process_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process tool calls and return results.

        Args:
            tool_calls: List of tool call objects from the API

        Returns:
            List of tool result messages
        """
        results = []

        for tool_call in tool_calls:
            tool_id = tool_call["id"]
            function = tool_call["function"]
            tool_name = function["name"]

            try:
                arguments = json.loads(function["arguments"])
            except json.JSONDecodeError:
                arguments = {}

            # Execute the tool
            result = self.tools.execute(tool_name, arguments)

            # Format result as message
            if result.success:
                content = json.dumps(result.data)
            else:
                content = json.dumps({"error": result.error})

            results.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "content": content
            })

        return results

    async def _call_llm_with_tools(self, messages: List[Dict[str, Any]], max_iterations: int = 10) -> str:
        """Call LLM with tools, handling tool calls in a loop.

        This implements the ReAct pattern where the LLM can iteratively call tools
        and receive results until it has enough information to respond.

        Args:
            messages: Messages to send to the LLM
            max_iterations: Maximum number of tool-calling iterations to prevent infinite loops

        Returns:
            Final text response from the LLM
        """
        tools_schema = self.tools.get_tools_schema()
        iteration = 0

        # Initial API call
        response = await self._call_api_with_retry(messages, tools_schema)
        response_data = response.json()

        # Track tokens
        if "usage" in response_data:
            self.metrics.track(
                response_data["usage"].get("prompt_tokens", 0),
                response_data["usage"].get("completion_tokens", 0)
            )

        assistant_message = response_data["choices"][0]["message"]

        # Handle tool calls in a loop (ReAct pattern)
        while "tool_calls" in assistant_message and assistant_message["tool_calls"]:
            iteration += 1
            if iteration > max_iterations:
                break

            # Process tool calls
            tool_results = await self._process_tool_calls(assistant_message["tool_calls"])

            # Add assistant message with tool calls to messages
            messages.append(assistant_message)

            # Add tool results
            messages.extend(tool_results)

            # Call API again with tool results
            response = await self._call_api_with_retry(messages, tools_schema)
            response_data = response.json()

            # Track tokens
            if "usage" in response_data:
                self.metrics.track(
                    response_data["usage"].get("prompt_tokens", 0),
                    response_data["usage"].get("completion_tokens", 0)
                )

            assistant_message = response_data["choices"][0]["message"]

        # Get final content
        return assistant_message.get("content", "")

    async def chat(self, message: str) -> str:
        """Send a message and get a response (non-streaming).

        Args:
            message: User's message

        Returns:
            Assistant's response
        """
        messages = self._build_messages(message)

        # Add user message to history
        self._add_to_history("user", message)

        # Call LLM with tool handling
        content = await self._call_llm_with_tools(messages)

        # Add to history
        self._add_to_history("assistant", content)

        return content

    async def chat_stream(self, message: str) -> AsyncGenerator[StreamChunk, None]:
        """Send a message and stream the response.

        Args:
            message: User's message

        Yields:
            StreamChunk objects as response comes in
        """
        messages = self._build_messages(message)
        tools_schema = self.tools.get_tools_schema()

        # Add user message to history
        self._add_to_history("user", message)

        try:
            async for chunk in self._stream_with_tools(messages, tools_schema):
                yield chunk
        except Exception as e:
            yield StreamChunk(type="error", error=str(e))

    async def _stream_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools_schema: List[dict]
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream response with tool calling support.

        Args:
            messages: Messages to send
            tools_schema: Tool schemas

        Yields:
            StreamChunk objects
        """
        headers = {
            "Authorization": f"Bearer {self.config.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://gyptech.com",
            "X-Title": "GypTech Command Center"
        }

        payload = {
            "model": self.config.llm_model,
            "messages": messages,
            "stream": True,
            "tools": tools_schema,
            "tool_choice": "auto"
        }

        accumulated_content = ""
        accumulated_tool_calls: List[Dict[str, Any]] = []
        current_tool_call: Optional[Dict[str, Any]] = None

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{self.config.openrouter_api_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield StreamChunk(
                        type="error",
                        error=f"API error {response.status_code}: {error_text.decode()}"
                    )
                    return

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    data = line[6:]  # Remove "data: " prefix

                    if data == "[DONE]":
                        break

                    try:
                        chunk_data = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    if not chunk_data.get("choices"):
                        continue

                    delta = chunk_data["choices"][0].get("delta", {})

                    # Handle text content
                    if "content" in delta and delta["content"]:
                        accumulated_content += delta["content"]
                        yield StreamChunk(type="text", content=delta["content"])

                    # Handle tool calls
                    if "tool_calls" in delta:
                        for tool_call_delta in delta["tool_calls"]:
                            index = tool_call_delta.get("index", 0)

                            # Extend accumulated_tool_calls if needed
                            while len(accumulated_tool_calls) <= index:
                                accumulated_tool_calls.append({
                                    "id": "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""}
                                })

                            tc = accumulated_tool_calls[index]

                            if "id" in tool_call_delta:
                                tc["id"] = tool_call_delta["id"]

                            if "function" in tool_call_delta:
                                func = tool_call_delta["function"]
                                if "name" in func:
                                    tc["function"]["name"] = func["name"]
                                    yield StreamChunk(
                                        type="tool_call",
                                        tool_name=func["name"]
                                    )
                                if "arguments" in func:
                                    tc["function"]["arguments"] += func["arguments"]

        # Process accumulated tool calls
        if accumulated_tool_calls:
            for tc in accumulated_tool_calls:
                if tc["function"]["name"]:
                    try:
                        args = json.loads(tc["function"]["arguments"]) if tc["function"]["arguments"] else {}
                    except json.JSONDecodeError:
                        args = {}

                    result = self.tools.execute(tc["function"]["name"], args)

                    yield StreamChunk(
                        type="tool_result",
                        tool_name=tc["function"]["name"],
                        tool_result=result.data if result.success else {"error": result.error}
                    )

                    # Add tool call and result to messages for continuation
                    messages.append({
                        "role": "assistant",
                        "tool_calls": [tc]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(result.data if result.success else {"error": result.error})
                    })

            # Continue conversation after tool calls
            async for chunk in self._stream_with_tools(messages, tools_schema):
                yield chunk
        else:
            # No more tool calls, add response to history
            if accumulated_content:
                self._add_to_history("assistant", accumulated_content)

            yield StreamChunk(type="done")


# Singleton instance
_agent: Optional[OmniousAgent] = None


def get_agent() -> OmniousAgent:
    """Get or create agent singleton."""
    global _agent
    if _agent is None:
        _agent = OmniousAgent()
    return _agent
