using System.Text.Json.Serialization;

namespace AliveOnD_ID.Models.Chat;

public class EVEMessageResponse
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [JsonPropertyName("content")]
    public string Content { get; set; } = string.Empty;

    [JsonPropertyName("emotion")]
    public string? Emotion { get; set; }

    [JsonPropertyName("is_final")]
    public bool IsFinal { get; set; }
}
