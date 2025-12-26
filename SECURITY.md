# Security Policy

## Credential Management

### Architecture

Genesis Studio is a **client application** that communicates with the Universal Living Memory orchestrator. All API keys and credentials are managed by the orchestrator, not by the studio.

### Best Practices

1. **Orchestrator Security**: Ensure the orchestrator is properly secured (see [universal-living-memory security policy](https://github.com/brian95240/universal-living-memory/blob/master/SECURITY.md))
2. **Network Security**: If running in production, use HTTPS and proper network isolation
3. **Access Control**: Limit access to the studio interface to authorized users only
4. **Voice Data**: Voice input is processed locally with Faster-Whisper; no audio is sent to external services

### Dependencies

- **Faster-Whisper**: Local speech-to-text processing (no external API calls)
- **Gradio**: Web interface framework
- **Orchestrator**: All AI provider credentials are managed here

### Setup Instructions

1. Ensure the Universal Living Memory orchestrator is running and secured
2. Configure `ORCHESTRATOR_URL` in `.env` if using a remote orchestrator
3. Launch studio: `python studio/genesis_studio.py`

### Reporting Security Issues

If you discover a security vulnerability, please email the maintainers directly. Do not open a public issue.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Features

- **No Credential Storage**: Studio does not store any API keys or credentials
- **Local Voice Processing**: Whisper runs locally, no audio sent to external services
- **Stateless**: Studio maintains no persistent user data
- **Orchestrator Delegation**: All authentication and authorization handled by orchestrator
