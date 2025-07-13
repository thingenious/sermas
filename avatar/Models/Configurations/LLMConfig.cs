namespace AliveOnD_ID.Models.Configurations;

public class LLMConfig
{
    public string ApiKey { get; set; } = string.Empty;
    public string BaseUrl { get; set; } = string.Empty;
    public string Model { get; set; } = string.Empty;
    public int Timeout { get; set; } = 60;
}
