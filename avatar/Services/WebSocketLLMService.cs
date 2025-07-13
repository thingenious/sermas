using AliveOnD_ID.Controllers.Responses;
using AliveOnD_ID.Models;
using AliveOnD_ID.Models.Chat;
using AliveOnD_ID.Models.Configurations;
using AliveOnD_ID.Services.Interfaces;
using Microsoft.Extensions.Options;
using System.Net.WebSockets;
using System.Reactive.Linq;
using System.Text;
using System.Text.Json;
using Websocket.Client;

namespace AliveOnD_ID.Services;

public class WebSocketLLMService : ILLMService, IDisposable
{
    private readonly ILogger<WebSocketLLMService> _logger;
    private readonly LLMConfig _config;
    private IWebsocketClient? _webSocketClient;

    // Connection management
    private readonly SemaphoreSlim _connectionSemaphore = new(1);
    private bool _isConnected = false;
    private IDisposable? _messageSubscription;
    private IDisposable? _reconnectionSubscription;

    // Conversation management
    private string? _currentConversationId;
    private readonly SemaphoreSlim _conversationLock = new(1);
    private TaskCompletionSource<bool>? _conversationStartTcs;

    // Request management
    private readonly Dictionary<string, PendingRequest> _pendingRequests = new();
    private readonly object _requestLock = new();

    // Message accumulation
    private readonly Dictionary<string, MessageAccumulator> _messageAccumulators = new();

    public WebSocketLLMService(
        IOptions<ServiceConfiguration> config,
        ILogger<WebSocketLLMService> logger)
    {
        _logger = logger;
        _config = config.Value.LLM;
    }

    #region Connection Management

    private async Task EnsureConnectedAsync()
    {
        if (_isConnected && _webSocketClient?.IsRunning == true)
            return;

        await _connectionSemaphore.WaitAsync();
        try
        {
            if (_isConnected && _webSocketClient?.IsRunning == true)
                return;

            await ConnectAsync();
        }
        finally
        {
            _connectionSemaphore.Release();
        }
    }

    private async Task ConnectAsync()
    {
        try
        {
            _logger.LogInformation("Connecting to WebSocket LLM endpoint: {BaseUrl}", _config.BaseUrl);

            var wsUrl = _config.BaseUrl;

            // Ensure proper WebSocket URL format
            if (!wsUrl.StartsWith("ws://") && !wsUrl.StartsWith("wss://"))
            {
                // Only replace if it's http/https
                wsUrl = wsUrl.Replace("https://", "wss://").Replace("http://", "ws://");
            }

            _logger.LogInformation("Using WebSocket URL: {WsUrl}", wsUrl);

            // Create WebSocket with authentication via subprotocol
            var factory = new Func<ClientWebSocket>(() =>
            {
                var client = new ClientWebSocket();
                if (!string.IsNullOrEmpty(_config.ApiKey))
                {
                    client.Options.AddSubProtocol("chat");
                    client.Options.AddSubProtocol(_config.ApiKey);
                    _logger.LogDebug("Added subprotocols: chat, [api-key]");
                }
                return client;
            });

            _webSocketClient = new WebsocketClient(new Uri(wsUrl), factory)
            {
                ReconnectTimeout = TimeSpan.FromMinutes(15),
                IsReconnectionEnabled = true,
                MessageEncoding = Encoding.UTF8
            };

            // Set up connection completion source
            var connectionTcs = new TaskCompletionSource<bool>();

            // Set up event handlers with connection tracking
            SetupEventHandlers(connectionTcs);

            // Start the connection
            _logger.LogInformation("Starting WebSocket connection...");
            await _webSocketClient.Start();

            // Wait for the connection to be established (with timeout)
            using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(10));
            try
            {
                await connectionTcs.Task.WaitAsync(cts.Token);
                _logger.LogInformation("WebSocket connection established successfully");
            }
            catch (OperationCanceledException)
            {
                throw new TimeoutException("WebSocket connection timeout - check if the URL is correct and accessible");
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to connect to WebSocket LLM endpoint");
            _isConnected = false;
            throw;
        }
    }

    private void SetupEventHandlers(TaskCompletionSource<bool>? connectionTcs = null)
    {
        // Message handler
        _messageSubscription?.Dispose();
        _messageSubscription = _webSocketClient!.MessageReceived
            .Where(msg => msg.MessageType == WebSocketMessageType.Text)
            .Subscribe(OnMessageReceived);

        // Reconnection handler
        _reconnectionSubscription?.Dispose();
        _reconnectionSubscription = _webSocketClient.ReconnectionHappened
            .Subscribe(info =>
            {
                OnReconnectionHappened(info);

                // Complete connection task if this is the initial connection
                if (connectionTcs != null && info.Type == ReconnectionType.Initial)
                {
                    _isConnected = true;
                    connectionTcs.TrySetResult(true);
                }
            });

        // Disconnection handler
        _webSocketClient.DisconnectionHappened
            .Subscribe(info =>
            {
                OnDisconnectionHappened(info);

                // If we're trying to connect and it fails, complete with error
                if (connectionTcs != null && !connectionTcs.Task.IsCompleted)
                {
                    connectionTcs.TrySetException(new Exception($"Connection failed: {info.CloseStatus} - {info.CloseStatusDescription}"));
                }
            });
    }

