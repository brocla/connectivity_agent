# Connectivity Agent

A small demonstration project showing how to build a multi-tool AI Agent using OpenAI’s **Responses API**. Although intended as an example, it also works amazingly well for network connectivity checking.

## Overview
The agent runs in a terminal. It chooses which tools to run for your query, interprets their output, and explain results in plain language. 

The included tools are:

- `ping`
- `curl`
- `ports`
- `tracert`
- `nslookup`
- `ipconfig`
- `routing_table`

Adding another tool requires only:
1. A Python function that performs the task  
2. A brief structured description so the agent knows how to call it  

## Why This Example Might Be Useful
If you're learning the Responses API or experimenting with AI agents that use multiple tools, this example shows a simple pattern without extra framework code. The source is in a single file. 

## Example Queries

**Basic Connectivity**
\>> How is the connection to google?

**Comprehensive Analysis**
\>> Describe the connectivity to www.amazon.com. Be exhaustive.

**Performance Comparison**
\>> Compare response times between AWS on the East and West coast.

**DNS Troubleshooting**
\>> I can't reach example.com. Is it a DNS problem?

**Local Network Diagnostics**
\>> Show me my current network configuration and default gateway.

**Port Analysis**
\>> What services are currently listening on my machine?

**Route Investigation**
\>> Why might packets to cloudflare.com be taking an unusual path?

**Multi-Protocol Testing**
\>> Can I reach github.com? Check both ping and HTTP connectivity.

**Security Assessment**
\>> Are there any unexpected connections to external IP addresses?

**Network Path Optimization**
\>> Which endpoint has better routing from my location: `https://www.nasa.gov` or `https://www.esa.int` ?

**Self Check**
\>> Run a self-diagnostic.

## Requirements
- Python 3.10 or higher
- OpenAI API Key

## Installation

### Installing from PyPI

Once published, you can install the package directly:

```bash
pip install connectivity-agent
```

### Installing from Source

1. Clone the repository:
```bash
git clone https://github.com/brocla/connectivity_agent.git
cd connectivity_agent
```

2. Install the package:
```bash
pip install -e .
```

Or install the required dependencies manually:
```bash
pip install openai>=2.8.0
```

## API Key Setup

The Connectivity Agent requires an OpenAI API key to function. You can obtain an API key from [OpenAI's platform](https://platform.openai.com/api-keys).

### Setting Up Your API Key

You have two options for providing your API key:

**Option 1: Environment Variable (Recommended)**

Set the `OPENAI_API_KEY` environment variable:

On Windows:
```bash
setx OPENAI_API_KEY "your-api-key-here"
```

On Linux/Mac:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

To make it permanent on Linux/Mac, add the export command to your `~/.bashrc` or `~/.zshrc` file.

**Option 2: Direct Configuration**

The OpenAI Python client will automatically look for the API key in the environment variable. Alternatively, you can modify the code to pass the key directly (not recommended for security reasons).

## Usage

After installation and API key setup, run the agent:

If installed via pip:
```bash
connectivity-agent
```

If running from source:
```bash
python connectivity_agent.py
```

The agent will start an interactive REPL where you can ask connectivity-related questions.


## Kudos
Thanks to Thomas Ptacek for his article [You Should Write an Agent](https://fly.io/blog/everyone-write-an-agent/?utm_source=www.pythonweekly.com&utm_medium=newsletter&utm_campaign=python-weekly-issue-722-november-13-2025&_bhlid=67fb3628f293fe779bb6f37f8e5ce33d85d11b38)
