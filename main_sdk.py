import asyncio
import os
import sys
from dotenv import load_dotenv
from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock, ToolUseBlock, ToolResultBlock

from src.core.sdk_config import load_sdk_options
from src.utils.ui import ToolProgress

# Load environment variables
load_dotenv()

async def main():
    print("=" * 60)
    print("🤖 AgentSphere-AI - Claude Agent SDK Interface")
    print("=" * 60)
    print()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found in .env file.")
        return

    print("🔄 Loading configuration...")
    options = load_sdk_options()
    
    # Initialize Client and ToolProgress
    tool_progress = ToolProgress()
    async with ClaudeSDKClient(options=options) as client:
        print("✅ Client initialized and connected to MCP servers")
        print()
        print("Commands:")
        print("  /exit - Exit the chat")
        print("  /interrupt - Interrupt current task")
        print()

        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
            
                if user_input.lower() == "/exit":
                    print("\n👋 Goodbye!\n")
                    break
                
                if user_input.lower() == "/interrupt":
                    await client.interrupt()
                    continue

                # Send query
                tool_progress.show_status("🤖 Assistant is thinking...")
                await client.query(user_input)

                # Process response stream
                current_tool = None
                text_started = False
                
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                # Show header for first text block
                                if not text_started:
                                    print("\n" + "=" * 60)
                                    print("🤖 Assistant Response:")
                                    print("=" * 60 + "\n")
                                    text_started = True
                                
                                # Stream text character by character (like main.py)
                                for char in block.text:
                                    print(char, end="", flush=True)
                                    await asyncio.sleep(0.01)  # Smooth streaming effect
                                
                            elif isinstance(block, ToolUseBlock):
                                # Start progress spinner for this tool
                                if text_started:
                                    print()  # New line after text
                                current_tool = block.name
                                tool_progress.start(block.name)
                                
                            elif isinstance(block, ToolResultBlock):
                                # Stop progress spinner when tool completes
                                if current_tool:
                                    tool_progress.stop()
                                    current_tool = None
                                    text_started = False  # Reset for next text block
                
                # Ensure spinner is stopped
                if current_tool:
                    tool_progress.stop()
                    
                if text_started:
                    print()  # Final newline
                print("=" * 60)
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user. Goodbye!\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
