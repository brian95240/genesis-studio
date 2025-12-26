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
        self.muted = False  # NEW: Mute state for noisy environments

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
        print("[✓] Whisper unloaded")

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

def add_provider(name, url, key):
    """Register a new provider at runtime"""
    if not name or not url:
        return {"error": "Name and URL are required"}
    
    payload = {
        "name": name,
        "base_url": url,
        "api_key_value": key if key else None,
        "models": ["default"]
    }
    try:
        r = requests.post(f"{ORCHESTRATOR}/v1/providers", json=payload, timeout=10)
        return r.json()
    except Exception as e: 
        return {"error": str(e)}

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
    with gr.Blocks(title="Vertex Genesis v1.0.1", theme=gr.themes.Monochrome()) as demo:
        gr.Markdown("# 🧬 Vertex Genesis v1.0.1 (Hyper-Dynamic)")
        
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
                
                # Hidden audio component for voice input
                mic = gr.Audio(source="microphone", streaming=True, visible=False)
                
                # Event handlers
                start_btn.click(
                    project_manager, 
                    inputs=[vision, provider_dropdown, log], 
                    outputs=log
                )
                mute_btn.click(toggle_mute, outputs=mute_status)
                refresh_providers.click(
                    lambda: gr.Dropdown(choices=get_providers()),
                    outputs=provider_dropdown
                )
                mic.stream(listen_loop, mic, None)
            
            # MATRIX TAB (Configuration)
            with gr.Tab("🔧 Matrix (Config)"):
                gr.Markdown("### Runtime Provider Registration")
                gr.Markdown("Add new AI providers on-the-fly without restarting the system.")
                
                with gr.Row():
                    p_name = gr.Textbox(label="Provider Name", placeholder="e.g., 'mistral', 'together'")
                    p_url = gr.Textbox(label="Base URL", placeholder="https://api.together.xyz/v1")
                    p_key = gr.Textbox(label="API Key (optional)", type="password")
                
                add_btn = gr.Button("➕ Register Provider", variant="primary")
                add_out = gr.JSON(label="Registration Result")
                
                add_btn.click(add_provider, inputs=[p_name, p_url, p_key], outputs=add_out)
                
                gr.Markdown("---")
                gr.Markdown("### Cloud Spot Pricing (Delta Engine)")
                gr.Markdown("Monitor real-time GPU spot pricing across cloud providers.")
                
                with gr.Row():
                    refresh_pricing = gr.Button("📊 Check Markets", variant="secondary")
                    unload_btn = gr.Button("🧹 Unload Whisper", variant="secondary")
                
                price_out = gr.JSON(label="Spot Pricing Data")
                
                refresh_pricing.click(get_pricing, outputs=price_out)
                unload_btn.click(
                    lambda: unload_whisper() or "Whisper model unloaded",
                    outputs=None
                )
            
            # ABOUT TAB
            with gr.Tab("ℹ️ About"):
                gr.Markdown("""
                ## Vertex Genesis v1.0.1 - Hyper-Dynamic
                
                ### Features
                - **Voice-Guided Creation**: Speak your vision, interrupt with voice commands
                - **Multi-Agent Workflow**: Architect → Engineer pipeline
                - **Runtime Provider Registration**: Add AI models without restart
                - **Cloud Spot Pricing**: Monitor cheapest GPU options
                - **Memory Integration**: Persistent context across sessions
                - **Mute Control**: Handle noisy environments mid-build
                
                ### Architecture
                - **Client**: Genesis Studio (Gradio + Faster-Whisper)
                - **Server**: Universal Living Memory (FastAPI + Qdrant)
                - **Providers**: Grok, Anthropic, Gemini, Local (Ollama)
                
                ### Keyboard Shortcuts
                - **Ctrl+Enter**: Start swarm
                - **Ctrl+M**: Toggle mute
                
                ### Links
                - [Core Orchestrator](https://github.com/brian95240/universal-living-memory)
                - [Genesis Studio](https://github.com/brian95240/genesis-studio)
                """)
        
    demo.queue().launch(server_port=int(os.getenv("STUDIO_PORT", "7860")))

if __name__ == "__main__":
    print("[GENESIS STUDIO v1.0.1] Starting...")
    print(f"[INFO] Orchestrator: {ORCHESTRATOR}")
    launch()
