"""
AgentSphere-AI Main Entry Point

Simple chat interface with:
- Anthropic SDK integration
- MCP server integration (GitHub)
"""

import asyncio
import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv
import anthropic
from src.core.mcp.manager import MCPManager


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
                print("🤖 Assistant is thinking...")
                response = await client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=4096,
                    tools=tools,
                    messages=messages
                )
                
                
                final_content = []
                
                
                while response.stop_reason == "tool_use":
                   
                    messages.append({"role": "assistant", "content": response.content})
                    
                    tool_results = []
                    
                    for block in response.content:
                        if block.type == "tool_use":
                            tool_name = block.name
                            tool_input = block.input
                            tool_use_id = block.id
                            
                            print(f"🛠️  Executing tool: {tool_name}")
                            
                            try:
                               
                                result = await mcp_manager.call_tool(tool_name, tool_input)
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
                    
                    
                    response = await client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=4096,
                        tools=tools,
                        messages=messages
                    )

               
                messages.append({"role": "assistant", "content": response.content})
                
                
                print("\n" + "=" * 60)
                print("🤖 Assistant Response:")
                print("=" * 60)
                
                for block in response.content:
                    if block.type == "text":
                        print(f"\n{block.text}\n")
                
                print("=" * 60)
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
