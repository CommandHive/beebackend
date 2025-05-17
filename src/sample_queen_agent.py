#!/usr/bin/env python3
"""
Test script to verify FastAgent functionality with JSON config loading.
"""

import asyncio
import json
from typing import Dict
from rich import print as rich_print

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
        "level": "info",
        "type": "console"
    },
    "pubsub_enabled": True,
    "pubsub_config": {
        "use_redis": True,
        "channel_name": "agent_queen_agent",  # This must match the agent name or channel used for publishing
        "redis": {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "channel_prefix": "agent:"
        }
    },
    "anthropic": {
          "api_key": ""
      }
}


fast = FastAgent(
        name="agent_queen_agent",  # Changed name to match channel name used in publishing
        json_config=sample_json_config,
        parse_cli_args=False
    )

@fast.agent(instruction="You are a helpful AI Agent", servers=["fetch"])
async def main():
    """Test initializing FastAgent with JSON config in interactive mode."""
    print("Testing FastAgent initialization with JSON config...")
    
    # Create FastAgent instance with JSON config
    # parse_cli_args=False to ensure we don't try to parse command line args in test mode
    
    # Register a simple agent and keep it running
    async with fast.run() as agent:
        rich_print("[bold green]Agent running in Redis-only mode![/bold green]")
        rich_print(f"Waiting for messages on Redis channel: [cyan]agent:agent_queen_agent[/cyan]")
        rich_print(f"Responses will be published to channel: [cyan]agent:agent_queen_agent_response[/cyan]")
        rich_print("[bold]Press Ctrl+C to stop the agent...[/bold]")
        
        # Create a simple pubsub client for direct listening
        import redis.asyncio as aioredis
        import json
        
        # Create Redis client
        redis_client = aioredis.Redis(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=True
        )
        
        try:
            # Subscribe to the input channel
            pubsub = redis_client.pubsub()
            await pubsub.subscribe("agent:agent_queen_agent")
            
            # Keep running until interrupted
            while True:
                # Process Redis messages directly
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message and message.get('type') == 'message':
                    try:
                        # Process the message data
                        data = message.get('data')
                        if isinstance(data, bytes):
                            data = data.decode('utf-8')
                        
                        # Try to parse JSON
                        try:
                            data_obj = json.loads(data)
                            rich_print(f"[blue]Received message:[/blue] {data_obj}")
                            
                            # If this is a user message, extract content and send to agent
                            if data_obj.get('type') == 'user' and 'content' in data_obj:
                                user_input = data_obj['content']
                                rich_print(f"[yellow]Processing user input:[/yellow] {user_input}")
                                
                                # Send the message to the agent
                                response = await agent.send(user_input)
                                rich_print(f"[green]Agent response:[/green] {response}")
                                
                                # Publish response back to response channel
                                response_channel = "agent:agent_queen_agent_response"
                                # Get metadata from the original message
                                metadata = data_obj.get('metadata', {})
                                if not isinstance(metadata, dict):
                                    metadata = {}
                                    
                                # Add our metadata
                                metadata["source"] = "agent_queen_agent"
                                
                                response_data = {
                                    "type": "assistant",
                                    "content": response,
                                    "channel_id": data_obj.get('channel_id', 'agent_queen_agent'),
                                    "metadata": metadata
                                }
                                await redis_client.publish(response_channel, json.dumps(response_data))
                                rich_print(f"[blue]Published response to[/blue] [cyan]{response_channel}[/cyan]")
                        except json.JSONDecodeError:
                            rich_print(f"[red]Received non-JSON message:[/red] {data}")
                    except Exception as e:
                        rich_print(f"[bold red]Error processing Redis message:[/bold red] {e}")
                        import traceback
                        rich_print(f"[dim red]{traceback.format_exc()}[/dim red]")
                
                # Small delay to prevent CPU spike
                await asyncio.sleep(0.01)
                
        except asyncio.CancelledError:
            rich_print("[yellow]Agent was cancelled[/yellow]")
        except KeyboardInterrupt:
            rich_print("[yellow]Agent stopped by user[/yellow]")
        finally:
            # Clean up Redis connection
            if pubsub:
                await pubsub.unsubscribe("agent:agent_queen_agent")
            await redis_client.close()
            rich_print("[green]Agent shutdown complete[/green]")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        rich_print("\n[yellow]Agent stopped by user[/yellow]")