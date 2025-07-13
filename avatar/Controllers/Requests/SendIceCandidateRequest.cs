using Newtonsoft.Json;

namespace AliveOnD_ID.Controllers.Requests;
#region Request Models

/// <summary>
/// Request to send ICE candidate
/// </summary>
public class SendIceCandidateRequest
{
    [JsonProperty("sessionId")]
    public string SessionId { get; set; } = string.Empty;

    [JsonProperty("candidate")]
    public string Candidate { get; set; } = string.Empty;

    [JsonProperty("mid")]
    public string Mid { get; set; } = string.Empty;

    [JsonProperty("lineIndex")]
    public int LineIndex { get; set; }
}

#endregion
