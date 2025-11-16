import subprocess
import platform
import json
from typing import List, Dict, Any, Optional, TypeAlias, TypedDict
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
            ["ping", count_flag, "1", host],
            capture_output=True,
            text=True,
            timeout=4
        )
        return {"host": host, "success": result.returncode == 0, "output": result.stdout.strip()}
    except Exception as e:
        return {"host": host, "error": str(e)}
    

def nslookup_tool(host: str) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            ["nslookup", host],
            capture_output=True,
            text=True,
            timeout=4
        )
        return {"host": host, "success": result.returncode == 0, "output": result.stdout.strip()}
    except Exception as e:
        return {"host": host, "error": str(e)}
    
def ipconfig_tool() -> Dict[str, Any]:
    try:
        result = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True,
            timeout=4
        )
        return { "success": result.returncode == 0, "output": result.stdout.strip()}
    except Exception as e:
        return { "error": str(e)}

def calculator_tool(expression: str) -> Dict[str, Any]:
    try:
        allowed = {"__builtins__": {}}
        result = eval(expression, allowed, {})
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

def weather_tool(city: str) -> Dict[str, Any]:
    data = {"Boise": "Sunny, 42°F", "Seattle": "Rainy, 48°F", "Salt Lake": "Clear, 38°F"}
    return {"weather": data.get(city, "No data for that location.")}

TOOLS: Dict[str, Any] = {"ping": ping_tool, "nslookup": nslookup_tool, "ipconfig": ipconfig_tool, "calculate": calculator_tool, "weather": weather_tool}

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
        "strict": False
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
        "strict": False
    },
    {
        "name": "ipconfig",
        "type": "function",
        "description": "Return the IP address, subnet mask and default gateway for each adapter bound to TCP/IP.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
        "strict": False
    },
    {
        "name": "calculate",
        "type": "function",
        "description": "Evaluate a simple math expression.",
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
        "strict": False
    },
    {
        "name": "weather",
        "type": "function",
        "description": "Get fake weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
        "strict": False
    }
]

# ---------------------------
# HELPERS
# ---------------------------
def parse_tool_arguments(arg_string: str) -> Dict[str, Any]:
    if not arg_string:
        return {}
    try:
        return json.loads(arg_string)
    except json.JSONDecodeError:
        print("[WARN] Model returned invalid JSON for tool arguments.")
        return {}

def dispatch_tool(tool_name: str|None, args: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name not in TOOLS:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return TOOLS[tool_name](**args)
    except Exception as e:
        return {"error": f"Tool execution failed: {e}"}



# ---------------------------
# UNIFIED REPL LOOP
# ---------------------------
def run_agent() -> None:
    last_response_id  = None
    print("🤖 AI Agent REPL — type 'exit' to quit.\n")

    while True:
        user_input = input(">>> ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break

        # Start with user message
        input_queue: ResponseInputParam = [{"type": "message", "role": "user", "content": user_input}]

        # Loop until the model produces no more tool calls
        while input_queue:
            response: Response = client.responses.create(
                model=MODEL,
                input=input_queue,
                tools=TOOLS_DEF,
                previous_response_id=last_response_id , 
            )
            # print("[DEBUG] id:", response.id)
            last_response_id = response.id 

            input_queue = []
            for resp in getattr(response, "output", []):
                resp_type = getattr(resp, "type", None)

                # Regular assistant messages
                if resp_type == "message":
                    content_list = getattr(resp, "content", [])
                    if content_list and hasattr(content_list[0], "text"):
                        msg_text = content_list[0].text
                        print("\n🤖 Assistant:", msg_text)

                # Tool / function calls
                elif resp_type == "function_call":
                    tool_name = getattr(resp, "name", None)
                    raw_args = getattr(resp, "arguments", "{}")
                    args = raw_args if isinstance(raw_args, dict) else parse_tool_arguments(raw_args)

                    print(f"\n[Tool Call] {tool_name}({args})")
                    result = dispatch_tool(tool_name, args)
                    print(f"[Tool Result] {result}\n")

                    # Feed tool result back to model
                    input_queue.append({
                        "type": "function_call_output",
                        "call_id": resp.call_id,
                        "output": str(result)
                    })

# ---------------------------
# RUN
# ---------------------------
if __name__ == "__main__":
    run_agent()
