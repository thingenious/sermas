// Avatar Chat - Simple JavaScript Implementation
// Debug logging utility
const DEBUG = false;

function addBrowserClass() {
    const ua = navigator.userAgent;
    const html = document.documentElement;
    if (ua.includes("Firefox")) {
        html.classList.add("firefox");
    } else if (ua.includes("Edg")) {
        html.classList.add("edge");
    } else if (ua.includes("Chrome") && !ua.includes("Edg") && !ua.includes("OPR")) {
        html.classList.add("chrome");
    } else if (/Safari/.test(ua) && !/Chrome/.test(ua) && !/Edg/.test(ua)) {
        html.classList.add("safari");
    }
}

function log(message, type = "info") {
    if (!DEBUG) return;

    const timestamp = new Date().toLocaleTimeString();
    const logEntry = `[${timestamp}] ${message}`;

    // Console log
    if (DEBUG) {
        console.log(logEntry);
        // Debug panel
        const debugPanel = document.getElementById("debug-panel");
        const logDiv = document.createElement("div");
        logDiv.className = `debug-log debug-${type}`;
        logDiv.textContent = logEntry;
        debugPanel.appendChild(logDiv);

        // Keep only last 10 logs
        while (debugPanel.children.length > 10) {
            debugPanel.removeChild(debugPanel.firstChild);
        }
    }
}

// API Configuration
const API_BASE_URL = window.location.origin;
const API_ENDPOINTS = {
    createSession: "/api/session/create",
    getSession: "/api/session",
    addMessage: "/api/session",
    createStream: "/api/avatar/stream/create",
    startStream: "/api/avatar/stream/", // {streamId}/start
    uploadAudio: "/api/audio/upload",
    testLLM: "/api/llm/send", // Updated endpoint
};

// Application State
let state = {
    sessionId: null,
    userId: null,
    streamId: null,
    streamSessionId: null,
    peerConnection: null,
    dataChannel: null, // ADD THIS
    isStreamReady: false, // ADD THIS
    isConnected: false,
    isRecording: false,
    mediaRecorder: null,
    audioChunks: [],
};

// DOM Elements
const elements = {
    status: document.getElementById("status"),
    video: document.getElementById("avatar-video"),
    chatMessages: document.getElementById("chat-messages"),
    messageInput: document.getElementById("message-input"),
    sendBtn: document.getElementById("send-btn"),
    connectBtn: document.getElementById("connect-btn"),
    recordBtn: document.getElementById("record-btn"),
};

// Update video debug info
function updateVideoDebug() {
    const debugSpan = document.getElementById("video-debug");
    if (debugSpan && elements.video) {
        const info = `${elements.video.videoWidth}x${elements.video.videoHeight} | Ready: ${
            elements.video.readyState
        } | Src: ${elements.video.srcObject ? "Yes" : "No"}`;
        debugSpan.textContent = info;
    }
}

