using Newtonsoft.Json;

namespace AliveOnD_ID.Controllers.Requests;
#region Request Models

/// <summary>
/// Request to start stream with WebRTC answer
/// </summary>
public class StartStreamRequest
{
    [JsonProperty("sessionId")]
    public string SessionId { get; set; } = string.Empty;

    [JsonProperty("sdpAnswer")]
    public object SdpAnswer { get; set; } = new();
}

#endregion
