# Genesis Studio

Voice-guided AI project creation studio with hyper-dynamic capabilities.

## 🚀 Features (v1.0.1)

### Core Capabilities
- **Voice Interaction**: Real-time voice input with Faster-Whisper
- **Agentic Architecture**: Multi-agent workflow (Architect + Engineer)
- **Memory Integration**: Seamless integration with Universal Living Memory orchestrator
- **Interrupt Capability**: Voice-based interruption of running processes
- **Gradio Interface**: Clean, modern UI for project creation

### v1.0.1 Enhancements
- **🔇 Mute Button**: Handle noisy environments mid-build without stopping the workflow
- **🔧 Matrix Tab**: Runtime provider registration UI (add AI models via voice/text)
- **📊 Cloud Pricing Monitor**: View real-time GPU spot pricing
- **🧹 Model Unloading**: Manually unload Whisper to free memory
- **🔄 Provider Refresh**: Dynamic provider list updates
- **ℹ️ About Tab**: Comprehensive feature documentation

## Dependencies

This client requires the [Universal Living Memory](https://github.com/brian95240/universal-living-memory) orchestrator to function.

## Quick Start

### Windows (PowerShell)

```powershell
.\scripts\deploy-symbiotic.ps1
```

### Manual Setup

```bash
# 1. Clone and start the core orchestrator
git clone https://github.com/brian95240/universal-living-memory.git core
cd core
python genesis.py
docker compose up -d

# 2. Wait for orchestrator to be ready
curl http://localhost:8000/health

# 3. Install studio dependencies
cd ..
pip install -r studio/requirements.txt

# 4. Launch studio
python studio/genesis_studio.py
```

## Interface Overview

### 🚀 Create Tab
- **Project Vision**: Describe your project in natural language
- **AI Provider**: Select which AI provider to use (Grok, Anthropic, etc.)
- **Initialize Swarm**: Start the multi-agent build process
- **Mute/Unmute Voice**: Toggle voice input for noisy environments
- **Swarm Log**: Real-time output from the agent workflow

### 🔧 Matrix Tab (Configuration)
- **Runtime Provider Registration**: Add new AI providers without restart
  - Provider Name (e.g., "together", "mistral")
  - Base URL (API endpoint)
  - API Key (optional, can use environment variables)
- **Cloud Spot Pricing**: Monitor cheapest GPU options across providers
- **Unload Whisper**: Free memory by unloading the voice model

### ℹ️ About Tab
- Feature documentation
- Architecture overview
- Keyboard shortcuts
- Repository links

## Usage Tips

### Voice Control
1. Click "Initialize Swarm" to start
2. Speak to interrupt the build process
3. Use "Mute/Unmute" button in noisy environments
4. Voice input automatically resumes when unmuted

### Adding Providers
1. Go to Matrix tab
2. Enter provider details:
   - Name: `together`
   - URL: `https://api.together.xyz/v1`
   - Key: Your API key
3. Click "Register Provider"
4. Return to Create tab and refresh provider list

### Monitoring Costs
1. Go to Matrix tab
2. Click "Check Markets"
3. View real-time GPU spot pricing
4. Compare providers and regions

## Architecture

- **Gradio UI**: Web-based interface with tabs
- **Faster-Whisper**: Local speech-to-text (GPU/CPU auto-detect)
- **Agentic Loop**: Architect → Engineer workflow
- **HTTP Client**: Communicates with orchestrator API
- **Dynamic Configuration**: Runtime provider management

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
- **Orchestrator**: Must be running and accessible

## Keyboard Shortcuts

- **Ctrl+Enter**: Start swarm (when in Vision field)
- **Ctrl+M**: Toggle mute

## Troubleshooting

### Voice Not Working
1. Check microphone permissions
2. Verify Whisper model loaded (check console)
3. Try unmuting if muted
4. Check audio input device settings

### Orchestrator Connection Failed
1. Verify orchestrator is running: `curl http://localhost:8000/health`
2. Check `ORCHESTRATOR_URL` environment variable
3. Ensure Docker containers are up: `docker ps`

### Memory Issues
1. Use "Unload Whisper" button in Matrix tab
2. Close unused tabs
3. Restart studio if needed

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## Security

See [SECURITY.md](SECURITY.md) for security policies.

## License

AGPL-3.0 + Commercial (see [LICENSE](LICENSE))

## Related Projects

- [Universal Living Memory](https://github.com/brian95240/universal-living-memory) - Core orchestrator

## Changelog

### v1.0.1 (Hyper-Dynamic)
- Added mute button for noisy environments
- Added Matrix tab for runtime configuration
- Added cloud spot pricing monitor
- Added Whisper model unloading
- Added About tab with documentation
- Enhanced UI with better organization

### v1.0.0 (Golden Master)
- Initial release
- Voice-guided project creation
- Multi-agent workflow
- Voice interrupt capability
