# FDA Drugs MCP Server

[![smithery badge](https://smithery.ai/badge/@plainyogurt21/fda-drugs-mcp)](https://smithery.ai/server/@plainyogurt21/fda-drugs-mcp)

A Model Context Protocol (MCP) server for accessing FDA drug data through the OpenFDA API.

## Features

- **Drug Name Search**: Search for drugs by brand or generic name
- **Indication Search**: Find drugs by medical condition or therapeutic indication  
- **Detailed Drug Information**: Get comprehensive drug details including clinical data
- **Similar Drug Discovery**: Find drugs with similar mechanisms of action or indications
- **Application History**: Access FDA application and approval history
- **BLA/NDA Focus**: Defaults to approved drugs (BLA/NDA), excludes generics (ANDA) unless specified

## Available Tools

1. `search_drug_by_name` - Search for drugs by brand or generic name
2. `search_drug_by_indication` - Search for drugs by medical indication
3. `get_drug_details` - Get comprehensive details for a specific drug
4. `search_similar_drugs` - Find drugs similar to a reference drug
5. `get_drug_application_history` - Get FDA application history

## Run Locally

- HTTP (recommended):
  ```bash
  pip install -r requirements.txt
  PORT=8081 TRANSPORT=http python server.py
  ```

- STDIO (backwards compatible):
  ```bash
  pip install -r requirements.txt
  python server.py
  ```

## Use With Clients

### Smithery (Custom Container)
- This repo includes `Dockerfile` and `smithery.yaml` configured for HTTP streamable transport.
- Deploy via https://smithery.ai/new by connecting your GitHub repo.
- Local test (HTTP):
  ```bash
  docker build -t fda-drugs-mcp .
  docker run -p 8081:8081 -e PORT=8081 fda-drugs-mcp
  npx @smithery/cli playground --port 8081
  ```

### Installing via Smithery

To install FDA Drugs MCP Server automatically via [Smithery](https://smithery.ai/server/@plainyogurt21/fda-drugs-mcp):

```bash
npx -y @smithery/cli install @plainyogurt21/fda-drugs-mcp
```

Config fields supported when launching via Smithery:
- `fdaApiKey`: OpenFDA API key
- `logLevel`: DEBUG | INFO | WARNING | ERROR | CRITICAL

### Cline (CLI MCP Client)
- Cline supports MCP over HTTP. Start the server:
  ```bash
  PORT=8081 TRANSPORT=http python server.py
  ```
- Then configure Cline to connect to `http://localhost:8081` as an MCP server.
  If Cline supports session config, pass `fdaApiKey` in the session config.

### Claude Code
- Claude Code supports both STDIO and HTTP MCP servers.
- Recommended: run HTTP and add a server entry pointing to `http://localhost:8081`.
- Alternative (STDIO): point Claude Code to run `python server.py` in this folder.

### Other MCP Clients
- Any MCP client that supports streamable HTTP can connect to `http://<host>:8081`.
- Per-request config can be passed using Smithery’s `config` query parameter format.

## Notes
- HTTP mode uses CORS with permissive defaults to work across clients.
- The server reads the OpenFDA API key from, in order of precedence:
  - Per-request config `fdaApiKey`
  - STDIO/runtime config or env `FDA_API_KEY`
  - Built-in default (see `utils/config.py`)

## Testing (local modules)
```bash
python test_server.py
```
