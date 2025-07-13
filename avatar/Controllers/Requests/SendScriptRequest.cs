using System.Text.Json.Serialization;
using AliveOnD_ID.Services.Models;

namespace AliveOnD_ID.Controllers.Requests;
#region Request Models

/// <summary>
/// Request to send script (text) to avatar
/// </summary>
public class SendScriptRequest
{
    [JsonPropertyName("session_id")]
    public string SessionId { get; set; } = string.Empty;

    [JsonPropertyName("script")]
    public ScriptData Script { get; set; } = new();

    [JsonPropertyName("config")]
    public ConfigData? Config { get; set; }

    [JsonPropertyName("presenter_config")]
    public PresenterConfigData? PresenterConfig { get; set; }

    [JsonPropertyName("background")]
    public BackgroundConfigData? Background { get; set; }
}

#endregion

//{
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
//  },
//  "config": {
//    "result_format": "mov"
//  },
//  "presenter_config": {
//    "crop": {
//        "type": "wide"
//    }
//},
//  "session_id": "ashjdkh"
//}
