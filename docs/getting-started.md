# Getting Started

This guide will walk you through connecting to the EVA WebSocket Chat API and sending your first message.

## Prerequisites

- An EVA API key (contact your administrator)
- WebSocket client capability (built into most modern languages)
- Basic understanding of JSON and WebSocket protocols

## Connection Setup

### WebSocket Endpoint

```text
ws://your-domain.com/ws
```

!!! tip "Security in Production"
    Use `wss://` (WebSocket Secure) in production environments for encrypted connections.

## Authentication Methods

EVA supports multiple authentication methods to fit different use cases. The server attempts authentication in this priority order:

1. **Authorization Header** (`Bearer <token>`)
2. **WebSocket Subprotocol** (`chat, <your-key>`)
3. **Query Parameters** (`?token=<your-key>`)
4. **Cookies** (`token=<your-key>`)

### Method 1: WebSocket Subprotocol (Recommended for JavaScript)

=== "JavaScript"
    ```javascript
    const ws = new WebSocket('ws://api.example.com/ws', ['chat', 'your-api-key']);
    ```

=== "Node.js"
    ```javascript
    const WebSocket = require('ws');

    const ws = new WebSocket('ws://api.example.com/ws', {
        protocols: ['chat', 'your-api-key']
    });
    ```

### Method 2: Authorization Header (Recommended for Python)

=== "Python (websockets)"
    ```python
    import websockets

    extra_headers = {"Authorization": "Bearer your-api-key"}
    ws = await websockets.connect('ws://api.example.com/ws', extra_headers=extra_headers)
    ```

=== "Python (websocket-client)"
    ```python
    import websocket

    header = {"Authorization": "Bearer your-api-key"}
    ws = websocket.WebSocket()
    ws.connect('ws://api.example.com/ws', header=header)
    ```

### Method 3: Query Parameter (Simple Testing)

```bash
# Using wscat
wscat -c "ws://api.example.com/ws?token=your-api-key"

# Using curl for testing
curl --include \
     --no-buffer \
     --header "Connection: Upgrade" \
     --header "Upgrade: websocket" \
     --header "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
     --header "Sec-WebSocket-Version: 13" \
     "ws://api.example.com/ws?token=your-api-key"
```

### Method 4: Cookie (Web Applications)

```javascript
// Set cookie first
document.cookie = "token=your-api-key; path=/; secure; samesite=strict";

// Then connect normally
const ws = new WebSocket('ws://api.example.com/ws');
```

## Basic Message Flow

### Step 1: Establish Connection

Choose your authentication method and connect to the WebSocket.

```javascript
const ws = new WebSocket('ws://api.example.com/ws', ['chat', 'your-api-key']);

ws.onopen = function() {
    console.log('Connected to EVA!');
    // Ready to start conversation
};

ws.onerror = function(error) {
    console.error('Connection error:', error);
};

ws.onclose = function(event) {
    if (event.code === 1008) {
        console.error('Authentication failed:', event.reason);
    } else {
        console.log('Disconnected');
    }
};
```

### Step 2: Start a Conversation

Before sending messages, you must start a conversation:

```javascript
// Start a new conversation
const startMessage = {
    type: 'start_conversation'
};

// Or continue an existing conversation
const continueMessage = {
    type: 'start_conversation',
    conversation_id: 'your-existing-conversation-id'
};

ws.send(JSON.stringify(startMessage));
```

### Step 3: Handle Conversation Started

```javascript
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'conversation_started') {
        console.log('Conversation ID:', data.conversation_id);
        // Store this ID for future reference
        conversationId = data.conversation_id;
        
        // Now you can send messages!
        sendMessage('Hello, EVA! How are you today?');
    }
};
```

### Step 4: Send Messages

```javascript
function sendMessage(content) {
    const message = {
        type: 'user_message',
        content: content
    };
    
    ws.send(JSON.stringify(message));
}
```

### Step 5: Handle Responses

EVA sends responses in segments, each with emotional context:

```javascript
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    switch (data.type) {
        case 'conversation_started':
            conversationId = data.conversation_id;
            console.log('Ready to chat!');
            break;
            
        case 'message':
            // Display the message segment
            displayMessage(data.content, data.emotion);
            
            // Check if this is the final segment
            if (data.is_final) {
                console.log('Response complete');
                enableInput(); // Re-enable user input
            }
            break;
            
        case 'error':
            console.error('EVA Error:', data.content);
            break;
    }
};

function displayMessage(content, emotion) {
    // Create message element with emotion styling
    const messageEl = document.createElement('div');
    messageEl.className = `message emotion-${emotion}`;
    messageEl.textContent = content;
    
    // Add to chat display
    document.getElementById('chat').appendChild(messageEl);
}
```

## Understanding Emotions

EVA provides emotional context with each response segment:

| Emotion | Description | Example Use |
|---------|-------------|-------------|
| `neutral` | Standard informational content | "The API documentation explains..." |
| `happy` | Positive, encouraging tone | "Great choice! This approach will work well." |
| `excited` | Enthusiastic, energetic | "This is amazing! The possibilities are endless!" |
| `thoughtful` | Analytical, contemplative | "Let me consider the implications..." |
| `curious` | Questioning, exploring | "I wonder if we could also try..." |
| `confident` | Assertive, certain | "I recommend using this method." |
| `concerned` | Addressing problems | "However, there are some potential issues..." |
| `empathetic` | Understanding, supportive | "I understand this can be frustrating." |

