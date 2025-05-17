# PubSub Integration Plan

## Overview

This plan outlines the approach for implementing a pub/sub messaging system for FastAgent output. Instead of displaying output directly to the terminal, we'll channel all messages through a pub/sub system where clients can subscribe to agent channels.

## Key Requirements

1. Each FastAgent instance should have its own pub/sub channel for messages
2. All console output currently shown to the user should be sent to the pub/sub channel
3. User can send messages to the channel as input (as in agent.interactive() mode)
4. Existing features and workflows should be maintained

## Integration Points

Based on our code analysis, we've identified the following key integration points:

### 1. ConsoleDisplay Class
- Central point for all UI display logic
- Methods: `show_assistant_message`, `show_user_message`, `show_tool_result`, `show_tool_call`
- Integration: Modify to publish to pub/sub channel in addition to console output

### 2. AugmentedLLM Class
- Uses ConsoleDisplay to render output
- Drives the interaction between agents and display
- Integration: Connect to pub/sub manager and ensure messages flow through channels

### 3. FastAgent Class
- Main entry point for running agents
- Integration: Initialize pub/sub channels during startup

### 4. Agent/BaseAgent Class
- Handles user interaction and tool calling
- Integration: Send all interaction messages through pub/sub

### 5. MCPConnectionManager
- Manages server connections
- Integration: Potentially use for pub/sub client connections

## Implementation Strategy

### Phase 1: Minimal Viable Change

1. **Create PubSubDisplay Adapter**
   - Create a wrapper around ConsoleDisplay that sends output to both console and pub/sub
   - Minimal changes to existing code structure
   - Allow toggling between console-only and pub/sub modes

2. **Modify AugmentedLLM**
   - Add PubSub channel initialization in constructor
   - Initialize display with pub/sub capability
   - Pass agent identifier to channel

3. **Agent Channel Management**
   - Ensure each FastAgent instance has a unique channel ID
   - Add channel management to FastAgent initialization

### Phase 2: Enhanced Integration

1. **Add Interactive Mode via PubSub**
   - Modify agent.interactive() to listen for input from pub/sub
   - Handle streaming responses through pub/sub channels

2. **Standardize Message Formats**
   - Define clear message schemas for different types (user, assistant, tool calls, etc.)
   - Ensure compatibility with both console rendering and client applications

3. **Add Client Connection Management**
   - Track active client connections
   - Implement reconnection logic
   - Handle client-specific state

### Phase 3: Client API and Documentation

1. **Create Client API**
   - Implement helper functions/classes for client applications
   - Document message formats and subscription patterns

2. **Add Configuration Options**
   - PubSub-specific settings in config files
   - Support for different transport mechanisms

## Code Changes Required

### 1. ConsoleDisplay Modifications

```python
# ui/console_display.py
class ConsoleDisplay:
    def __init__(self, config=None, pubsub_enabled=False) -> None:
        # Add pubsub support
        self.pubsub_enabled = pubsub_enabled
        self.pubsub_channel = None
        self.pubsub_manager = None
        if pubsub_enabled:
            from mcp_agent.mcp.pubsub import get_pubsub_manager
            self.pubsub_manager = get_pubsub_manager()

    def set_pubsub_channel(self, channel_id):
        """Set the pubsub channel for this display"""
        if self.pubsub_enabled and self.pubsub_manager:
            self.pubsub_channel = self.pubsub_manager.get_or_create_channel(channel_id)

    async def show_assistant_message(self, message_text, aggregator=None, highlight_namespaced_tool="", title="ASSISTANT", name=None) -> None:
        # Original console display
        if self.config and self.config.logger.show_chat:
            # ... existing display code ...
            
        # PubSub publishing
        if self.pubsub_enabled and self.pubsub_channel:
            from mcp_agent.mcp.pubsub_formatter import PubSubFormatter
            message = PubSubFormatter.format_assistant_message(
                message_text, channel_id=self.pubsub_channel.channel_id, 
                metadata={"highlight_tool": highlight_namespaced_tool, "name": name}
            )
            await self.pubsub_channel.publish(message)
```

### 2. AugmentedLLM Modifications

```python
# llm/augmented_llm.py
def __init__(self, provider, agent=None, server_names=None, ...) -> None:
    # ... existing initialization ...
    
    # Initialize the display component with pubsub support
    pubsub_enabled = getattr(self.context.config, "pubsub_enabled", False)
    self.display = ConsoleDisplay(config=self.context.config, pubsub_enabled=pubsub_enabled)
    
    # Set pubsub channel if enabled
    if pubsub_enabled and agent:
        channel_id = f"agent_{agent.name}"
        self.display.set_pubsub_channel(channel_id)
```

### 3. FastAgent Modifications

```python
# core/fastagent.py
@asynccontextmanager
async def run(self):
    # ... existing initialization ...
    
    # Initialize PubSub if enabled
    pubsub_enabled = getattr(self.context.config, "pubsub_enabled", False)
    if pubsub_enabled:
        from mcp_agent.mcp.pubsub_diagnostic import instrument_key_components
        instrument_key_components()
    
    # ... rest of the method ...
```

### 4. Agent Input Handling

```python
# agents/base_agent.py
async def prompt(self, default_prompt: str = "") -> str:
    """Start an interactive prompt session with the agent."""
    # ... existing code ...
    
    # Check for pubsub mode
    pubsub_enabled = getattr(self.context.config, "pubsub_enabled", False)
    if pubsub_enabled:
        return await self._pubsub_interactive_prompt(default_prompt)
    
    # ... existing terminal prompt code ...

async def _pubsub_interactive_prompt(self, default_prompt: str = "") -> str:
    """Interactive prompt using pubsub for communication."""
    # Implementation will handle subscribing to messages from clients
    # and publishing responses back
```

## Testing Strategy

1. **Unit Tests**
   - Test PubSub message formatting
   - Test channel creation and management
   - Test message publishing and subscription

2. **Integration Tests**
   - Test complete workflow from user input to agent response
   - Test parallel agents with separate channels
   - Test reconnection scenarios

3. **Manual Testing**
   - Create simple client application that connects via PubSub
   - Test interactive mode with real-time responses

## Rollout Plan

1. **Phase 1**: Implement basic pub/sub integration with console output preserved
   - Add configuration toggle to enable/disable pub/sub
   - Default to console-only mode for backward compatibility

2. **Phase 2**: Add interactive mode via pub/sub
   - Create example client application
   - Document API for client integration

3. **Phase 3**: Full pub/sub implementation
   - Support client reconnection
   - Add advanced features (history tracking, multiple subscriptions)

## Conclusion

The proposed implementation provides a clean way to integrate pub/sub messaging while maintaining compatibility with existing code. By wrapping the ConsoleDisplay component and making minimal changes to the agent and LLM implementation, we can add pub/sub support with low risk of breaking existing functionality.