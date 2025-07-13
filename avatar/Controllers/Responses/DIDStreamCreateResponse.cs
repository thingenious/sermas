using AliveOnD_ID.Services.Models;
using System.Text.Json.Serialization;

namespace AliveOnD_ID.Controllers.Responses;

// D-ID API Response Models
public class DIDStreamCreateResponse
{
    [JsonPropertyName("id")]
    public string? Id { get; set; }

    [JsonPropertyName("session_id")]
    public string? SessionId { get; set; }

    [JsonPropertyName("offer")]
    public object? Offer { get; set; }

    [JsonPropertyName("ice_servers")]
    public List<DIDIceServer>? IceServers { get; set; }
}
