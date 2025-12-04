"""
AgentSphere-AI Main Entry Point

Simple chat interface with:
- Anthropic SDK integration
- MCP server integration (GitHub)
- Streaming responses with progress indicators
"""

import asyncio
import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv
import anthropic
from src.core.mcp.manager import MCPManager
from src.utils.ui import ToolProgress


load_dotenv()

async def main():
    """Main async function for continuous chat."""
    
    print("=" * 60)
    print("🤖 AgentSphere-AI - Anthropic & MCP Interface")
    print("=" * 60)
    print()

    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found in .env file.")
        print("Please add your Anthropic API key to the .env file.")
        return


    client = anthropic.AsyncAnthropic(api_key=api_key)
    
    
    print("🔄 Initializing MCP Manager...")
    mcp_manager = MCPManager()
    tool_progress = ToolProgress()
    await mcp_manager.initialize()
    
    
    tools = mcp_manager.registry.get_tool_schemas()
    print(f"✅ Initialized {len(tools)} tools")
    
    print(f"✅ Application initialized")
    print()
    print("Commands:")
    print("  /exit - Exit the chat")
    print()
    
    
    messages: List[Dict[str, Any]] = []
    
   
    while True:
        try:
       
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
        
            if user_input.lower() == "/exit":
                print("\n👋 Goodbye!\n")
                break
            
            messages.append({"role": "user", "content": user_input})
            
            
            try:
                tool_progress.show_status("🤖 Assistant is thinking...")
                
                # Use streaming API
                async with client.messages.stream(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=4096,
                    tools=tools,
                    messages=messages
                ) as stream:
                    
                    # Track current state
                    current_text = ""   
                    assistant_content = []
                    text_started = False
                    
                    # Process stream events
                    async for event in stream:
                        # Text delta - stream it in real-time
                        if event.type == "content_block_start":
                            if event.content_block.type == "text":
                                if not text_started:
                                    print("\n" + "=" * 60)
                                    print("🤖 Assistant Response:")
                                    print("=" * 60 + "\n")
                                    text_started = True
                        
                        elif event.type == "content_block_delta":
                            if hasattr(event.delta, "text"):
                                # Stream text character by character
                                print(event.delta.text, end="", flush=True)
                                current_text += event.delta.text
                    
                    # Get final message
                    final_message = await stream.get_final_message()
                    messages.append({"role": "assistant", "content": final_message.content})
                    
                    # Handle tool use if needed
                    while final_message.stop_reason == "tool_use":
                        if text_started:
                            print("\n")  # New line after text
                        
                        tool_results = []
                        
                        for block in final_message.content:
                            if block.type == "tool_use":
                                tool_name = block.name
                                tool_input = block.input
                                tool_use_id = block.id
                                
                                try:
                                    result = await tool_progress.run_with_progress(
                                        tool_name, 
                                        mcp_manager.call_tool(tool_name, tool_input)
                                    )
                                    tool_result_content = str(result)
                                except Exception as e:
                                    tool_result_content = f"Error executing tool: {str(e)}"
                                
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": tool_result_content
                                })
                        
                        messages.append({
                            "role": "user",
                            "content": tool_results
                        })
                        
                        # Stream the next response after tool execution
                        text_started = False
                        async with client.messages.stream(
                            model="claude-haiku-4-5-20251001",
                            max_tokens=4096,
                            tools=tools,
                            messages=messages
                        ) as stream:
                            
                            async for event in stream:
                                if event.type == "content_block_start":
                                    if event.content_block.type == "text":
                                        if not text_started:
                                            print("\n" + "=" * 60)
                                            print("🤖 Assistant Response:")
                                            print("=" * 60 + "\n")
                                            text_started = True
                                
                                elif event.type == "content_block_delta":
                                    if hasattr(event.delta, "text"):
                                        print(event.delta.text, end="", flush=True)
                            
                            final_message = await stream.get_final_message()
                            messages.append({"role": "assistant", "content": final_message.content})
                
                print("\n" + "=" * 60)
                print()
                
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")
                import traceback
                traceback.print_exc()
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!\n")
            break
        
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")

    
    await mcp_manager.cleanup()

def sync_main():
    """Synchronous wrapper for async main."""
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    sync_main()
