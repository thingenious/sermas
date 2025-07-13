using System.Text.Json.Serialization;

namespace AliveOnD_ID.Services.Models;
#region Request Models

/// <summary>
/// Stream configuration
/// </summary>
public class ConfigData
{
    [JsonPropertyName("stitch")]
    public bool Stitch { get; set; } = true;
}

#endregion
