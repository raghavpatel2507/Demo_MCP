# AgentSphere-AI - Simplified (No Database)

## Overview

This is a simplified version of AgentSphere-AI with all database and checkpointer functionality removed. The application now runs in **stateless mode** with in-memory conversation state.


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
- And more...

## Troubleshooting

### API Key Errors
Make sure your `.env` file is in the project root and contains valid API keys.

### MCP Server Errors
Check that MCP servers are properly configured in `mcp_config.json` and required dependencies are installed.

