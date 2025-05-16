#!/usr/bin/env python3
"""
Test script to verify FastAgent functionality with JSON config loading.
"""

import asyncio
from typing import Dict

from mcp_agent.core.fastagent import FastAgent

# Sample JSON config for MCP
sample_json_config = {
    "mcp": {
        "servers": {
            "fetch": {
                "name": "fetch",
                "description": "A server for fetching links",
                "transport": "stdio",
                "command": "uvx",
                "args": ["mcp-server-fetch"]
            }
        }
    },
    "default_model": "haiku",   
    "logger": {
        "level": "debug",
        "type": "console"
    },
    "anthropic": {
          "api_key": "key"
      }
}

fast = FastAgent(
        name="json_config_test", 
        json_config=sample_json_config,
        parse_cli_args=False
    )

@fast.agent(instruction="You are a helpful AI Agent", servers=["fetch"])
async def main():
    """Test initializing FastAgent with JSON config in interactive mode."""
    print("Testing FastAgent initialization with JSON config...")
    
    # Create FastAgent instance with JSON config
    # parse_cli_args=False to ensure we don't try to parse command line args in test mode
    
    
    # Register a simple agent
    async with fast.run() as agent:
        await agent.interactive()
if __name__ == "__main__":
    asyncio.run(main())