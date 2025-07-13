namespace AliveOnD_ID.Models.Configurations;

public class ChatConfig
{
    public int SessionTimeoutMinutes { get; set; } = 30;
    public int MaxMessagesPerSession { get; set; } = 100;
    public int MaxAudioDurationSeconds { get; set; } = 60;
}
