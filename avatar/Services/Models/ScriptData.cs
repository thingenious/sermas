using System.Text.Json.Serialization;

namespace AliveOnD_ID.Services.Models;
#region Request Models

/// <summary>
/// Script data structure
/// </summary>
public class ScriptData
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "text";

    [JsonPropertyName("provider")]
    public ProviderData? Provider { get; set; }

    [JsonPropertyName("input")]
    public string Input { get; set; } = string.Empty;

    [JsonPropertyName("ssml")]
    public bool Ssml { get; set; } = true;
}

#endregion

//    "script": {
//    "type": "text",
//    "provider": {
//        "type": "microsoft",
//        "voice_id": "Sara",
//        "voice_config": {
//            "style": "cheerful",
//            "rate": "1",
//            "pitch": "1"
//        }
//    },
//    "ssml": true,
//    "input": "this is an example"
//  }
