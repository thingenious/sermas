namespace AliveOnD_ID.Models;

public class AvatarStreamInfo
{
    public string StreamId { get; set; } = string.Empty;
    public string SessionId { get; set; } = string.Empty;
    public StreamStatus Status { get; set; } = StreamStatus.Disconnected;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
