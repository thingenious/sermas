namespace AliveOnD_ID.Controllers.Requests;

public class TestLLMWithSessionRequest
{
    public string Message { get; set; } = string.Empty;
    public string? UserId { get; set; }
    public string? SessionId { get; set; }
}
