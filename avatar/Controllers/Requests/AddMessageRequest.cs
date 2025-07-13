using AliveOnD_ID.Models;
using System.Text.Json.Serialization;

namespace AliveOnD_ID.Controllers.Requests;

public class AddMessageRequest
{
    [JsonPropertyName("sessionId")]
    public string SessionId { get; set; } = string.Empty;

    [JsonPropertyName("type")]
    public MessageType Type { get; set; }

    [JsonPropertyName("content")]
    public string Content { get; set; } = string.Empty;

    [JsonPropertyName("emotion")]
    public string? Emotion { get; set; }
}
