# Client Examples

Production-ready client implementations for different platforms and use cases.

## JavaScript/TypeScript Web Client

### Full-Featured Chat Client

```javascript
class EVAChatClient {
    constructor(apiKey, options = {}) {
        this.apiKey = apiKey;
        this.baseUrl = options.baseUrl || 'ws://localhost:8000';
        this.autoReconnect = options.autoReconnect !== false;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectDelay = options.reconnectDelay || 1000;
        
        // State
        this.ws = null;
        this.conversationId = null;
        this.connectionState = 'disconnected';
        this.reconnectAttempts = 0;
        this.messageQueue = [];
        this.responseBuffer = new Map();
        
        // Event handlers
        this.onConnectionChange = options.onConnectionChange || (() => {});
        this.onMessage = options.onMessage || (() => {});
        this.onError = options.onError || (() => {});
        this.onConversationStart = options.onConversationStart || (() => {});
    }
    
    async connect() {
        if (this.connectionState === 'connecting' || this.connectionState === 'connected') {
            return;
        }
        
        this.connectionState = 'connecting';
        this.onConnectionChange('connecting');
        
        try {
            // Use subprotocol authentication (recommended for web)
            const protocols = ['chat', `${this.apiKey}`];
            this.ws = new WebSocket(`${this.baseUrl}/ws`, protocols);
            
            this.setupEventHandlers();
            
            // Wait for connection to open
            await new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Connection timeout'));
                }, 10000);
                
                this.ws.onopen = () => {
                    clearTimeout(timeout);
                    resolve();
                };
                
                this.ws.onerror = (error) => {
                    clearTimeout(timeout);
                    reject(error);
                };
            });
            
        } catch (error) {
            this.connectionState = 'disconnected';
            this.onConnectionChange('disconnected');
            
            if (this.autoReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
                await this.scheduleReconnect();
            } else {
                throw error;
            }
        }
    }
    
    setupEventHandlers() {
        this.ws.onopen = () => {
            this.connectionState = 'connected';
            this.reconnectAttempts = 0;
            this.onConnectionChange('connected');
            
            // Process queued messages
            this.processMessageQueue();
        };
        
        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                this.onError(new Error('Failed to parse message: ' + error.message));
            }
        };
        
        this.ws.onclose = (event) => {
            this.connectionState = 'disconnected';
            this.onConnectionChange('disconnected');
            
            if (event.code === 1008) {
                this.onError(new Error(`Authentication failed: ${event.reason}`));
                return;
            }
            
            // Auto-reconnect if enabled and not a normal closure
            if (this.autoReconnect && event.code !== 1000 && 
                this.reconnectAttempts < this.maxReconnectAttempts) {
                this.scheduleReconnect();
            }
        };
        
        this.ws.onerror = (error) => {
            this.onError(error);
        };
    }
    
    async scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'conversation_started':
                this.conversationId = data.conversation_id;
                this.onConversationStart(data.conversation_id);
                break;
                
            case 'message':
                this.handleResponseChunk(data);
                break;
                
            case 'error':
                this.onError(new Error(data.content));
                break;
        }
    }
    
    handleResponseChunk(data) {
        const messageId = data.metadata?.conversation_id || 'unknown';
        
        if (!this.responseBuffer.has(messageId)) {
            this.responseBuffer.set(messageId, {
                chunks: [],
                metadata: data.metadata
            });
        }
        
        const response = this.responseBuffer.get(messageId);
        response.chunks.push({
            content: data.content,
            emotion: data.emotion,
            chunk_id: data.chunk_id,
            timestamp: data.metadata?.timestamp
        });
        
        // Emit chunk for real-time display
        this.onMessage({
            type: 'chunk',
            chunk: {
                content: data.content,
                emotion: data.emotion,
                chunk_id: data.chunk_id
            },
            isComplete: data.is_final,
            metadata: data.metadata
        });
        
        // Emit complete message when final
        if (data.is_final) {
            this.onMessage({
                type: 'complete',
                chunks: response.chunks,
                metadata: response.metadata,
                fullContent: response.chunks.map(c => c.content).join('')
            });
            
            this.responseBuffer.delete(messageId);
        }
    }
    
    async startConversation(conversationId = null) {
        const message = {
            type: 'start_conversation',
            conversation_id: conversationId
        };
        
        return this.send(message);
    }
    
    async sendMessage(content) {
        if (!this.conversationId) {
            throw new Error('No active conversation. Call startConversation() first.');
        }
        
        const message = {
            type: 'user_message',
            content: content
        };
        
        return this.send(message);
    }
    
    async send(message) {
        if (this.connectionState !== 'connected') {
            if (this.autoReconnect) {
                // Queue message for later
                this.messageQueue.push(message);
                await this.connect();
                return;
            } else {
                throw new Error('WebSocket not connected');
            }
        }
        
        this.ws.send(JSON.stringify(message));
    }
    
    processMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.ws.send(JSON.stringify(message));
        }
    }
    
    disconnect() {
        this.autoReconnect = false;
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
        }
    }
    
    // Utility methods
    isConnected() {
        return this.connectionState === 'connected';
    }
    
    getConnectionState() {
        return this.connectionState;
    }
    
    getConversationId() {
        return this.conversationId;
    }
}
```

### React Chat Component

```jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { EVAChatClient } from './EVAChatClient';

const ChatInterface = ({ apiKey, onError }) => {
    const [client, setClient] = useState(null);
    const [connectionState, setConnectionState] = useState('disconnected');
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isResponding, setIsResponding] = useState(false);
    const [currentResponse, setCurrentResponse] = useState('');
    const messagesEndRef = useRef(null);
    
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };
    
    useEffect(() => {
        scrollToBottom();
    }, [messages, currentResponse]);
    
    const handleMessage = useCallback((messageData) => {
        if (messageData.type === 'chunk') {
            setCurrentResponse(prev => prev + messageData.chunk.content);
            
            if (messageData.isComplete) {
                setMessages(prev => [...prev, {
                    id: Date.now(),
                    type: 'assistant',
                    content: currentResponse + messageData.chunk.content,
                    emotion: messageData.chunk.emotion,
                    timestamp: new Date(),
                    sources: messageData.metadata?.sources || []
                }]);
                setCurrentResponse('');
                setIsResponding(false);
            }
        }
    }, [currentResponse]);
    
    const handleConnectionChange = useCallback((state) => {
        setConnectionState(state);
    }, []);
    
    const handleConversationStart = useCallback((conversationId) => {
        console.log('Conversation started:', conversationId);
    }, []);
    
    useEffect(() => {
        const evaClient = new EVAChatClient(apiKey, {
            onMessage: handleMessage,
            onConnectionChange: handleConnectionChange,
            onConversationStart: handleConversationStart,
            onError: onError
        });
        
        setClient(evaClient);
        
        // Auto-connect and start conversation
        evaClient.connect().then(() => {
            return evaClient.startConversation();
        }).catch(onError);
        
        return () => {
            evaClient.disconnect();
        };
    }, [apiKey, handleMessage, handleConnectionChange, handleConversationStart, onError]);
    
    const sendMessage = async () => {
        if (!inputValue.trim() || !client || !client.isConnected()) return;
        
        const messageContent = inputValue.trim();
        setInputValue('');
        
        // Add user message to chat
        setMessages(prev => [...prev, {
            id: Date.now(),
            type: 'user',
            content: messageContent,
            timestamp: new Date()
        }]);
        
        setIsResponding(true);
        
        try {
            await client.sendMessage(messageContent);
        } catch (error) {
            onError(error);
            setIsResponding(false);
        }
    };
    
    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };
    
    const getEmotionEmoji = (emotion) => {
        const emojis = {
            neutral: '💬',
            happy: '😊',
            excited: '🎉',
            thoughtful: '🤔',
            curious: '🤨',
            confident: '💪',
            concerned: '⚠️',
            empathetic: '🤗'
        };
        return emojis[emotion] || '💬';
    };
    
    const getConnectionStatusColor = () => {
        switch (connectionState) {
            case 'connected': return 'green';
            case 'connecting': return 'orange';
            case 'disconnected': return 'red';
            default: return 'gray';
        }
    };
    
    return (
        <div className="chat-interface">
            <div className="chat-header">
                <h2>EVA Chat</h2>
                <div className="connection-status">
                    <span 
                        className="status-indicator"
                        style={{ backgroundColor: getConnectionStatusColor() }}
                    />
                    {connectionState}
                </div>
            </div>
            
            <div className="chat-messages">
                {messages.map((message) => (
                    <div key={message.id} className={`message ${message.type}`}>
                        <div className="message-content">
                            {message.type === 'assistant' && (
                                <span className="emotion-indicator">
                                    {getEmotionEmoji(message.emotion)}
                                </span>
                            )}
                            {message.content}
                        </div>
                        {message.sources && message.sources.length > 0 && (
                            <div className="message-sources">
                                <small>Sources: {message.sources.join(', ')}</small>
                            </div>
                        )}
                        <div className="message-time">
                            {message.timestamp.toLocaleTimeString()}
                        </div>
                    </div>
                ))}
                
                {isResponding && currentResponse && (
                    <div className="message assistant typing">
                        <div className="message-content">
                            {currentResponse}
                            <span className="typing-cursor">|</span>
                        </div>
                    </div>
                )}
                
                {isResponding && !currentResponse && (
                    <div className="message assistant typing">
                        <div className="typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                )}
                
                <div ref={messagesEndRef} />
            </div>
            
            <div className="chat-input">
                <textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Type your message..."
                    disabled={!client?.isConnected() || isResponding}
                    rows={1}
                />
                <button 
                    onClick={sendMessage}
                    disabled={!inputValue.trim() || !client?.isConnected() || isResponding}
                >
                    Send
                </button>
            </div>
        </div>
    );
};

export default ChatInterface;
```

### CSS Styles for React Component

```css
.chat-interface {
    display: flex;
    flex-direction: column;
    height: 600px;
    width: 100%;
    max-width: 800px;
    border: 1px solid #ddd;
    border-radius: 8px;
    overflow: hidden;
}

.chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background: #f8f9fa;
    border-bottom: 1px solid #ddd;
}

.chat-header h2 {
    margin: 0;
    color: #333;
}

.connection-status {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.9rem;
    color: #666;
}

.status-indicator {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    background: #fff;
}

.message {
    margin-bottom: 1rem;
    max-width: 80%;
}

.message.user {
    align-self: flex-end;
    margin-left: auto;
}

.message.user .message-content {
    background: #007bff;
    color: white;
    border-radius: 18px 18px 4px 18px;
}

.message.assistant .message-content {
    background: #f1f3f4;
    color: #333;
    border-radius: 18px 18px 18px 4px;
}

.message-content {
    padding: 12px 16px;
    display: inline-block;
    word-wrap: break-word;
    position: relative;
}

.emotion-indicator {
    position: absolute;
    top: -8px;
    left: -8px;
    background: white;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.message-sources {
    margin-top: 4px;
    color: #666;
    font-style: italic;
}

.message-time {
    font-size: 0.8rem;
    color: #999;
    margin-top: 4px;
}

.typing .message-content {
    background: #f1f3f4;
}

.typing-cursor {
    animation: blink 1s infinite;
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}

.typing-indicator {
    display: flex;
    gap: 4px;
    padding: 12px 16px;
}

.typing-indicator span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #999;
    animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
    animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes typing {
    0%, 60%, 100% {
        transform: translateY(0);
    }
    30% {
        transform: translateY(-10px);
    }
}

.chat-input {
    display: flex;
    padding: 1rem;
    background: #f8f9fa;
    border-top: 1px solid #ddd;
    gap: 8px;
}

.chat-input textarea {
    flex: 1;
    border: 1px solid #ddd;
    border-radius: 20px;
    padding: 8px 16px;
    resize: none;
    outline: none;
    font-family: inherit;
}

.chat-input textarea:focus {
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
}

.chat-input button {
    background: #007bff;
    color: white;
    border: none;
    border-radius: 20px;
    padding: 8px 20px;
    cursor: pointer;
    font-weight: 500;
}

.chat-input button:hover:not(:disabled) {
    background: #0056b3;
}

.chat-input button:disabled {
    background: #ccc;
    cursor: not-allowed;
}
```

## Python Client

### Async Python Client

