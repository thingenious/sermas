# EVA WebSocket Chat API Documentation

## Overview

EVA is a real-time chat API service built with WebSocket technology, featuring conversation history, intelligent summarization, and Retrieval-Augmented Generation (RAG) capabilities. The service provides structured responses with emotional context for enhanced conversational experiences.

## 🚀 Quick Start

### Connection

Connect to the WebSocket endpoint with authentication:

```text
ws://your-domain.com/ws
```

If using wscat (`npm install [-g] wscat`),
you can quickly check if a ws connection can be made:

```shell
API_KEY="your-api-key"
wscat -c "ws://localhost:8000/ws?token=${API_KEY}"
wscat -c "ws://localhost:8000/ws" -H "Authorization: Bearer ${API_KEY}"
wscat -c "ws://localhost:8000/ws" -s "chat" -s "${API_KEY}"
```

### Recommended Authentication

- **JavaScript/Browser**: Use WebSocket Subprotocol
- **Python/Server**: Use Authorization Header
- **Simple Testing**: Use Query Parameter

### Basic Flow

1. **Connect** → Establish WebSocket connection with authentication
2. **Start Conversation** → Initialize new or continue existing conversation
3. **Send Messages** → Exchange messages with intelligent responses
4. **Receive Responses** → Get segmented responses with emotional context

---

## 🔐 Authentication

EVA supports flexible authentication through multiple methods. The server attempts authentication in this priority order:

1. **Authorization Header** (`Bearer <token>`)
2. **WebSocket Subprotocol** (`chat, <your-key>`)
3. **Query Parameters** (`?token=<your-key>`)
4. **Cookies** (`token=<your-key>`)

### Authentication Methods

#### 1. WebSocket Subprotocol (Recommended for JavaScript)

```javascript
const ws = new WebSocket("ws://api.example.com/ws", ["chat", "your-api-key"]);
```

#### 2. Authorization Header (Recommended for Python)

```python
import websockets

extra_headers = {"Authorization": "Bearer your-api-key"}
ws = await websockets.connect('ws://api.example.com/ws', extra_headers=extra_headers)
```

#### 3. Query Parameter (Simple Testing)

```text
ws://api.example.com/ws?token=your-api-key
```

#### 4. Cookie (Web Applications)

```javascript
document.cookie = "token=your-api-key; path=/";
const ws = new WebSocket("ws://api.example.com/ws");
```

**Error Response** (Invalid/Missing Authentication):

```text
WebSocket closes with code 1008 and reason "Invalid or missing API key"
```

---

## 📡 Message Protocol

### Message Schema

All messages follow this JSON structure:

```json
{
  "type": "message|system|error|conversation_started|user_message|start_conversation",
  "content": "Message content",
  "emotion": "neutral|happy|excited|thoughtful|curious|confident|concerned|empathetic",
  "chunk_id": "uuid-string",
  "is_final": true|false,
  "metadata": {
    "conversation_id": "uuid-string",
    "timestamp": "2025-01-01T12:00:00.000Z",
    "sources": ["doc_id_1", "doc_id_2"]
  }
}
```

### Message Types

| Type                   | Direction       | Description                         |
| ---------------------- | --------------- | ----------------------------------- |
| `start_conversation`   | Client → Server | Initialize or continue conversation |
| `conversation_started` | Server → Client | Confirmation of conversation start  |
| `user_message`         | Client → Server | User's chat message                 |
| `message`              | Server → Client | Assistant's response segment        |
| `error`                | Server → Client | Error messages                      |

---

## 🎭 Emotion Context

Responses are segmented with emotional indicators to enhance user experience:

### Available Emotions

| Emotion      | Description                    | Use Cases                                  |
| ------------ | ------------------------------ | ------------------------------------------ |
| `neutral`    | Standard informational content | Facts, explanations, general responses     |
| `happy`      | Positive, encouraging tone     | Good news, achievements, positive feedback |
| `excited`    | Enthusiastic, energetic        | Discoveries, breakthroughs, celebrations   |
| `thoughtful` | Analytical, contemplative      | Analysis, considerations, deep thinking    |
| `curious`    | Questioning, exploring         | Questions, investigations, wonder          |
| `confident`  | Assertive, certain             | Recommendations, clear statements          |
| `concerned`  | Addressing problems            | Warnings, issues, troubleshooting          |
| `empathetic` | Understanding, supportive      | Emotional support, understanding           |

