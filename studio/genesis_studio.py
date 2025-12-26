import os, time, requests, importlib, queue, threading
import gradio as gr

ORCHESTRATOR_URL = "http://localhost:8000/v1/chat/completions"
# Lazy Globals
WHISPER = None
TORCH = None

class State:
    def __init__(self):
        self.listening = False
        self.interrupt = False

st = State()

def lazy_load():
    global WHISPER, TORCH
    if not WHISPER:
        import torch
        from faster_whisper import WhisperModel
        device = "cuda" if torch.cuda.is_available() else "cpu"
        WHISPER = WhisperModel("distil-large-v3", device=device, compute_type="int8")

def call_core(messages, provider="grok"):
    try:
        resp = requests.post(ORCHESTRATOR_URL, json={
            "provider": provider, "messages": messages, "use_memory": True
        }, timeout=120)
        return resp.json()["content"]
    except Exception as e:
        return f"[System Error]: {e}"

def project_manager(prompt, history):
    st.listening = True
    yield history + f"\n\n> [GENESIS]: Architecting '{prompt}'..."
    
    # 1. Architect
    design = call_core([
        {"role": "system", "content": "You are a Chief Architect. Outline files needed."},
        {"role": "user", "content": prompt}
    ], provider="anthropic")
    
    history += f"\n\n> [ARCHITECT]:\n{design}\n"
    yield history
    
    if st.interrupt:
        yield history + "\n[!] INTERRUPTED BY VOICE"
        st.interrupt = False
        return

    # 2. Engineer
    history += "\n> [ENGINEER]: Generating code..."
    yield history
    code = call_core([
        {"role": "system", "content": "You are a 10x Engineer. Write the main code."},
        {"role": "user", "content": design}
    ], provider="grok")
    
    yield history + f"\n\n> [CODE]:\n{code[:500]}...\n[DONE]"

def listen_loop(audio):
    if not st.listening: return None
    lazy_load()
    segments, _ = WHISPER.transcribe(audio, beam_size=1)
    text = " ".join([s.text for s in segments]).strip()
    if len(text) > 2:
        st.interrupt = True
        return f"[🎤 VOICE]: {text}"
    return None

def launch():
    with gr.Blocks(title="Vertex Genesis", theme=gr.themes.Monochrome()) as demo:
        gr.Markdown("# Genesis Studio v1.0")
        with gr.Row():
            inp = gr.Textbox(label="Vision")
            log = gr.Textbox(label="Swarm Log", lines=20)
        mic = gr.Audio(source="microphone", streaming=True, visible=False)
        btn = gr.Button("Initialize Swarm")
        
        btn.click(project_manager, [inp, log], log)
        mic.stream(listen_loop, mic, None)
        
    demo.queue().launch(server_port=7860)

if __name__ == "__main__":
    launch()
