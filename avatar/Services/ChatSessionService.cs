using Microsoft.Extensions.Options;
using AliveOnD_ID.Models;
using AliveOnD_ID.Services.Interfaces;
using AliveOnD_ID.Models.Configurations;

namespace AliveOnD_ID.Services;

public class ChatSessionService : IChatSessionService
{
    private readonly IStorageService _storage;
    private readonly ChatConfig _config;
    private readonly ILogger<ChatSessionService> _logger;

    public ChatSessionService(
        IStorageService storage,
        IOptions<ChatConfig> config,
        ILogger<ChatSessionService> logger)
    {
        _storage = storage;
        _config = config.Value;
        _logger = logger;
    }

    public async Task<ChatSession> CreateSessionAsync(string userId)
    {
        try
        {
            var session = new ChatSession
            {
                SessionId = Guid.NewGuid().ToString(),
                UserId = userId,
                CreatedAt = DateTime.UtcNow,
                LastActivityAt = DateTime.UtcNow
            };

            var sessionKey = GetSessionKey(session.SessionId);
            var userSessionsKey = GetUserSessionsKey(userId);

            // Store the session
            var expiry = TimeSpan.FromMinutes(_config.SessionTimeoutMinutes);
            await _storage.SetAsync(sessionKey, session, expiry);

            // Get existing user sessions or create empty list
            var userSessions = await _storage.GetAsync<List<ChatSession>>(userSessionsKey) ?? new List<ChatSession>();

            // Add new session to user's session list
            userSessions.Add(session);
            await _storage.SetAsync(userSessionsKey, userSessions, expiry);

            _logger.LogInformation("Created session {SessionId} for user {UserId}", session.SessionId, userId);
            return session;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating session for user {UserId}", userId);
            throw;
        }
    }

    public async Task<ChatSession?> GetSessionAsync(string sessionId)
    {
        try
        {
            var sessionKey = GetSessionKey(sessionId);
            var session = await _storage.GetAsync<ChatSession>(sessionKey);

            if (session != null)
            {
                // Update last activity
                session.LastActivityAt = DateTime.UtcNow;
                await UpdateSessionAsync(session);
            }

            return session;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving session {SessionId}", sessionId);
            return null;
        }
    }

    public async Task<bool> UpdateSessionAsync(ChatSession session)
    {
        try
        {
            var sessionKey = GetSessionKey(session.SessionId);
            session.LastActivityAt = DateTime.UtcNow;

            var expiry = TimeSpan.FromMinutes(_config.SessionTimeoutMinutes);
            var result = await _storage.SetAsync(sessionKey, session, expiry);

            if (result)
            {
                _logger.LogDebug("Updated session {SessionId}", session.SessionId);
            }

            return result;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating session {SessionId}", session.SessionId);
            return false;
        }
    }

    public async Task<bool> DeleteSessionAsync(string sessionId)
    {
        try
        {
            var session = await GetSessionAsync(sessionId);
            if (session == null) return false;

            var sessionKey = GetSessionKey(sessionId);
            var userSessionsKey = GetUserSessionsKey(session.UserId);

            // Remove from storage
            await _storage.DeleteAsync(sessionKey);

            // Update user's session list
            var userSessions = await GetUserSessionsAsync(session.UserId);
            userSessions.RemoveAll(s => s.SessionId == sessionId);
            await _storage.SetAsync(userSessionsKey, userSessions);

            _logger.LogInformation("Deleted session {SessionId}", sessionId);
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting session {SessionId}", sessionId);
            return false;
        }
    }

    public async Task<List<ChatSession>> GetUserSessionsAsync(string userId)
    {
        try
        {
            var userSessionsKey = GetUserSessionsKey(userId);
            var sessions = await _storage.GetAsync<List<ChatSession>>(userSessionsKey);

            // If the key doesn't exist, return null to indicate user doesn't exist
            // If the key exists but is empty list, return empty list
            return sessions ?? new List<ChatSession>();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving sessions for user {UserId}", userId);
            throw; // Re-throw to let controller handle it
        }
    }

    public async Task<bool> UserExistsAsync(string userId)
    {
        try
        {
            var userSessionsKey = GetUserSessionsKey(userId);
            return await _storage.ExistsAsync(userSessionsKey);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error checking if user {UserId} exists", userId);
            return false;
        }
    }

    public async Task<bool> AddMessageAsync(string sessionId, ChatMessage message)
    {
        try
        {
            var session = await GetSessionAsync(sessionId);
            if (session == null)
            {
                _logger.LogWarning("Session {SessionId} not found when adding message", sessionId);
                return false;
            }

            message.SessionId = sessionId;
            session.Messages.Add(message);

            // Limit messages per session
            if (session.Messages.Count > _config.MaxMessagesPerSession)
            {
                var messagesToRemove = session.Messages.Count - _config.MaxMessagesPerSession;
                session.Messages.RemoveRange(0, messagesToRemove);
                _logger.LogInformation("Trimmed {Count} old messages from session {SessionId}",
                    messagesToRemove, sessionId);
            }

            var result = await UpdateSessionAsync(session);

            if (result)
            {
                _logger.LogDebug("Added message {MessageId} to session {SessionId}",
                    message.Id, sessionId);
            }

            return result;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error adding message to session {SessionId}", sessionId);
            return false;
        }
    }

    public async Task<bool> UpdateMessageAsync(string sessionId, ChatMessage message)
    {
        try
        {
            var session = await GetSessionAsync(sessionId);
            if (session == null)
            {
                _logger.LogWarning("Session {SessionId} not found when updating message", sessionId);
                return false;
            }

            var existingMessage = session.Messages.FirstOrDefault(m => m.Id == message.Id);
            if (existingMessage == null)
            {
                _logger.LogWarning("Message {MessageId} not found in session {SessionId}",
                    message.Id, sessionId);
                return false;
            }

            // Update the message
            var index = session.Messages.IndexOf(existingMessage);
            session.Messages[index] = message;

            var result = await UpdateSessionAsync(session);

            if (result)
            {
                _logger.LogDebug("Updated message {MessageId} in session {SessionId}",
                    message.Id, sessionId);
            }

            return result;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating message in session {SessionId}", sessionId);
            return false;
        }
    }

    private static string GetSessionKey(string sessionId) => $"session:{sessionId}";
    private static string GetUserSessionsKey(string userId) => $"user_sessions:{userId}";
}
