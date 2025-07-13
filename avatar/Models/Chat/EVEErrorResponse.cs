using System.Text.Json.Serialization;

namespace AliveOnD_ID.Models.Chat;

public class EVEErrorResponse
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [JsonPropertyName("content")]
    public string Content { get; set; } = string.Empty;
}