---

## 💬 Conversation Flow

### 1. Start Conversation

**Client Request:**

```json
{
  "type": "start_conversation",
  "conversation_id": "optional-existing-conversation-id"
}
```

**Server Response:**

```json
{
  "type": "conversation_started",
  "conversation_id": "uuid-conversation-id"
}
```

### 2. Send Message

**Client Request:**

```json
{
  "type": "user_message",
  "content": "What can you tell me about machine learning?"
}
```

### 3. Receive Segmented Response

**Server Response Stream:**

```json
{
  "type": "message",
  "content": "Machine learning is a subset of artificial intelligence that focuses on algorithms learning from data.",
  "emotion": "neutral",
  "chunk_id": "uuid-1",
  "is_final": false,
  "metadata": {
    "conversation_id": "uuid-conversation-id",
    "timestamp": "2025-01-01T12:00:00.000Z",
    "sources": ["ml_basics.pdf", "ai_overview.txt"]
  }
}
```

```json
{
  "type": "message",
  "content": "This is particularly exciting because it enables computers to improve their performance automatically!",
  "emotion": "excited",
  "chunk_id": "uuid-2",
  "is_final": false,
  "metadata": {
    "conversation_id": "uuid-conversation-id",
    "timestamp": "2025-01-01T12:00:01.000Z",
    "sources": ["ml_basics.pdf"]
  }
}
```

```json
{
  "type": "message",
  "content": "However, we should consider the ethical implications and data privacy aspects carefully.",
  "emotion": "thoughtful",
  "chunk_id": "uuid-3",
  "is_final": true,
  "metadata": {
    "conversation_id": "uuid-conversation-id",
    "timestamp": "2025-01-01T12:00:02.000Z",
    "sources": ["ethics_ai.pdf"]
  }
}
```

---

## 🧠 RAG Integration

The service automatically searches relevant documents to enhance responses:

### Features

- **Automatic Context**: Relevant documents are retrieved based on your message
- **Source Attribution**: Responses include source document references
- **Intelligent Filtering**: Only pertinent information is included

### Metadata Sources

Each response includes source attribution in the `metadata.sources` array:

- Document IDs that contributed to the response
- Empty array if no RAG context was used
- Helps track information provenance

---

## 📚 Conversation History

### Automatic Management

- **Persistent Storage**: All conversations are saved automatically
- **Smart Summarization**: Long conversations are intelligently summarized
- **Context Preservation**: Historical context maintained across sessions

### Summarization Behavior

- Triggered when conversation exceeds configurable threshold (default: 30 messages)
- Previous summaries are incorporated for continuity
- Recent messages remain detailed while older content is condensed
- Summaries are provided as context for better responses

---

## 🔧 Client Implementation Examples

### JavaScript/TypeScript (Recommended: Subprotocol)

```javascript
class EVAChatClient {
  constructor(apiKey, baseUrl = "ws://localhost:8000") {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.ws = null;
    this.conversationId = null;
  }

  // Recommended for JavaScript: WebSocket Subprotocol
  async connect() {
    const subprotocols = ["chat", this.apiKey];
    this.ws = new WebSocket(`${this.baseUrl}/ws`, subprotocols);
    this.setupEventHandlers();
  }

  // Alternative: Query Parameter (for simple testing)
  async connectWithQueryParam() {
    this.ws = new WebSocket(`${this.baseUrl}/ws?token=${encodeURIComponent(this.apiKey)}`);
    this.setupEventHandlers();
  }

  setupEventHandlers() {
    this.ws.onopen = () => console.log("Connected to EVA chat service");
    this.ws.onmessage = event => this.handleMessage(JSON.parse(event.data));
    this.ws.onerror = error => console.error("WebSocket error:", error);
    this.ws.onclose = event => {
      if (event.code === 1008) {
        console.error("Authentication failed:", event.reason);
      } else {
        console.log("Disconnected from EVA chat service");
      }
    };
  }

  startConversation(conversationId = null) {
    this.send({
      type: "start_conversation",
      conversation_id: conversationId,
    });
  }

  sendMessage(content) {
    this.send({
      type: "user_message",
      content: content,
    });
  }

  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  handleMessage(data) {
    switch (data.type) {
      case "conversation_started":
        this.conversationId = data.conversation_id;
        console.log("Conversation started:", this.conversationId);
        break;

      case "message":
        console.log(`[${data.emotion}] ${data.content}`);
        if (data.is_final) {
          console.log("Response complete");
        }
        break;

      case "error":
        console.error("Error:", data.content);
        break;
    }
  }
}

// Usage
const client = new EVAChatClient("your-api-key");
await client.connect();
client.startConversation();
client.sendMessage("Hello, how are you?");
```

