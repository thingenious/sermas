using System.Text.Json.Serialization;

namespace AliveOnD_ID.Models.Chat;

public class EVEUserMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "user_message";

    [JsonPropertyName("content")]
    public string Content { get; set; } = string.Empty;
}