## Complete Minimal Example

Here's a complete working example:

=== "JavaScript"
    ```javascript
    class SimpleEVAClient {
        constructor(apiKey, url = 'ws://localhost:8000/ws') {
            this.apiKey = apiKey;
            this.url = url;
            this.conversationId = null;
        }

        connect() {
            this.ws = new WebSocket(this.url, ['chat', `${this.apiKey}`]);
            
            this.ws.onopen = () => {
                console.log('✅ Connected to EVA');
                this.startConversation();
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };
            
            this.ws.onclose = (event) => {
                if (event.code === 1008) {
                    console.error('❌ Authentication failed');
                }
            };
        }
        
        startConversation() {
            this.send({ type: 'start_conversation' });
        }
        
        sendMessage(content) {
            this.send({ type: 'user_message', content });
        }
        
        send(message) {
            this.ws.send(JSON.stringify(message));
        }
        
        handleMessage(data) {
            switch (data.type) {
                case 'conversation_started':
                    this.conversationId = data.conversation_id;
                    console.log('🚀 Ready to chat!');
                    break;
                    
                case 'message':
                    console.log(`[${data.emotion}] ${data.content}`);
                    if (data.is_final) {
                        console.log('✨ Response complete\n');
                    }
                    break;
                    
                case 'error':
                    console.error('💥 Error:', data.content);
                    break;
            }
        }
    }
    
    // Usage
    const client = new SimpleEVAClient('your-api-key');
    client.connect();
    
    // After connection is established, you can send messages
    setTimeout(() => {
        client.sendMessage('Hello EVA! Tell me about machine learning.');
    }, 1000);
    ```

=== "Python"
    ```python
    import asyncio
    import json
    import websockets

    class SimpleEVAClient:
        def __init__(self, api_key: str, url: str = "ws://localhost:8000/ws"):
            self.api_key = api_key
            self.url = url
            self.conversation_id = None
            self.ws = None
        
        async def connect(self):
            headers = {"Authorization": f"Bearer {self.api_key}"}
            self.ws = await websockets.connect(self.url, extra_headers=headers)
            print("✅ Connected to EVA")
            await self.start_conversation()
        
        async def start_conversation(self):
            await self.send({"type": "start_conversation"})
        
        async def send_message(self, content: str):
            await self.send({"type": "user_message", "content": content})
        
        async def send(self, message: dict):
            await self.ws.send(json.dumps(message))
        
        async def listen(self):
            async for message in self.ws:
                data = json.loads(message)
                await self.handle_message(data)
        
        async def handle_message(self, data: dict):
            msg_type = data.get("type")
            
            if msg_type == "conversation_started":
                self.conversation_id = data.get("conversation_id")
                print("🚀 Ready to chat!")
            
            elif msg_type == "message":
                emotion = data.get("emotion", "neutral")
                content = data.get("content", "")
                print(f"[{emotion}] {content}")
                
                if data.get("is_final"):
                    print("✨ Response complete\n")
            
            elif msg_type == "error":
                print(f"💥 Error: {data.get('content')}")
    
    # Usage
    async def main():
        client = SimpleEVAClient("your-api-key")
        await client.connect()
        
        # Send a message
        await client.send_message("Hello EVA! Tell me about machine learning.")
        
        # Listen for responses
        await client.listen()
    
    if __name__ == "__main__":
        asyncio.run(main())
    ```

## Testing Your Connection

### Quick Test with wscat

```bash
# Install wscat if you don't have it
npm install -g wscat

# Test connection
API_KEY="your-api-key"
wscat -c "ws://localhost:8000/ws?token=${API_KEY}"

# Once connected, send:
{"type": "start_conversation"}

# Then send a message:
{"type": "user_message", "content": "Hello!"}
```

## Common Issues

### Authentication Failed (Code 1008)

!!! error "Connection closes immediately"
    ```text
    WebSocket connection closed with code 1008: Invalid or missing API key
    ```

    **Solutions:**

    - Verify your API key is correct
    - Check that you're using the right authentication method
    - Ensure special characters in your API key are properly encoded

### No Response to Messages

!!! warning "Messages sent but no response"
    **Common causes:**
    - Forgot to send `start_conversation` first
    - WebSocket connection is not fully established
    - Message format is incorrect

    **Solution:** Always start a conversation before sending messages.

### Connection Timeout

!!! info "Connection takes too long or fails"
    **Solutions:**
    - Check network connectivity
    - Verify the WebSocket URL is correct
    - Implement connection retry logic
    - Check firewall settings

## Next Steps

Now that you're connected and chatting with EVA, explore:

- **[API Reference](api-reference.md)** - Complete message schemas and advanced features
- **[Client Examples](client-examples.md)** - Production-ready client implementations
- **RAG Integration** - How EVA uses documents to enhance responses
- **Conversation Management** - Working with conversation history and summarization

Happy chatting! 🚀
