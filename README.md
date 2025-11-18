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

## Requirements
- OpenAI API Key
- Python  

## Example Queries

\>> How is the connection to google?

\>> Describe the connectivity to www.amazon.com. Be exhaustive.

\>> Compare response times between AWS on the East and West coast.