```python
import asyncio
import json
import logging
import time
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

@dataclass
class Message:
    type: str
    content: str
    emotion: Optional[str] = None
    chunk_id: Optional[str] = None
    is_final: bool = False
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

class EVAChatClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "ws://localhost:8000",
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 5,
        reconnect_delay: float = 1.0,
        logger: Optional[logging.Logger] = None
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.logger = logger or logging.getLogger(__name__)
        
        # State
        self.ws = None
        self.conversation_id = None
        self.connection_state = "disconnected"
        self.reconnect_attempts = 0
        self.message_queue = []
        self.response_buffers = {}
        
        # Event handlers
        self.message_handlers: List[Callable[[Message], None]] = []
        self.error_handlers: List[Callable[[Exception], None]] = []
        self.connection_handlers: List[Callable[[str], None]] = []
        self.conversation_start_handlers: List[Callable[[str], None]] = []
    
    def on_message(self, handler: Callable[[Message], None]):
        """Register a message handler"""
        self.message_handlers.append(handler)
    
    def on_error(self, handler: Callable[[Exception], None]):
        """Register an error handler"""
        self.error_handlers.append(handler)
    
    def on_connection_change(self, handler: Callable[[str], None]):
        """Register a connection state change handler"""
        self.connection_handlers.append(handler)
    
    def on_conversation_start(self, handler: Callable[[str], None]):
        """Register a conversation start handler"""
        self.conversation_start_handlers.append(handler)
    
    async def connect(self):
        """Connect to the EVA WebSocket API"""
        if self.connection_state in ["connecting", "connected"]:
            return
        
        self.connection_state = "connecting"
        self._notify_connection_handlers("connecting")
        
        try:
            # Use Authorization header (recommended for Python)
            extra_headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            self.ws = await websockets.connect(
                f"{self.base_url}/ws",
                extra_headers=extra_headers,
                ping_interval=30,
                ping_timeout=10
            )
            
            self.connection_state = "connected"
            self.reconnect_attempts = 0
            self._notify_connection_handlers("connected")
            self.logger.info("Connected to EVA WebSocket API")
            
            # Process any queued messages
            await self._process_message_queue()
            
        except Exception as e:
            self.connection_state = "disconnected"
            self._notify_connection_handlers("disconnected")
            self.logger.error(f"Connection failed: {e}")
            
            if (self.auto_reconnect and 
                self.reconnect_attempts < self.max_reconnect_attempts):
                await self._schedule_reconnect()
            else:
                self._notify_error_handlers(e)
                raise
    
    async def _schedule_reconnect(self):
        """Schedule a reconnection attempt with exponential backoff"""
        self.reconnect_attempts += 1
        delay = self.reconnect_delay * (2 ** (self.reconnect_attempts - 1))
        
        self.logger.info(
            f"Scheduling reconnect attempt {self.reconnect_attempts} "
            f"in {delay:.1f} seconds"
        )
        
        await asyncio.sleep(delay)
        await self.connect()
    
    async def listen(self):
        """Listen for incoming messages"""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse message: {e}")
                    self._notify_error_handlers(e)
                except Exception as e:
                    self.logger.error(f"Error handling message: {e}")
                    self._notify_error_handlers(e)
                    
        except ConnectionClosedError as e:
            self.connection_state = "disconnected"
            self._notify_connection_handlers("disconnected")
            
            if e.code == 1008:  # Policy violation (auth failed)
                error = Exception(f"Authentication failed: {e.reason}")
                self.logger.error(error)
                self._notify_error_handlers(error)
                return
            
            # Auto-reconnect if enabled
            if (self.auto_reconnect and e.code != 1000 and 
                self.reconnect_attempts < self.max_reconnect_attempts):
                await self._schedule_reconnect()
                await self.listen()  # Resume listening after reconnect
                
        except ConnectionClosedOK:
            self.logger.info("Connection closed normally")
            self.connection_state = "disconnected"
            self._notify_connection_handlers("disconnected")
    
    async def _handle_message(self, data: dict):
        """Handle incoming WebSocket messages"""
        msg_type = data.get("type")
        
        if msg_type == "conversation_started":
            self.conversation_id = data.get("conversation_id")
            self.logger.info(f"Conversation started: {self.conversation_id}")
            for handler in self.conversation_start_handlers:
                handler(self.conversation_id)
        
        elif msg_type == "message":
            await self._handle_response_chunk(data)
        
        elif msg_type == "error":
            error_msg = data.get("content", "Unknown error")
            error = Exception(f"Server error: {error_msg}")
            self.logger.error(error)
            self._notify_error_handlers(error)
    
    async def _handle_response_chunk(self, data: dict):
        """Handle response message chunks"""
        conversation_id = data.get("metadata", {}).get("conversation_id", "unknown")
        
        if conversation_id not in self.response_buffers:
            self.response_buffers[conversation_id] = {
                "chunks": [],
                "metadata": data.get("metadata", {})
            }
        
        buffer = self.response_buffers[conversation_id]
        chunk_data = {
            "content": data.get("content", ""),
            "emotion": data.get("emotion", "neutral"),
            "chunk_id": data.get("chunk_id"),
            "timestamp": datetime.fromisoformat(
                data.get("metadata", {}).get("timestamp", "").replace("Z", "+00:00")
            ) if data.get("metadata", {}).get("timestamp") else datetime.now()
        }
        
        buffer["chunks"].append(chunk_data)
        
        # Create message object for chunk
        message = Message(
            type="chunk",
            content=chunk_data["content"],
            emotion=chunk_data["emotion"],
            chunk_id=chunk_data["chunk_id"],
            is_final=data.get("is_final", False),
            metadata=data.get("metadata", {}),
            timestamp=chunk_data["timestamp"]
        )
        
        # Notify handlers of chunk
        for handler in self.message_handlers:
            handler(message)
        
        # If final chunk, create complete message
        if data.get("is_final", False):
            complete_content = "".join(chunk["content"] for chunk in buffer["chunks"])
            complete_message = Message(
                type="complete",
                content=complete_content,
                emotion=buffer["chunks"][-1]["emotion"],  # Use last emotion
                is_final=True,
                metadata=buffer["metadata"],
                timestamp=buffer["chunks"][-1]["timestamp"]
            )
            
            # Notify handlers of complete message
            for handler in self.message_handlers:
                handler(complete_message)
            
            # Clean up buffer
            del self.response_buffers[conversation_id]
    
    async def start_conversation(self, conversation_id: Optional[str] = None):
        """Start a new conversation or continue an existing one"""
        message = {
            "type": "start_conversation"
        }
        if conversation_id:
            message["conversation_id"] = conversation_id
        
        await self.send(message)
    
    async def send_message(self, content: str):
        """Send a user message"""
        if not self.conversation_id:
            raise Exception("No active conversation. Call start_conversation() first.")
        
        message = {
            "type": "user_message",
            "content": content
        }
        
        await self.send(message)
    
    async def send(self, message: dict):
        """Send a message to the WebSocket"""
        if self.connection_state != "connected":
            if self.auto_reconnect:
                # Queue message for later
                self.message_queue.append(message)
                await self.connect()
                return
            else:
                raise Exception("WebSocket not connected")
        
        try:
            await self.ws.send(json.dumps(message))
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            self._notify_error_handlers(e)
            raise
    
    async def _process_message_queue(self):
        """Process any queued messages"""
        while self.message_queue:
            message = self.message_queue.pop(0)
            try:
                await self.ws.send(json.dumps(message))
            except Exception as e:
                self.logger.error(f"Failed to send queued message: {e}")
                # Re-queue the message
                self.message_queue.insert(0, message)
                break
    
    async def disconnect(self):
        """Disconnect from the WebSocket"""
        self.auto_reconnect = False
        if self.ws:
            await self.ws.close(code=1000, reason="Client disconnect")
        self.connection_state = "disconnected"
        self._notify_connection_handlers("disconnected")
    
    def _notify_connection_handlers(self, state: str):
        """Notify connection state change handlers"""
        for handler in self.connection_handlers:
            try:
                handler(state)
            except Exception as e:
                self.logger.error(f"Error in connection handler: {e}")
    
    def _notify_error_handlers(self, error: Exception):
        """Notify error handlers"""
        for handler in self.error_handlers:
            try:
                handler(error)
            except Exception as e:
                self.logger.error(f"Error in error handler: {e}")
    
    # Utility methods
    def is_connected(self) -> bool:
        """Check if connected to WebSocket"""
        return self.connection_state == "connected"
    
    def get_connection_state(self) -> str:
        """Get current connection state"""
        return self.connection_state
    
    def get_conversation_id(self) -> Optional[str]:
        """Get current conversation ID"""
        return self.conversation_id


# Example usage and CLI client
class EVAChatCLI:
    def __init__(self, api_key: str, base_url: str = "ws://localhost:8000"):
        self.client = EVAChatClient(api_key, base_url)
        self.current_response = ""
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup event handlers for the CLI"""
        self.client.on_message(self.handle_message)
        self.client.on_error(self.handle_error)
        self.client.on_connection_change(self.handle_connection_change)
        self.client.on_conversation_start(self.handle_conversation_start)
    
    def handle_message(self, message: Message):
        """Handle incoming messages"""
        if message.type == "chunk":
            # Print chunk content immediately for real-time feel
            print(message.content, end="", flush=True)
            
            if message.is_final:
                print()  # New line after complete response
                if message.metadata and message.metadata.get("sources"):
                    sources = message.metadata["sources"]
                    print(f"\n📚 Sources: {', '.join(sources)}")
                print()  # Extra line for spacing
        
        elif message.type == "complete":
            # Could be used for additional processing if needed
            pass
    
    def handle_error(self, error: Exception):
        """Handle errors"""
        print(f"\n❌ Error: {error}")
    
    def handle_connection_change(self, state: str):
        """Handle connection state changes"""
        status_emojis = {
            "connecting": "🔄",
            "connected": "✅",
            "disconnected": "❌"
        }
        emoji = status_emojis.get(state, "❓")
        print(f"{emoji} Connection: {state}")
    
    def handle_conversation_start(self, conversation_id: str):
        """Handle conversation start"""
        print(f"🚀 Conversation started: {conversation_id[:8]}...")
        print("Type your messages below (type 'quit' to exit):\n")
    
    async def run(self):
        """Run the CLI chat interface"""
        print("🤖 EVA Chat CLI")
        print("Connecting to EVA...")
        
        try:
            # Connect and start conversation
            await self.client.connect()
            await self.client.start_conversation()
            
            # Start listening in background
            listen_task = asyncio.create_task(self.client.listen())
            
            # Handle user input
            while True:
                try:
                    user_input = await asyncio.get_event_loop().run_in_executor(
                        None, input, "You: "
                    )
                    
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    if user_input.strip():
                        print("EVA: ", end="", flush=True)
                        await self.client.send_message(user_input)
                
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error sending message: {e}")
            
            # Clean up
            listen_task.cancel()
            await self.client.disconnect()
            print("\n👋 Goodbye!")
            
        except Exception as e:
            print(f"Failed to start chat: {e}")


# Example script
async def main():
    import os
    import sys
    
    # Get API key from environment or command line
    api_key = os.getenv("EVA_API_KEY")
    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    if not api_key:
        print("Please provide API key via EVA_API_KEY environment variable or command line argument")
        sys.exit(1)
    
    # Run CLI
    cli = EVAChatCLI(api_key)
    await cli.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
```

