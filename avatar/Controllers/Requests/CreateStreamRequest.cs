using Newtonsoft.Json;

namespace AliveOnD_ID.Controllers.Requests;
#region Request Models

/// <summary>
/// Request to create a new D-ID stream
/// </summary>
public class CreateStreamRequest
{
    [JsonProperty("presenter_id")]
    public string? PresenterId { get; set; }

    [JsonProperty("driver_id")]
    public string? DriverId { get; set; }
}

#endregion