    #endregion

    #region Event Handlers

    private void OnMessageReceived(ResponseMessage message)
    {
        try
        {
            HandleMessage(message.Text);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error handling WebSocket message");
        }
    }

    private void OnReconnectionHappened(ReconnectionInfo info)
    {
        _logger.LogInformation("WebSocket reconnected: {Type}", info.Type);
        _isConnected = true;

        // Reset conversation state on reconnection
        _currentConversationId = null;

        // Fail any pending requests
        FailAllPendingRequests("Connection was lost and reconnected");
    }

    private void OnDisconnectionHappened(DisconnectionInfo info)
    {
        _logger.LogWarning("WebSocket disconnected: {Type} - {CloseStatus}",
            info.Type, info.CloseStatus);
        _isConnected = false;

        // Fail any pending requests
        FailAllPendingRequests($"Connection lost: {info.CloseStatus}");
    }

    #endregion

    #region Message Handling

    private void HandleMessage(string message)
    {
        _logger.LogDebug("Received WebSocket message: {Message}", message);

        try
        {
            using var doc = JsonDocument.Parse(message);
            var root = doc.RootElement;

            if (!root.TryGetProperty("type", out var typeElement))
            {
                _logger.LogWarning("Received message without type field");
                return;
            }

            var messageType = typeElement.GetString();

            switch (messageType)
            {
                case "conversation_started":
                    HandleConversationStarted(root);
                    break;

                case "message":
                    HandleChatMessage(root);
                    break;

                case "error":
                    HandleErrorMessage(root);
                    break;

                default:
                    _logger.LogWarning("Unknown message type: {Type}", messageType);
                    break;
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error parsing WebSocket message");
        }
    }

    private void HandleConversationStarted(JsonElement root)
    {
        if (root.TryGetProperty("conversation_id", out var convIdElement))
        {
            _currentConversationId = convIdElement.GetString();
            _logger.LogInformation("Conversation started: {ConversationId}", _currentConversationId);

            // Complete the conversation start task
            _conversationStartTcs?.TrySetResult(true);
        }
    }

    private void HandleChatMessage(JsonElement root)
    {
        var content = root.TryGetProperty("content", out var contentEl)
            ? contentEl.GetString() ?? ""
            : "";

        var emotion = root.TryGetProperty("emotion", out var emotionEl)
            ? emotionEl.GetString()
            : null;

        var isFinal = root.TryGetProperty("is_final", out var finalEl)
            && finalEl.GetBoolean();

        // Find the active request
        PendingRequest? activeRequest = null;
        lock (_requestLock)
        {
            activeRequest = _pendingRequests.Values.FirstOrDefault(r => r.IsActive);
        }

        if (activeRequest == null)
        {
            _logger.LogWarning("Received message segment but no active request found");
            return;
        }

        // Get or create accumulator for this request
        if (!_messageAccumulators.TryGetValue(activeRequest.Id, out var accumulator))
        {
            accumulator = new MessageAccumulator();
            _messageAccumulators[activeRequest.Id] = accumulator;
        }

        // Accumulate the message
        accumulator.AppendContent(content);
        accumulator.LastEmotion = emotion ?? accumulator.LastEmotion;

        // If this is the final segment, complete the request
        if (isFinal)
        {
            CompleteRequest(activeRequest.Id, accumulator);
        }
    }

    private void HandleErrorMessage(JsonElement root)
    {
        var error = root.TryGetProperty("content", out var contentEl)
            ? contentEl.GetString() ?? "Unknown error"
            : "Unknown error";

        _logger.LogError("EVE API Error: {Error}", error);

        // Fail the active request
        lock (_requestLock)
        {
            var activeRequest = _pendingRequests.Values.FirstOrDefault(r => r.IsActive);
            if (activeRequest != null)
            {
                activeRequest.TaskCompletionSource.TrySetException(
                    new Exception($"EVE API Error: {error}"));
                _pendingRequests.Remove(activeRequest.Id);
            }
        }
    }

    #endregion

    #region Conversation Management

    private async Task<bool> EnsureConversationStartedAsync()
    {
        if (!string.IsNullOrEmpty(_currentConversationId))
            return true;

        await _conversationLock.WaitAsync();
        try
        {
            if (!string.IsNullOrEmpty(_currentConversationId))
                return true;

            return await StartConversationAsync();
        }
        finally
        {
            _conversationLock.Release();
        }
    }

    private async Task<bool> StartConversationAsync(string? existingConversationId = null)
    {
        try
        {
            _conversationStartTcs = new TaskCompletionSource<bool>();

            var startMessage = existingConversationId != null
                ? new EVEStartConversationMessage{ Type = "start_conversation", ConversationID = existingConversationId }
                : new EVEStartConversationMessage{ Type = "start_conversation" };

            await SendMessageAsync(JsonSerializer.Serialize(startMessage));

            // Wait for conversation_started response with timeout
            using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(10));
            await _conversationStartTcs.Task.WaitAsync(cts.Token);

            return !string.IsNullOrEmpty(_currentConversationId);
        }
        catch (OperationCanceledException)
        {
            _logger.LogError("Timeout waiting for conversation to start");
            return false;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to start conversation");
            return false;
        }
    }