## Node.js Server-Side Client

### Express.js Integration

```javascript
const WebSocket = require('ws');
const EventEmitter = require('events');

class EVAChatClient extends EventEmitter {
    constructor(apiKey, options = {}) {
        super();
        this.apiKey = apiKey;
        this.baseUrl = options.baseUrl || 'ws://localhost:8000';
        this.autoReconnect = options.autoReconnect !== false;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectDelay = options.reconnectDelay || 1000;
        
        // State
        this.ws = null;
        this.conversationId = null;
        this.connectionState = 'disconnected';
        this.reconnectAttempts = 0;
        this.messageQueue = [];
        this.responseBuffers = new Map();
    }
    
    async connect() {
        if (this.connectionState === 'connecting' || this.connectionState === 'connected') {
            return;
        }
        
        this.connectionState = 'connecting';
        this.emit('connectionChange', 'connecting');
        
        try {
            // Use Authorization header (recommended for server-side)
            const headers = {
                'Authorization': `Bearer ${this.apiKey}`
            };
            
            this.ws = new WebSocket(`${this.baseUrl}/ws`, { headers });
            this.setupEventHandlers();
            
            // Wait for connection
            await new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Connection timeout'));
                }, 10000);
                
                this.ws.once('open', () => {
                    clearTimeout(timeout);
                    resolve();
                });
                
                this.ws.once('error', (error) => {
                    clearTimeout(timeout);
                    reject(error);
                });
            });
            
        } catch (error) {
            this.connectionState = 'disconnected';
            this.emit('connectionChange', 'disconnected');
            
            if (this.autoReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
                await this.scheduleReconnect();
            } else {
                throw error;
            }
        }
    }
    
    setupEventHandlers() {
        this.ws.on('open', () => {
            this.connectionState = 'connected';
            this.reconnectAttempts = 0;
            this.emit('connectionChange', 'connected');
            this.processMessageQueue();
        });
        
        this.ws.on('message', (data) => {
            try {
                const message = JSON.parse(data.toString());
                this.handleMessage(message);
            } catch (error) {
                this.emit('error', new Error(`Failed to parse message: ${error.message}`));
            }
        });
        
        this.ws.on('close', (code, reason) => {
            this.connectionState = 'disconnected';
            this.emit('connectionChange', 'disconnected');
            
            if (code === 1008) {
                this.emit('error', new Error(`Authentication failed: ${reason}`));
                return;
            }
            
            if (this.autoReconnect && code !== 1000 && 
                this.reconnectAttempts < this.maxReconnectAttempts) {
                this.scheduleReconnect();
            }
        });
        
        this.ws.on('error', (error) => {
            this.emit('error', error);
        });
        
        // Heartbeat to keep connection alive
        this.ws.on('ping', () => {
            this.ws.pong();
        });
    }
    
    async scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'conversation_started':
                this.conversationId = data.conversation_id;
                this.emit('conversationStart', data.conversation_id);
                break;
                
            case 'message':
                this.handleResponseChunk(data);
                break;
                
            case 'error':
                this.emit('error', new Error(data.content));
                break;
        }
    }
    
    handleResponseChunk(data) {
        const messageId = data.metadata?.conversation_id || 'unknown';
        
        if (!this.responseBuffers.has(messageId)) {
            this.responseBuffers.set(messageId, {
                chunks: [],
                metadata: data.metadata
            });
        }
        
        const response = this.responseBuffers.get(messageId);
        const chunk = {
            content: data.content,
            emotion: data.emotion,
            chunk_id: data.chunk_id,
            timestamp: data.metadata?.timestamp
        };
        
        response.chunks.push(chunk);
        
        // Emit chunk event
        this.emit('messageChunk', {
            chunk,
            isComplete: data.is_final,
            metadata: data.metadata
        });
        
        // Emit complete message when final
        if (data.is_final) {
            const fullContent = response.chunks.map(c => c.content).join('');
            this.emit('messageComplete', {
                content: fullContent,
                chunks: response.chunks,
                metadata: response.metadata
            });
            
            this.responseBuffers.delete(messageId);
        }
    }
    
    async startConversation(conversationId = null) {
        const message = {
            type: 'start_conversation'
        };
        
        if (conversationId) {
            message.conversation_id = conversationId;
        }
        
        return this.send(message);
    }
    
    async sendMessage(content) {
        if (!this.conversationId) {
            throw new Error('No active conversation. Call startConversation() first.');
        }
        
        const message = {
            type: 'user_message',
            content: content
        };
        
        return this.send(message);
    }
    
    async send(message) {
        if (this.connectionState !== 'connected') {
            if (this.autoReconnect) {
                this.messageQueue.push(message);
                await this.connect();
                return;
            } else {
                throw new Error('WebSocket not connected');
            }
        }
        
        this.ws.send(JSON.stringify(message));
    }
    
    processMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.ws.send(JSON.stringify(message));
        }
    }
    
    disconnect() {
        this.autoReconnect = false;
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
        }
    }
    
    isConnected() {
        return this.connectionState === 'connected';
    }
}

module.exports = EVAChatClient;
```

