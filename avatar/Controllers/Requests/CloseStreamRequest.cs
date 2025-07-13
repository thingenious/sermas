using Newtonsoft.Json;

namespace AliveOnD_ID.Controllers.Requests;
#region Request Models

/// <summary>
/// Request to close stream
/// </summary>
public class CloseStreamRequest
{
    [JsonProperty("session_id")]
    public string SessionId { get; set; } = string.Empty;
}

#endregion
