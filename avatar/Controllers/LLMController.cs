using Microsoft.AspNetCore.Mvc;
using AliveOnD_ID.Models;
using AliveOnD_ID.Services.Interfaces;
using AliveOnD_ID.Controllers.Requests;
using AliveOnD_ID.Controllers.Responses;

namespace AliveOnD_ID.Controllers;

[ApiController]
[Route("api/[controller]")]
public class LLMController : ControllerBase
{
    private readonly ILLMService _llmService;
    private readonly ILogger<LLMController> _logger;

    public LLMController(ILLMService llmService, ILogger<LLMController> logger)
    {
        _llmService = llmService;
        _logger = logger;
    }

    /// <summary>
    /// Test LLM service with a simple message
    /// </summary>
    [HttpPost("Send")]
    public async Task<ActionResult<LLMResponse>> SendToLLM([FromBody] TestLLMRequest request)
    {
        try
        {
            // Explicitly call the overload with conversation history
            var response = await _llmService.GetResponseAsync(request.Message, (List<ChatMessage>?)null);
            return Ok(response);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error testing LLM service");
            return StatusCode(500, new { error = "LLM service error", details = ex.Message });
        }
    }

    /// <summary>
    /// Test LLM service with session context
    /// </summary>
    [HttpPost("test-with-session")]
    public async Task<ActionResult<LLMResponse>> TestLLMWithSession([FromBody] TestLLMWithSessionRequest request)
    {
        try
        {
            // Use the overload with userId and sessionId
            var response = await _llmService.GetResponseAsync(request.Message, request.UserId, request.SessionId);
            return Ok(response);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error testing LLM service with session");
            return StatusCode(500, new { error = "LLM service error", details = ex.Message });
        }
    }
}