### Express.js API Server Example

```javascript
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const EVAChatClient = require('./EVAChatClient');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

app.use(express.json());
app.use(express.static('public'));

// Store active EVA clients for each socket
const evaClients = new Map();

io.on('connection', (socket) => {
    console.log('Client connected:', socket.id);
    
    socket.on('authenticate', async (data) => {
        try {
            const { apiKey } = data;
            
            // Create EVA client for this socket
            const evaClient = new EVAChatClient(apiKey);
            
            // Setup event handlers
            evaClient.on('connectionChange', (state) => {
                socket.emit('connectionChange', { state });
            });
            
            evaClient.on('conversationStart', (conversationId) => {
                socket.emit('conversationStart', { conversationId });
            });
            
            evaClient.on('messageChunk', (data) => {
                socket.emit('messageChunk', data);
            });
            
            evaClient.on('messageComplete', (data) => {
                socket.emit('messageComplete', data);
            });
            
            evaClient.on('error', (error) => {
                socket.emit('error', { message: error.message });
            });
            
            // Connect to EVA
            await evaClient.connect();
            evaClients.set(socket.id, evaClient);
            
            socket.emit('authenticated', { success: true });
            
        } catch (error) {
            socket.emit('authenticated', { 
                success: false, 
                error: error.message 
            });
        }
    });
    
    socket.on('startConversation', async (data) => {
        const evaClient = evaClients.get(socket.id);
        if (!evaClient) {
            socket.emit('error', { message: 'Not authenticated' });
            return;
        }
        
        try {
            await evaClient.startConversation(data.conversationId);
        } catch (error) {
            socket.emit('error', { message: error.message });
        }
    });
    
    socket.on('sendMessage', async (data) => {
        const evaClient = evaClients.get(socket.id);
        if (!evaClient) {
            socket.emit('error', { message: 'Not authenticated' });
            return;
        }
        
        try {
            await evaClient.sendMessage(data.content);
        } catch (error) {
            socket.emit('error', { message: error.message });
        }
    });
    
    socket.on('disconnect', () => {
        console.log('Client disconnected:', socket.id);
        const evaClient = evaClients.get(socket.id);
        if (evaClient) {
            evaClient.disconnect();
            evaClients.delete(socket.id);
        }
    });
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        activeConnections: evaClients.size
    });
});

// Start server
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
```

## Testing Examples

### Unit Tests (Jest)

```javascript
// tests/EVAChatClient.test.js
const EVAChatClient = require('../src/EVAChatClient');
const WS = require('jest-websocket-mock');

describe('EVAChatClient', () => {
    let server;
    let client;
    
    beforeEach(() => {
        server = new WS('ws://localhost:8000/ws');
        client = new EVAChatClient('test-api-key');
    });
    
    afterEach(() => {
        if (client) client.disconnect();
        WS.clean();
    });
    
    test('should connect with proper authentication', async () => {
        const connectPromise = client.connect();
        await server.connected;
        
        expect(server).toHaveReceivedMessage(expect.any(String));
        await connectPromise;
        expect(client.isConnected()).toBe(true);
    });
    
    test('should start conversation and receive conversation_started', async () => {
        await client.connect();
        await server.connected;
        
        const conversationPromise = new Promise((resolve) => {
            client.on('conversationStart', resolve);
        });
        
        client.startConversation();
        
        // Simulate server response
        server.send(JSON.stringify({
            type: 'conversation_started',
            conversation_id: 'test-conv-123'
        }));
        
        const conversationId = await conversationPromise;
        expect(conversationId).toBe('test-conv-123');
        expect(client.getConversationId()).toBe('test-conv-123');
    });
    
    test('should handle message chunks correctly', async () => {
        await client.connect();
        await server.connected;
        
        // Start conversation first
        client.startConversation();
        server.send(JSON.stringify({
            type: 'conversation_started',
            conversation_id: 'test-conv-123'
        }));
        
        const chunks = [];
        let completeMessage = null;
        
        client.on('messageChunk', (data) => {
            chunks.push(data.chunk);
        });
        
        client.on('messageComplete', (data) => {
            completeMessage = data;
        });
        
        // Send message chunks
        server.send(JSON.stringify({
            type: 'message',
            content: 'Hello, ',
            emotion: 'happy',
            chunk_id: 'chunk-1',
            is_final: false,
            metadata: { conversation_id: 'test-conv-123' }
        }));
        
        server.send(JSON.stringify({
            type: 'message',
            content: 'how are you?',
            emotion: 'curious',
            chunk_id: 'chunk-2',
            is_final: true,
            metadata: { conversation_id: 'test-conv-123' }
        }));
        
        // Wait for processing
        await new Promise(resolve => setTimeout(resolve, 10));
        
        expect(chunks).toHaveLength(2);
        expect(chunks[0].content).toBe('Hello, ');
        expect(chunks[1].content).toBe('how are you?');
        expect(completeMessage.content).toBe('Hello, how are you?');
    });
    
    test('should handle authentication errors', async () => {
        const errorPromise = new Promise((resolve) => {
            client.on('error', resolve);
        });
        
        const connectPromise = client.connect();
        await server.connected;
        
        // Simulate auth failure
        server.close({ code: 1008, reason: 'Invalid API key' });
        
        const error = await errorPromise;
        expect(error.message).toContain('Authentication failed');
    });
});
```

