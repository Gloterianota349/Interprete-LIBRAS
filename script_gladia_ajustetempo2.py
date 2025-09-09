import asyncio
import websockets
import requests
import json
import sounddevice as sd
import numpy as np
import queue
import threading
import time
import re
from flask import Flask, render_template_string, request

# ========== CONFIGURAÇÕES DO VLIBRAS/FLASK ==========
app = Flask(__name__)
current_text = "Aguardando início da tradução..."

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>VLibras Player</title>
    <style>
        body { font-family: sans-serif; padding: 40px; }
        #text-container { font-size: 28px; margin-bottom: 20px; color: #333; cursor: pointer; }
    </style>
</head>
<body>
    <div id="text-container">{{ text }}</div>

    <div vw class="enabled">
        <div vw-access-button class="active"></div>
        <div vw-plugin-wrapper>
            <div class="vw-plugin-top-wrapper"></div>
        </div>
    </div>

<script src="https://vlibras.gov.br/app/vlibras-plugin.js"></script>
<script>
    new window.VLibras.Widget('https://vlibras.gov.br/app');

    function simulateClick(el) {
        if (el) {
            el.dispatchEvent(new MouseEvent("click", { bubbles: true }));
        }
    }

    window.addEventListener("load", () => {
        setTimeout(() => {
            const accessButton = document.querySelector("[vw-access-button]");
            simulateClick(accessButton);
            simulateClick(document.getElementById("text-container"));

            setTimeout(() => {
                const botoes = document.querySelectorAll('button');
                const botaoVelocidade = Array.from(botoes).find(btn => btn.textContent.includes('x'));
                if (botaoVelocidade) {
                    simulateClick(botaoVelocidade);
                    simulateClick(botaoVelocidade);
                    console.log("⚡ Botão de velocidade clicado");
                }
            }, 10000);
        }, 1000);
    });

    let currentText = "";

    setInterval(() => {
        fetch("/text")
            .then(res => res.json())
            .then(data => {
                if (data.text !== currentText) {
                    currentText = data.text;
                    const textEl = document.getElementById("text-container");
                    textEl.innerText = currentText;
                    simulateClick(textEl);
                }
            });
    }, 2000);
</script>

</body>
</html>
"""  # (mantenha o conteúdo completo do seu HTML aqui)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, text=current_text)

@app.route('/text')
def get_text():
    return {"text": current_text}

@app.route('/update', methods=['POST'])
def update():
    global current_text
    data = request.json
    current_text = data.get("text", current_text)
    return {"status": "ok", "text": current_text}

def run_flask():
    app.run(port=5000)

# ========== CONFIGURAÇÕES DO ÁUDIO E GLADIA ==========
API_KEY = "834bdbfa-60cf-4d3b-9497-d3188a7888ca"
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
CHANNELS = 1
DTYPE = 'int16'

audio_queue = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print("⚠️ Erro de captura:", status)
    audio_queue.put(indata.copy())

def start_audio_stream():
    return sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=DTYPE,
        callback=audio_callback,
        blocksize=CHUNK_SIZE
    )

def separar_frases(texto):
    frases = re.split(r'(?<=[.!?])\s+', texto.strip())
    return [f for f in frases if f]

# ========== FUNÇÃO PRINCIPAL COM GLADIA ==========
async def iniciar_transcricao_gladia():
    print("🌐 Iniciando sessão na Gladia...")
    response = requests.post(
        "https://api.gladia.io/v2/live",
        headers={
            "Content-Type": "application/json",
            "x-gladia-key": API_KEY
        },
        json={  # Parâmetros válidos
            "encoding": "wav/pcm",
            "sample_rate": SAMPLE_RATE,
            "bit_depth": 16,
            "channels": CHANNELS
        }
    )

    if not response.ok:
        print("❌ Erro ao iniciar sessão:", response.status_code, response.text)
        return

    ws_url = response.json()["url"]
    print(f"🔗 WebSocket conectado: {ws_url}")

    try:
        async with websockets.connect(ws_url) as ws:
            print("✅ Conectado ao WebSocket")
            with start_audio_stream():
                print("🎙️ Capturando áudio em tempo real...")

                async def enviar_audio():
                    while True:
                        chunk = audio_queue.get()
                        await ws.send(chunk.tobytes())
                        await asyncio.sleep(0.01)

                async def receber_transcricoes():
                    buffer = ""
                    while True:
                        message = await ws.recv()
                        data = json.loads(message)

                        if data["type"] == "transcript":
                            text = data["data"]["utterance"]["text"]
                            is_final = data["data"].get("is_final", False)

                            if is_final:
                                buffer += " " + text
                                frases = separar_frases(buffer)
                                for frase in frases[:-1]:
                                    print(f"\n📝 Frase completa: {frase}")
                                    requests.post("http://localhost:5000/update", json={"text": frase})
                                    await asyncio.sleep(0.4 + len(frase) * 0.03)  # Delay inteligente
                                buffer = frases[-1] if frases else ""
                            else:
                                print(f"🗣️ Parcial: {text}")

                await asyncio.gather(enviar_audio(), receber_transcricoes())

    except Exception as e:
        print(f"❌ Erro com WebSocket: {e}")

# ========== EXECUÇÃO ==========
if __name__ == "__main__":
    print("🚀 Iniciando servidor Flask + Gladia...")
    threading.Thread(target=run_flask, daemon=True).start()
    time.sleep(2)

    while True:
        try:
            asyncio.run(iniciar_transcricao_gladia())
        except Exception as e:
            print(f"⚠️ Transcrição interrompida. Tentando reconectar em 5s...\nDetalhes: {e}")
            time.sleep(5)