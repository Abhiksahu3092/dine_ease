"""
LLM Client via OpenRouter API.
OpenRouter provides unified access to many LLMs (GPT-4, Claude, Gemini, Llama, etc.).
"""

import os
from typing import List, Dict, Any, Optional
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠ WARNING: openai package not installed. Run: pip install openai")


class LLMClient:
    """
    Client for LLM access via OpenRouter API.

    OpenRouter provides API access to GPT-4, Claude, Gemini, Llama, and other models.
    Get your API key at: https://openrouter.ai
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "meta-llama/llama-3.1-8b-instruct",
        base_url: str = "https://openrouter.ai/api/v1",
    ):
        """
        Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key (falls back to OPENROUTER_API_KEY env var)
            model_name: Model to use (default: meta-llama/llama-3.1-8b-instruct)
                       Options: meta-llama/llama-3.1-8b-instruct (fast, good for tool calling)
                               meta-llama/llama-3.3-70b-instruct (better quality, larger model)
                               google/gemini-flash-1.5 (FREE, fast)
                               qwen/qwen-2-7b-instruct:free (FREE, decent quality)
                               openai/gpt-4o-mini (paid, excellent function calling)
            base_url: OpenRouter API URL
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package required. Run: pip install openai")

        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model_name
        self.base_url = base_url

        if not self.api_key:
            print("⚠ WARNING: No OPENROUTER_API_KEY found.")
            print("  Get your API key at: https://openrouter.ai/keys")
            print("  Set it: set OPENROUTER_API_KEY=your_key_here")
            return

        # Initialize OpenAI client with OpenRouter
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

        print(f"✓ OpenRouter client initialized with {model_name}")

    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        """
        Generate response from LLM via OpenRouter API.

        Args:
            messages: Message history with 'role' and 'content'
            tools: Optional tool definitions for function calling
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Dict with content, tool_calls, finish_reason, usage
        """
        if not self.api_key:
            return {
                "content": "No API key configured. Please set OPENROUTER_API_KEY environment variable.",
                "tool_calls": None,
                "finish_reason": "error",
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            }

        try:
            # Convert tools to OpenAI format if provided
            formatted_tools = None
            if tools:
                formatted_tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool["name"],
                            "description": tool["description"],
                            "parameters": tool["parameters"],
                        },
                    }
                    for tool in tools
                ]

            # Call OpenRouter via OpenAI-compatible API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=formatted_tools,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Parse response
            choice = response.choices[0]
            result = {
                "content": choice.message.content or "",
                "tool_calls": None,
                "finish_reason": choice.finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }

            # Handle tool calls if present
            if choice.message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments),
                    }
                    for tc in choice.message.tool_calls
                ]
            # FALLBACK: If model outputs tool calls as text instead of structured format
            elif (
                result["content"]
                and "{" in result["content"]
                and '"name":' in result["content"]
            ):
                try:
                    # Try to extract JSON from text (common with some models)
                    content = result["content"].strip()

                    # Remove any <|python_tag|> or similar markers
                    content = content.replace("<|python_tag|>", "").strip()

                    # Try to parse as JSON
                    tool_call_json = json.loads(content)

                    # If it has 'name' and 'parameters', it's a tool call
                    if "name" in tool_call_json:
                        result["tool_calls"] = [
                            {
                                "id": f"call_{tool_call_json['name']}",
                                "name": tool_call_json["name"],
                                "arguments": tool_call_json.get("parameters", {}),
                            }
                        ]
                        result["content"] = ""  # Clear the text content
                        print(
                            f"[LLM] Parsed tool call from text: {tool_call_json['name']}"
                        )
                except (json.JSONDecodeError, KeyError) as e:
                    # If parsing fails, leave it as text content
                    print(f"[LLM] Could not parse tool call from text: {e}")

            return result

        except Exception as e:
            print(f"❌ OpenRouter API error: {e}")
            import traceback

            traceback.print_exc()
            return {
                "content": f"I apologize, but I'm having trouble connecting to the AI. Error: {str(e)}",
                "tool_calls": None,
                "finish_reason": "error",
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            }

    def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Convenience method for generating with tool support.

        Args:
            messages: Conversation messages
            tools: Available tools
            temperature: Sampling temperature

        Returns:
            LLM response with potential tool calls
        """
        return self.generate(
            messages=messages,
            tools=tools,
            temperature=temperature,
        )

    def create_tool_definitions(
        self, tool_descriptions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Return tool definitions (will be formatted in generate method).

        Args:
            tool_descriptions: List of tool description dictionaries

        Returns:
            Tool definitions
        """
        return tool_descriptions