### Integration Test Script

```javascript
// scripts/test-integration.js
const EVAChatClient = require('../src/EVAChatClient');

async function testEVAIntegration() {
    const apiKey = process.env.EVA_API_KEY;
    if (!apiKey) {
        console.error('Please set EVA_API_KEY environment variable');
        process.exit(1);
    }
    
    console.log('🧪 Starting EVA integration test...');
    
    const client = new EVAChatClient(apiKey, {
        baseUrl: process.env.EVA_BASE_URL || 'ws://localhost:8000'
    });
    
    let testsPassed = 0;
    let testsFailed = 0;
    
    const test = (name, condition) => {
        if (condition) {
            console.log(`✅ ${name}`);
            testsPassed++;
        } else {
            console.log(`❌ ${name}`);
            testsFailed++;
        }
    };
    
    try {
        // Test 1: Connection
        console.log('\n📡 Testing connection...');
        await client.connect();
        test('Connection established', client.isConnected());
        
        // Test 2: Conversation start
        console.log('\n🚀 Testing conversation start...');
        const conversationPromise = new Promise((resolve) => {
            client.on('conversationStart', resolve);
        });
        
        await client.startConversation();
        const conversationId = await conversationPromise;
        test('Conversation started', !!conversationId);
        test('Conversation ID set', client.getConversationId() === conversationId);
        
        // Test 3: Message sending and receiving
        console.log('\n💬 Testing message exchange...');
        let receivedChunks = 0;
        let receivedComplete = false;
        
        client.on('messageChunk', () => {
            receivedChunks++;
        });
        
        client.on('messageComplete', () => {
            receivedComplete = true;
        });
        
        await client.sendMessage('Hello EVA! This is a test message.');
        
        // Wait for response
        await new Promise(resolve => {
            const checkResponse = () => {
                if (receivedComplete) {
                    resolve();
                } else {
                    setTimeout(checkResponse, 100);
                }
            };
            checkResponse();
        });
        
        test('Received message chunks', receivedChunks > 0);
        test('Received complete message', receivedComplete);
        
        // Test 4: Multiple messages
        console.log('\n🔄 Testing multiple messages...');
        let secondResponseReceived = false;
        
        const secondResponsePromise = new Promise((resolve) => {
            client.on('messageComplete', () => {
                if (receivedComplete) {  // Skip first response
                    secondResponseReceived = true;
                    resolve();
                }
            });
        });
        
        await client.sendMessage('Can you tell me about machine learning?');
        await secondResponsePromise;
        
        test('Second response received', secondResponseReceived);
        
        // Test 5: Disconnection
        console.log('\n🔌 Testing disconnection...');
        await client.disconnect();
        test('Disconnected successfully', !client.isConnected());
        
    } catch (error) {
        console.error(`\n💥 Test failed with error: ${error.message}`);
        testsFailed++;
    }
    
    // Results
    console.log('\n📊 Test Results:');
    console.log(`✅ Passed: ${testsPassed}`);
    console.log(`❌ Failed: ${testsFailed}`);
    console.log(`📈 Success Rate: ${((testsPassed / (testsPassed + testsFailed)) * 100).toFixed(1)}%`);
    
    if (testsFailed === 0) {
        console.log('\n🎉 All tests passed!');
        process.exit(0);
    } else {
        console.log('\n😞 Some tests failed.');
        process.exit(1);
    }
}

if (require.main === module) {
    testEVAIntegration().catch(console.error);
}

module.exports = testEVAIntegration;
```

## Mobile Client Examples

### React Native Client

