using System.Text.Json.Serialization;

namespace AliveOnD_ID.Models.Chat;

public class EVEStartConversationMessage
{
    [JsonPropertyName("type")]
    public string Type { get; set; }

    [JsonPropertyName("conversation_id")]
    public string? ConversationID { get; set; } = string.Empty;
}