### Python (Recommended: Authorization Header)

```python
import asyncio
import json
import websockets

class EVAChatClient:
    def __init__(self, api_key: str, base_url: str = "ws://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.ws = None
        self.conversation_id = None

    # Recommended for Python: Authorization Header
    async def connect(self):
        extra_headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        self.ws = await websockets.connect(f"{self.base_url}/ws", extra_headers=extra_headers)
        print("Connected to EVA chat service")

    # Alternative: Query Parameter (for simple testing)
    async def connect_with_query_param(self):
        from urllib.parse import urlencode
        params = urlencode({"token": self.api_key})
        uri = f"{self.base_url}/ws?{params}"
        self.ws = await websockets.connect(uri)
        print("Connected to EVA chat service")

    async def start_conversation(self, conversation_id: str = None):
        await self.send({
            "type": "start_conversation",
            "conversation_id": conversation_id
        })

    async def send_message(self, content: str):
        await self.send({
            "type": "user_message",
            "content": content
        })

    async def send(self, message: dict):
        if self.ws:
            await self.ws.send(json.dumps(message))

    async def listen(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosedError as e:
            if e.code == 1008:
                print(f"Authentication failed: {e.reason}")
            else:
                print(f"Connection closed: {e}")

    async def handle_message(self, data: dict):
        msg_type = data.get("type")

        if msg_type == "conversation_started":
            self.conversation_id = data.get("conversation_id")
            print(f"Conversation started: {self.conversation_id}")

        elif msg_type == "message":
            emotion = data.get("emotion", "neutral")
            content = data.get("content", "")
            is_final = data.get("is_final", False)

            print(f"[{emotion}] {content}")
            if is_final:
                print("Response complete")

        elif msg_type == "error":
            print(f"Error: {data.get('content')}")

# Usage
async def main():
    client = EVAChatClient("your-api-key")
    await client.connect()  # Uses recommended authorization header
    await client.start_conversation()
    await client.send_message("Hello, how are you?")
    await client.listen()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## ⚠️ Error Handling

### Common Error Scenarios

| Error                        | Cause                                     | Solution                                 |
| ---------------------------- | ----------------------------------------- | ---------------------------------------- |
| `Invalid or missing API key` | Wrong/missing authentication              | Verify API key and authentication method |
| `No active conversation`     | Message sent before starting conversation | Send `start_conversation` first          |
| `Server error`               | Internal service issue                    | Check service status, retry connection   |
| `Connection timeout`         | Network issues                            | Implement reconnection logic             |

### Authentication Error (Code 1008)

```javascript
// JavaScript
ws.onclose = event => {
  if (event.code === 1008) {
    console.error("Authentication failed:", event.reason);
    // Handle authentication failure
  }
};
```

```python
# Python
try:
    async for message in ws:
        # Handle messages
except websockets.exceptions.ConnectionClosedError as e:
    if e.code == 1008:
        print(f"Authentication failed: {e.reason}")
```

### Error Response Format

```json
{
  "type": "error",
  "content": "Description of the error",
  "emotion": "concerned"
}
```

---

## 🔧 Configuration & Deployment

### Environment Variables

```bash
# Required
CHAT_API_KEY=your-secret-api-key-here
ANTHROPIC_API_KEY=your-anthropic-key  # or OPENAI_API_KEY
RAG_DOCS_FOLDER=./documents

