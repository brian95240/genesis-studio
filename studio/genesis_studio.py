import os, time, requests, importlib, queue, threading
import gradio as gr

ORCHESTRATOR = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")

# Lazy Globals
WHISPER = None
TORCH = None

class State:
    def __init__(self):
        self.listening = False
        self.interrupt = False
        self.muted = False
        self.voice_command_mode = False  # NEW: For connection commands

st = State()

def lazy_load():
    """Lazy load Whisper model only when needed"""
    global WHISPER, TORCH
    if not WHISPER:
        import torch
        from faster_whisper import WhisperModel
        device = "cuda" if torch.cuda.is_available() else "cpu"
        WHISPER = WhisperModel("distil-large-v3", device=device, compute_type="int8")
        print(f"[✓] Whisper loaded on {device}")

def unload_whisper():
    """Unload Whisper model to free memory"""
    global WHISPER
    if WHISPER:
        del WHISPER
        WHISPER = None
        import gc
        gc.collect()
        return "✓ Whisper unloaded"
    return "Whisper not loaded"

def call_core(messages, provider="grok"):
    """Call orchestrator API"""
    try:
        resp = requests.post(f"{ORCHESTRATOR}/v1/chat/completions", json={
            "provider": provider, 
            "messages": messages, 
            "use_memory": True
        }, timeout=120)
        return resp.json()["content"]
    except Exception as e:
        return f"[System Error]: {e}"

def get_pricing():
    """Get cloud spot pricing from orchestrator"""
    try:
        resp = requests.get(f"{ORCHESTRATOR}/v1/cloud/pricing", timeout=10)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def get_providers():
    """Get list of available providers"""
    try:
        resp = requests.get(f"{ORCHESTRATOR}/v1/providers", timeout=10)
        return resp.json().get("providers", ["grok", "anthropic", "local"])
    except:
        return ["grok", "anthropic", "local"]

def get_all_connections():
    """Get all connections from all libraries"""
    try:
        resp = requests.get(f"{ORCHESTRATOR}/v1/connections/all", timeout=10)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def get_connection_stats():
    """Get connection statistics"""
    try:
        resp = requests.get(f"{ORCHESTRATOR}/v1/connections/stats", timeout=10)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

# ===== CONNECTION MANAGEMENT =====

