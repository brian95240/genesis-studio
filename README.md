# Genesis Studio

Voice-guided AI project creation studio.

## Features

- **Voice Interaction**: Real-time voice input with Faster-Whisper
- **Agentic Architecture**: Multi-agent workflow (Architect + Engineer)
- **Memory Integration**: Seamless integration with Universal Living Memory orchestrator
- **Interrupt Capability**: Voice-based interruption of running processes
- **Gradio Interface**: Clean, modern UI for project creation

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

## Architecture

- **Gradio UI**: Web-based interface
- **Faster-Whisper**: Local speech-to-text
- **Agentic Loop**: Architect → Engineer workflow
- **HTTP Client**: Communicates with orchestrator API

## License

AGPL-3.0 + Commercial
