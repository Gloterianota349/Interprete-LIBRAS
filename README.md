Este projeto integra **VLibras** e a **API de transcrição em tempo real da Gladia**, permitindo que o áudio capturado do microfone seja convertido em texto e exibido no navegador, com tradução automática em Libras.

---

## ⚡ Funcionalidades

- Captura de áudio em tempo real do microfone.
- Transcrição via Gladia API usando WebSocket.
- Atualização dinâmica do texto em uma interface web Flask.
- Integração automática com o **VLibras Widget** para tradução em Libras.
- Reconexão automática caso haja falha na transcrição.

---

## 🛠 Pré-requisitos

- Python 3.10 ou superior
- Microfone funcional
- Conexão com a internet
- API Key válida da [Gladia](https://gladia.io)

---

## 💾 Instalação

1. Clone o projeto ou baixe os arquivos.
2. Crie um ambiente virtual (recomendado):

```bash
python -m venv venv
````

3. Ative o ambiente virtual:

* **Windows**

```bash
venv\Scripts\activate
```

* **Linux/macOS**

```bash
source venv/bin/activate
```

4. Instale as dependências:

```bash
pip install flask requests websockets sounddevice numpy
```

> ⚠️ No Windows, se houver problema com `sounddevice`, instale via `pipwin`:

```bash
pip install pipwin
pipwin install sounddevice
```

---

## ⚙️ Configuração

1. Abra o arquivo `script_gladia_ajustetempo2.py`.
2. Substitua a variável `API_KEY` pela sua chave de acesso da Gladia:

```python
API_KEY = "SUA_API_KEY_AQUI"
```

---

## 🚀 Execução

No terminal, execute:

```bash
python script_gladia_ajustetempo2.py
```

* O servidor Flask será iniciado na porta **5000**.
* A captura de áudio começará automaticamente.
* O WebSocket da Gladia será conectado para transcrição em tempo real.

Abra o navegador e acesse:

```
http://localhost:5000
```

* O texto transcrito será atualizado automaticamente.
* O VLibras Widget exibirá a tradução em Libras.

---

## 🔄 Reconexão automática

Caso ocorra algum erro na transcrição, o script tentará reconectar automaticamente a cada 5 segundos.

---

## 📝 Observações

* A qualidade da transcrição depende da velocidade da internet.
* Certifique-se de que o microfone esteja configurado corretamente.
* O código já divide o texto em frases completas antes de atualizar a interface.
