# API Reference

Complete technical reference for the EVA WebSocket Chat API.

## Message Schema

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

## Message Types

### Client → Server Messages

#### start_conversation

Initialize a new conversation or continue an existing one.

```json
{
  "type": "start_conversation",
  "conversation_id": "optional-existing-conversation-id"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | ✅ | Must be `"start_conversation"` |
| `conversation_id` | string | ❌ | UUID of existing conversation to continue |

#### user_message

Send a message in the active conversation.

```json
{
  "type": "user_message",
  "content": "Your message content here"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | ✅ | Must be `"user_message"` |
| `content` | string | ✅ | The message content (max length configurable) |

### Server → Client Messages

#### conversation_started

Confirmation that a conversation has been started.

```json
{
  "type": "conversation_started",
  "conversation_id": "uuid-conversation-id",
  "metadata": {
    "timestamp": "2025-01-01T12:00:00.000Z"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Always `"conversation_started"` |
| `conversation_id` | string | UUID for the conversation |
| `metadata.timestamp` | string | ISO 8601 timestamp |

#### message

Response segments from the AI assistant.

```json
{
  "type": "message",
  "content": "Response content segment",
  "emotion": "thoughtful",
  "chunk_id": "uuid-chunk-id",
  "is_final": false,
  "metadata": {
    "conversation_id": "uuid-conversation-id",
    "timestamp": "2025-01-01T12:00:00.000Z",
    "sources": ["doc_id_1", "doc_id_2"]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Always `"message"` |
| `content` | string | The response content segment |
| `emotion` | string | Emotional context (see [Emotions](#emotions)) |
| `chunk_id` | string | Unique identifier for this chunk |
| `is_final` | boolean | `true` if this is the last chunk in the response |
| `metadata.conversation_id` | string | UUID of the conversation |
| `metadata.timestamp` | string | ISO 8601 timestamp |
| `metadata.sources` | array | Document IDs used in RAG (empty if none) |

#### error

Error messages from the server.

```json
{
  "type": "error",
  "content": "Error description",
  "emotion": "concerned",
  "metadata": {
    "timestamp": "2025-01-01T12:00:00.000Z",
    "error_code": "NO_ACTIVE_CONVERSATION"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Always `"error"` |
| `content` | string | Human-readable error description |
| `emotion` | string | Usually `"concerned"` |
| `metadata.error_code` | string | Machine-readable error code |

## Emotions

Response segments include emotional context to enhance user experience:

### Emotion Types

| Emotion | Description | Typical Usage |
|---------|-------------|---------------|
| `neutral` | Standard, informational tone | Facts, explanations, general responses |
| `happy` | Positive, encouraging tone | Good news, achievements, positive feedback |
| `excited` | Enthusiastic, energetic | Discoveries, breakthroughs, celebrations |
| `thoughtful` | Analytical, contemplative | Analysis, considerations, deep thinking |
| `curious` | Questioning, exploring | Questions, investigations, expressing wonder |
| `confident` | Assertive, certain | Recommendations, definitive statements |
| `concerned` | Addressing problems | Warnings, issues, troubleshooting |
| `empathetic` | Understanding, supportive | Emotional support, showing understanding |

### Using Emotions in UI

```javascript
function getEmotionStyle(emotion) {
    const styles = {
        neutral: { color: '#333', icon: '💬' },
        happy: { color: '#28a745', icon: '😊' },
        excited: { color: '#ffc107', icon: '🎉' },
        thoughtful: { color: '#6f42c1', icon: '🤔' },
        curious: { color: '#17a2b8', icon: '🤨' },
        confident: { color: '#007bff', icon: '💪' },
        concerned: { color: '#dc3545', icon: '⚠️' },
        empathetic: { color: '#fd7e14', icon: '🤗' }
    };
    return styles[emotion] || styles.neutral;
}
```

## Authentication

### Authentication Methods Priority

The server attempts authentication in this order:

1. **Authorization Header** - `Authorization: Bearer <token>`
2. **WebSocket Subprotocol** - `protocols: ['chat', '<api-key>']`
3. **Query Parameter** - `?token=<api-key>`
4. **Cookie** - `Cookie: token=<api-key>`

### Error Codes

| Code | Reason | Description |
|------|--------|-------------|
| 1008 | Policy Violation | Invalid or missing API key |
| 1000 | Normal Closure | Clean disconnection |
| 1001 | Going Away | Server shutting down |
| 1011 | Internal Error | Server error occurred |

## RAG Integration

### Automatic Document Retrieval

EVA automatically searches relevant documents based on user messages:

- **Context-aware**: Searches are based on message content and conversation history
- **Source attribution**: All sources are listed in `metadata.sources`
- **Relevance filtering**: Only pertinent information is included

### Source Metadata

```json
{
  "type": "message",
  "content": "Based on the documentation...",
  "metadata": {
    "sources": [
      "user_manual_v2.pdf",
      "api_changelog.md",
      "troubleshooting_guide.txt"
    ]
  }
}
```

## Conversation Management

### Conversation Lifecycle

1. **Start** - Initialize with `start_conversation`
2. **Chat** - Exchange messages with `user_message` and `message` responses
3. **Persist** - Conversations are automatically saved
4. **Resume** - Continue later using the `conversation_id`
5. **Summarize** - Long conversations are automatically summarized

### Automatic Summarization

- **Trigger**: Configurable message threshold (default: 30 messages)
- **Process**: Previous messages are intelligently condensed
- **Preservation**: Recent context is maintained while older content is summarized
- **Continuity**: Summaries include previous summaries for full context

## Rate Limits & Performance

### Default Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| Connections per API key | 10 | Configurable |
| Messages per minute | 60 | Configurable |
| Message length | 4096 chars | Configurable |
| Conversation history | 1000 messages | Before summarization |

### Optimization Tips

- **Reuse conversations** instead of creating new ones frequently
- **Buffer chunks** until `is_final: true` for better UX
- **Implement reconnection logic** for network resilience
- **Cache conversation IDs** to resume conversations

## Error Handling

### Common Error Scenarios

#### Authentication Errors

```json
{
  "type": "error",
  "content": "Invalid API key provided",
  "metadata": {
    "error_code": "INVALID_API_KEY"
  }
}
```

**WebSocket closes with code 1008**

#### No Active Conversation

```json
{
  "type": "error",
  "content": "No active conversation. Please start a conversation first.",
  "metadata": {
    "error_code": "NO_ACTIVE_CONVERSATION"
  }
}
```

**Solution**: Send `start_conversation` before sending messages.

#### Server Errors

```json
{
  "type": "error",
  "content": "Internal server error occurred",
  "metadata": {
    "error_code": "INTERNAL_ERROR",
    "request_id": "req_12345"
  }
}
```

### Error Codes Reference

| Code | Description | Action |
|------|-------------|--------|
| `INVALID_API_KEY` | API key is invalid or expired | Check API key, contact admin |
| `NO_ACTIVE_CONVERSATION` | Message sent without starting conversation | Send `start_conversation` first |
| `MESSAGE_TOO_LONG` | Message exceeds length limit | Shorten message content |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Implement backoff, reduce frequency |
| `INTERNAL_ERROR` | Server-side error | Retry request, contact support if persistent |
| `CONVERSATION_NOT_FOUND` | Invalid conversation ID | Start new conversation |

## Configuration & Deployment

### Environment Variables

```bash
# Core Configuration
CHAT_API_KEY=your-secret-api-key-here
ANTHROPIC_API_KEY=your-anthropic-key  # or OPENAI_API_KEY
RAG_DOCS_FOLDER=./documents

# Server Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info

# Conversation Management
MAX_HISTORY_MESSAGES=50
SUMMARY_THRESHOLD=30

# Database Configuration
DATABASE_URL=sqlite:///eva.db
# DATABASE_URL=postgresql://user:password@localhost:5432/evadb

# Security
TRUSTED_HOSTS=localhost,127.0.0.1,your-domain.com
TRUSTED_ORIGINS=https://your-frontend.com

# Rate Limiting
MAX_CONNECTIONS_PER_KEY=10
MAX_MESSAGES_PER_MINUTE=60
MAX_MESSAGE_LENGTH=4096
```

### Docker Configuration

```yaml
version: '3.8'
services:
  eva-chat:
    image: eva-chat-api:latest
    ports:
      - "8000:8000"
    environment:
      - CHAT_API_KEY=${CHAT_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/evadb
      - RAG_DOCS_FOLDER=/app/documents
    volumes:
      - ./documents:/app/documents:ro
      - eva_data:/app/data
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=evadb
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  eva_data:
  postgres_data:
```

## Security Best Practices

### API Key Management

- **Environment Variables**: Store keys in environment variables, never in code
- **Rotation**: Regularly rotate API keys
- **Scope**: Use separate keys for different environments (dev/staging/prod)
- **Monitoring**: Monitor API key usage for unusual patterns

### Connection Security

- **WSS**: Use `wss://` (WebSocket Secure) in production
- **CORS**: Configure trusted origins properly
- **Headers**: Validate all incoming headers
- **Rate Limiting**: Implement client-side and server-side rate limiting

### Input Validation

- **Message Length**: Enforce maximum message lengths
- **Content Filtering**: Validate message content format
- **JSON Schema**: Validate all incoming JSON against schemas
- **Sanitization**: Sanitize user inputs before processing

## WebSocket Connection Lifecycle

### Connection States

```mermaid
stateDiagram-v2
    [*] --> Connecting
    Connecting --> Connected : Authentication Success
    Connecting --> Failed : Authentication Failed (1008)
    Connected --> ConversationReady : start_conversation
    ConversationReady --> Chatting : user_message
    Chatting --> Chatting : message exchange
    Chatting --> Disconnected : connection closed
    Connected --> Disconnected : connection closed
    ConversationReady --> Disconnected : connection closed
    Failed --> [*]
    Disconnected --> [*]
```

### Connection Events

```javascript
// Connection event handling
ws.onopen = function(event) {
    console.log('WebSocket connection opened');
    // Connection established, ready to start conversation
};

ws.onclose = function(event) {
    switch(event.code) {
        case 1000: // Normal closure
            console.log('Connection closed normally');
            break;
        case 1008: // Policy violation (auth failed)
            console.error('Authentication failed:', event.reason);
            break;
        case 1011: // Internal error
            console.error('Server error:', event.reason);
            break;
        default:
            console.warn('Connection closed unexpectedly:', event.code, event.reason);
    }
};

ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};
```

## Advanced Features

### Conversation History Management

Conversations are automatically managed with intelligent features:

#### History Preservation

- All messages are stored with full context
- Metadata includes timestamps and source attribution
- Conversation state persists across connections

#### Smart Summarization

When conversations exceed the configured threshold:

1. **Analysis**: System analyzes conversation flow and key topics
2. **Summarization**: Older messages are condensed while preserving important context
3. **Integration**: Summaries are seamlessly integrated into conversation context
4. **Continuity**: New responses consider both recent messages and historical summaries

```json
{
  "type": "message",
  "content": "Based on our earlier discussion about API design...",
  "emotion": "thoughtful",
  "metadata": {
    "conversation_id": "uuid",
    "has_summary": true,
    "summary_version": 2
  }
}
```

### RAG Document Integration

#### Document Processing

- **Automatic Indexing**: Documents are processed and indexed for semantic search
- **Context Extraction**: Relevant passages are extracted based on conversation context
- **Source Tracking**: Full attribution chain from documents to responses

#### Search Strategy

1. **Query Analysis**: User message is analyzed for key concepts
2. **Semantic Search**: Documents are searched using semantic similarity
3. **Context Ranking**: Results are ranked by relevance to conversation
4. **Integration**: Selected content is integrated into AI context

## Monitoring & Observability

### Health Monitoring

#### Health Check Endpoint

```bash
# HTTP health check (if available)
curl http://your-domain.com/health

# Response
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00.000Z",
  "version": "1.0.0",
  "uptime": 3600,
  "active_connections": 42
}
```

#### WebSocket Ping/Pong

```javascript
// Implement heartbeat to monitor connection health
setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.ping(); // Browser doesn't support ping, use custom message
        // Or send a custom heartbeat message
        ws.send(JSON.stringify({type: 'ping'}));
    }
}, 30000); // Every 30 seconds
```

### Logging & Metrics

Key metrics to monitor:

- **Connection Count**: Active WebSocket connections
- **Message Rate**: Messages per second/minute
- **Response Time**: Time from user message to first response chunk
- **Error Rate**: Percentage of failed requests
- **Conversation Length**: Average messages per conversation
- **RAG Hit Rate**: Percentage of responses using document context

## Testing & Development

### Testing Tools

#### wscat (Command Line)

```bash
# Install wscat
npm install -g wscat

# Test connection with different auth methods
wscat -c "ws://localhost:8000/ws?token=test-key"
wscat -c "ws://localhost:8000/ws" -H "Authorization: Bearer test-key"
wscat -c "ws://localhost:8000/ws" -s "chat" -s "test-key"
```

#### Postman/Insomnia

Both tools support WebSocket testing with:

- Authentication headers
- Message templating  
- Response validation
- Connection management

### Development Environment

#### Local Setup

```shell
# Clone repository
git clone https://github.com/thingenious/eva.git
cd eva

# Install dependencies
pip install -r requirements/all.txt

# Set environment variables
export CHAT_API_KEY=dev-test-key-12345
export ANTHROPIC_API_KEY=your-anthropic-key
export RAG_DOCS_FOLDER=./test_documents
export DATABASE_URL=sqlite:///dev_eva.db

# Run development server
python -m eva.main --host 0.0.0.0 --port 8000
# or:
python -m uvicorn eva.main:app --reload --host 0.0.0.0 --port 8000
```

#### Test Documents

Place test documents in your RAG folder:

```text
test_documents/
├── api_docs.md
├── user_manual.pdf
├── faq.txt
└── troubleshooting.json
```

## Troubleshooting Guide

### Common Issues & Solutions

#### Issue: Connection Rejected (Code 1008)

**Symptoms**: WebSocket closes immediately with authentication error

**Possible Causes**:

- Invalid API key
- Incorrect authentication method
- Special characters in API key not properly encoded
- API key expired or revoked

**Solutions**:

```javascript
// Verify API key encoding
const apiKey = "your-api-key";
const encodedKey = encodeURIComponent(apiKey);

// Test different auth methods
// Method 1: Query parameter
const ws1 = new WebSocket(`ws://localhost:8000/ws?token=${encodedKey}`);

// Method 2: Subprotocol
const ws2 = new WebSocket('ws://localhost:8000/ws', ['chat', `${apiKey}`]);

// Method 3: Header (if your client supports it)
// This varies by WebSocket client implementation
```

#### Issue: No Response to Messages

**Symptoms**: Messages sent but no response received

**Possible Causes**:

- Conversation not started
- WebSocket connection not fully established
- Invalid message format
- Server processing error

**Solutions**:

```javascript
// Ensure proper sequence
ws.onopen = function() {
    // 1. Start conversation first
    ws.send(JSON.stringify({type: 'start_conversation'}));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'conversation_started') {
        // 2. Only send messages after conversation started
        ws.send(JSON.stringify({
            type: 'user_message',
            content: 'Hello!'
        }));
    }
};
```

#### Issue: Incomplete Responses

**Symptoms**: Response appears cut off or missing segments

**Possible Causes**:

- Not handling message chunks properly
- Ignoring `is_final` flag
- Connection interruption during response

**Solutions**:

```javascript
let responseBuffer = [];
let currentChunkId = null;

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'message') {
        // Buffer all chunks
        responseBuffer.push({
            content: data.content,
            emotion: data.emotion,
            chunk_id: data.chunk_id
        });
        
        // Only process complete response
        if (data.is_final) {
            displayCompleteResponse(responseBuffer);
            responseBuffer = []; // Reset for next response
        }
    }
};
```

#### Issue: High Latency

**Symptoms**: Slow response times

**Possible Causes**:

- Network latency
- Server overload
- Large document corpus for RAG
- Complex conversation context

**Solutions**:

- Implement connection pooling
- Use geographically closer servers
- Optimize document indexing
- Consider conversation summarization frequency

## API Changelog

### Version 1.0.0 (Current)

- Initial release with core WebSocket functionality
- Authentication via multiple methods
- Conversation management with summarization
- RAG integration with source attribution
- Emotional context in responses
- Segmented response delivery

### Planned Features

- **Message History API**: REST endpoints for conversation history
- **Batch Processing**: Send multiple messages in one request
- **Custom Emotions**: User-defined emotional contexts
- **File Upload**: Direct document upload for RAG
- **Conversation Templates**: Pre-defined conversation starters
- **Analytics Dashboard**: Usage metrics and insights

---

*This API reference is for EVA WebSocket Chat API v1.0. For the latest updates and changes, check the changelog or contact support.*
