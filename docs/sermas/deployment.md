---
sidebar_position: 0.0007
---

# Deployment

This guide outlines how to deploy the ALIVE system using the official Docker images. ALIVE consists of two main services:

- `sermas-eva`: Backend for chat, emotion tagging, RAG, and LLM integration
- `sermas-avatar`: Avatar rendering and emotional TTS using D-ID and Azure

---

## Prerequisites

Before you begin, ensure you have:

- Docker installed (v27+ recommended) including the compose plugin
- A valid OpenAI or Anthropic API key
- An Azure Speech key (for TTS)
- A D-ID API key (for the 3D avatar)

---

## Docker Images

The official images are hosted on Docker Hub:

| Component | Image |
|-----------|-------|
| EVA       | [`thingenious/sermas-eva`](https://hub.docker.com/r/thingenious/sermas-eva) |
| AVATAR    | [`thingenious/sermas-avatar`](https://hub.docker.com/r/thingenious/sermas-avatar) |

---

## Quick Start with `docker-compose`

1. Copy and rename the example configuration:

    ```shell
    cp compose.example.yaml compose.yaml
    # you might want to commment out / remove the "build" sections
    cp .env.example .env
    ```

2. Edit the `.env` file and fill in:

    ```env
    OPENAI_API_KEY=your-key
    AZURE_SPEECH_API_KEY=your-key
    DID_API_KEY=your-did-key
    CHAT_API_KEY=choose-a-secret
    # example generation with:
    # openssl rand -hex 32
    # or python -c "import secrets; print(secrets.token_hex(32))"
    ```

3. Start the stack:

    ```shell
    docker compose -f compose.yaml up -d
    ```

Once running:

- EVA backend: [http://localhost:8000](http://localhost:8000), WebSocket at [ws://localhost:8000/ws](ws://localhost:8000/ws)
- AVATAR frontend: [http://localhost:3000](http://localhost:3000)

---

## Reverse Proxy with Nginx and HTTPS (Recommended)

To expose ALIVE services over the internet securely, you can place an Nginx reverse proxy in front of the EVA and AVATAR containers and enable HTTPS using Let's Encrypt and Certbot.

### Example Nginx Config (for `/etc/nginx/sites-available/alive`)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;  # AVATAR frontend
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://localhost:8000/ws/;  # EVA WebSocket
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }

    location /admin/ {
        proxy_pass http://localhost:8000/admin/;
    }

    location /healthz {
        proxy_pass http://localhost:8000/healthz;
    }
}
```

## Advanced Configuration

You can configure behavior via environment variables. Some key options:

| Variable | Description |
|----------|-------------|
| `LLM_PROVIDER` | `openai` or `anthropic` |
| `MAX_HISTORY_MESSAGES` | Number of chat messages retained |
| `CHROMA_DB_DIR` | Directory for Chroma vector DB |
| `CHAT_WS_URL` | URL for WebSocket clients |
| `ADMIN_API_KEY` | Protects admin endpoints |

---

## Health & Debug

- EVA: `GET /healthz` → `{ "status": "ok" }`
- Admin Panel: `GET /admin/` (requires token)

You can inspect container logs with:

```shell
docker compose logs -f
```

---

## Deployment Notes

- Designed to work locally or behind a reverse proxy (e.g., nginx)
- For production use, mount volumes and enable HTTPS
- You may configure persistent PostgreSQL storage if needed

---

## Source & Updates

For latest changes, visit the GitHub repository:

👉 [`thingenious/sermas`](https://github.com/thingenious/sermas)
