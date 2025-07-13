namespace AliveOnD_ID.Models.Configurations;

public class RedisConfig
{
    public string ConnectionString { get; set; } = "localhost:6379";
    public int DefaultDatabase { get; set; } = 0;
    public string KeyPrefix { get; set; } = "AvatarChat:";
}
