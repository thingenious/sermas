---
sidebar_position: 0.0006
---
# Architecture

**ALIVE** is a modular system consisting of both frontend and backend subsystems, with clear separation of concerns, containerized deployment, and real-time multimodal interaction support.

---

## System Overview

ALIVE is split into two main subsystems:

### EVA – Empathetic Virtual Assistant (Backend)

- Built with **FastAPI** in **Python**
- Real-time WebSocket chat with LLM and RAG
- Emotional response tagging and summarization
- Handles user session, message history, and document retrieval

### AVATAR – Emotional Avatar Renderer (Frontend + API)

- Built with **ASP.NET Core** and **C#**
- Provides a REST API and WebRTC interface for avatar rendering
- Integrates with:
  - **D-ID Clips API** for face animation
  - **Azure Speech Services** for emotional TTS
- Supports dynamic rendering based on emotion-tagged content

---

## Subsystem Components

### EVA (FastAPI Application)

- `/eva/main.py` – Entrypoint with WebSocket routing and lifecycle hooks
- `/eva/llm/` – Interfaces for calling OpenAI/Anthropic APIs, emotion segmentation
- `/eva/rag/` – Local RAG document store using **ChromaDB**
- `/eva/db/` – Conversation storage and admin setting persistence (SQLite/PostgreSQL)
- `/eva/admin/` – Secure admin panel for prompt configuration, document uploads, and conversation management

### AVATAR (ASP.NET Core Service)

- `/avatar/` – Main backend orchestrating avatar generation
- `/avatar/wwwroot/` – Web frontend assets for avatar display
- `/avatar/Program.cs`, `/avatar/appsettings.json` – Service initialization and configuration

---

## Supporting Services

- **ChromaDB** (embedded) – RAG vector store for semantic search
- **Azure TTS** – Expressive speech synthesis based on emotion
- **D-ID API** – Avatar face animation based on transcript and voice
- **WebRTC** – Low-latency avatar playback

---

## Deployment Stack

| Component      | Tech             | Role                          |
|----------------|------------------|-------------------------------|
| EVA            | Python + FastAPI | WebSocket chat, LLM, RAG      |
| AVATAR         | C# + ASP.NET     | Audio/visual rendering        |
| Chroma         | Rust (DB engine) | Vector database for RAG       |
| D-ID API       | SaaS             | Face animation                |
| Azure Speech   | SaaS             | Emotion-aware TTS             |
| Frontend       | HTML/CSS/JS      | User interface for avatar     |
| DB             | PostgreSQL/SQLite| Conversation persistence      |

---

## Communication Flow

![Architecture](images/diagram.svg 'Architecture')

---

## Extensibility

- Swap model providers using `LLM_PROVIDER=openai|anthropic` in `.env`
- Extend document support by dropping files into `documents/` (or configuring another vector store)
- Customize the avatar renderer by modifying the AVATAR pipeline or using alternatives to D-ID
- Replace Azure TTS with ElevenLabs or local TTS via configurable adapters
