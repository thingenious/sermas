using System.Text.Json.Serialization;

namespace AliveOnD_ID.Services.Models;
#region Request Models

/// <summary>
/// Stream configuration
/// </summary>
public class PresenterConfigData
{
    [JsonPropertyName("crop")]
    public CropConfigData? CropConfigData { get; set; }
}

#endregion
