"""
AI Connectivity Diagnostic Agent
--------------------------------
This module defines an interactive AI agent that diagnoses network connectivity
issues by orchestrating system-level tools (ping, tracert, nslookup, ipconfig, etc.)
through the OpenAI Responses API.

Features
--------
- Provides a REPL loop where users can interact with the agent.
- Executes system commands to test connectivity, routing, and DNS resolution.
- Supports helper tools for math evaluation and mock weather data.
- Demonstrates integration of function tools with AI responses.

Usage
-----
Run directly from the command line:

    python agent.py

Then interact with the agent in the REPL:

    >>> How is the connection to google ?
    >>> Describe the connectivity to www.amazon.com. Be exhaustive.
    >>> Which host has the faster connection, www.wikipedia.org or www.bing.com ?
    >>> quit
"""

import subprocess
import platform
import json
from typing import List, Dict, Any
from openai import OpenAI
from openai.types.responses import Response
from openai.types.responses.function_tool_param import FunctionToolParam
from openai.types.responses import ResponseInputParam

# ---------------------------
# GLOBALS
# ---------------------------
Message = Dict[str, Any]
MODEL = "gpt-4.1-mini"
client = OpenAI()


# ---------------------------
# TOOLS
# ---------------------------
def ping_tool(host: str) -> Dict[str, Any]:
    count_flag = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        result = subprocess.run(
            ["ping", count_flag, "1", host], capture_output=True, text=True, timeout=4
        )
        return {
            "host": host,
            "success": result.returncode == 0,
            "output": result.stdout.strip(),
        }
    except Exception as e:
        return {"host": host, "error": str(e)}


def tracert_tool(host: str) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            ["tracert", "-d -h 4 -w 2000", host],
            capture_output=True,
            text=True,
            timeout=20,
        )
        return {
            "host": host,
            "success": result.returncode == 0,
            "output": result.stdout.strip(),
        }
    except Exception as e:
        return {"host": host, "error": str(e)}


def nslookup_tool(host: str) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            ["nslookup", host], capture_output=True, text=True, timeout=4
        )
        return {
            "host": host,
            "success": result.returncode == 0,
            "output": result.stdout.strip(),
        }
    except Exception as e:
        return {"host": host, "error": str(e)}


def ipconfig_tool() -> Dict[str, Any]:
    try:
        result = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=4)
        return {"success": result.returncode == 0, "output": result.stdout.strip()}
    except Exception as e:
        return {"error": str(e)}


def routing_table_tool() -> Dict[str, Any]:
    try:
        result = subprocess.run(
            ["netstat", "-r"], capture_output=True, text=True, timeout=4
        )
        return {"success": result.returncode == 0, "output": result.stdout.strip()}
    except Exception as e:
        return {"error": str(e)}


def ports_tool() -> Dict[str, Any]:
    try:
        result = subprocess.run(
            ["netstat", "-an"], capture_output=True, text=True, timeout=4
        )
        return {"success": result.returncode == 0, "output": result.stdout.strip()}
    except Exception as e:
        return {"error": str(e)}





TOOLS: Dict[str, Any] = {
    "ping": ping_tool,
    "tracert": tracert_tool,
    "nslookup": nslookup_tool,
    "ipconfig": ipconfig_tool,
    "ports": ports_tool,
    "routing_table": routing_table_tool,

}

# ---------------------------
# TOOL DEFINITIONS
# ---------------------------
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


# ---------------------------
# HELPERS
# ---------------------------
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


def print_message(resp) -> None:
    """Print a message from the model in a readable format."""
    content_list = getattr(resp, "content", [])
    if content_list and hasattr(content_list[0], "text"):
        msg_text = content_list[0].text
        print("\n🤖 Assistant:", msg_text)


def get_call_params(resp):
    """Extract tool call name and arguments from a function_call response block."""
    tool_name = getattr(resp, "name", None)
    raw_args = getattr(resp, "arguments", "{}")
    args = raw_args if isinstance(raw_args, dict) else parse_tool_arguments(raw_args)
    return tool_name, args


# ---------------------------
# UNIFIED REPL LOOP
# ---------------------------
def run_agent() -> None:
    last_response_id = None
    print("🤖 AI Agent REPL — type 'exit' to quit.\n")

    while True:
        user_input = input(">>> ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break

        # Start with user message
        input_queue: ResponseInputParam = [
            {"type": "message", "role": "user", "content": user_input},
            {
                "type": "message",
                "role": "system",
                "content": "You are a helpful assistant that is expert in network connectivity.",
            },
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

                # Regular assistant messages
                if resp_type == "message":
                    print_message(resp)

                # Tool / function calls
                elif resp_type == "function_call":
                    tool_name, args = get_call_params(resp)

                    print(f"\n[Tool Call] {tool_name}({args})")
                    result = dispatch_tool(tool_name, args)
                    print(f"[Tool Result] {result}\n")

                    # Feed tool result back to model
                    input_queue.append(
                        {
                            "type": "function_call_output",
                            "call_id": resp.call_id,
                            "output": str(result),
                        }
                    )


# ---------------------------
# RUN
# ---------------------------
if __name__ == "__main__":
    run_agent()
