"""
AI Connectivity Diagnostic Agent
................................
This module defines an interactive AI agent that diagnoses network connectivity
issues by orchestrating system-level tools (ping, tracert, nslookup, ipconfig, etc.)
through the OpenAI Responses API.

Features
........
- Provides a REPL loop where users can interact with the agent.
- Executes system commands to test connectivity, routing, and DNS resolution.
- Supports helper tools for math evaluation and mock weather data.
- Demonstrates integration of function tools with AI responses.

- An OpenAI API key is required to run this code.

Usage
.....
Run directly from the command line:

    python agent.py

Then interact with the agent in the REPL:

    >>> How is the connection to google ?
    >>> Describe the connectivity to www.amazon.com. Be exhaustive.
    >>> Which host has the faster connection, www.wikipedia.org or www.bing.com ?
    >>> exit
"""

import subprocess
import json
from functools import partial
from typing import List, Dict, Any
from openai import OpenAI
from openai.types.responses import Response, ResponseInputParam, ResponseOutputItem
from openai.types.responses.function_tool_param import FunctionToolParam

# ...........................
# GLOBALS
# ...........................
MODEL = "gpt-5.1"
# Valid Model Options:
#     "gpt-5.1"
#     "gpt-5.1-mini"
#     "gpt-4.1"
#     "gpt-4.1-mini"

Message = Dict[str, Any]
client = OpenAI()


