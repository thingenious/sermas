using AliveOnD_ID.Controllers.Responses;
using AliveOnD_ID.Models;

namespace AliveOnD_ID.Services.Interfaces;

public interface ILLMService
{
    Task<LLMResponse> GetResponseAsync(string userMessage, List<ChatMessage>? conversationHistory = null);
    Task<LLMResponse> GetResponseAsync(string userMessage, string? userId = null, string? sessionId = null);
}
