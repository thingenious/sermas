using AliveOnD_ID.Models.Configurations;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Options;

namespace AliveOnD_ID.Controllers;


[ApiController]
[Route("api/speech")]
public class SpeechController : ControllerBase
{
    private readonly AzureSpeechServicesConfig _configuration;
    private readonly ILogger<SpeechController> _logger;

    public SpeechController(IOptions<AzureSpeechServicesConfig> configuration, ILogger<SpeechController> logger)
    {
        _configuration = configuration.Value;
        _logger = logger;
    }

    [HttpGet("config")]
    public AzureSpeechServicesConfig GetSpeechConfig()
    {
        try
        {
            // Validate required config values
            var key = _configuration.ApiKey;
            var region = _configuration.Region;

            if (string.IsNullOrEmpty(key) || string.IsNullOrEmpty(region))
            {
                _logger.LogError("Azure Speech Services credentials not configured");
                // Return an empty config or throw, depending on your error handling preference
                return null!;
            }

            return _configuration;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving speech configuration");
            return null!;
        }
    }
}