# Optional
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
MAX_HISTORY_MESSAGES=50
SUMMARY_THRESHOLD=30

# Database (SQLite for development, PostgreSQL for production)
DATABASE_URL=sqlite:///eva.db
# DATABASE_URL=postgresql://user:password@localhost:5432/evadb

# Security
TRUSTED_HOSTS=localhost,127.0.0.1,your-domain.com
TRUSTED_ORIGINS=https://your-frontend.com
```

### Docker Deployment

```yaml
version: "3.8"
services:
  eva-chat:
    image: your-eva-image
    ports:
      - "8000:8000"
    environment:
      - CHAT_API_KEY=your-secret-key
      - ANTHROPIC_API_KEY=your-anthropic-key
      - DATABASE_URL=postgresql://user:pass@postgres:5432/evadb
    volumes:
      - ./documents:/app/documents
```

---

## 🔧 Best Practices

### Authentication Recommendations

- **JavaScript/Browser Applications**: Use WebSocket Subprotocol for clean implementation
- **Python/Server Applications**: Use Authorization Header for standard compliance
- **Quick Testing**: Use Query Parameter for simplicity
- **Web Applications with existing auth**: Use Cookies

### Connection Management

- **Implement reconnection logic** for network failures
- **Handle authentication errors** (code 1008) appropriately
- **Use heartbeat/ping messages** for connection health checks
- **Choose appropriate authentication method** for your platform

### Message Handling

- **Buffer incomplete responses** until `is_final: true`
- **Display emotion indicators** to enhance user experience
- **Show typing indicators** during response streaming
- **Handle out-of-order messages** using `chunk_id`

### Security

- **Store API keys securely** (environment variables, secure storage)
- **Use WSS (WebSocket Secure)** in production
- **Implement rate limiting** on the client side
- **Validate all incoming messages** before processing

---

## 📊 Rate Limits & Performance

### Current Limits

- **Connections**: Configurable per API key
- **Messages**: Configurable per conversation
- **Conversation History**: Configurable message retention
- **Document Storage**: Based on your deployment

### Performance Optimization

- **Reuse conversations** instead of creating new ones frequently
- **Implement client-side caching** for conversation history
- **Use recommended authentication method** for your platform
- **Monitor WebSocket connection health**

---

## 🆘 Support & Troubleshooting

### Common Issues

**Connection Rejected (1008)**:

- Verify API key is correct
- Check authentication method implementation
- Ensure proper encoding for special characters in tokens

**No Response to Messages**:

- Ensure conversation is started first with `start_conversation`
- Check WebSocket connection status
- Verify message format matches the expected schema

**Authentication Method Selection**:

- **JavaScript**: Prefer subprotocol for cleaner implementation
- **Python**: Prefer authorization header for standard compliance
- **Testing**: Use query parameter for quick testing

### Authentication Priority Debug

Remember the server authentication priority order:

1. Authorization Header (Bearer token)
2. WebSocket Subprotocol ([chat,token])
3. Query Parameters (?token=key)
4. Cookies (token=key)

### Debugging

Enable detailed logging to troubleshoot issues:

```bash
LOG_LEVEL=debug
```

### Example Debug Connection Test

```bash
# Test authentication with different methods
API_KEY="your-api-key"
wscat -c "ws://localhost:8000/ws?token=${API_KEY}"
wscat -c "ws://localhost:8000/ws" -H "Authorization: Bearer ${API_KEY}"
wscat -c "ws://localhost:8000/ws" -s "chat" -s "${API_KEY}"
```

---

## 📖 Additional Resources

### Quick Reference

- **JavaScript**: Use `['chat', 'your-api-key']` as subprotocols
- **Python**: Use `{"Authorization": "Bearer your-api-key"}` as extra_headers
- **Testing**: Append `?token=your-api-key` to WebSocket URL

### Sample Applications

- **JavaScript Client**: Use the subprotocol method for production applications
- **Python Client**: Use the authorization header method for server-side applications
- **Testing Tools**: Use query parameter method for quick testing with tools like wscat
