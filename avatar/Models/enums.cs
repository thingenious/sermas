namespace AliveOnD_ID.Models;

public enum MessageStatus
{
    Pending,
    Processing,
    Completed,
    Failed
}

public enum StreamStatus
{
    Disconnected,
    Connecting,
    Connected,
    Speaking,
    Error
}

public enum MessageType
{
    UserText,
    UserAudio,
    AssistantText,
    AssistantAvatar,
    System
}

public enum LogLevel
{
    Info,
    Success,
    Warning,
    Error
}
