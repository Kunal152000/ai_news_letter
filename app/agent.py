import json
import re
import traceback
import httpx
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.sse import sse_client
from app.config.settings import OPENROUTER_API_KEY

async def process_chat_query(query: str) -> str:
    """
    Connects to the local MCP server over SSE,
    gets available tools, passes them to OpenRouter LLM,
    and executes tools if the LLM decides to.
    """
    mcp_url = "https://ai-news-letter-b9lx.onrender.com/mcp/sse"
    
    if not OPENROUTER_API_KEY:
        return "Error: OPENROUTER_API_KEY is not set."

    async with AsyncExitStack() as stack:
        try:
            # Connect to MCP server over network (SSE)
            print(f"Connecting to MCP SSE at {mcp_url}...")
            sse_transport = await stack.enter_async_context(sse_client(url=mcp_url))
            session = await stack.enter_async_context(ClientSession(*sse_transport))
            await session.initialize()
            
            # 1. Get tools
            response = await session.list_tools()
            tools = []
            for t in response.tools:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.inputSchema
                    }
                })
                
            # 2. Call OpenRouter LLM
            system_prompt = (
                "You are an AI assistant that fetches and analyzes AI news and tools. "
                "Use tools instead of inventing facts or URLs. "
                "When calling filter_ai_news, pass the `articles` parameter as a JSON array copied from "
                "get_news output—never put that array inside a string (URLs break JSON escaping). "
                "For deploy_newsletter_page, pass `news` and optional `github_repos` as JSON arrays the same way. "
                "Newsletter flow: get_news → get_github_repos → filter_ai_news(articles=[...]) → "
                "deploy_newsletter_page(news=[...], github_repos=[...]) → send_email with issue_url=public_url, "
                "highlights=[short teaser lines from top stories], subject, recipients; optional html_content. "
                "If the user does not specify dates, use the last 7 days for get_news. "
                "Format final answers clearly for the user."
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            }
            
            # Using a reliable model for tool-calling
            payload = {
                "model": "google/gemini-2.0-flash-001",
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto"
            }
            
            max_rounds = 100
            async with httpx.AsyncClient(timeout=120.0) as client:
                for _round in range(max_rounds):
                    payload["messages"] = messages
                    payload["tool_choice"] = "auto"
                    resp = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    if resp.status_code != 200:
                        return f"OpenRouter API Error: {resp.status_code} - {resp.text}"

                    llm_result = resp.json()
                    if "choices" not in llm_result or not llm_result["choices"]:
                        return "Error: Empty response from LLM."

                    message = llm_result["choices"][0]["message"]
                    messages.append(message)

                    if not message.get("tool_calls"):
                        return message.get("content", "No final content.")

                    for tool_call in message["tool_calls"]:
                        func_name = tool_call["function"]["name"]
                        try:
                            arg_text = tool_call["function"]["arguments"]
                            try:
                                func_args = json.loads(arg_text)
                            except json.JSONDecodeError:
                                match = re.search(r"\{.*\}", arg_text, re.DOTALL)
                                if match:
                                    func_args = json.loads(match.group())
                                else:
                                    raise ValueError("Could not parse JSON")
                        except Exception:
                            continue

                        tool_result = await session.call_tool(func_name, arguments=func_args)
                        content = tool_result.content[0].text if tool_result.content else "{}"

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "name": func_name,
                                "content": content,
                            }
                        )

                return "Stopped: maximum tool rounds reached without a final answer."
                    
        except Exception as e:
            traceback.print_exc()
            return f"Error interacting with MCP or LLM: {str(e)}"
