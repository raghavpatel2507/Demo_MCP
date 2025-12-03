import json
import os
import logging
import base64
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

from claude_agent_sdk import (
    ClaudeAgentOptions,
    HookMatcher,
    HookContext,
)
from claude_agent_sdk.types import (
    McpServerConfig,
    McpStdioServerConfig,
    McpHttpServerConfig,
)

logger = logging.getLogger(__name__)

async def save_image_hook(
    input_data: Dict[str, Any],
    tool_use_id: Optional[str],
    context: HookContext
) -> Dict[str, Any]:
    """
    Post-tool-use hook to intercept and save base64 images from tool results.
    """
    tool_name = input_data.get("tool_name")
    tool_result = input_data.get("tool_result", {})
    
    # Check if result has content
    content = tool_result.get("content", [])
    if not content:
        return {}
        
    modified_content = []
    has_changes = False
    
    for item in content:
        if item.get("type") == "image" and "data" in item:
            try:
                data = item["data"]
                # Threshold check (optional, but good practice)
                if len(data) > 1000: 
                    os.makedirs("screenshots", exist_ok=True)
                    filename = f"screenshot_{uuid.uuid4()}.png"
                    filepath = os.path.join("screenshots", filename)
                    
                    with open(filepath, "wb") as f:
                        f.write(base64.b64decode(data))
                        
                    # Replace data with file path reference for the agent context
                    # We return a modified result to the agent
                    modified_item = item.copy()
                    modified_item["data"] = f"[Image saved to {os.path.abspath(filepath)}]"
                    modified_item["saved_to"] = os.path.abspath(filepath)
                    modified_content.append(modified_item)
                    has_changes = True
                    logger.info(f"Saved image from tool {tool_name} to {filepath}")
                    continue
            except Exception as e:
                logger.error(f"Failed to save image in hook: {e}")
                
        modified_content.append(item)
        
    if has_changes:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "modifiedResult": {
                    "content": modified_content,
                    "is_error": tool_result.get("is_error", False)
                }
            }
        }
        
    return {}

def load_sdk_options(config_path: str = "mcp_config.json") -> ClaudeAgentOptions:
    """
    Load SDK options from mcp_config.json and environment.
    """
    mcp_servers: Dict[str, McpServerConfig] = {}
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            for server in config.get("mcp_servers", []):
                if not server.get("enabled", False):
                    continue
                    
                name = server.get("name")
                server_type = server.get("type")
                
                if server_type == "node" or server_type == "python":
                    # Map to Stdio config
                    cmd = server.get("command")
                    args = server.get("args", [])
                    env = server.get("env", {})
                    
                    # Resolve env vars
                    resolved_env = {}
                    for k, v in env.items():
                        if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                            env_var = v[2:-1]
                            val = os.getenv(env_var)
                            if val:
                                resolved_env[k] = val
                        else:
                            resolved_env[k] = v
                            
                    # Merge with current env
                    full_env = os.environ.copy()
                    full_env.update(resolved_env)
                    
                    mcp_servers[name] = {
                        "command": cmd,
                        "args": args,
                        "env": full_env
                    }
                    
                elif server_type == "httpx":
                    # Map to HTTP config
                    url = server.get("url")
                    headers = server.get("headers", {})
                    
                    # Resolve headers env vars
                    resolved_headers = {}
                    for k, v in headers.items():
                        if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                            env_var = v[2:-1]
                            val = os.getenv(env_var)
                            if val:
                                resolved_headers[k] = val
                        else:
                            resolved_headers[k] = v
                            
                    mcp_servers[name] = {
                        "type": "http",
                        "url": url,
                        "headers": resolved_headers
                    }
                    
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            
    # Load tool defaults
    tool_defaults = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                for server in config.get("mcp_servers", []):
                    if server.get("enabled", False) and "tool_defaults" in server:
                        # Map server name to its defaults
                        # Note: We need to know which tools belong to which server.
                        # The SDK names tools as mcp__{server_name}__{tool_name}
                        server_name = server.get("name")
                        defaults = server.get("tool_defaults", {})
                        
                        # Resolve env vars in defaults
                        resolved_defaults = {}
                        for k, v in defaults.items():
                            if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                                env_var = v[2:-1]
                                val = os.getenv(env_var)
                                if val:
                                    resolved_defaults[k] = val
                            else:
                                resolved_defaults[k] = v
                        
                        tool_defaults[server_name] = resolved_defaults
        except Exception:
            pass

    async def inject_defaults_hook(
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: HookContext
    ) -> Dict[str, Any]:
        """
        Pre-tool-use hook to inject default arguments.
        """
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        
        # Check if this tool belongs to a server with defaults
        # Tool name format: mcp__{server_name}__{tool_name}
        if tool_name.startswith("mcp__"):
            parts = tool_name.split("__")
            if len(parts) >= 3:
                server_name = parts[1]
                if server_name in tool_defaults:
                    defaults = tool_defaults[server_name]
                    # Inject defaults if not present
                    updated_input = tool_input.copy()
                    for k, v in defaults.items():
                        if k not in updated_input:
                            updated_input[k] = v
                            
                    return {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "toolInput": updated_input
                        }
                    }
        return {}

    # Configure Hooks
    hooks = {
        "PreToolUse": [
            HookMatcher(hooks=[inject_defaults_hook]),
        ],
        "PostToolUse": [
            HookMatcher(hooks=[save_image_hook])
        ]
    }
            
    return ClaudeAgentOptions(
        mcp_servers=mcp_servers,
        hooks=hooks,
        permission_mode="bypassPermissions",
    )
