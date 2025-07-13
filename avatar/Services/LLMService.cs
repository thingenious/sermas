using Microsoft.Extensions.Options;
using AliveOnD_ID.Models;
using AliveOnD_ID.Services.Interfaces;
using AliveOnD_ID.Models.Configurations;
using AliveOnD_ID.Controllers.Responses;

namespace AliveOnD_ID.Services;

// LLM Service - Already clean, no retry policy needed
public class LLMService : BaseHttpService, ILLMService
{
    private readonly LLMConfig _config;

    public LLMService(
        HttpClient httpClient,
        IOptions<ServiceConfiguration> config,
        ILogger<LLMService> logger) : base(httpClient, logger)
    {
        _config = config.Value.LLM;
        _httpClient.BaseAddress = new Uri(_config.BaseUrl);
        _httpClient.Timeout = TimeSpan.FromSeconds(_config.Timeout);
    }

    public async Task<LLMResponse> GetResponseAsync(string userMessage, List<ChatMessage>? conversationHistory = null)
    {
        try
        {
            _logger.LogInformation("Getting LLM response for message length: {Length}", userMessage.Length);

            // TODO: Replace with your actual LLM API endpoint and format
            var endpoint = "/api/chat/completions"; // Replace with actual endpoint


            var requestData = new
            {
                model = _config.Model,
                messages = BuildMessageHistory(userMessage, conversationHistory),
                max_tokens = 1000,
                temperature = 0.7
            };

            var authHeader = !string.IsNullOrEmpty(_config.ApiKey) ? $"Bearer {_config.ApiKey}" : null;
            var result = await PostJsonAsync<LLMResponse>(endpoint, requestData, authHeader);

            _logger.LogInformation("LLM response received. Response length: {Length}",
                result?.Text?.Length ?? 0);

            return result ?? new LLMResponse { Text = "I'm sorry, I couldn't process your request right now." };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting LLM response");
            throw;
        }
    }

    public async Task<LLMResponse> GetResponseAsync(string userMessage, string? userId = null, string? sessionId = null)
    {
        // For now, this just calls the main method without additional context
        // You can extend this to fetch conversation history based on sessionId
        return await GetResponseAsync(userMessage, null);
    }

    private object[] BuildMessageHistory(string userMessage, List<ChatMessage>? conversationHistory)
    {
        var messages = new List<object>();

        // Add system message
        messages.Add(new { role = "system", content = "You are a helpful AI assistant with a friendly personality." });

        // Add conversation history
        if (conversationHistory != null)
        {
            foreach (var message in conversationHistory.TakeLast(10)) // Limit to last 10 messages
            {
                if (message.Type == MessageType.UserText || message.Type == MessageType.UserAudio)
                {
                    messages.Add(new { role = "user", content = message.Content });
                }
                else if (message.Type == MessageType.AssistantText)
                {
                    messages.Add(new { role = "assistant", content = message.Content });
                }
            }
        }

        // Add current user message
        messages.Add(new { role = "user", content = userMessage });

        return messages.ToArray();
    }
}