function debugMediaState() {
    log("=== MEDIA STATE DEBUG ===", "info");

    if (elements.video.srcObject) {
        const stream = elements.video.srcObject;
        const audioTracks = stream.getAudioTracks();
        const videoTracks = stream.getVideoTracks();

        log(`Stream active: ${stream.active}`, "info");
        log(`Video element muted: ${elements.video.muted}`, "info");
        log(`Video element volume: ${elements.video.volume}`, "info");
        log(`Video element paused: ${elements.video.paused}`, "info");

        log(`Audio tracks: ${audioTracks.length}`, "info");
        audioTracks.forEach((track, i) => {
            log(
                `  Audio ${i}: enabled=${track.enabled}, muted=${track.muted}, readyState=${track.readyState}`,
                "info",
            );
        });

        log(`Video tracks: ${videoTracks.length}`, "info");
        videoTracks.forEach((track, i) => {
            log(
                `  Video ${i}: enabled=${track.enabled}, muted=${track.muted}, readyState=${track.readyState}`,
                "info",
            );
        });
    } else {
        log("No srcObject attached to video element", "error");
    }
}
// Microsoft TTS config loaded from backend
let ttsConfig = {
    voiceId: "en-US-JennyNeural",
    defaultStyle: "neutral",
};
// Fetch TTS config from backend
// Fetch both TTS and Speech-to-Text config from backend and update state
async function fetchSpeechAndTTSConfig() {
    try {
        log("Fetching Azure Speech and TTS configuration from backend...", "info");

        const response = await fetch(`${API_BASE_URL}/api/speech/config`, {
            method: "GET",
            headers: { "Content-Type": "application/json" },
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const config = await response.json();

        log(`Loaded Azure Speech config: ${JSON.stringify(config)}`, "success");
        return config;
    } catch (error) {
        log("Using default TTS config and no Azure Speech key/region", "warning");
        throw error;
    }
}

// Initialize
document.addEventListener("DOMContentLoaded", async () => {
    log("Application initialized");
    addBrowserClass();
    setupEventListeners();
    createChatSession();

    try {
        await setupAzureSpeech();
    } catch (error) {
        log("Speech services will not be available", "warning");
    }
    if (DEBUG) {
        document.querySelector(".debug-panel").style.display = "unset";
        document.querySelector(".debug-buttons").style.display = "unset";
        document.querySelector(".status-badge").style.bottom = "90px"; // above the debug panel
        // Update video debug info periodically
        setInterval(updateVideoDebug, 500);
    }
});

// Event Listeners
function setupEventListeners() {
    elements.connectBtn.addEventListener("click", handleConnect);
    elements.sendBtn.addEventListener("click", handleSendMessage);
    elements.recordBtn.addEventListener("click", handleRecord);
    elements.messageInput.addEventListener("keypress", e => {
        if (e.key === "Enter") handleSendMessage();
    });

    // Video element event listeners for debugging
    elements.video.addEventListener("loadstart", () => {
        log("Video load started", "info");
    });
    elements.video.addEventListener("loadeddata", () => {
        log("Video data loaded", "success");
    });
    elements.video.addEventListener("loadedmetadata", () => {
        log(`Video metadata loaded: ${elements.video.videoWidth}x${elements.video.videoHeight}`, "success");
    });
    elements.video.addEventListener("canplay", () => {
        log("Video can start playing", "success");
    });
    elements.video.addEventListener("playing", () => {
        log("Video is playing", "success");
    });
    elements.video.addEventListener("waiting", () => {
        log("Video is waiting for data", "info");
    });
    elements.video.addEventListener("stalled", () => {
        log("Video stalled", "error");
    });
    elements.video.addEventListener("error", e => {
        const error = elements.video.error;
        if (error) {
            log(`Video error: ${error.message} (code: ${error.code})`, "error");
        }
    });
}

// Create Chat Session
async function createChatSession() {
    try {
        state.userId = `user_${Date.now()}`;
        log(`Creating session for user: ${state.userId}`);

        const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.createSession}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ userId: state.userId }),
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const session = await response.json();
        state.sessionId = session.sessionId;
        log(`Session created: ${state.sessionId}`, "success");
    } catch (error) {
        log(`Failed to create session: ${error.message}`, "error");
        addMessageBubble("Failed to create chat session", "system");
    }
}

// Connect to Avatar
async function handleConnect() {
    if (state.isConnected) {
        await disconnectAvatar();
    } else {
        await connectAvatar();
    }
}

async function connectAvatar() {
    try {
        updateStatus("connecting");
        elements.connectBtn.disabled = true;
        log("Creating D-ID stream...");

        // Create D-ID stream with additional options based on SDK docs
        const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.createStream}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                // Add stream options that might help
                compatibilityMode: "auto",
                streamWarmup: true,
            }),
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const streamData = await response.json();

        // Debug: log the entire response
        log(`D-ID response: ${JSON.stringify(streamData)}`, "info");

        state.streamId = streamData.id;
        // Try both formats since D-ID might return either
        state.streamSessionId = streamData.session_id || streamData.sessionId;

        if (!state.streamSessionId) {
            log("WARNING: No session ID found in response!", "error");
        }

        log(`Stream created: ${state.streamId}`, "success");
        log(`Session ID: ${state.streamSessionId}`, "info");

        // Setup WebRTC
        await setupWebRTC(streamData);
    } catch (error) {
        log(`Connection failed: ${error.message}`, "error");
        updateStatus("disconnected");
        elements.connectBtn.disabled = false;
    }
}

