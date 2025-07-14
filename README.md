# ALIVE – Avatar Liveness for Intelligent Virtual Empathy

[![Coverage Status](https://coveralls.io/repos/github/thingenious/sermas/badge.svg)](https://coveralls.io/github/thingenious/sermas)

**ALIVE** is an integrated conversational AI system combining empathetic WebSocket-based chat (`eva/`) with avatar-driven emotional speech and facial animation (`avatar/`). It enables immersive, emotionally intelligent interactions using LLMs, RAG, D-ID, Azure Speech, and WebRTC.

---

## 🧠 System Overview

- 💬 WebSocket-based chat backend with LLM, memory, RAG
- 🎭 Emotion-tagged responses for enhanced UX
- 📚 Retrieval-Augmented Generation with source attribution
- 🧍‍♀️ Avatar rendering with emotional speech and facial animation
- 🎙️ Multi-modal input: text + voice
- ⚙️ Dockerized deployment for full stack (FastAPI + .NET)

---

## 📁 Repository Structure

```txt
/
├── eva/                  # EVA (FastAPI backend for chat and LLM)
├── avatar/               # Avatar interface (ASP.NET Core + WebRTC)
├── .env.example          # Environment variables (template)
├── compose.example.yaml  # Docker Compose stack (template)
├── Eva.Containerfile     # Dockerfile for EVA backend
├── Avatar.Containerfile  # Dockerfile for Avatar service
└── README.md             # You're here
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/thingenious/alive.git
cd alive
cp .env.example .env
cp compose.example.yaml docker-compose.yaml
```

Update `.env` with valid API keys for:

- `CHAT_API_KEY` (LLM backend)
- `DID_API_KEY` (D-ID Clips API)
- `AZURE_SPEECH_API_KEY` (Microsoft Azure Speech)

### 2. Run with Docker Compose

```bash
docker compose --env-file .env -f docker-compose.yaml up --build
```

Services will be available at:

- EVA (WebSocket backend): `ws://localhost:8000/ws`
- AVATAR UI/API: `http://localhost:3000`

---

## 🔧 Configuration

All configuration is driven via the `.env` file. Example:

```env
# Common
CHAT_API_KEY=your-chat-key
CHAT_WS_URL=ws://localhost:8000/ws

# Avatar
DID_API_KEY=your-did-key
AZURE_SPEECH_API_KEY=your-azure-key
AVATAR_PORT=3000

# EVA
EVA_PORT=8000
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
RAG_DOCS_FOLDER=documents
DATABASE_URL=postgresql://alive:alive@db:5432/alive
```

> ✅ See `.env.example` for full list

---

## 🧱 Build Images Manually (Optional)

To build and run the containers manually:

### EVA

```bash
docker build -t thingenious/sermas-eva -f Eva.Containerfile .
docker run --env-file .env -p 8000:8000 thingenious/sermas-eva
```

### Avatar

```bash
docker build -t thingenious/sermas-avatar -f Avatar.Containerfile .
docker run --env-file .env -p 3000:3000 thingenious/sermas-avatar
```

---

## 🧩 Components

### EVA (`/eva`)

- WebSocket-based FastAPI backend
- LLM-powered chat with emotion tagging and memory
- RAG integration (via ChromaDB or other)
- Message schema includes emotion, chunk ID, metadata
- Includes persistent conversation storage and summarization

📖 See [`eva.README.md`](./eva.README.md) for message protocols and API usage.

---

### AVATAR (`/avatar`)

- ASP.NET Core service that:
  - Receives LLM responses and maps emotions to TTS styles
  - Streams avatar video using D-ID
  - Synthesizes speech via Azure Speech Services
- Serves frontend chat interface with:
  - WebRTC video
  - Voice + text input
  - Real-time streaming avatar response

📖 See [`avatar/README.md`](./avatar/README.md) for service API and frontend integration.

---

## 🧪 Health Checks

Both services expose health endpoints used in Docker Compose:

- EVA: `http://localhost:8000/health`
- AVATAR: `http://localhost:3000/health`

---

## 🔒 Security Notes

- All API keys are managed via environment variables
- Use HTTPS in production for avatar/microphone support
- Never expose `.env` or secrets in public deployments
- Implement authentication if deploying beyond local

---

## 📝 License

This project is developed as part of the [SERMAS Project](https://sermasproject.eu/).  
Please refer to the official documentation or maintainers for licensing terms.

---

## 👥 Maintainers

**Thingenious**  
GitHub: [@thingenious](https://github.com/thingenious)
