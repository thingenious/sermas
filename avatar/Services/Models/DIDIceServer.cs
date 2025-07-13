using System.Text.Json;
using System.Text.Json.Serialization;

namespace AliveOnD_ID.Services.Models;

public class DIDIceServer
{
    [JsonPropertyName("urls")]
    public object? UrlsRaw { get; set; }  // Handle both string and array

    [JsonPropertyName("username")]
    public string? Username { get; set; }

    [JsonPropertyName("credential")]
    public string? Credential { get; set; }

    // Helper property to get URLs as List<string> - ignored during JSON serialization
    [JsonIgnore]
    public List<string> Urls
    {
        get
        {
            if (UrlsRaw == null) return new List<string>();

            // If it's already a JsonElement array
            if (UrlsRaw is JsonElement element)
            {
                if (element.ValueKind == JsonValueKind.Array)
                {
                    return element.EnumerateArray().Select(e => e.GetString() ?? string.Empty).ToList();
                }
                else if (element.ValueKind == JsonValueKind.String)
                {
                    return new List<string> { element.GetString() ?? string.Empty };
                }
            }

            // If it's a string
            if (UrlsRaw is string singleUrl)
            {
                return new List<string> { singleUrl };
            }

            return new List<string>();
        }
    }
}