async function setupWebRTC(streamData) {
    try {
        log("Setting up WebRTC connection...");

        // Create peer connection
        state.peerConnection = new RTCPeerConnection({
            iceServers: streamData.iceServers,
        });

        // Add data channel for stream events
        state.dataChannel = state.peerConnection.createDataChannel("JanusDataChannel");
        state.isStreamReady = false; // Add this to state

        // Handle data channel events
        state.dataChannel.onopen = () => {
            log("Data channel opened", "success");
        };

        state.dataChannel.onmessage = event => {
            const [eventType, _] = event.data.split(":");
            log(`Data channel event: ${event.data}`, "info");

            if (eventType === "stream/ready") {
                log("Stream is ready!", "success");
                state.isStreamReady = true;
            }
        };

        // Store ICE candidates that arrive before we set remote description
        const pendingCandidates = [];

        // Setup event handlers
        state.peerConnection.onicecandidate = async event => {
            if (event.candidate) {
                try {
                    const { candidate, sdpMid, sdpMLineIndex } = event.candidate;
                    log(`ICE candidate: ${candidate}\n mid: ${sdpMid}\n lineIndex: ${sdpMLineIndex}`, "info");
                    // Send ICE candidate to backend with explicit fields
                    const response = await fetch(
                        `${API_BASE_URL}${API_ENDPOINTS.startStream}${state.streamId}/ice`,
                        {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                                sessionId: state.streamSessionId,
                                candidate: candidate,
                                mid: sdpMid,
                                lineIndex: sdpMLineIndex,
                            }),
                        },
                    );
                    if (!response.ok) {
                        log("Failed to send ICE candidate", "error");
                    }
                } catch (error) {
                    log(`ICE candidate error: ${error.message}`, "error");
                }
            }
        };

        state.peerConnection.ontrack = event => {
            log(
                `Received ${event.track.kind} track - ID: ${event.track.id}, Label: ${event.track.label}`,
                "info",
            );

            if (event.streams && event.streams[0]) {
                const stream = event.streams[0];
                log(`Stream ID: ${stream.id}, Active: ${stream.active}`, "info");

                const audioTracks = stream.getAudioTracks();
                const videoTracks = stream.getVideoTracks();

                log(`Audio tracks: ${audioTracks.length}, Video tracks: ${videoTracks.length}`, "info");

                audioTracks.forEach((track, index) => {
                    log(
                        `Audio track ${index}: ${track.label}, enabled: ${track.enabled}, muted: ${track.muted}`,
                        "info",
                    );
                });
            }

            if (event.track.kind === "video" && event.streams && event.streams[0]) {
                // Clear any existing source first
                elements.video.srcObject = null;

                // Set the new stream
                elements.video.srcObject = event.streams[0];
                log("Video stream attached to element");

                // Force load
                elements.video.load();

                // Try to play after a short delay
                setTimeout(() => {
                    elements.video
                        .play()
                        .then(() => {
                            log("Video play started", "success");
                        })
                        .catch(e => {
                            log(`Video play failed: ${e.message}`, "error");
                            // Try playing muted if autoplay fails
                            elements.video.muted = true;
                            elements.video
                                .play()
                                .then(() => {
                                    log("Video playing muted", "info");
                                })
                                .catch(e2 => {
                                    log(`Muted play also failed: ${e2.message}`, "error");
                                });
                        });
                }, 100);
            }
        };

        state.peerConnection.ontrack = event => {
            OnTrackReceived(event);
        };

        state.peerConnection.onconnectionstatechange = () => {
            log(`Connection state: ${state.peerConnection.connectionState}`);
            if (state.peerConnection.connectionState === "connected") {
                // onConnected();
                log("Peer connection established", "success");
            } else if (state.peerConnection.connectionState === "failed") {
                onDisconnected();
            }
        };

        state.peerConnection.oniceconnectionstatechange = () => {
            // log(`ICE connection state: ${state.peerConnection.iceConnectionState}`);
            if (
                state.peerConnection.iceConnectionState === "disconnected" ||
                state.peerConnection.iceConnectionState === "failed"
            ) {
                onDisconnected();
            } else if (state.peerConnection.iceConnectionState === "connected") {
                log(`ICE connection state changed: ${state.peerConnection.iceConnectionState}`, "info");
                onConnected();
            }
        };

        // Set remote description (offer from D-ID)
        await state.peerConnection.setRemoteDescription(streamData.offer);
        log("Remote description set");

        // Create answer
        const answer = await state.peerConnection.createAnswer();
        await state.peerConnection.setLocalDescription(answer);
        log("Local description set");

        // Send answer to D-ID
        log("Sending answer to D-ID...");
        const startResponse = await fetch(
            `${API_BASE_URL}${API_ENDPOINTS.startStream}${state.streamId}/start`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    sessionId: state.streamSessionId, // camelCase for our backend
                    sdpAnswer: answer,
                }),
            },
        );

        if (!startResponse.ok) {
            throw new Error("Failed to start stream");
        }

        log("Answer sent to D-ID successfully", "success");
    } catch (error) {
        log(`WebRTC setup failed: ${error.message}`, "error");
        throw error;
    }
}

