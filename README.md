# Genesis Studio

Voice-guided AI project creation studio with universal connection management.

## 🚀 Features (v1.1.0 - Universal)

### Universal Connection Management
- **🎤 Voice-Commanded Connections**: Add any service via voice with AI confirmation
  - Simply describe what you want to connect
  - AI parses your command and confirms details
  - Automatic spelling and URL validation
  
- **🔌 Three Connection Libraries**:
  - **API Connections**: Any AI model or API service
  - **Webhooks**: Event-driven integrations (Zapier, n8n, etc.)
  - **MCP Servers**: Model Context Protocol integrations

### Core Capabilities
- **Voice Interaction**: Real-time voice input with Faster-Whisper
- **Agentic Architecture**: Multi-agent workflow (Architect + Engineer)
- **Memory Integration**: Seamless integration with orchestrator
- **Interrupt Capability**: Voice-based interruption
- **Mute Control**: Handle noisy environments

## Dependencies

Requires [Universal Living Memory](https://github.com/brian95240/universal-living-memory) orchestrator.

## Quick Start

```bash
# 1. Clone and start the core orchestrator
git clone https://github.com/brian95240/universal-living-memory.git core
cd core
python genesis.py
docker compose up -d

# 2. Install studio dependencies
cd ..
git clone https://github.com/brian95240/genesis-studio.git
cd genesis-studio
pip install -r studio/requirements.txt

# 3. Launch studio
python studio/genesis_studio.py
```

## Interface Overview

### 🚀 Create Tab
- **Project Vision**: Describe your project
- **AI Provider**: Select provider
- **Initialize Swarm**: Start multi-agent build
- **Mute/Unmute Voice**: Toggle voice input
- **Swarm Log**: Real-time output

### 🔌 Connections Tab (NEW!)
Manage all three connection libraries with voice or manual input.

#### 🔑 API Connections
**Voice Command Example:**
> *"Add API connection for Together AI at api.together.xyz with bearer token xyz123 supporting Mixtral model"*

The AI will parse your command and confirm:
- Connection ID: `together_ai`
- Name: `Together AI`
- Base URL: `https://api.together.xyz/v1`
- Auth Type: `bearer`
- Models: `mixtral-8x7b`

**Manual Input Available:**
- Connection ID
- Name
- Base URL
- Auth Type (bearer, api_key, custom)
- API Key
- Models (comma-separated)

#### 🪝 Webhooks
**Voice Command Example:**
> *"Add webhook for Zapier at hooks.zapier.com/xyz listening to completion and error events"*

**Manual Input Available:**
- Webhook ID
- Name
- URL
- Method (POST, GET, PUT)
- Events (comma-separated)

#### 🔧 MCP Servers
**Voice Command Example:**
> *"Add MCP server for filesystem using npx with arguments filesystem and /tmp"*

**Manual Input Available:**
- Server ID
- Name
- Command
- Arguments (comma-separated)

### 🔧 Matrix Tab
- **Cloud Spot Pricing**: Monitor GPU prices
- **Unload Whisper**: Free memory
- **System Health**: Check orchestrator status

### ℹ️ About Tab
- Feature documentation
- Voice command examples
- Architecture overview
- Version history

## Voice Command Examples

### Adding API Connections
- *"Add OpenRouter API at openrouter.ai with my API key"*
- *"Connect to Mistral AI API with bearer authentication"*
- *"Add Together AI supporting Mixtral and Llama models"*

### Adding Webhooks
- *"Add Slack webhook at hooks.slack.com for all events"*
- *"Connect Zapier webhook for completion events"*
- *"Add n8n webhook with POST method"*

### Adding MCP Servers
- *"Add filesystem MCP server for /home directory"*
- *"Connect PostgreSQL MCP server"*
- *"Add GitHub MCP server"*

## Supported Services

### AI Models
- OpenAI, Anthropic, Google, Grok
- Together AI, Mistral, Cohere
- Replicate, OpenRouter
- Any OpenAI-compatible API

### Webhooks
- Zapier, n8n, Make
- IFTTT, Slack, Discord
- Custom webhooks

### MCP Servers
- Filesystem, PostgreSQL, SQLite
- GitHub, Google Drive
- Custom MCP servers

## Architecture

- **Gradio UI**: Web-based interface with tabs
- **Faster-Whisper**: Local speech-to-text
- **Voice Command Parser**: AI-powered connection parsing
- **Connection Manager**: Add/remove/list connections
- **Agentic Loop**: Architect → Engineer workflow

## Environment Variables

```bash
# Optional: Override orchestrator URL
ORCHESTRATOR_URL=http://localhost:8000

# Optional: Change studio port
STUDIO_PORT=7860
```

## System Requirements

- **Python**: 3.11+
- **RAM**: 4GB minimum (8GB+ for GPU)
- **GPU**: Optional (CUDA for faster Whisper)
- **Microphone**: Required for voice input
- **Orchestrator**: Must be running

## Troubleshooting

### Voice Commands Not Parsing
1. Speak clearly and include key details (name, URL, auth type)
2. Review AI-parsed output before confirming
3. Use manual input if voice parsing fails
4. Check orchestrator connection

### Connection Not Added
1. Verify all required fields are filled
2. Check URL format (include https://)
3. Ensure API key is valid
4. Review result JSON for error details

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## Security

See [SECURITY.md](SECURITY.md) for security policies.

## License

AGPL-3.0 + Commercial (see [LICENSE](LICENSE))

## Related Projects

- [Universal Living Memory](https://github.com/brian95240/universal-living-memory) - Core orchestrator

## Changelog

### v1.1.0 (Universal)
- Added Universal Connection Management UI
- Added voice-commanded connection additions
- Added AI confirmation for connections
- Added three connection library tabs (API, Webhook, MCP)
- Added connection statistics dashboard
- Enhanced UI organization

### v1.0.1 (Hyper-Dynamic)
- Added mute button for noisy environments
- Added Matrix tab for runtime configuration
- Added cloud spot pricing monitor

### v1.0.0 (Golden Master)
- Initial release
- Voice-guided project creation
- Multi-agent workflow