# ...........................
# TOOL HELPER
# ...........................
def run_command(func_call: List[str], host: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    """
    Run a command-line tool with optional host argument.

    Parameters
    ..........
    func_call : list of str
        The base command and flags to execute.
    host : str, optional
        Hostname or IP address to append to the command.
    timeout : int, optional
        Timeout in seconds. Defaults to 8 if host is provided, else 4.

    Returns
    .......
    dict
        Result dictionary containing:
        - 'success': True if command succeeded, False otherwise
        - 'output': stdout from the command
        - 'error': error message if execution failed
        - 'host': included only if a host argument was provided
    """
    if host:
        func_call = func_call + [host]
    if timeout is None:
        timeout = 8 if host else 4

    try:
        print(f"[DEBUG: Run_Command]  {' '.join(func_call)} with timeout {timeout}s")
        result = subprocess.run(func_call, capture_output=True, text=True, timeout=timeout)
        output = {"success": result.returncode == 0, "output": result.stdout.strip()}
        if host:
            output["host"] = host
        return output
    except Exception as e:
        error = {"error": str(e)}
        if host:
            error["host"] = host
        return error

# ...........................
# TOOLS
# ...........................
# ping_tool = partial(run_command, ["ping", "-n", "4"])  # linux use "-c"
# ports_tool = partial(run_command, ["netstat", "-an"])
# tracert_tool = partial(run_command, ["tracert", "-d", "-h", "4", "-w", "2000"])
# nslookup_tool = partial(run_command, ["nslookup"])
# ipconfig_tool = partial(run_command, ["ipconfig"])
# routing_table_tool = partial(run_command, ["netstat", "-r"])


# Mapping of tool names to their implementations
TOOLS: Dict[str, Any] = {
    "ping": partial(run_command, ["ping", "-n", "4"]),  # linux use "-c"
    "curl": partial(run_command, ["curl", "-I"]),
    "ports": partial(run_command, ["netstat", "-an"]),
    "tracert": partial(run_command, ["tracert", "-d", "-h", "4", "-w", "2000"]),
    "nslookup": partial(run_command, ["nslookup"]),
    "ipconfig": partial(run_command, ["ipconfig"]),
    "routing_table": partial(run_command, ["netstat", "-r"]),
}
# TOOLS: Dict[str, Any] = {
#     "ping": ping_tool,
#     "ports": ports_tool,
#     "tracert": tracert_tool,
#     "nslookup": nslookup_tool,
#     "ipconfig": ipconfig_tool,
#     "routing_table": routing_table_tool,
# }

# ...........................
# TOOL DEFINITIONS
# ...........................
TOOLS_DEF: List[FunctionToolParam] = [
    {
        "name": "ping",
        "type": "function",
        "description": "Ping a host to check network connectivity.",
        "parameters": {
            "type": "object",
            "properties": {"host": {"type": "string"}},
            "required": ["host"],
        },
        "strict": False,
    },
    {
        "name": "curl",
        "type": "function",
        "description": "fetch the HTTP headers from a host.",
        "parameters": {
            "type": "object",
            "properties": {"host": {"type": "string"}},
            "required": ["host"],
        },
        "strict": False,
    },
    {
        "name": "tracert",
        "type": "function",
        "description": "track the route that data packets take as they travel from this computer to another host.",
        "parameters": {
            "type": "object",
            "properties": {"host": {"type": "string"}},
            "required": ["host"],
        },
        "strict": False,
    },
    {
        "name": "nslookup",
        "type": "function",
        "description": "Check if DNS is working.",
        "parameters": {
            "type": "object",
            "properties": {"host": {"type": "string"}},
            "required": ["host"],
        },
        "strict": False,
    },
    {
        "name": "ipconfig",
        "type": "function",
        "description": "Return the IP address, subnet mask and default gateway for each adapter bound to TCP/IP.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
        "strict": False,
    },
    {
        "name": "routing_table",
        "type": "function",
        "description": "Display the routing table.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
        "strict": False,
    },
    {
        "name": "ports",
        "type": "function",
        "description": "Display all connections and listening ports in numerical form.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
        "strict": False,
    },
]


# ...........................
# AGENT HELPERS
# ...........................
def parse_tool_arguments(arg_string: str) -> Dict[str, Any]:
    """
    Parse a JSON string of tool arguments into a Python dictionary.
    """
    if not arg_string:
        return {}
    try:
        return json.loads(arg_string)
    except json.JSONDecodeError:
        print("[WARN] Model returned invalid JSON for tool arguments.")
        return {}


def dispatch_tool(tool_name: str | None, args: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch a tool call to the appropriate function."""

    if tool_name not in TOOLS:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        return TOOLS[tool_name](**args)
    except Exception as e:
        return {"error": f"Tool execution failed: {e}"}


def print_message(resp: ResponseOutputItem) -> None:
    """Print a message from the model in a readable format."""
    content_list = getattr(resp, "content", [])
    if content_list and hasattr(content_list[0], "text"):
        msg_text = content_list[0].text
        print("\n🤖 Assistant:", msg_text)


def get_call_params(resp: ResponseOutputItem) -> tuple[str | None, Dict[str, Any]]:
    """Extract tool call name and arguments from a function_call response block."""
    tool_name = getattr(resp, "name", None)
    raw_args = getattr(resp, "arguments", "{}")
    args = raw_args if isinstance(raw_args, dict) else parse_tool_arguments(raw_args)
    return tool_name, args


# ...........................
#  AGENT REPL
# ...........................
def run_agent() -> None:
    last_response_id = None
    print("🤖 AI Connectivity Agent — type 'exit' to quit.\n")

    while True:
        user_input = input(">>> ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break

        input_queue: ResponseInputParam = [
            {"type": "message", "role": "user", "content": user_input},
        ]

        # Loop until the model produces no more tool calls
        while input_queue:
            response: Response = client.responses.create(
                model=MODEL,
                input=input_queue,
                tools=TOOLS_DEF,
                previous_response_id=last_response_id,
            )
            last_response_id = response.id

            input_queue = []
            for resp in getattr(response, "output", []):
                resp_type = getattr(resp, "type", None)

                # Print regular assistant messages
                if resp_type == "message":
                    print_message(resp)

                # Call a Tool
                elif resp_type == "function_call":
                    tool_name, args = get_call_params(resp)

                    print(f"\n[DEBUG: Tool Call] {tool_name}({args})")
                    result = dispatch_tool(tool_name, args)
                    print(f"[DEBUG: Tool Result] {result}\n")

                    # Feed tool result back to model
                    input_queue.append(
                        {
                            "type": "function_call_output",
                            "call_id": resp.call_id,
                            "output": str(result),
                        }
                    )


if __name__ == "__main__":
    run_agent()