function OnTrackReceived(event) {
    log(`=== TRACK RECEIVED ===`, "info");
    log(`Track kind: ${event.track.kind}`, "info");
    log(`Track ID: ${event.track.id}`, "info");
    log(`Track enabled: ${event.track.enabled}`, "info");
    log(`Track muted: ${event.track.muted}`, "info");
    log(`Track readyState: ${event.track.readyState}`, "info");

    if (event.streams && event.streams[0]) {
        const stream = event.streams[0];
        log(`Stream ID: ${stream.id}`, "info");

        // Log ALL tracks in the stream
        const allTracks = stream.getTracks();
        log(`Total tracks in stream: ${allTracks.length}`, "info");

        allTracks.forEach((track, index) => {
            log(`  Track ${index}: ${track.kind} - ${track.label} (enabled: ${track.enabled})`, "info");
        });

        // Count audio and video tracks
        const audioTracks = stream.getAudioTracks();
        const videoTracks = stream.getVideoTracks();
        log(
            `Stream contains: ${audioTracks.length} audio tracks, ${videoTracks.length} video tracks`,
            "info",
        );

        // Log detailed audio track info
        audioTracks.forEach((track, i) => {
            log(
                `  Audio Track ${i}: Label="${track.label}", ID="${track.id}", enabled=${track.enabled}, muted=${track.muted}`,
                "info",
            );
        });

        // Attach the stream to video element only once
        if (!elements.video.srcObject || elements.video.srcObject.id !== stream.id) {
            // Clear any existing source first
            if (elements.video.srcObject) {
                log("Replacing existing stream", "info");
            }

            elements.video.srcObject = stream;
            log("Stream attached to video element", "success");

            // Force load
            elements.video.load();

            // Try to play after a short delay
            setTimeout(async () => {
                try {
                    // Check current state before playing
                    log(
                        `Before play: muted=${elements.video.muted}, volume=${elements.video.volume}`,
                        "info",
                    );

                    // First try to play with audio
                    await elements.video.play();
                    log("Video playing with audio", "success");

                    // Double-check audio state after play
                    const postPlayAudioTracks = elements.video.srcObject.getAudioTracks();
                    log(`After play: ${postPlayAudioTracks.length} audio tracks`, "info");
                    postPlayAudioTracks.forEach((track, i) => {
                        log(`  Post-play Audio ${i}: enabled=${track.enabled}`, "info");
                    });
                } catch (e) {
                    log(`Autoplay failed: ${e.name} - ${e.message}`, "error");

                    // Handle autoplay policy restrictions
                    if (e.name === "NotAllowedError") {
                        // Check if there's already an audio enable button
                        const existingBtn = document.getElementById("enable-audio-btn");
                        if (!existingBtn) {
                            // Create a button to manually enable audio
                            const enableAudioBtn = document.createElement("button");
                            enableAudioBtn.id = "enable-audio-btn";
                            enableAudioBtn.textContent = "🔊 Click to Enable Audio";
                            enableAudioBtn.style.cssText = `
                                position: absolute;
                                top: 50%;
                                left: 50%;
                                transform: translate(-50%, -50%);
                                z-index: 1000;
                                padding: 15px 30px;
                                font-size: 18px;
                                background: #3b82f6;
                                color: white;
                                border: none;
                                border-radius: 25px;
                                cursor: pointer;
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                            `;

                            elements.video.parentElement.appendChild(enableAudioBtn);

                            enableAudioBtn.onclick = async () => {
                                try {
                                    elements.video.muted = false;
                                    elements.video.volume = 1.0;
                                    await elements.video.play();
                                    enableAudioBtn.remove();
                                    log("Audio enabled by user interaction", "success");

                                    // Log final audio state
                                    const audioTracks = elements.video.srcObject.getAudioTracks();
                                    log(
                                        `Audio enabled: ${audioTracks.length} tracks, muted=${elements.video.muted}, volume=${elements.video.volume}`,
                                        "success",
                                    );
                                } catch (err) {
                                    log(`Failed to enable audio: ${err.message}`, "error");
                                }
                            };
                        }

                        // Try to play muted as fallback
                        try {
                            elements.video.muted = true;
                            await elements.video.play();
                            log(
                                "Playing muted due to autoplay policy - click button to enable audio",
                                "warning",
                            );
                        } catch (e2) {
                            log(`Even muted play failed: ${e2.message}`, "error");
                        }
                    } else {
                        // Other errors
                        log(`Play error: ${e.toString()}`, "error");
                    }
                }
            }, 100);
        } else {
            log("Stream already attached, skipping", "info");
        }
    } else {
        log("No streams in track event!", "error");
    }

    // Log specific track type
    if (event.track.kind === "video") {
        log("Video track processing complete", "success");
    } else if (event.track.kind === "audio") {
        log("Audio track processing complete", "success");
        // Additional audio-specific debugging
        if (event.streams && event.streams[0]) {
            const audioTracks = event.streams[0].getAudioTracks();
            if (audioTracks.length > 0) {
                log(`Audio track settings: ${JSON.stringify(audioTracks[0].getSettings())}`, "info");
            }
        }
    }
}

