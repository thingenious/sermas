namespace AliveOnD_ID.Models.Configurations;

public class ServiceConfiguration
{
    public LLMConfig LLM { get; set; } = new();
    public DIDConfig DID { get; set; } = new();
    public AzureSpeechServicesConfig AzureSpeechServices { get; set; } = new();
}
