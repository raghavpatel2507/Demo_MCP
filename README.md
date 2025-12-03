# AgentSphere-AI - Simplified (No Database)

## Overview

This is a simplified version of AgentSphere-AI with all database and checkpointer functionality removed. The application now runs in **stateless mode** with in-memory conversation state.

## What Changed



## Running the Application

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Set up environment variables:**
   Create a `.env` file with your API keys:
   ```env
   # LLM Configuration
   GEMINI_API_KEY=your_gemini_api_key
   
   # MCP Server Configurations
   GITHUB_MCP_TOKEN=your_github_token
   GITHUB_USERNAME=your_github_username
   YOUTUBE_API_KEY=your_youtube_key
   # ... other MCP server keys
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

## Usage

- Type your messages and press Enter
- Type `/exit` to quit
- Conversation history is maintained in-memory during the session
- History is lost when you restart the application

## Architecture

```
main.py (Simple chat loop)
  ↓
supervisor.py (Agent orchestration)
  ↓
Dynamic Agents (MCP-based experts)
  ↓
MCP Servers (GitHub, YouTube, Gmail, etc.)
```

## MCP Servers

The application supports multiple MCP servers configured in `mcp_config.json`:

- **GitHub**: Repository management, issues, PRs
- **YouTube**: Video search and data
- **Gmail**: Email operations
- **Notion**: Workspace management
- **Google Drive**: File management
- **Discord**: Messaging
- **PowerPoint**: Presentation creation
- And more...

## Notes

- **No persistence**: Conversations are not saved between sessions
- **No HITL**: Tools execute immediately without approval prompts
- **Stateless**: Each restart starts fresh
- **In-memory**: All state is kept in memory during runtime

## Troubleshooting

### Token Limit Errors
If you get token limit errors, restart the application to clear conversation history.

### API Key Errors
Make sure your `.env` file is in the project root and contains valid API keys.

### MCP Server Errors
Check that MCP servers are properly configured in `mcp_config.json` and required dependencies are installed.
