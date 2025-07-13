# ALIVE - Avatar Liveness for Intelligent Virtual Empathy

## Project Overview

ALIVE (Avatar Liveness for Intelligent Virtual Empathy) Release 5 is an AI-powered virtual assistant system that provides empathetic conversational experiences through realistic avatar representations. The system is part of the [SERMAS Project](https://sermasproject.eu/meet-the-project-alive/) initiative.

### Key Features

- **Multi-modal Input**: Support for both voice (microphone) and text-based interactions
- **Empathetic AI Responses**: Powered by EVE LLM (Thingenious) for contextually appropriate and emotionally aware responses
- **Realistic Avatar Visualization**: D-ID Clips API integration for lifelike avatar animations with SSML-enhanced emotional speech
- **Emotional Speech Synthesis**: Microsoft Azure Speech Services for voice input recognition
- **Real-time Interaction**: WebRTC-based streaming for synchronized audio-visual avatar responses

## System Architecture

### Technology Stack

- **Backend**: ASP.NET Core 6.0+ (C#)
- **Frontend**: JavaScript (Vanilla) with WebRTC
- **Avatar Engine**: D-ID Clips API
- **Speech Recognition**: Microsoft Azure Speech Services
- **LLM**: EVE by Thingenious (WebSocket-based)
- **Real-time Communication**: WebRTC for avatar video streaming

### Component Overview

```text
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Web Browser   │────▶│  ASP.NET Core    │────▶│   D-ID API      │
│  (JavaScript)   │     │    Backend       │     │ (Avatar Clips)  │
│   WebRTC        │     │                  │     └─────────────────┘
└─────────────────┘     │                  │
                        │                  │     ┌─────────────────┐
                        │                  │────▶│ Microsoft Azure │
                        │                  │     │ Speech Services │
                        │                  │     └─────────────────┘
                        │                  │
                        │                  │     ┌─────────────────┐
                        │                  │────▶│    EVE LLM      │
                        │                  │     │  (WebSocket)    │
                        └──────────────────┘     └─────────────────┘
```

## Prerequisites

- .NET 6.0 SDK or higher
- Active D-ID account with API access
- Microsoft Azure account with Speech Services enabled
- Access to EVE LLM endpoint (Thingenious)
- Modern web browser with WebRTC support
- HTTPS-enabled development environment (required for microphone access)

## Installation

### 1. Clone Repository

```bash
git clone [repository-url]
cd ALIVE
```

### 2. Install Dependencies

```bash
dotnet restore
```

### 3. Configure SSL Certificate (Development)

```bash
dotnet dev-certs https --trust
```

## Configuration

### 1. Application Settings

Create or update `appsettings.json` with the following structure:

```json
{
  "Services": {
    "DID": {
      "ApiKey": "[YOUR_D-ID_API_KEY]",
      "BaseUrl": "https://api.d-id.com",
      "PresenterId": "[SELECTED_PRESENTER_ID]",
      "DriverId": "[SELECTED_DRIVER_ID]"
    },
    "AzureSpeechServices": {
      "ApiKey": "[YOUR_AZURE_SPEECH_KEY]",
      "Region": "[YOUR_AZURE_REGION]",
      "VoiceId": "[SELECTED_VOICE_WITH_STYLES]"
    },
    "LLM": {
      "ApiKey": "[CHAT_API_KEY]",
      "BaseUrl": "[CHAT_WS_URL]",
      "Model": "EVE",
      "Timeout": 60
    }
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  }
}
```

### 2. Environment Variables

For production deployments, the system supports environment variable substitution. Set these environment variables:

```bash
export DID_API_KEY="your-d-id-api-key"
export AZURE_SPEECH_KEY="your-azure-speech-key"
export EVE_API_KEY="your-eve-api-key"
```

Then reference them in appsettings.json:

```json
{
  "Services": {
    "DID": {
      "ApiKey": "DID_API_KEY"
    },
    "AzureSpeechServices": {
      "ApiKey": "AZURE_SPEECH_KEY"
    },
    "LLM": {
      "ApiKey": "EVE_API_KEY"
    }
  }
}
```

### 3. Avatar Selection

Available presenters can be retrieved from: <https://api.d-id.com/clips/presenters>

Example presenter configuration:

```json
"PresenterId": "amy-Aq6OmGZnMt",
"DriverId": "Vcq0R4a8F0"
```

### 4. Voice Selection

Choose a voice that supports multiple emotional styles from the [Microsoft Voice Gallery](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts#voice-styles-and-roles).

Recommended voices with style support:

- `en-US-JennyNeural` (supports: cheerful, sad, angry, excited, friendly, hopeful, shouting, whispering)
- `en-US-AriaNeural` (supports: angry, cheerful, excited, friendly, hopeful, sad, shouting, unfriendly, whispering)
- `en-US-GuyNeural` (supports: angry, cheerful, excited, friendly, hopeful, sad, shouting, unfriendly, whispering)

## API Endpoints

### Session Management

**Create Session**

```shell
POST /api/session/create
Content-Type: application/json

{
  "userId": "string"
}

Response:
{
  "id": "string",
  "userId": "string",
  "messages": [],
  "createdAt": "2025-01-07T12:00:00Z",
  "lastUpdated": "2025-01-07T12:00:00Z"
}
```

**Get Session**

```shell
GET /api/session/{sessionId}

Response: ChatSession object
```

**Add Message to Session**

```shell
POST /api/session/{sessionId}/messages
Content-Type: application/json

{
  "type": "user|assistant",
  "content": "string",
  "emotion": "string"
}
```

### Avatar Management

**Create Avatar Stream**

```shell
POST /api/avatar/stream/create
Content-Type: application/json

{
  "presenterId": "string", // optional, uses default if not provided
  "driverId": "string"     // optional, uses default if not provided
}

Response:
{
  "streamId": "string",
  "sessionId": "string",
  "iceServers": [...],
  "sdpOffer": {...}
}
```

**Send Script to Avatar**

```shell
POST /api/avatar/stream/{streamId}
Content-Type: application/json

{
  "sessionId": "string",
  "script": {
    "type": "text",
    "input": "string",
    "provider": {
      "type": "microsoft",
      "voiceId": "string",
      "voiceConfig": {
        "style": "cheerful|sad|angry|..."
      }
    }
  }
}
```

**Start Stream with SDP Answer**

```shell
POST /api/avatar/stream/{streamId}/start
Content-Type: application/json

{
  "sessionId": "string",
  "sdpAnswer": {...}
}
```

**Send ICE Candidate**

```shell
POST /api/avatar/stream/{streamId}/ice
Content-Type: application/json

{
  "sessionId": "string",
  "candidate": "string",
  "mid": "string",
  "lineIndex": 0
}
```

**Close Stream**

```shell
DELETE /api/avatar/stream/{streamId}
Content-Type: application/json

{
  "session_id": "string"
}
```

### LLM Integration

**Send Message to LLM**

```shell
POST /api/llm/Send
Content-Type: application/json

{
  "message": "string"
}

Response:
{
  "text": "string",
  "emotion": "happy|sad|excited|thoughtful|curious|confident|concerned|empathetic",
  "response": "string", // same as text
  "metadata": {
    "conversation_id": "string"
  }
}
```

### Speech Configuration

**Get Speech Configuration**

```shell
GET /api/speech/config

Response:
{
  "apiKey": "string",
  "region": "string",
  "voiceId": "string"
}
```

## Frontend Integration

### Avatar Chat Interface

The main interface is served at the root URL and includes:

1. **WebRTC Video Element**: Displays the avatar stream
2. **Chat Interface**: Shows conversation history with user/assistant bubbles
3. **Input Controls**: Text input and microphone recording button
4. **Debug Panel**: Shows connection status and logs (development mode)

### JavaScript API Usage

```javascript
// Configuration
const API_ENDPOINTS = {
  createSession: "/api/session/create",
  createStream: "/api/avatar/stream/create",
  startStream: "/api/avatar/stream/",
  testLLM: "/api/llm/send",
};

// Create avatar stream
const streamResponse = await fetch(`${API_BASE_URL}${API_ENDPOINTS.createStream}`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({}),
});

// Setup WebRTC connection
const pc = new RTCPeerConnection(configuration);
// ... WebRTC setup code ...

// Send text to LLM and avatar
const llmResponse = await fetch(`${API_BASE_URL}${API_ENDPOINTS.testLLM}`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message: userInput }),
});

const llmData = await llmResponse.json();
// Avatar automatically speaks the response with appropriate emotion
```

## Usage

### Starting the Application

```bash
dotnet run --launch-profile https
```

The application will be available at `https://localhost:7031`

### Basic Workflow

1. **Initialize Session**: Open the web interface, the system automatically creates a session
2. **Connect Avatar**: Click "Connect" to initialize the D-ID avatar stream and establish WebRTC connection
3. **Input Method**:
   - **Voice**: Click and hold the microphone button to record
   - **Text**: Type in the input field and press Enter or click Send
4. **Processing Pipeline**:
   - User input is sent to EVE LLM
   - EVE returns response with emotional context
   - Response is sent to D-ID with appropriate voice style
   - Avatar speaks with synchronized video and emotional voice

### Emotion Mapping

The system maps EVE's emotional responses to Microsoft TTS styles:

| EVE Emotion | TTS Style  |
| ----------- | ---------- |
| happy       | cheerful   |
| excited     | excited    |
| thoughtful  | hopeful    |
| curious     | chat       |
| confident   | friendly   |
| concerned   | sad        |
| empathetic  | empathetic |

## Troubleshooting

### Common Issues

**WebRTC Connection Failed**

- Ensure HTTPS is enabled
- Check browser console for ICE candidate errors
- Verify firewall allows WebRTC connections

**No Audio from Avatar**

- Check browser autoplay policies
- Ensure user interaction before playing audio
- Verify D-ID stream is properly initialized

**Microphone Not Working**

- Check browser permissions
- Ensure HTTPS is enabled
- Verify microphone is not in use by another application

**LLM Connection Issues**

- Check WebSocket connection to EVE
- Verify API key is valid
- Monitor browser console for connection errors

### Debug Mode

The application includes a debug panel showing:

- Connection status
- WebRTC state
- API call logs
- Error messages

Enable verbose logging in browser console:

```javascript
const DEBUG = true; // Set in avatar-chat.js
```

## Performance Considerations

- **Response Time**: 2-4 seconds total (LLM processing + avatar generation)
- **Browser Requirements**: Chrome 90+, Firefox 88+, Safari 14.1+, Edge 90+
- **Network**: Requires stable internet connection for WebRTC streaming
- **Concurrent Users**: Each session maintains separate WebSocket and WebRTC connections

## Security Considerations

- All API keys should be stored securely and never exposed to frontend
- HTTPS is mandatory for production deployment
- Implement rate limiting for public deployments
- Regular security audits of dependencies

## Development Notes

### Project Structure

```shell
ALIVE/
├── Controllers/          # API Controllers
│   ├── AvatarController.cs
│   ├── LLMController.cs
│   ├── SessionController.cs
│   └── SpeechController.cs
├── Services/            # Business Logic
│   ├── AvatarStreamService.cs
│   ├── WebSocketLLMService.cs
│   └── ChatSessionService.cs
├── Models/              # Data Models
├── wwwroot/            # Static Files
│   ├── index.html
│   ├── avatar-chat.js
│   └── styles.css
├── appsettings.json    # Configuration
└── Program.cs          # Application Entry Point
```

### Key Services

- **AvatarStreamService**: Manages D-ID API communication
- **WebSocketLLMService**: Handles EVE LLM WebSocket connection
- **ChatSessionService**: Manages conversation sessions

## Support

For technical issues or questions regarding the ALIVE system, please contact the development team or refer to the [SERMAS Project documentation](https://sermasproject.eu/).

## License

This project is part of the SERMAS Project. Please refer to the project's licensing terms for usage rights and restrictions.
