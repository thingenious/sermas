using System.Text.Json.Serialization;

namespace AliveOnD_ID.Services.Models;
#region Request Models

/// <summary>
/// TTS Provider configuration
/// </summary>
public class ProviderData
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "microsoft";

    [JsonPropertyName("voice_id")]
    public string? VoiceId { get; set; } // Nullable, set from config

    [JsonPropertyName("voice_config")]
    public VoiceConfigData? VoiceConfig { get; set; } // Nullable, set from config or left null
}

#endregion

//    "provider": {
//        "type": "microsoft",
//        "voice_id": "Sara",
//        "voice_config": {
//            "style": "cheerful",
//            "rate": "1",
//            "pitch": "1"
//        }
//    }