function onConnected() {
    state.isConnected = true;
    updateStatus("connected");
    elements.connectBtn.textContent = "Disconnect";
    elements.connectBtn.disabled = false;
    elements.messageInput.disabled = false;
    elements.sendBtn.disabled = false;
    elements.recordBtn.disabled = false;

    addMessageBubble("Avatar connected! You can now start chatting.", "system");
    log("Avatar connected successfully", "success");

    let greetingSent = false;

    const sendGreetingWhenReady = () => {
        if (greetingSent) {
            log("Greeting already sent, skipping", "info");
            return;
        }

        if (!state.isStreamReady) {
            log("Waiting for stream to be ready...", "info");
            setTimeout(sendGreetingWhenReady, 500); // Check every 500ms
            return;
        }

        // Mark as sent immediately to prevent duplicates
        greetingSent = true;

        // Now send the greeting
        log("Sending greeting to activate avatar...");
        const greetingText = "Hello! I'm your AI assistant. How can I help you today?";
        const greetingRequest = CreateAvatarScriptRequest(
            state.streamSessionId,
            ttsConfig.voiceId,
            greetingText,
            ttsConfig.defaultStyle,
        );
        fetch(`${API_BASE_URL}${API_ENDPOINTS.startStream}${state.streamId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(greetingRequest),
        })
            .then(response => {
                if (response.ok) {
                    log("Greeting sent to avatar", "success");
                    addMessageBubble(greetingText, "assistant");
                } else {
                    response.text().then(errorText => {
                        log(`Failed to send greeting: ${response.status} - ${errorText}`, "error");
                    });
                }
            })
            .catch(error => {
                log(`Greeting error: ${error.message}`, "error");
            });
    };

    // Start checking for readiness
    sendGreetingWhenReady();

    // Fallback: force ready after 5 seconds if no stream/ready event
    setTimeout(() => {
        if (!state.isStreamReady) {
            log("Forcing stream ready state after timeout", "warning");
            state.isStreamReady = true;
        }
    }, 5000);

    // Debug video element state after a delay
    setTimeout(() => {
        if (elements.video.srcObject) {
            const stream = elements.video.srcObject;
            log(
                `Video element state: readyState=${elements.video.readyState}, videoWidth=${elements.video.videoWidth}, videoHeight=${elements.video.videoHeight}`,
            );
            log(`Stream active: ${stream.active}, tracks: ${stream.getTracks().length}`);
            stream.getTracks().forEach(track => {
                log(`Track: ${track.kind}, enabled=${track.enabled}, readyState=${track.readyState}`);
            });
        } else {
            log("No srcObject on video element!", "error");
        }
    }, 3000);
}

function onDisconnected() {
    state.isConnected = false;
    updateStatus("disconnected");
    elements.connectBtn.textContent = "Connect Avatar";
    elements.connectBtn.disabled = false;
    elements.messageInput.disabled = true;
    elements.sendBtn.disabled = true;
    elements.recordBtn.disabled = true;

    if (state.peerConnection) {
        state.peerConnection.close();
        state.peerConnection = null;
    }

    // Properly clean up video element
    if (elements.video.srcObject) {
        const stream = elements.video.srcObject;
        stream.getTracks().forEach(track => track.stop());
        elements.video.srcObject = null;
    }

    addMessageBubble("Avatar disconnected", "system");
    log("Avatar disconnected");
}

async function disconnectAvatar() {
    log("Disconnecting avatar...");

    // Close the D-ID stream properly
    if (state.streamId && state.streamSessionId) {
        try {
            const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.startStream}${state.streamId}`, {
                method: "DELETE",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: state.streamSessionId, // Note: underscore format
                }),
            });

            if (response.ok) {
                log("Stream closed successfully", "success");
            } else {
                log("Failed to close stream properly", "error");
            }
        } catch (error) {
            log(`Error closing stream: ${error.message}`, "error");
        }
    }

    onDisconnected();
}

