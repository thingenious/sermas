using AliveOnD_ID.Models;

namespace AliveOnD_ID.Services.Interfaces;

public interface IChatSessionService
{
    Task<ChatSession> CreateSessionAsync(string userId);
    Task<ChatSession?> GetSessionAsync(string sessionId);
    Task<bool> UpdateSessionAsync(ChatSession session);
    Task<bool> DeleteSessionAsync(string sessionId);
    Task<List<ChatSession>> GetUserSessionsAsync(string userId);
    Task<bool> UserExistsAsync(string userId);
    Task<bool> AddMessageAsync(string sessionId, ChatMessage message);
    Task<bool> UpdateMessageAsync(string sessionId, ChatMessage message);
}
