using System.Text.Json.Serialization;

namespace AliveOnD_ID.Services.Models;
#region Request Models

/// <summary>
/// Stream configuration
/// </summary>
public class RectangleConfigData
{
    [JsonPropertyName("bottom")]
    public double Bottom { get; set; } = 1;

    [JsonPropertyName("right")]
    public double Right { get; set; } = 1;

    [JsonPropertyName("left")]
    public double Left { get; set; } = 0;

    [JsonPropertyName("top")]
    public double Top { get; set; } = 0;
}

#endregion