```javascript
// EVAChatClient.js for React Native
import { EventEmitter } from 'events';

class EVAChatClientRN extends EventEmitter {
    constructor(apiKey, options = {}) {
        super();
        this.apiKey = apiKey;
        this.baseUrl = options.baseUrl || 'ws://localhost:8000';
        this.autoReconnect = options.autoReconnect !== false;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectDelay = options.reconnectDelay || 1000;
        
        // State
        this.ws = null;
        this.conversationId = null;
        this.connectionState = 'disconnected';
        this.reconnectAttempts = 0;
        this.messageQueue = [];
        this.responseBuffers = new Map();
    }
    
    connect() {
        return new Promise((resolve, reject) => {
            if (this.connectionState === 'connecting' || this.connectionState === 'connected') {
                resolve();
                return;
            }
            
            this.connectionState = 'connecting';
            this.emit('connectionChange', 'connecting');
            
            try {
                // React Native WebSocket doesn't support subprotocols reliably
                // Use query parameter for mobile apps
                const url = `${this.baseUrl}/ws?token=${encodeURIComponent(this.apiKey)}`;
                this.ws = new WebSocket(url);
                
                this.ws.onopen = () => {
                    this.connectionState = 'connected';
                    this.reconnectAttempts = 0;
                    this.emit('connectionChange', 'connected');
                    this.processMessageQueue();
                    resolve();
                };
                
                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        this.handleMessage(data);
                    } catch (error) {
                        this.emit('error', new Error(`Failed to parse message: ${error.message}`));
                    }
                };
                
                this.ws.onclose = (event) => {
                    this.connectionState = 'disconnected';
                    this.emit('connectionChange', 'disconnected');
                    
                    if (event.code === 1008) {
                        const error = new Error(`Authentication failed: ${event.reason}`);
                        this.emit('error', error);
                        reject(error);
                        return;
                    }
                    
                    if (this.autoReconnect && event.code !== 1000 && 
                        this.reconnectAttempts < this.maxReconnectAttempts) {
                        this.scheduleReconnect();
                    }
                };
                
                this.ws.onerror = (error) => {
                    this.emit('error', error);
                    if (this.connectionState === 'connecting') {
                        reject(error);
                    }
                };
                
            } catch (error) {
                this.connectionState = 'disconnected';
                this.emit('connectionChange', 'disconnected');
                reject(error);
            }
        });
    }
    
    scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        setTimeout(() => {
            this.connect().catch(() => {
                // Reconnection failed, will be handled by the connect method
            });
        }, delay);
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'conversation_started':
                this.conversationId = data.conversation_id;
                this.emit('conversationStart', data.conversation_id);
                break;
                
            case 'message':
                this.handleResponseChunk(data);
                break;
                
            case 'error':
                this.emit('error', new Error(data.content));
                break;
        }
    }
    
    handleResponseChunk(data) {
        const messageId = data.metadata?.conversation_id || 'unknown';
        
        if (!this.responseBuffers.has(messageId)) {
            this.responseBuffers.set(messageId, {
                chunks: [],
                metadata: data.metadata
            });
        }
        
        const response = this.responseBuffers.get(messageId);
        const chunk = {
            content: data.content,
            emotion: data.emotion,
            chunk_id: data.chunk_id,
            timestamp: data.metadata?.timestamp
        };
        
        response.chunks.push(chunk);
        
        // Emit chunk event
        this.emit('messageChunk', {
            chunk,
            isComplete: data.is_final,
            metadata: data.metadata
        });
        
        // Emit complete message when final
        if (data.is_final) {
            const fullContent = response.chunks.map(c => c.content).join('');
            this.emit('messageComplete', {
                content: fullContent,
                chunks: response.chunks,
                metadata: response.metadata
            });
            
            this.responseBuffers.delete(messageId);
        }
    }
    
    async startConversation(conversationId = null) {
        const message = {
            type: 'start_conversation'
        };
        
        if (conversationId) {
            message.conversation_id = conversationId;
        }
        
        return this.send(message);
    }
    
    async sendMessage(content) {
        if (!this.conversationId) {
            throw new Error('No active conversation. Call startConversation() first.');
        }
        
        const message = {
            type: 'user_message',
            content: content
        };
        
        return this.send(message);
    }
    
    send(message) {
        return new Promise((resolve, reject) => {
            if (this.connectionState !== 'connected') {
                if (this.autoReconnect) {
                    this.messageQueue.push({ message, resolve, reject });
                    this.connect().catch(reject);
                    return;
                } else {
                    reject(new Error('WebSocket not connected'));
                    return;
                }
            }
            
            try {
                this.ws.send(JSON.stringify(message));
                resolve();
            } catch (error) {
                reject(error);
            }
        });
    }
    
    processMessageQueue() {
        while (this.messageQueue.length > 0) {
            const { message, resolve, reject } = this.messageQueue.shift();
            try {
                this.ws.send(JSON.stringify(message));
                resolve();
            } catch (error) {
                reject(error);
                break;
            }
        }
    }
    
    disconnect() {
        this.autoReconnect = false;
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
        }
    }
    
    isConnected() {
        return this.connectionState === 'connected';
    }
    
    getConnectionState() {
        return this.connectionState;
    }
    
    getConversationId() {
        return this.conversationId;
    }
}

export default EVAChatClientRN;
```

### React Native Chat Screen

