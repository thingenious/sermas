namespace AliveOnD_ID.Models.Configurations;

public class AzureSpeechServicesConfig
{
    public string ApiKey { get; set; } = string.Empty;
    public string BaseUrl { get; set; } = string.Empty;
    public string Region { get; set; } = string.Empty;
    public string VoiceId { get; set; } = string.Empty;
    public string DefaultStyle { get; set; } = "neutral";
}
