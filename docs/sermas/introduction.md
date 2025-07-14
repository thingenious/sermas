---
sidebar_position: 0.0005
---
# Introduction

**ALIVE** (Avatar Liveness for Intelligent Virtual Empathy) is an open, modular system for building emotionally intelligent, multimodal virtual assistants. Designed as part of the [SERMAS Project](https://sermasproject.eu/), ALIVE integrates natural language processing, emotional modeling, real-time WebSocket communication, and 3D avatar animation into a unified experience.

At its core, ALIVE aims to combine **meaningful dialogue** with **human-like presence** by bringing together:

- 🤖 **Conversational AI** – powered by LLMs and RAG
- 🎭 **Emotional Context** – responses tagged with affective cues
- 🧍‍♀️ **Avatar Expression** – lifelike visual feedback using D-ID and emotional TTS
- 🎙️ **Multimodal Input** – support for both typed and spoken interactions
- 🌐 **Real-Time WebSocket Streaming** – ensures low-latency conversational flow

---

## System Components

ALIVE is composed of two tightly-integrated subsystems:

### EVA – Empathetic Virtual Assistant

- Real-time WebSocket chat backend (FastAPI)
- LLM-driven generation with context memory and summarization
- Emotionally segmented responses with RAG source attribution
- Conversation persistence and summarization

### AVATAR – Emotional Avatar Rendering

- ASP.NET Core API + Web frontend
- Integration with D-ID Clips for animated face generation
- Azure Speech Services for expressive TTS output
- WebRTC streaming for real-time avatar playback

---

## Key Capabilities

- **Emotion-Aware Messaging**  
  Every message is tagged with emotional tone (e.g., happy, concerned, thoughtful) to drive both voice and facial expression.

- **Contextual Memory**  
  Conversations are persisted, summarized, and reused to maintain continuity across sessions.

- **Hybrid Input & Output**  
  Supports both voice and text inputs and delivers multimodal avatar responses.

- **Open and Modular**  
  Designed to be composable, Dockerized, and adaptable for research, prototyping, or production deployments.

---

## Source Code and Docker Images

ALIVE is maintained under the open-source [`thingenious/sermas`](https://github.com/thingenious/sermas) repository on GitHub.

You can also run the system using our prebuilt Docker images:

- [`thingenious/sermas-eva`](https://hub.docker.com/r/thingenious/sermas-eva): The FastAPI-based backend with LLM and RAG support
- [`thingenious/sermas-avatar`](https://hub.docker.com/r/thingenious/sermas-avatar): The ASP.NET Core service for avatar animation and voice rendering
