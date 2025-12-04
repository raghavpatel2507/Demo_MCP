import asyncio
from typing import Optional, Dict
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

class ToolProgress:
    """
    Handles visual progress indication for tool execution using Rich.
    Dynamically generates friendly messages from tool names.
    """
    
    # Action verb mapping for common operations
    ACTION_VERBS = {
        "search": "Searching",
        "list": "Listing",
        "read": "Reading",
        "get": "Fetching",
        "create": "Creating",
        "update": "Updating",
        "delete": "Deleting",
        "send": "Sending",
        "fetch": "Fetching",
        "download": "Downloading",
        "upload": "Uploading",
        "find": "Finding",
        "query": "Querying",
        "execute": "Executing",
        "run": "Running",
        "start": "Starting",
        "stop": "Stopping",
        "open": "Opening",
        "close": "Closing",
        "write": "Writing",
        "edit": "Editing",
        "modify": "Modifying",
        "remove": "Removing",
        "add": "Adding",
        "set": "Setting",
    }

    def __init__(self):
        self.console = Console()
        self.live: Optional[Live] = None
        
    def _parse_tool_name(self, tool_name: str) -> str:
        """
        Dynamically parse tool name to create a friendly message.
        
        Examples:
            github_search_repositories -> Searching GitHub repositories
            gmail_send_email -> Sending Gmail email
            mcp__github__create_repository -> Creating GitHub repository
            get_file_contents -> Fetching file contents
        """
        # Handle empty or very short names
        if not tool_name or len(tool_name) < 2:
            return f"Executing {tool_name}"
        
        # Handle SDK format: mcp__server__tool_name
        if tool_name.startswith("mcp__"):
            # Remove mcp__ prefix and split by double underscore
            parts = tool_name[5:].split("__", 1)  # Split only on first __ after mcp__
            if len(parts) == 2:
                service_name = parts[0].capitalize()
                # Now parse the actual tool name
                tool_parts = parts[1].replace('-', '_').split('_')
                tool_parts = [p for p in tool_parts if p]
                
                if not tool_parts:
                    return f"Using {service_name}"
                
                # Get action verb
                action = tool_parts[0]
                if action.lower() in self.ACTION_VERBS:
                    action_verb = self.ACTION_VERBS[action.lower()]
                else:
                    action_verb = f"{action.capitalize()}ing"
                
                # Get object
                object_parts = tool_parts[1:] if len(tool_parts) > 1 else []
                object_name = " ".join(object_parts) if object_parts else ""
                
                if object_name:
                    return f"{action_verb} {service_name} {object_name}"
                else:
                    return f"{action_verb} {service_name}"
        
        # Regular format: service_action_object or action_object
        parts = tool_name.replace('-', '_').split('_')
        parts = [p for p in parts if p]
        
        if not parts:
            return f"Executing {tool_name}"
        
        # Extract service name (first part if it looks like a service)
        service_name = ""
        action_parts = parts
        
        # Check if first part is a service name (e.g., github, gmail, slack)
        # Service names are typically lowercase and > 2 chars
        if len(parts) > 1 and parts[0].isalpha() and len(parts[0]) > 2:
            # Common service names
            known_services = ['github', 'gmail', 'slack', 'discord', 'notion', 'google', 'drive', 'calendar']
            if parts[0].lower() in known_services or not parts[0].lower() in self.ACTION_VERBS:
                service_name = parts[0].capitalize()
                action_parts = parts[1:]
        
        if not action_parts:
            # Only service name, no action
            return f"Using {service_name}" if service_name else f"Executing {tool_name}"
        
        # Find action verb (first part of remaining)
        action = action_parts[0]
        
        # Get the action verb or create a sensible default
        if action.lower() in self.ACTION_VERBS:
            action_verb = self.ACTION_VERBS[action.lower()]
        else:
            # For unknown actions, just capitalize without adding "ing"
            # This prevents "glob" -> "Globing"
            action_verb = f"{action.capitalize()}ing"
        
        # Get object (remaining parts)
        object_parts = action_parts[1:] if len(action_parts) > 1 else []
        object_name = " ".join(object_parts) if object_parts else ""
        
        # Construct message
        if service_name and object_name:
            return f"{action_verb} {service_name} {object_name}"
        elif service_name:
            return f"{action_verb} {service_name}"
        elif object_name:
            return f"{action_verb} {object_name}"
        else:
            return f"{action_verb}"
        
    def get_friendly_message(self, tool_name: str) -> str:
        """Get a friendly message for a tool."""
        message = self._parse_tool_name(tool_name)
        return f"{message}..."

    def start(self, tool_name: str):
        """Start the progress spinner."""
        message = self.get_friendly_message(tool_name)
        spinner = Spinner("dots", text=Text(f" {message}", style="cyan"))
        
        self.live = Live(
            spinner,
            console=self.console,
            refresh_per_second=10,
            transient=True
        )
        self.live.start()

    def stop(self):
        """Stop the progress spinner."""
        if self.live:
            self.live.stop()
            self.live = None

    def print_streaming_text(self, text: str, end: str = ""):
        """
        Print streaming text without interfering with spinners.
        Stops any active spinner, prints the text, then can restart if needed.
        """
        # If spinner is active, temporarily stop it
        was_active = self.live is not None
        if was_active:
            self.live.stop()
        
        # Print the text
        self.console.print(text, end=end)
        
    def show_status(self, message: str, style: str = "bold cyan"):
        """Show a status message (e.g., 'Assistant is thinking...')"""
        self.console.print(f"\n{message}", style=style)

    async def run_with_progress(self, tool_name: str, coro):
        """Run a coroutine with a progress spinner."""
        self.start(tool_name)
        try:
            return await coro
        finally:
            self.stop()