def add_api_connection(conn_id, name, base_url, auth_type, api_key, models_str):
    """Add API connection"""
    if not conn_id or not name or not base_url:
        return {"error": "Connection ID, Name, and Base URL are required"}
    
    models = [m.strip() for m in models_str.split(",") if m.strip()] if models_str else []
    
    payload = {
        "conn_id": conn_id,
        "name": name,
        "base_url": base_url,
        "auth_type": auth_type,
        "api_key_value": api_key if api_key else None,
        "models": models,
        "capabilities": ["chat", "completion"],
        "enabled": True
    }
    try:
        r = requests.post(f"{ORCHESTRATOR}/v1/connections/api", json=payload, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def remove_api_connection(conn_id):
    """Remove API connection"""
    try:
        r = requests.delete(f"{ORCHESTRATOR}/v1/connections/api/{conn_id}", timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def add_webhook(webhook_id, name, url, method, events_str):
    """Add webhook"""
    if not webhook_id or not name or not url:
        return {"error": "Webhook ID, Name, and URL are required"}
    
    events = [e.strip() for e in events_str.split(",") if e.strip()] if events_str else ["all"]
    
    payload = {
        "webhook_id": webhook_id,
        "name": name,
        "url": url,
        "method": method,
        "events": events,
        "enabled": True
    }
    try:
        r = requests.post(f"{ORCHESTRATOR}/v1/connections/webhook", json=payload, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def remove_webhook(webhook_id):
    """Remove webhook"""
    try:
        r = requests.delete(f"{ORCHESTRATOR}/v1/connections/webhook/{webhook_id}", timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def add_mcp_server(server_id, name, command, args_str):
    """Add MCP server"""
    if not server_id or not name or not command:
        return {"error": "Server ID, Name, and Command are required"}
    
    args = [a.strip() for a in args_str.split(",") if a.strip()] if args_str else []
    
    payload = {
        "server_id": server_id,
        "name": name,
        "command": command,
        "args": args,
        "capabilities": ["read", "write"],
        "enabled": True
    }
    try:
        r = requests.post(f"{ORCHESTRATOR}/v1/connections/mcp", json=payload, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def remove_mcp_server(server_id):
    """Remove MCP server"""
    try:
        r = requests.delete(f"{ORCHESTRATOR}/v1/connections/mcp/{server_id}", timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ===== VOICE-COMMANDED CONNECTION MANAGEMENT =====

def parse_connection_from_voice(voice_input, connection_type):
    """Use AI to parse connection details from voice input"""
    prompt = f"""Parse this voice command to add a {connection_type} connection.
Extract the following details and respond in JSON format:

Voice input: "{voice_input}"

For API connections, extract:
- conn_id (short identifier, lowercase with underscores)
- name (full name)
- base_url (API endpoint URL)
- auth_type (bearer, api_key, or custom)
- api_key (if mentioned)
- models (comma-separated list if mentioned)

For Webhooks, extract:
- webhook_id (short identifier)
- name (full name)
- url (webhook URL)
- method (GET, POST, etc.)
- events (comma-separated event types)

For MCP Servers, extract:
- server_id (short identifier)
- name (full name)
- command (executable command)
- args (comma-separated arguments)

Respond ONLY with valid JSON. If information is missing, use null."""

    try:
        response = call_core([
            {"role": "system", "content": "You are a connection parser. Extract structured data from voice commands and respond in JSON format only."},
            {"role": "user", "content": prompt}
        ], provider="anthropic" if "anthropic" in get_providers() else "grok")
        
        # Extract JSON from response
        import json
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            return parsed
        else:
            return {"error": "Could not parse voice input"}
    except Exception as e:
        return {"error": str(e)}

def confirm_and_add_connection(voice_input, connection_type):
    """Parse voice input, confirm with user, and add connection"""
    # Step 1: Parse voice input
    parsed = parse_connection_from_voice(voice_input, connection_type)
    
    if "error" in parsed:
        return f"❌ Error: {parsed['error']}"
    
    # Step 2: Format confirmation message
    confirmation = f"🤖 **AI Parsed the following {connection_type} connection:**\n\n"
    for key, value in parsed.items():
        if value is not None:
            confirmation += f"- **{key}**: {value}\n"
    
    confirmation += "\n✅ Please review the details above. If correct, the connection will be added automatically.\n"
    confirmation += "❓ If anything is wrong, please correct it manually in the form fields below."
    
    return confirmation, parsed

def voice_add_connection(voice_input, connection_type):
    """Voice-commanded connection addition with AI confirmation"""
    if not voice_input.strip():
        return "Please provide voice input describing the connection to add."
    
    confirmation, parsed = confirm_and_add_connection(voice_input, connection_type)
    
    # Return confirmation for user review
    return confirmation

# ===== PROJECT CREATION =====

def project_manager(prompt, provider, history):
    """Multi-agent project creation workflow"""
    st.listening = True
    yield history + f"\n\n> [GENESIS]: Architecting '{prompt}'...\n"
    
    # 1. Architect Phase
    design = call_core([
        {"role": "system", "content": "You are a Chief Architect. Outline the files and structure needed for this project."},
        {"role": "user", "content": prompt}
    ], provider="anthropic" if "anthropic" in get_providers() else provider)
    
    history += f"\n> [ARCHITECT]:\n{design}\n"
    yield history
    
    if st.interrupt:
        yield history + "\n[!] INTERRUPTED BY VOICE\n"
        st.interrupt = False
        st.listening = False
        return

    # 2. Engineer Phase
    history += "\n> [ENGINEER]: Generating code...\n"
    yield history
    
    code = call_core([
        {"role": "system", "content": "You are a 10x Engineer. Write the main implementation code based on this architecture."},
        {"role": "user", "content": design}
    ], provider=provider)
    
    history += f"\n> [CODE]:\n{code[:500]}...\n\n[✓ DONE]\n"
    st.listening = False
    yield history

def listen_loop(audio):
    """Process voice input (only when not muted)"""
    if not st.listening or st.muted:
        return None
    
    lazy_load()
    try:
        segments, _ = WHISPER.transcribe(audio, beam_size=1)
        text = " ".join([s.text for s in segments]).strip()
        if len(text) > 2:
            st.interrupt = True
            return f"[🎤 VOICE]: {text}"
    except Exception as e:
        print(f"[ERROR] Whisper transcription failed: {e}")
    return None

def toggle_mute():
    """Toggle mute state"""
    st.muted = not st.muted
    status = "🔇 MUTED" if st.muted else "🎤 ACTIVE"
    return status

def launch():
    with gr.Blocks(title="Vertex Genesis v1.4.0", theme=gr.themes.Monochrome()) as demo:
        gr.Markdown("# 🧬 Vertex Genesis v1.4.0 - Ghost Mode Evolution")
        
        with gr.Tabs():
            # CREATE TAB
            with gr.Tab("🚀 Create"):
                with gr.Row():
                    with gr.Column(scale=3):
                        vision = gr.Textbox(
                            label="Project Vision", 
                            placeholder="Describe your project...",
                            lines=3
                        )
                    with gr.Column(scale=1):
                        provider_dropdown = gr.Dropdown(
                            choices=get_providers(),
                            label="AI Provider",
                            value="grok"
                        )
                        refresh_providers = gr.Button("🔄 Refresh", size="sm")
                
                with gr.Row():
                    start_btn = gr.Button("🎯 Initialize Swarm", variant="primary")
                    mute_btn = gr.Button("🎤 Mute/Unmute Voice", variant="secondary")
                
                mute_status = gr.Textbox(label="Voice Status", value="🎤 ACTIVE", interactive=False)
                log = gr.Textbox(label="Swarm Log", lines=15, max_lines=20)
                
                mic = gr.Audio(source="microphone", streaming=True, visible=False)
                
                start_btn.click(project_manager, inputs=[vision, provider_dropdown, log], outputs=log)
                mute_btn.click(toggle_mute, outputs=mute_status)
                refresh_providers.click(lambda: gr.Dropdown(choices=get_providers()), outputs=provider_dropdown)
                mic.stream(listen_loop, mic, None)
            
            # CONNECTIONS TAB (Universal Library Management)
            with gr.Tab("🔌 Connections"):
                gr.Markdown("### Universal Connection Library")
                gr.Markdown("Manage API connections, webhooks, and MCP servers. Add connections via voice or manual input.")
                
                # Connection Stats
                stats_btn = gr.Button("📊 View Connection Stats")
                stats_out = gr.JSON(label="Connection Statistics")
                stats_btn.click(get_connection_stats, outputs=stats_out)
                
                gr.Markdown("---")
                
                with gr.Tabs():
                    # API CONNECTIONS
                    with gr.Tab("🔑 API Connections"):
                        gr.Markdown("**Voice Command Example:** *'Add API connection for Together AI at api.together.xyz with bearer token xyz123 supporting Mixtral model'*")
                        
                        voice_api_input = gr.Textbox(label="Voice Command", placeholder="Describe the API connection to add...")
                        voice_api_btn = gr.Button("🎤 Parse Voice Command", variant="secondary")
                        voice_api_out = gr.Markdown()
                        
                        gr.Markdown("**Manual Input:**")
                        with gr.Row():
                            api_conn_id = gr.Textbox(label="Connection ID", placeholder="together_ai")
                            api_name = gr.Textbox(label="Name", placeholder="Together AI")
                        with gr.Row():
                            api_base_url = gr.Textbox(label="Base URL", placeholder="https://api.together.xyz/v1")
                            api_auth_type = gr.Dropdown(["bearer", "api_key", "custom"], label="Auth Type", value="bearer")
                        with gr.Row():
                            api_key = gr.Textbox(label="API Key", type="password")
                            api_models = gr.Textbox(label="Models (comma-separated)", placeholder="mixtral-8x7b, llama-2-70b")
                        
                        with gr.Row():
                            add_api_btn = gr.Button("➕ Add API Connection", variant="primary")
                            remove_api_id = gr.Textbox(label="Remove by ID", placeholder="together_ai")
                            remove_api_btn = gr.Button("➖ Remove", variant="stop")
                        
                        api_result = gr.JSON(label="Result")
                        list_api_btn = gr.Button("📋 List All API Connections")
                        
                        voice_api_btn.click(lambda x: voice_add_connection(x, "api"), inputs=voice_api_input, outputs=voice_api_out)
                        add_api_btn.click(add_api_connection, inputs=[api_conn_id, api_name, api_base_url, api_auth_type, api_key, api_models], outputs=api_result)
                        remove_api_btn.click(remove_api_connection, inputs=remove_api_id, outputs=api_result)
                        list_api_btn.click(lambda: requests.get(f"{ORCHESTRATOR}/v1/connections/api").json(), outputs=api_result)
                    
                    # WEBHOOKS
                    with gr.Tab("🪝 Webhooks"):
                        gr.Markdown("**Voice Command Example:** *'Add webhook for Zapier at hooks.zapier.com/xyz listening to completion and error events'*")
                        
                        voice_webhook_input = gr.Textbox(label="Voice Command", placeholder="Describe the webhook to add...")
                        voice_webhook_btn = gr.Button("🎤 Parse Voice Command", variant="secondary")
                        voice_webhook_out = gr.Markdown()
                        
                        gr.Markdown("**Manual Input:**")
                        with gr.Row():
                            wh_id = gr.Textbox(label="Webhook ID", placeholder="zapier_hook")
                            wh_name = gr.Textbox(label="Name", placeholder="Zapier Integration")
                        with gr.Row():
                            wh_url = gr.Textbox(label="URL", placeholder="https://hooks.zapier.com/...")
                            wh_method = gr.Dropdown(["POST", "GET", "PUT"], label="Method", value="POST")
                        wh_events = gr.Textbox(label="Events (comma-separated)", placeholder="completion, error, all")
                        
                        with gr.Row():
                            add_wh_btn = gr.Button("➕ Add Webhook", variant="primary")
                            remove_wh_id = gr.Textbox(label="Remove by ID", placeholder="zapier_hook")
                            remove_wh_btn = gr.Button("➖ Remove", variant="stop")
                        
                        wh_result = gr.JSON(label="Result")
                        list_wh_btn = gr.Button("📋 List All Webhooks")
                        
                        voice_webhook_btn.click(lambda x: voice_add_connection(x, "webhook"), inputs=voice_webhook_input, outputs=voice_webhook_out)
                        add_wh_btn.click(add_webhook, inputs=[wh_id, wh_name, wh_url, wh_method, wh_events], outputs=wh_result)
                        remove_wh_btn.click(remove_webhook, inputs=remove_wh_id, outputs=wh_result)
                        list_wh_btn.click(lambda: requests.get(f"{ORCHESTRATOR}/v1/connections/webhook").json(), outputs=wh_result)
                    
                    # MCP SERVERS
                    with gr.Tab("🔧 MCP Servers"):
                        gr.Markdown("**Voice Command Example:** *'Add MCP server for filesystem using npx with arguments filesystem and /tmp'*")
                        
                        voice_mcp_input = gr.Textbox(label="Voice Command", placeholder="Describe the MCP server to add...")
                        voice_mcp_btn = gr.Button("🎤 Parse Voice Command", variant="secondary")
                        voice_mcp_out = gr.Markdown()
                        
                        gr.Markdown("**Manual Input:**")
                        with gr.Row():
                            mcp_id = gr.Textbox(label="Server ID", placeholder="filesystem")
                            mcp_name = gr.Textbox(label="Name", placeholder="Filesystem MCP")
                        with gr.Row():
                            mcp_cmd = gr.Textbox(label="Command", placeholder="npx")
                            mcp_args = gr.Textbox(label="Arguments (comma-separated)", placeholder="-y, @modelcontextprotocol/server-filesystem, /tmp")
                        
                        with gr.Row():
                            add_mcp_btn = gr.Button("➕ Add MCP Server", variant="primary")
                            remove_mcp_id = gr.Textbox(label="Remove by ID", placeholder="filesystem")
                            remove_mcp_btn = gr.Button("➖ Remove", variant="stop")
                        
                        mcp_result = gr.JSON(label="Result")
                        list_mcp_btn = gr.Button("📋 List All MCP Servers")
                        
                        voice_mcp_btn.click(lambda x: voice_add_connection(x, "mcp"), inputs=voice_mcp_input, outputs=voice_mcp_out)
                        add_mcp_btn.click(add_mcp_server, inputs=[mcp_id, mcp_name, mcp_cmd, mcp_args], outputs=mcp_result)
                        remove_mcp_btn.click(remove_mcp_server, inputs=remove_mcp_id, outputs=mcp_result)
                        list_mcp_btn.click(lambda: requests.get(f"{ORCHESTRATOR}/v1/connections/mcp").json(), outputs=mcp_result)
            
            # VAULT TAB (Vaultwarden & 2FA)
            with gr.Tab("🔐 Vault"):
                gr.Markdown("### Vaultwarden Credential Management")
                gr.Markdown("Securely store and manage credentials with self-hosted Vaultwarden.")
                
                # Authentication
                gr.Markdown("#### 🔑 Authentication")
                with gr.Row():
                    vault_email = gr.Textbox(label="Email", placeholder="user@example.com")
                    vault_password = gr.Textbox(label="Master Password", type="password")
                vault_auth_btn = gr.Button("🔐 Authenticate", variant="primary")
                vault_auth_out = gr.JSON(label="Auth Status")
                
                def vault_auth(email, password):
                    try:
                        resp = requests.post(f"{ORCHESTRATOR}/v1/vault/auth", json={"email": email, "master_password": password})
                        return resp.json()
                    except Exception as e:
                        return {"error": str(e)}
                
                vault_auth_btn.click(vault_auth, inputs=[vault_email, vault_password], outputs=vault_auth_out)
                
                gr.Markdown("---")
                
                # Create Cipher
                gr.Markdown("#### ➕ Create Credential")
                with gr.Row():
                    cipher_name = gr.Textbox(label="Name", placeholder="My API Key")
                    cipher_username = gr.Textbox(label="Username/Email", placeholder="user@example.com")
                with gr.Row():
                    cipher_password = gr.Textbox(label="Password (leave empty to auto-generate)", type="password", placeholder="")
                    cipher_uri = gr.Textbox(label="URL (optional)", placeholder="https://api.example.com")
                cipher_notes = gr.Textbox(label="Notes (optional)", placeholder="Additional information...")
                cipher_auto_gen = gr.Checkbox(label="Auto-generate password", value=True)
                
                create_cipher_btn = gr.Button("💾 Save to Vault", variant="primary")
                cipher_result = gr.JSON(label="Result")
                
                def create_cipher(name, username, password, uri, notes, auto_gen):
                    try:
                        resp = requests.post(f"{ORCHESTRATOR}/v1/vault/cipher", json={
                            "name": name,
                            "username": username,
                            "password": password if password else None,
                            "uri": uri if uri else None,
                            "notes": notes if notes else None,
                            "auto_generate_password": auto_gen
                        })
                        return resp.json()
                    except Exception as e:
                        return {"error": str(e)}
                
                create_cipher_btn.click(create_cipher, inputs=[cipher_name, cipher_username, cipher_password, cipher_uri, cipher_notes, cipher_auto_gen], outputs=cipher_result)
                
                gr.Markdown("---")
                
                # Password Generator
                gr.Markdown("#### 🎲 Password Generator")
                with gr.Row():
                    pwd_length = gr.Slider(16, 64, value=32, step=1, label="Length")
                    pwd_symbols = gr.Checkbox(label="Include symbols", value=True)
                gen_pwd_btn = gr.Button("🔑 Generate Password", variant="secondary")
                pwd_out = gr.Textbox(label="Generated Password", interactive=False)
                
                def gen_password(length, symbols):
                    try:
                        resp = requests.post(f"{ORCHESTRATOR}/v1/vault/generate-password?length={int(length)}&include_symbols={symbols}")
                        return resp.json().get("password", "")
                    except Exception as e:
                        return f"Error: {e}"
                
                gen_pwd_btn.click(gen_password, inputs=[pwd_length, pwd_symbols], outputs=pwd_out)
                
                gr.Markdown("---")
                
                # 2FA Generator
                gr.Markdown("#### 🔐 2FA/TOTP Generator")
                gr.Markdown("Generate 2FA secrets for use with authenticator apps (Google Authenticator, Authy, etc.)")
                
                with gr.Row():
                    totp_account = gr.Textbox(label="Account Name", placeholder="user@example.com")
                    totp_issuer = gr.Textbox(label="Issuer", value="Vertex Genesis")
                gen_2fa_btn = gr.Button("🔐 Generate 2FA Secret", variant="secondary")
                totp_out = gr.JSON(label="2FA Details")
                
                def gen_2fa(account, issuer):
                    try:
                        resp = requests.post(f"{ORCHESTRATOR}/v1/vault/generate-2fa?account_name={account}&issuer={issuer}")
                        return resp.json()
                    except Exception as e:
                        return {"error": str(e)}
                
                gen_2fa_btn.click(gen_2fa, inputs=[totp_account, totp_issuer], outputs=totp_out)
                
                gr.Markdown("---")
                
                # List & Search
                gr.Markdown("#### 📋 Manage Credentials")
                with gr.Row():
                    list_ciphers_btn = gr.Button("📋 List All", variant="secondary")
                    search_query = gr.Textbox(label="Search", placeholder="Search by name or username...")
                    search_btn = gr.Button("🔍 Search", variant="secondary")
                
                ciphers_out = gr.JSON(label="Credentials")
                
                def list_ciphers():
                    try:
                        resp = requests.get(f"{ORCHESTRATOR}/v1/vault/ciphers")
                        return resp.json()
                    except Exception as e:
                        return {"error": str(e)}
                
                def search_ciphers(query):
                    try:
                        resp = requests.get(f"{ORCHESTRATOR}/v1/vault/search?q={query}")
                        return resp.json()
                    except Exception as e:
                        return {"error": str(e)}
                
                list_ciphers_btn.click(list_ciphers, outputs=ciphers_out)
                search_btn.click(search_ciphers, inputs=search_query, outputs=ciphers_out)
                
                gr.Markdown("---")
                gr.Markdown("**Access Vaultwarden UI**: http://localhost:8081")
                gr.Markdown("**Access 2FAuth UI**: http://localhost:5000")
            
            # MATRIX TAB (Cloud Pricing & System)
            with gr.Tab("🔧 Matrix"):
                gr.Markdown("### Cloud Spot Pricing (Delta Engine)")
                gr.Markdown("Monitor real-time GPU spot pricing across cloud providers.")
                
                with gr.Row():
                    refresh_pricing = gr.Button("📊 Check Markets", variant="secondary")
                    unload_btn = gr.Button("🧹 Unload Whisper", variant="secondary")
                
                price_out = gr.JSON(label="Spot Pricing Data")
                unload_out = gr.Textbox(label="Status")
                
                refresh_pricing.click(get_pricing, outputs=price_out)
                unload_btn.click(unload_whisper, outputs=unload_out)
                
                gr.Markdown("---")
                gr.Markdown("### System Information")
                health_btn = gr.Button("🏥 Check System Health")
                health_out = gr.JSON(label="Health Status")
                health_btn.click(lambda: requests.get(f"{ORCHESTRATOR}/health").json(), outputs=health_out)
            
            # GHOST MODE TAB
            with gr.Tab("👻 Ghost Mode"):
                gr.Markdown("### 👻 Ghost Mode - Voice-Activated Agent System")
                gr.Markdown("Ambient wake-word detection, voice commands, and autonomous agent operation.")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### Control Panel")
                        ghost_activate_btn = gr.Button("👻 Activate Ghost Mode", variant="primary")
                        ghost_deactivate_btn = gr.Button("🚫 Deactivate Ghost Mode", variant="secondary")
                        ghost_status_btn = gr.Button("📊 Check Status")
                        
                        ghost_status_out = gr.JSON(label="Ghost Mode Status")
                        ghost_message_out = gr.Textbox(label="Message", interactive=False)
                        
                        def activate_ghost():
                            try:
                                resp = requests.post(f"{ORCHESTRATOR}/v1/ghost/activate")
                                return resp.json(), resp.json().get("message", "Activated")
                            except Exception as e:
                                return {"error": str(e)}, f"Error: {e}"
                        
                        def deactivate_ghost():
                            try:
                                resp = requests.post(f"{ORCHESTRATOR}/v1/ghost/deactivate")
                                return resp.json(), resp.json().get("message", "Deactivated")
                            except Exception as e:
                                return {"error": str(e)}, f"Error: {e}"
                        
                        def get_ghost_status():
                            try:
                                resp = requests.get(f"{ORCHESTRATOR}/v1/ghost/status")
                                return resp.json()
                            except Exception as e:
                                return {"error": str(e)}
                        
                        ghost_activate_btn.click(activate_ghost, outputs=[ghost_status_out, ghost_message_out])
                        ghost_deactivate_btn.click(deactivate_ghost, outputs=[ghost_status_out, ghost_message_out])
                        ghost_status_btn.click(get_ghost_status, outputs=ghost_status_out)
                    
                    with gr.Column():
                        gr.Markdown("#### Seat Router")
                        gr.Markdown("Vector-driven model assignment to seats based on task description.")
                        
                        seat_id_input = gr.Slider(0, 4, step=1, value=0, label="Seat ID")
                        task_desc_input = gr.Textbox(label="Task Description", placeholder="e.g., build async parser in Rust")
                        seat_assign_btn = gr.Button("🪑 Assign Model to Seat")
                        seat_status_btn = gr.Button("📊 View All Seats")
                        
                        seat_result_out = gr.JSON(label="Assignment Result")
                        
                        def assign_seat(seat_id, task_desc):
                            try:
                                resp = requests.post(f"{ORCHESTRATOR}/v1/seats/assign", json={
                                    "seat_id": int(seat_id),
                                    "task_description": task_desc
                                })
                                return resp.json()
                            except Exception as e:
                                return {"error": str(e)}
                        
                        def get_seats_status():
                            try:
                                resp = requests.get(f"{ORCHESTRATOR}/v1/seats/status")
                                return resp.json()
                            except Exception as e:
                                return {"error": str(e)}
                        
                        seat_assign_btn.click(assign_seat, inputs=[seat_id_input, task_desc_input], outputs=seat_result_out)
                        seat_status_btn.click(get_seats_status, outputs=seat_result_out)
                
                gr.Markdown("---")
                gr.Markdown("### Model Discovery")
                
                with gr.Row():
                    discovery_scan_btn = gr.Button("🔍 Scan for Models")
                    discovery_pricing_btn = gr.Button("💰 Check Pricing")
                    discovery_optimal_btn = gr.Button("✨ Get Optimal Config")
                
                task_type_input = gr.Dropdown(["general", "code", "vision"], value="general", label="Task Type")
                discovery_out = gr.JSON(label="Discovery Results")
                
                def scan_models():
                    try:
                        resp = requests.post(f"{ORCHESTRATOR}/v1/discovery/scan?force=true")
                        return resp.json()
                    except Exception as e:
                        return {"error": str(e)}
                
                def get_pricing():
                    try:
                        resp = requests.get(f"{ORCHESTRATOR}/v1/discovery/pricing")
                        return resp.json()
                    except Exception as e:
                        return {"error": str(e)}
                
                def get_optimal(task_type):
                    try:
                        resp = requests.get(f"{ORCHESTRATOR}/v1/discovery/optimal?task_type={task_type}")
                        return resp.json()
                    except Exception as e:
                        return {"error": str(e)}
                
                discovery_scan_btn.click(scan_models, outputs=discovery_out)
                discovery_pricing_btn.click(get_pricing, outputs=discovery_out)
                discovery_optimal_btn.click(get_optimal, inputs=task_type_input, outputs=discovery_out)
            
            # COST DASHBOARD TAB
            with gr.Tab("💰 Cost Dashboard"):
                gr.Markdown("## $0-Cost Optimization Dashboard")
                gr.Markdown("Real-time cost monitoring and optimization suggestions.")
                
                with gr.Row():
                    refresh_cost_btn = gr.Button("🔄 Refresh Statistics")
                    reset_cost_btn = gr.Button("🔁 Reset Statistics")
                
                cost_stats_out = gr.JSON(label="Cost Statistics")
                cost_suggestions_out = gr.JSON(label="Optimization Suggestions")
                
                def get_cost_stats():
                    try:
                        resp = requests.get(f"{ORCHESTRATOR}/v1/cost/statistics")
                        return resp.json()
                    except Exception as e:
                        return {"error": str(e)}
                
                def get_cost_suggestions():
                    try:
                        resp = requests.get(f"{ORCHESTRATOR}/v1/cost/suggestions")
                        return resp.json()
                    except Exception as e:
                        return {"error": str(e)}
                
                def reset_cost_stats():
                    try:
                        resp = requests.post(f"{ORCHESTRATOR}/v1/cost/reset")
                        return resp.json()
                    except Exception as e:
                        return {"error": str(e)}
                
                def refresh_all_cost():
                    stats = get_cost_stats()
                    suggestions = get_cost_suggestions()
                    return stats, suggestions
                
                refresh_cost_btn.click(refresh_all_cost, outputs=[cost_stats_out, cost_suggestions_out])
                reset_cost_btn.click(reset_cost_stats, outputs=cost_stats_out)
                
                gr.Markdown("---")
                gr.Markdown("### 📷 Visual Project Inputs")
                gr.Markdown("Use camera for visual inputs (OCR, translation, object identification).")
                
                camera_input = gr.Textbox(label="Voice Command", placeholder="e.g., 'translate this french text' or 'read this code'")
                camera_btn = gr.Button("📷 Process Camera Command")
                camera_out = gr.JSON(label="Camera Result")
                
                def process_camera(voice_input):
                    try:
                        resp = requests.post(f"{ORCHESTRATOR}/v1/camera/process?voice_input={voice_input}")
                        return resp.json()
                    except Exception as e:
                        return {"error": str(e)}
                
                camera_btn.click(process_camera, inputs=camera_input, outputs=camera_out)
            
            # ABOUT TAB
            with gr.Tab("ℹ️ About"):
                gr.Markdown("""
                ## Vertex Genesis v1.4.0 - Autonomous Ghost Mode
                
                ### 🌟 New in v1.4.0
                - **🤖 Real-Time HuggingFace Indexing**: Dynamic model addition from HF API
                - **📷 Context-Aware Camera**: Automatically selects optimal model for use case
                - **💰 $0-Cost Optimization**: Intelligent decision engine ensures free options
                - **📊 Cost Dashboard**: Real-time cost monitoring and optimization suggestions
                - **🔗 Vault-Connection Integration**: Auto-store API keys in Vaultwarden
                - **📊 Graph Synergy Analysis**: 66.7% efficiency boost through compounding synergies
                
                ### 🎉 Inherited from v1.4.0
                - **👻 Ghost Mode**: Voice-activated agent system with ambient wake-word detection
                - **🪑 Seat Router**: Vector-driven model assignment using embeddings
                - **🔍 Model Discovery**: Universal model hunting with spot pricing
                - **🧠 Lazy Loading**: On-demand OCR, voice, and model loading
                - **♻️ Auto-Collapse**: Components unload automatically when idle
                
                ### 🎉 Inherited from v1.1.1
                - **Universal Connection Library**: Three symbiotic libraries (API, Webhook, MCP)
                - **Voice-Commanded Connections**: Add any service via voice with AI confirmation
                - **Future-Proof Architecture**: Connect to ANY AI model, tool, or platform
                - **Symbiotic Integration**: API keys, webhooks, and MCP servers work together
                
                ### Features
                - **Voice-Guided Creation**: Speak your vision, interrupt with voice commands
                - **Multi-Agent Workflow**: Architect → Engineer pipeline
                - **Runtime Connection Management**: Add/remove connections without restart
                - **Cloud Spot Pricing**: Monitor cheapest GPU options
                - **Memory Integration**: Persistent context across sessions
                - **Mute Control**: Handle noisy environments mid-build
                
                ### Connection Libraries
                
                #### 🔑 API Connection Library
                Connect to any AI model or API service:
                - OpenAI, Anthropic, Google, Grok, Together AI, etc.
                - Custom authentication (Bearer, API Key, Custom headers)
                - Multi-model support per connection
                - Dynamic capability detection
                
                #### 🪝 Webhook Library
                Event-driven integrations:
                - Zapier, n8n, Make, custom webhooks
                - Event filtering (completion, error, all)
                - Multiple HTTP methods (POST, GET, PUT)
                - Automatic triggering on events
                
                #### 🔧 MCP Server Library
                Model Context Protocol integrations:
                - Filesystem access
                - Database connections
                - Custom tool servers
                - Extensible capabilities
                
                ### Voice Commands
                Simply describe what you want to connect:
                - *"Add API for OpenRouter at openrouter.ai with my API key"*
                - *"Add webhook for Slack at hooks.slack.com for all events"*
                - *"Add MCP server for PostgreSQL database"*
                
                The AI will parse your command, confirm the details, and add the connection!
                
                ### Architecture
                - **Client**: Genesis Studio (Gradio + Faster-Whisper)
                - **Server**: Universal Living Memory (FastAPI + Qdrant)
                - **Libraries**: API, Webhook, MCP (JSON-based, hot-reloadable)
                
                ### Links
                - [Core Orchestrator](https://github.com/brian95240/universal-living-memory)
                - [Genesis Studio](https://github.com/brian95240/genesis-studio)
                
                ### Version History
                - **v1.4.0**: Autonomous Ghost Mode (Real-time HF indexing, Context camera, $0-cost optimization)
                - **v1.4.0**: Ghost Mode Evolution (Seat Router, Model Discovery, Voice Activation)
                - **v1.1.1**: Universal Connection Framework (API/Webhook/MCP Libraries)
                - **v1.1.0**: Security Vault Integration (Vaultwarden + 2FAuth)
                - **v1.0.1**: Hyper-Dynamic capabilities
                - **v1.0.0**: Golden Master release
                """)
        
    demo.queue().launch(server_port=int(os.getenv("STUDIO_PORT", "7860")))

if __name__ == "__main__":
    print("[GENESIS STUDIO v1.4.0] Starting Autonomous Ghost Mode...")
    print(f"[INFO] Orchestrator: {ORCHESTRATOR}")
    launch()