    #endregion

    #region Request Management

    public async Task<LLMResponse> GetResponseAsync(string userMessage, List<ChatMessage>? conversationHistory = null)
    {
        try
        {
            await EnsureConnectedAsync();

            // Ensure conversation is started
            if (!await EnsureConversationStartedAsync())
            {
                throw new InvalidOperationException("Failed to start conversation with EVE");
            }

            // Create and register the request
            var request = new PendingRequest(Guid.NewGuid().ToString());

            lock (_requestLock)
            {
                _pendingRequests[request.Id] = request;
            }

            // Send the user message
            var userMessageData = new EVEUserMessage
            {
                Content = userMessage
            };

            await SendMessageAsync(JsonSerializer.Serialize(userMessageData));
            _logger.LogInformation("Sent user message to EVE");

            // Wait for response with timeout
            using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(_config.Timeout));
            try
            {
                var response = await request.TaskCompletionSource.Task.WaitAsync(cts.Token);
                _logger.LogInformation("Received complete LLM response");
                return response;
            }
            catch (OperationCanceledException)
            {
                CleanupRequest(request.Id);
                throw new TimeoutException($"LLM request timed out after {_config.Timeout} seconds");
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting LLM response");
            throw;
        }
    }

    public async Task<LLMResponse> GetResponseAsync(string userMessage, string? userId = null, string? sessionId = null)
    {
        // If sessionId is provided, use it as conversation_id
        if (!string.IsNullOrEmpty(sessionId) && sessionId != _currentConversationId)
        {
            await StartConversationAsync(sessionId);
        }

        return await GetResponseAsync(userMessage, (List<ChatMessage>?)null);
    }

    private void CompleteRequest(string requestId, MessageAccumulator accumulator)
    {
        lock (_requestLock)
        {
            if (_pendingRequests.TryGetValue(requestId, out var request))
            {
                var response = new LLMResponse
                {
                    Text = accumulator.GetFullMessage(),
                    Emotion = accumulator.LastEmotion,
                    Metadata = new Dictionary<string, object>
                    {
                        ["conversation_id"] = _currentConversationId ?? ""
                    }
                };

                request.TaskCompletionSource.TrySetResult(response);
                CleanupRequest(requestId);
            }
        }
    }

    private void CleanupRequest(string requestId)
    {
        lock (_requestLock)
        {
            _pendingRequests.Remove(requestId);
            _messageAccumulators.Remove(requestId);
        }
    }

    private void FailAllPendingRequests(string reason)
    {
        lock (_requestLock)
        {
            foreach (var request in _pendingRequests.Values)
            {
                request.TaskCompletionSource.TrySetException(new Exception(reason));
            }
            _pendingRequests.Clear();
            _messageAccumulators.Clear();
        }
    }

    #endregion

    #region Utility Methods

    private async Task SendMessageAsync(string message)
    {
        if (_webSocketClient == null)
            throw new InvalidOperationException("WebSocket client is not initialized");

        if (!_webSocketClient.IsRunning)
        {
            _logger.LogError("WebSocket is not running. IsStarted: {IsStarted}, IsRunning: {IsRunning}",
                _webSocketClient.IsStarted, _webSocketClient.IsRunning);
            throw new InvalidOperationException("WebSocket is not connected. Check if the URL is correct and the server is accessible.");
        }

        _logger.LogDebug("Sending WebSocket message: {Message}", message);
        _webSocketClient.Send(message);
        await Task.CompletedTask;
    }

    #endregion

    #region IDisposable

    public void Dispose()
    {
        _logger.LogInformation("Disposing WebSocket LLM Service");

        FailAllPendingRequests("Service is being disposed");

        _messageSubscription?.Dispose();
        _reconnectionSubscription?.Dispose();
        _webSocketClient?.Dispose();
        _connectionSemaphore?.Dispose();
        _conversationLock?.Dispose();
    }

    #endregion


}

// EVE API Message Formats:
/*
// Start conversation:
{
  "type": "start_conversation"
}

// Continue existing conversation:
{
  "type": "start_conversation",
  "conversation_id": "existing-conversation-id"
}

// User message:
{
  "type": "user_message",
  "content": "Hello, how are you?"
}

// Response: conversation_started
{
  "type": "conversation_started",
  "conversation_id": "unique-conversation-id"
}

// Response: message segment
{
  "type": "message",
  "content": "I'm doing well, ",
  "emotion": "happy",
  "is_final": false
}

// Response: final message segment
{
  "type": "message",
  "content": "thank you for asking!",
  "emotion": "happy",
  "is_final": true
}

// Error response:
{
  "type": "error",
  "content": "Error description here"
}
*/
