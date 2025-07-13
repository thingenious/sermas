using Microsoft.AspNetCore.Mvc;
using AliveOnD_ID.Models;
using AliveOnD_ID.Services.Interfaces;
using AliveOnD_ID.Controllers.Requests;

namespace AliveOnD_ID.Controllers;

[ApiController]
[Route("api/[controller]")]
public class SessionController : ControllerBase
{
    private readonly IChatSessionService _sessionService;
    private readonly ILogger<SessionController> _logger;

    public SessionController(IChatSessionService sessionService, ILogger<SessionController> logger)
    {
        _sessionService = sessionService;
        _logger = logger;
    }

    /// <summary>
    /// Create a new chat session
    /// </summary>
    [HttpPost("create")]
    public async Task<ActionResult<ChatSession>> CreateSession([FromBody] CreateSessionRequest request)
    {
        try
        {
            // Validate userId
            if (string.IsNullOrWhiteSpace(request.UserId))
            {
                return BadRequest("UserId is required and cannot be empty");
            }

            if (request.UserId.Length > 100) // Reasonable limit
            {
                return BadRequest("UserId cannot exceed 100 characters");
            }

            var session = await _sessionService.CreateSessionAsync(request.UserId);
            return Ok(session);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating session for user {UserId}", request.UserId);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Get an existing chat session
    /// </summary>
    [HttpGet("{sessionId}")]
    public async Task<ActionResult<ChatSession>> GetSession([FromRoute] string sessionId)
    {
        try
        {
            var session = await _sessionService.GetSessionAsync(sessionId);
            if (session == null)
            {
                return NotFound($"Session {sessionId} not found");
            }
            return Ok(session);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving session {SessionId}", sessionId);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Add a message to a session
    /// </summary>
    [HttpPost("{sessionId}/messages")]
    public async Task<ActionResult> AddMessage([FromRoute] string sessionId, [FromBody] AddMessageRequest request)
    {
        try
        {
            var message = new ChatMessage
            {
                Type = request.Type,
                Content = request.Content,
                Emotion = request.Emotion
            };

            var success = await _sessionService.AddMessageAsync(sessionId, message);
            if (!success)
            {
                return BadRequest("Failed to add message");
            }

            return Ok(new { messageId = message.Id });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error adding message to session {SessionId}", sessionId);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Get all sessions for a user
    /// </summary>
    [HttpGet("user/{userId}")]
    public async Task<ActionResult<List<ChatSession>>> GetUserSessions([FromRoute] string userId)
    {
        try
        {
            // Validate userId format
            if (string.IsNullOrWhiteSpace(userId))
            {
                return BadRequest("UserId cannot be empty");
            }

            // Check if user exists
            var userExists = await _sessionService.UserExistsAsync(userId);
            if (!userExists)
            {
                return NotFound($"User '{userId}' does not exist");
            }

            // Get user sessions
            var sessions = await _sessionService.GetUserSessionsAsync(userId);
            return Ok(sessions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving sessions for user {UserId}", userId);
            return StatusCode(500, "Internal server error");
        }
    }
}
