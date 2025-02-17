# 🐳 podman-mcp

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![smithery badge](https://smithery.ai/badge/podman-mcp)](https://smithery.ai/protocol/podman-mcp)

A powerful Model Context Protocol (MCP) server for Podman operations, enabling seamless container and compose stack management through Claude AI.

## ✨ Features

- 🚀 Container creation and instantiation
- 📦 Podman Compose stack deployment
- 🔍 Container logs retrieval
- 📊 Container listing and status monitoring

### 🎬 Demos
#### Deploying a Podman Compose Stack


https://github.com/user-attachments/assets/b5f6e40a-542b-4a39-ba12-7fdf803ee278



#### Analyzing Container Logs



https://github.com/user-attachments/assets/da386eea-2fab-4835-82ae-896de955d934



## 🚀 Quickstart

To try this in Claude Desktop app, add this to your claude config files:
```json
{
  "mcpServers": {
    "podman-mcp": {
      "command": "uvx",
      "args": [
        "podman-mcp"
      ]
    }
  }
}
```

### Installing via Smithery

To install Podman MCP for Claude Desktop automatically via [Smithery](https://smithery.ai/protocol/podman-mcp):

```bash
npx @smithery/cli install podman-mcp --client claude
```

### Prerequisites

- UV (package manager)
- Python 3.12+
- Podman
- Podman Compose (for multi-container deployments)
- Claude Desktop

### Installation

#### Podman Setup

1. Install Podman following the [official installation guide](https://podman.io/docs/installation)
2. For multi-container deployments, install Podman Compose:
   ```bash
   pip install podman-compose
   ```

#### Claude Desktop Configuration

Add the server configuration to your Claude Desktop config file:

**MacOS**: `~/Library/Application\ Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>💻 Development Configuration</summary>

```json
{
  "mcpServers": {
    "podman-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "<path-to-podman-mcp>",
        "run",
        "podman-mcp"
      ]
    }
  }
}
```
</details>

<details>
  <summary>🚀 Production Configuration</summary>

```json
{
  "mcpServers": {
    "podman-mcp": {
      "command": "uvx",
      "args": [
        "podman-mcp"
      ]
    }
  }
}
```
</details>

## 🛠️ Development

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/QuantGeekDev/podman-mcp.git
cd podman-mcp
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
uv sync
```

### 🔍 Debugging

Launch the MCP Inspector for debugging:

```bash
npx @modelcontextprotocol/inspector uv --directory <path-to-podman-mcp> run podman-mcp
```

The Inspector will provide a URL to access the debugging interface.

## 📝 Available Tools

The server provides the following tools:

### create-container
Creates a standalone Podman container
```json
{
    "image": "image-name",
    "name": "container-name",
    "ports": {"80": "80"},
    "environment": {"ENV_VAR": "value"}
}
```

### deploy-compose
Deploys a Podman Compose stack
```json
{
    "project_name": "example-stack",
    "compose_yaml": "version: '3.8'\nservices:\n  service1:\n    image: image1:latest\n    ports:\n      - '8080:80'"
}
```

### get-logs
Retrieves logs from a specific container
```json
{
    "container_name": "my-container"
}
```

### list-containers
Lists all Podman containers
```json
{}
```

## 🚧 Current Limitations

- No built-in environment variable support for containers
- No volume management
- No network management
- No container health checks
- No container restart policies
- No container resource limits

## 🤝 Contributing

1. Fork the repository from [podman-mcp](https://github.com/QuantGeekDev/podman-mcp)
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ✨ Authors

- **Alex Andru** - *Initial work | Core contributor* - [@QuantGeekDev](https://github.com/QuantGeekDev)
- **Ali Sadykov** - *Initial work  | Core contributor* - [@md-archive](https://github.com/md-archive)

---
Made with ❤️
