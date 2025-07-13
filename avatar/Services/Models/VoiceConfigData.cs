using System.Text.Json.Serialization;

namespace AliveOnD_ID.Services.Models
{
    public class VoiceConfigData
    {
        [JsonPropertyName("style")]
        public string Style { get; set; } = "cheerful";

        [JsonPropertyName("rate")]
        public string Rate { get; set; } = "1";

        [JsonPropertyName("pitch")]
        public string Pitch { get; set; } = "1";
    }
}

//"voice_config": {
//            "style": "cheerful",
//            "rate": "1",
//            "pitch": "1"
//        }
