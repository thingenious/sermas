using System.Text.Json.Serialization;

namespace AliveOnD_ID.Services.Models;
#region Request Models

/// <summary>
/// Stream configuration
/// </summary>
public class BackgroundConfigData
{
    [JsonPropertyName("color")]
    public string Color { get; set; } = "false";

}

#endregion
