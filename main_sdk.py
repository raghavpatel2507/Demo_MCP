import asyncio
import os
import sys
from dotenv import load_dotenv
from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock, ToolUseBlock, ToolResultBlock

from src.core.sdk_config import load_sdk_options

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
    
    # Initialize Client
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
                print("🤖 Assistant is thinking...")
                await client.query(user_input)

                # Process response stream
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                print(f"\n{block.text}\n")
                            elif isinstance(block, ToolUseBlock):
                                print(f"🛠️  Tool Use: {block.name}")
                            elif isinstance(block, ToolResultBlock):
                                # Usually we don't print raw tool results unless debugging
                                pass
                                
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