```jsx
// ChatScreen.js
import React, { useState, useEffect, useRef } from 'react';
import {
    View,
    Text,
    TextInput,
    TouchableOpacity,
    FlatList,
    Alert,
    ActivityIndicator,
    StatusBar,
    KeyboardAvoidingView,
    Platform,
    StyleSheet
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import EVAChatClientRN from '../services/EVAChatClient';

const ChatScreen = ({ apiKey }) => {
    const [client, setClient] = useState(null);
    const [connectionState, setConnectionState] = useState('disconnected');
    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState('');
    const [isResponding, setIsResponding] = useState(false);
    const [currentResponse, setCurrentResponse] = useState('');
    const flatListRef = useRef(null);
    
    useEffect(() => {
        const evaClient = new EVAChatClientRN(apiKey);
        
        // Setup event handlers
        evaClient.on('connectionChange', (state) => {
            setConnectionState(state);
        });
        
        evaClient.on('conversationStart', (conversationId) => {
            console.log('Conversation started:', conversationId);
        });
        
        evaClient.on('messageChunk', (data) => {
            setCurrentResponse(prev => prev + data.chunk.content);
            
            if (data.isComplete) {
                setMessages(prev => [...prev, {
                    id: Date.now(),
                    type: 'assistant',
                    content: currentResponse + data.chunk.content,
                    emotion: data.chunk.emotion,
                    timestamp: new Date(),
                    sources: data.metadata?.sources || []
                }]);
                setCurrentResponse('');
                setIsResponding(false);
            }
        });
        
        evaClient.on('error', (error) => {
            Alert.alert('Error', error.message);
            setIsResponding(false);
        });
        
        setClient(evaClient);
        
        // Auto-connect
        evaClient.connect()
            .then(() => evaClient.startConversation())
            .catch((error) => {
                Alert.alert('Connection Failed', error.message);
            });
        
        return () => {
            evaClient.disconnect();
        };
    }, [apiKey]);
    
    const sendMessage = async () => {
        if (!inputText.trim() || !client || !client.isConnected()) return;
        
        const messageContent = inputText.trim();
        setInputText('');
        
        // Add user message
        setMessages(prev => [...prev, {
            id: Date.now(),
            type: 'user',
            content: messageContent,
            timestamp: new Date()
        }]);
        
        setIsResponding(true);
        
        try {
            await client.sendMessage(messageContent);
        } catch (error) {
            Alert.alert('Send Failed', error.message);
            setIsResponding(false);
        }
    };
    
    const getEmotionEmoji = (emotion) => {
        const emojis = {
            neutral: '💬',
            happy: '😊',
            excited: '🎉',
            thoughtful: '🤔',
            curious: '🤨',
            confident: '💪',
            concerned: '⚠️',
            empathetic: '🤗'
        };
        return emojis[emotion] || '💬';
    };
    
    const getConnectionColor = () => {
        switch (connectionState) {
            case 'connected': return '#28a745';
            case 'connecting': return '#ffc107';
            case 'disconnected': return '#dc3545';
            default: return '#6c757d';
        }
    };
    
    const renderMessage = ({ item }) => (
        <View style={[
            styles.messageContainer,
            item.type === 'user' ? styles.userMessage : styles.assistantMessage
        ]}>
            <View style={[
                styles.messageBubble,
                item.type === 'user' ? styles.userBubble : styles.assistantBubble
            ]}>
                {item.type === 'assistant' && (
                    <Text style={styles.emotionEmoji}>
                        {getEmotionEmoji(item.emotion)}
                    </Text>
                )}
                <Text style={[
                    styles.messageText,
                    item.type === 'user' ? styles.userText : styles.assistantText
                ]}>
                    {item.content}
                </Text>
                {item.sources && item.sources.length > 0 && (
                    <Text style={styles.sourcesText}>
                        📚 Sources: {item.sources.join(', ')}
                    </Text>
                )}
            </View>
            <Text style={styles.timestamp}>
                {item.timestamp.toLocaleTimeString()}
            </Text>
        </View>
    );
    
    const renderTypingIndicator = () => (
        <View style={[styles.messageContainer, styles.assistantMessage]}>
            <View style={[styles.messageBubble, styles.assistantBubble]}>
                {currentResponse ? (
                    <Text style={styles.assistantText}>
                        {currentResponse}
                        <Text style={styles.typingCursor}>|</Text>
                    </Text>
                ) : (
                    <ActivityIndicator size="small" color="#666" />
                )}
            </View>
        </View>
    );
    
    return (
        <SafeAreaView style={styles.container}>
            <StatusBar barStyle="dark-content" backgroundColor="#f8f9fa" />
            
            {/* Header */}
            <View style={styles.header}>
                <Text style={styles.headerTitle}>EVA Chat</Text>
                <View style={styles.connectionStatus}>
                    <View style={[
                        styles.statusDot,
                        { backgroundColor: getConnectionColor() }
                    ]} />
                    <Text style={styles.statusText}>{connectionState}</Text>
                </View>
            </View>
            
            {/* Messages */}
            <KeyboardAvoidingView
                style={styles.messagesContainer}
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            >
                <FlatList
                    ref={flatListRef}
                    data={messages}
                    renderItem={renderMessage}
                    keyExtractor={(item) => item.id.toString()}
                    onContentSizeChange={() => flatListRef.current?.scrollToEnd()}
                    onLayout={() => flatListRef.current?.scrollToEnd()}
                    ListFooterComponent={isResponding ? renderTypingIndicator : null}
                    style={styles.messagesList}
                />
                
                {/* Input */}
                <View style={styles.inputContainer}>
                    <TextInput
                        style={styles.textInput}
                        value={inputText}
                        onChangeText={setInputText}
                        placeholder="Type your message..."
                        multiline
                        maxLength={1000}
                        editable={client?.isConnected() && !isResponding}
                    />
                    <TouchableOpacity
                        style={[
                            styles.sendButton,
                            (!inputText.trim() || !client?.isConnected() || isResponding) &&
                            styles.sendButtonDisabled
                        ]}
                        onPress={sendMessage}
                        disabled={!inputText.trim() || !client?.isConnected() || isResponding}
                    >
                        <Text style={styles.sendButtonText}>Send</Text>
                    </TouchableOpacity>
                </View>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#fff',
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 16,
        backgroundColor: '#f8f9fa',
        borderBottomWidth: 1,
        borderBottomColor: '#dee2e6',
    },
    headerTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#333',
    },
    connectionStatus: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    statusDot: {
        width: 10,
        height: 10,
        borderRadius: 5,
        marginRight: 8,
    },
    statusText: {
        fontSize: 14,
        color: '#666',
        textTransform: 'capitalize',
    },
    messagesContainer: {
        flex: 1,
    },
    messagesList: {
        flex: 1,
        paddingHorizontal: 16,
    },
    messageContainer: {
        marginVertical: 4,
        maxWidth: '80%',
    },
    userMessage: {
        alignSelf: 'flex-end',
    },
    assistantMessage: {
        alignSelf: 'flex-start',
    },
    messageBubble: {
        padding: 12,
        borderRadius: 18,
        position: 'relative',
    },
    userBubble: {
        backgroundColor: '#007bff',
        borderBottomRightRadius: 4,
    },
    assistantBubble: {
        backgroundColor: '#f1f3f4',
        borderBottomLeftRadius: 4,
    },
    messageText: {
        fontSize: 16,
        lineHeight: 20,
    },
    userText: {
        color: '#fff',
    },
    assistantText: {
        color: '#333',
    },
    emotionEmoji: {
        position: 'absolute',
        top: -8,
        left: -8,
        backgroundColor: '#fff',
        borderRadius: 12,
        width: 24,
        height: 24,
        textAlign: 'center',
        lineHeight: 24,
        fontSize: 14,
        elevation: 2,
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.2,
        shadowRadius: 2,
    },
    sourcesText: {
        fontSize: 12,
        color: '#666',
        fontStyle: 'italic',
        marginTop: 4,
    },
    timestamp: {
        fontSize: 12,
        color: '#999',
        marginTop: 4,
        textAlign: 'center',
    },
    typingCursor: {
        opacity: 0.5,
    },
    inputContainer: {
        flexDirection: 'row',
        padding: 16,
        backgroundColor: '#f8f9fa',
        borderTopWidth: 1,
        borderTopColor: '#dee2e6',
        alignItems: 'flex-end',
    },
    textInput: {
        flex: 1,
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 20,
        paddingHorizontal: 16,
        paddingVertical: 8,
        marginRight: 8,
        maxHeight: 100,
        fontSize: 16,
        backgroundColor: '#fff',
    },
    sendButton: {
        backgroundColor: '#007bff',
        borderRadius: 20,
        paddingHorizontal: 20,
        paddingVertical: 10,
        justifyContent: 'center',
        alignItems: 'center',
    },
    sendButtonDisabled: {
        backgroundColor: '#ccc',
    },
    sendButtonText: {
        color: '#fff',
        fontWeight: '600',
        fontSize: 16,
    },
});

export default ChatScreen;
```

## Best Practices Summary

### Authentication Best Practices

1. **Platform-specific choices**:
   - **JavaScript/Browser**: WebSocket Subprotocol
   - **Python/Server**: Authorization Header  
   - **React Native**: Query Parameter (most reliable)
   - **Testing**: Query Parameter

2. **Security considerations**:
   - Store API keys securely (environment variables, keychain)
   - Use WSS in production
   - Implement token rotation
   - Monitor for unusual usage patterns

### Connection Management

1. **Reconnection logic**:
   - Exponential backoff for reconnection attempts
   - Maximum retry limits
   - Queue messages during disconnection
   - Handle different close codes appropriately

2. **Health monitoring**:
   - Implement heartbeat/ping mechanisms
   - Monitor connection state changes
   - Log connection metrics
   - Alert on repeated failures

### Message Handling

1. **Response processing**:
   - Buffer chunks until `is_final: true`
   - Display chunks in real-time for better UX
   - Handle out-of-order delivery
   - Preserve message metadata

2. **Error handling**:
   - Graceful degradation on errors
   - User-friendly error messages
   - Automatic retry for transient failures
   - Logging for debugging

### Performance Optimization

1. **Resource management**:
   - Reuse connections where possible
   - Clean up resources on disconnect
   - Limit concurrent connections
   - Implement connection pooling for high-traffic applications

2. **User experience**:
   - Show typing indicators during responses
   - Implement optimistic UI updates
   - Cache conversation history locally
   - Smooth scrolling and animations

---

*These client examples provide production-ready implementations for various platforms. Choose the appropriate example based on your target platform and customize according to your specific requirements.*