// Send Message
// Updated Send Message function with LLM integration
async function handleSendMessage() {
    const message = elements.messageInput.value.trim();
    if (!message || !state.isConnected) return;

    if (!state.isStreamReady) {
        log("Stream not ready yet, cannot send message", "warning");
        addMessageBubble("Please wait, avatar is still initializing...", "system");
        return;
    }

    elements.messageInput.value = "";
    elements.sendBtn.disabled = true;

    // Add user message
    addMessageBubble(message, "user");

    try {
        // Call LLM service
        log("Calling LLM service...");
        const llmResponse = await fetch(`${API_BASE_URL}${API_ENDPOINTS.testLLM}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: message,
                // Optional: include session context if you want conversation history
                // sessionId: state.sessionId,
                // userId: state.userId
            }),
        });

        if (!llmResponse.ok) {
            throw new Error(`LLM error: ${llmResponse.status}`);
        }

        const llmData = await llmResponse.json();

        // Extract the response text and emotion
        const responseText = llmData.text || llmData.response || "I'm sorry, I couldn't process that.";
        const emotion = llmData.emotion || "neutral"; // EVE provides emotion data

        log(`LLM response received: ${responseText} (emotion: ${emotion})`, "success");

        // Add assistant message
        addMessageBubble(responseText, "assistant");

        // Send text to avatar with emotion-aware voice selection
        log("Sending text to avatar with emotion...");

        // Map emotions to appropriate voice characteristics
        const voiceMapping = {
            happy: { voice: ttsConfig.voiceId, style: "cheerful" }, // Default happy voice
            excited: { voice: ttsConfig.voiceId, style: "excited" },
            thoughtful: { voice: ttsConfig.voiceId, style: "hopeful" },
            curious: { voice: ttsConfig.voiceId, style: "chat" },
            confident: { voice: ttsConfig.voiceId, style: "friendly" },
            concerned: { voice: ttsConfig.voiceId, style: "sad" },
            empathetic: { voice: ttsConfig.voiceId, style: "empathetic" },
        };

        const voiceConfig = voiceMapping[emotion] || {
            voice: ttsConfig.voiceId,
            style: ttsConfig.defaultStyle,
        };
        log(
            `TTS DEBUG: Using voiceId='${ttsConfig.voiceId}' with style='${voiceConfig.style}' for emotion='${emotion}'`,
            "info",
        );

        const scriptRequest = CreateAvatarScriptRequest(
            state.streamSessionId,
            voiceConfig.voice,
            responseText,
            voiceConfig.style,
        );
        const url = `${API_BASE_URL}${API_ENDPOINTS.startStream}${state.streamId}`;
        const avatarResponse = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(scriptRequest),
        });

        if (!avatarResponse.ok) {
            const errorText = await avatarResponse.text();
            throw new Error(`Avatar error: ${avatarResponse.status}: ${errorText}`);
        }

        log("Text sent to avatar successfully with emotion styling", "success");

        // Store conversation in session (if implemented)
        if (state.sessionId) {
            storeMessageInSession(message, "user");
            storeMessageInSession(responseText, "assistant", emotion);
        }
    } catch (error) {
        log(`Message send failed: ${error.message}`, "error");

        // Provide user-friendly error messages
        if (error.message.includes("LLM error")) {
            addMessageBubble("Sorry, I'm having trouble thinking right now. Please try again.", "system");
        } else if (error.message.includes("Avatar error")) {
            addMessageBubble(
                "I understood you, but I'm having trouble speaking. Here's what I wanted to say:",
                "system",
            );
            // Still show the LLM response even if avatar fails
            if (typeof responseText !== "undefined") {
                addMessageBubble(responseText, "assistant");
            }
        } else {
            addMessageBubble("Failed to send message. Please check your connection.", "system");
        }
    } finally {
        elements.sendBtn.disabled = false;
    }
}

// Helper to create POST requests to the avatar stream endpoint
function CreateAvatarScriptRequest(sessionId, voiceId, inputText, style) {
    const body = {
        session_id: sessionId,
        script: {
            type: "text",
            provider: {
                type: "microsoft",
                voice_id: voiceId,
                voice_config: {
                    rate: "+0%", // Normal speaking rate
                    pitch: "+0%",
                    style: style,
                },
            },
            input: inputText,
            ssml: style !== "neutral", // Use SSML only if style is not neutral
            //ssml: false
        },
        presenter_config: {
            crop: {
                type: "wide",
                rectangle: {
                    bottom: 1,
                    right: 1,
                    left: 0,
                    top: 0,
                },
            },
        },
        background: {
            color: "#16213e",
        },
        //    config: {
        //        stitch: true
        //    }
    };
    return body;
}

// Optional: Store messages in session for conversation history
async function storeMessageInSession(content, role, emotion = null) {
    try {
        const messageData = {
            sessionId: state.sessionId,
            type: role === "user" ? "UserText" : "AssistantText",
            content: content,
            timestamp: new Date().toISOString(),
        };

        if (emotion) {
            messageData.emotion = emotion;
        }

        await fetch(`${API_BASE_URL}${API_ENDPOINTS.addMessage}/${state.sessionId}/messages`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(messageData),
        });

        log(`Message stored in session: ${role}`, "info");
    } catch (error) {
        log(`Failed to store message: ${error.message}`, "warning");
        // Don't fail the main flow if session storage fails
    }
}

// Audio Recording
async function handleRecord() {
    if (state.isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

// UI Helper Functions
function updateStatus(status) {
    elements.status.className = `status-badge status-${status}`;
    elements.status.textContent = status.charAt(0).toUpperCase() + status.slice(1);
}

function addMessageBubble(text, type) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = text;

    elements.chatMessages.appendChild(messageDiv);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

    // Store message in session (simplified)
    if (state.sessionId && type !== "system") {
        // In real implementation, call API to store message
    }
}

// Utility function to check WebRTC support
function checkWebRTCSupport() {
    const supported = !!(
        window.RTCPeerConnection &&
        navigator.mediaDevices &&
        navigator.mediaDevices.getUserMedia
    );

    log(`WebRTC support: ${supported}`, supported ? "success" : "error");

    if (!supported) {
        addMessageBubble("Your browser does not support WebRTC. Please use a modern browser.", "system");
        elements.connectBtn.disabled = true;
    }
}

// Add to your state object
state.speechConfig = null;
state.recognizer = null;
state.azureKey = null; // We'll set this securely
state.azureRegion = null;

// Azure Speech configuration
async function setupAzureSpeech() {
    try {
        // Fetch credentials from your C# backend
        const config = await fetchSpeechAndTTSConfig();

        // Update TTS config
        if (config.voiceId) ttsConfig.voiceId = config.voiceId;
        if (config.defaultStyle) ttsConfig.defaultStyle = config.defaultStyle;

        // Update STT config in state
        if (config.apiKey) state.azureKey = config.apiKey;
        if (config.region) state.azureRegion = config.region;

        // Ensure the Speech SDK is loaded
        if (typeof SpeechSDK === "undefined") {
            throw new Error("Azure Speech SDK not loaded. Please check your script include.");
        }

        state.speechConfig = SpeechSDK.SpeechConfig.fromSubscription(state.azureKey, state.azureRegion);

        // Configure for optimal real-time performance
        state.speechConfig.speechRecognitionLanguage = "en-US";
        state.speechConfig.outputFormat = SpeechSDK.OutputFormat.Detailed;

        // Enable punctuation and capitalization
        state.speechConfig.setServiceProperty(
            "punctuation",
            "explicit",
            SpeechSDK.ServicePropertyChannel.UriQueryParameter,
        );

        log("Azure Speech configured successfully", "success");
        elements.recordBtn.title = "Click to start voice input";
        return true;
    } catch (error) {
        log(`Azure Speech setup failed: ${error.message}`, "error");

        // Disable the record button if setup fails
        elements.recordBtn.disabled = true;
        elements.recordBtn.title = "Speech recognition not available";

        return false;
    }
}

// Modified recording functions with Azure Speech
async function startRecording() {
    try {
        if (!state.speechConfig) {
            const configured = await setupAzureSpeech();
            if (!configured) {
                alert("Speech recognition not configured");
                return;
            }
        }

        log("Starting Azure Speech recognition...", "info");

        // Create audio config from default microphone
        const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();

        // Create recognizer
        state.recognizer = new SpeechSDK.SpeechRecognizer(state.speechConfig, audioConfig);

        // Track interim results
        let currentTranscript = "";

        // Real-time transcription (interim results)
        state.recognizer.recognizing = (s, e) => {
            if (e.result.reason === SpeechSDK.ResultReason.RecognizingSpeech) {
                currentTranscript = e.result.text;
                elements.messageInput.value = currentTranscript + "...";
                log(`Recognizing: ${currentTranscript}`, "info");
            }
        };

        // Final results
        state.recognizer.recognized = (s, e) => {
            if (e.result.reason === SpeechSDK.ResultReason.RecognizedSpeech) {
                currentTranscript = e.result.text;
                elements.messageInput.value = currentTranscript;
                log(`Recognized: ${currentTranscript}`, "success");

                // Auto-send option (comment out if you don't want this)
                if (currentTranscript.trim() && state.isConnected) {
                    setTimeout(() => {
                        if (!state.isRecording) {
                            // Only auto-send if stopped recording
                            handleSendMessage();
                        }
                    }, 500);
                }
            } else if (e.result.reason === SpeechSDK.ResultReason.NoMatch) {
                log("No speech recognized", "warning");
            }
        };

        // Handle errors
        state.recognizer.canceled = (s, e) => {
            log(`Recognition canceled: ${e.reason}`, "error");
            if (e.reason === SpeechSDK.CancellationReason.Error) {
                log(`Error details: ${e.errorDetails}`, "error");
            }
            stopRecording();
        };

        // Start continuous recognition
        state.recognizer.startContinuousRecognitionAsync(
            () => {
                state.isRecording = true;
                elements.recordBtn.classList.add("recording");
                elements.recordBtn.textContent = "⏹️ Stop";
                log("Azure recognition started", "success");
            },
            error => {
                log(`Failed to start: ${error}`, "error");
                stopRecording();
            },
        );
    } catch (error) {
        log(`Recording failed: ${error.message}`, "error");
        alert("Microphone access denied or Azure Speech not configured");
    }
}

function stopRecording() {
    if (state.recognizer && state.isRecording) {
        state.recognizer.stopContinuousRecognitionAsync(
            () => {
                state.isRecording = false;
                elements.recordBtn.classList.remove("recording");
                elements.recordBtn.textContent = "🎤 Record";
                log("Recognition stopped", "info");

                // Clean up
                state.recognizer.close();
                state.recognizer = null;

                // Auto-send the transcribed text if any
                const transcribedText = elements.messageInput.value.trim();
                if (transcribedText && state.isConnected) {
                    log(`Auto-sending transcribed text: ${transcribedText}`, "info");
                    // Small delay to ensure everything is cleaned up
                    setTimeout(() => {
                        handleSendMessage();
                    }, 100);
                    if (transcribedText && state.isConnected) {
                        // Visual feedback that message is being sent
                        elements.messageInput.disabled = true;
                        elements.messageInput.style.opacity = "0.5";

                        setTimeout(() => {
                            handleSendMessage();
                            // Re-enable after sending
                            setTimeout(() => {
                                elements.messageInput.disabled = false;
                                elements.messageInput.style.opacity = "1";
                            }, 200);
                        }, 100);
                    }
                } else if (!transcribedText) {
                    log("No text to send", "info");
                } else if (!state.isConnected) {
                    log("Cannot send - avatar not connected", "warning");
                }
            },
            error => {
                log(`Stop error: ${error}`, "error");
                state.isRecording = false;
                elements.recordBtn.classList.remove("recording");
                elements.recordBtn.textContent = "🎤 Record";
            },
        );
    }
}

// Check support on load
checkWebRTCSupport();

window.debugMediaState = debugMediaState;
