using System.Text.Json.Serialization;

namespace AliveOnD_ID.Services.Models;
#region Request Models

/// <summary>
/// Stream configuration
/// </summary>
public class CropConfigData
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "wide";

    [JsonPropertyName("rectangle")]
    public RectangleConfigData? Rectangle { get; set; }
}

#endregion
