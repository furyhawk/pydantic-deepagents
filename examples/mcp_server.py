"""Example demonstrating MCP server integration.

Shows how to connect to MCP servers using pydantic-ai's MCP support:
- `MCPToolset(StdioTransport(...))` for local subprocess MCP servers (stdio transport)
- `MCPServerSSE` for remote SSE-based MCP servers
- `MCPToolset` for FastMCP-based connections (recommended)
- `MCP` capability for model-native MCP support

MCP tools appear as native tools alongside deep agent's built-in tools.
"""

import asyncio
from http import client
import os
from pathlib import Path

from fastmcp.client import Client
from fastmcp.client.transports import StdioTransport, StreamableHttpTransport
from pydantic_ai.capabilities import MCP, PrefixTools
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.toolsets import PrefixedToolset

from pydantic_deep import DeepAgentDeps, StateBackend, create_deep_agent

model = OpenAIResponsesModel(
    "gemma-4-12B-it-qat-GGUF",
    provider=OpenAIProvider(
        base_url=os.getenv("LLM_BASE_URL", "http://localhost:8011/v1"),
        api_key=os.getenv("LLM_API_KEY", "no-key-required"),
    ),
)


async def basic_mcp_via_toolset():
    """Connect to a remote MCP server using MCPToolset (recommended for HTTP)."""
    agent = create_deep_agent(
        model=model,
        toolsets=[
            MCPToolset("http://localhost:8000/mcp"),
        ],
    )

    deps = DeepAgentDeps(backend=StateBackend())
    result = await agent.run("Use the MCP tools to complete this task", deps=deps)
    print(result.output)


async def basic_mcp_via_capability():
    """Connect to an MCP server using the native model MCP capability."""
    agent = create_deep_agent(
        model=model,
        capabilities=[
            MCP(url="http://localhost:8000/mcp"),
        ],
    )

    deps = DeepAgentDeps(backend=StateBackend())
    result = await agent.run("Use the MCP tools to complete this task", deps=deps)
    print(result.output)


async def multiple_mcp_via_toolsets():
    """Connect to multiple MCP servers with namespacing via toolsets."""
    agent = create_deep_agent(
        model=model,
        toolsets=[
            MCPToolset("http://localhost:8001/mcp"),
            MCPToolset("http://localhost:8002/mcp"),
        ],
    )

    deps = DeepAgentDeps(backend=StateBackend())
    result = await agent.run(
        "Create a GitHub issue and notify the team on Slack",
        deps=deps,
    )
    print(result.output)


async def multiple_mcp_via_capabilities():
    """Connect to multiple MCP servers with namespacing via capabilities."""
    agent = create_deep_agent(
        model=model,
        capabilities=[
            PrefixTools(MCP(url="http://localhost:8001/mcp"), prefix="github"),
            PrefixTools(MCP(url="http://localhost:8002/mcp"), prefix="slack"),
        ],
    )

    deps = DeepAgentDeps(backend=StateBackend())
    result = await agent.run(
        "Create a GitHub issue and notify the team on Slack",
        deps=deps,
    )
    print(result.output)


async def local_mcp_via_stdio():
    """Connect to a local MCP server via stdio using MCPToolset with StdioTransport."""
    agent = create_deep_agent(
        model=model,
        toolsets=[
            PrefixedToolset(
                MCPToolset(
                    StdioTransport(
                        command="npx",
                        args=["-y", "@modelcontextprotocol/server-filesystem", str(Path.cwd())],
                    ),
                ),
                prefix="mcp_fs",
            ),
        ],
    )

    deps = DeepAgentDeps(backend=StateBackend())
    result = await agent.run("List files in the workspace", deps=deps)
    print(result.output)


async def remote_mcp_via_sse():
    """Connect to a remote MCP server via SSE transport."""
    sse_client = Client(
        StreamableHttpTransport(
            url="http://localhost:3001/sse",
        )
    )
    agent = create_deep_agent(
        model=model,
        toolsets=[
            MCPToolset(client=sse_client),
        ],
    )

    deps = DeepAgentDeps(backend=StateBackend())
    result = await agent.run("Use the MCP tools to complete this task", deps=deps)
    print(result.output)


async def tavily_mcp_via_toolset():
    """Connect to a remote MCP server via HTTP transport."""
    agent = create_deep_agent(
        model=model,
        toolsets=[
            PrefixedToolset(
                MCPToolset(
                    StdioTransport(
                        command="npx",
                        args=["-y", "tavily-mcp@latest"],
                        env={"TAVILY_API_KEY": os.getenv("TAVILY_API_KEY")},
                    ),
                    max_retries=3,
                ),
                prefix="tavily",
            ),
        ],
    )

    deps = DeepAgentDeps(backend=StateBackend())
    result = await agent.run("Search for the latest news on AI", deps=deps)
    print(result.output)


if __name__ == "__main__":
    asyncio.run(tavily_mcp_via_toolset())
