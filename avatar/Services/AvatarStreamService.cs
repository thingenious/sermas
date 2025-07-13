using AliveOnD_ID.Controllers.Requests;
using AliveOnD_ID.Controllers.Responses;
using AliveOnD_ID.Models;
using AliveOnD_ID.Models.Configurations;
using AliveOnD_ID.Services.Interfaces;
using Microsoft.Extensions.Options;
using System.IO;
using System.Text;
using System.Text.Json;
using static System.Net.Mime.MediaTypeNames;

namespace AliveOnD_ID.Services;

public class AvatarStreamService : BaseHttpService, IAvatarStreamService
{
    private readonly DIDConfig _config;
    private readonly AzureSpeechServicesConfig _azureSpeechConfig;

    public AvatarStreamService(
        HttpClient httpClient,
        IOptions<ServiceConfiguration> config,
        ILogger<AvatarStreamService> logger) : base(httpClient, logger)
    {
        _config = config.Value.DID;
        _azureSpeechConfig = config.Value.AzureSpeechServices;
        _httpClient.BaseAddress = new Uri(_config.BaseUrl);
        _httpClient.Timeout = TimeSpan.FromSeconds(60); // Longer timeout for streaming
    }

    public async Task<DIDStreamResponse> CreateStreamAsync(string? presenterId = null, string? driverId = null)
    {
        try
        {
            _logger.LogInformation("Creating D-ID Clips stream with presenter: {PresenterId}, driver: {DriverId}",
                presenterId ?? _config.PresenterId, driverId ?? _config.DriverId);

            var endpoint = "/clips/streams";
            var requestData = new
            {
                presenter_id = presenterId ?? _config.PresenterId,
                driver_id = driverId ?? _config.DriverId,
                stream_warmup = true  // Add this
            };

            var authHeader = $"Basic {_config.ApiKey}";

            // Let's get the raw response first
            using var request = new HttpRequestMessage(HttpMethod.Post, endpoint);
            request.Headers.Add("Authorization", authHeader);
            request.Content = new StringContent(JsonSerializer.Serialize(requestData), Encoding.UTF8, "application/json");

            var response = await _httpClient.SendAsync(request);
            var rawJson = await response.Content.ReadAsStringAsync();

            _logger.LogDebug("Raw D-ID response: {RawResponse}", rawJson);
            // Now parse it
            var result = JsonSerializer.Deserialize<DIDStreamCreateResponse>(rawJson, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });

            if (response.Headers.TryGetValues("Set-Cookie", out var cookies))
            {
                _logger.LogDebug("Set-Cookie headers: {Cookies}", string.Join("; ", cookies));
            }

            // In AvatarStreamService.CreateStreamAsync method
            var response_parsed = new DIDStreamResponse
            {
                Id = result?.Id ?? string.Empty,
                SessionId = result?.SessionId ?? string.Empty, // Check both formats
                Offer = result?.Offer ?? new object(),
                IceServers = result?.IceServers?.Select(ice => new IceServer
                {
                    Urls = ice.Urls,
                    Username = ice.Username,
                    Credential = ice.Credential
                }).ToList() ?? new List<IceServer>()
            };
            _logger.LogInformation("D-ID stream created successfully. StreamId: {StreamId}, SessionId: {SessionId}",
                response_parsed.Id, response_parsed.SessionId);

            return response_parsed;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating D-ID stream");
            throw;
        }
    }

    public async Task<bool> StartStreamAsync(string streamId, string sessionId, object sdpAnswer)
    {
        try
        {
            _logger.LogInformation("Starting D-ID stream: {StreamId}", streamId);
            _logger.LogDebug("Using sessionId as-is: {SessionId}", sessionId);

            var endpoint = $"/clips/streams/{streamId}/sdp";
            var requestData = new
            {
                answer = sdpAnswer,
                session_id = sessionId  // Send exactly as received from D-ID
            };

            var authHeader = $"Basic {_config.ApiKey}";
            var success = await PostAsync(endpoint, requestData, authHeader);

            if (success)
            {
                _logger.LogInformation("D-ID stream started successfully: {StreamId}", streamId);
            }
            else
            {
                _logger.LogWarning("Failed to start D-ID stream: {StreamId}", streamId);
            }

            return success;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error starting D-ID stream {StreamId}", streamId);
            return false;
        }
    }

    public async Task<bool> SendIceCandidateAsync(string streamId, string sessionId, string candidate, string mid, int lineIndex)
    {
        try
        {
            _logger.LogDebug("Sending ICE candidate for stream: {StreamId}", streamId);

            var endpoint = $"/clips/streams/{streamId}/ice";
            var requestData = new
            {
                candidate = candidate,
                session_id = sessionId,
                sdpMid = mid,
                sdpMLineIndex = lineIndex
            };

            var authHeader = $"Basic {_config.ApiKey}";
            return await PostAsync(endpoint, requestData, authHeader);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error sending ICE candidate for stream {StreamId}", streamId);
            return false;
        }
    }

    public async Task<bool> SendTextToAvatarAsync(string streamId, string sessionId, string text, string? emotion = null)
    {
        try
        {
            _logger.LogInformation("Sending text to D-ID avatar stream {StreamId}: {Text}", streamId, text);
            _logger.LogInformation("Using TTS voice: {VoiceId}, style: {Style}", _azureSpeechConfig.VoiceId, _azureSpeechConfig.DefaultStyle);

            var endpoint = $"/clips/streams/{streamId}";

            // Construct script data with proper TTS provider configuration
            var scriptData = new
            {
                type = "text",
                input = text,
                provider = new
                {
                    type = "microsoft",
                    voice_id = _azureSpeechConfig.VoiceId,
                    voice_config = new
                    {
                        rate = "+0%",  // Normal speaking rate
                        pitch = "+0%",
                        style = _azureSpeechConfig.DefaultStyle
                    }
                },
                config = new
                {
                    logo = false,
                    result_format = "mp4"
                },
                presenter_config = new
                {
                    crop = new
                    {
                        type = "wide",
                        rectangle = new
                        {
                            bottom = 1,
                            right = 1,
                            left = 0,
                            top = 0
                        }
                    }
                },
                background = new
                {
                    color = false
                }
            };

            // Build configuration with detailed driver settings
            var configDict = new Dictionary<string, object>
            {
                ["stitch"] = true,
                ["driver"] = new
                {
                    loop = false,
                    enable_audio_normalization = true,
                    motion_speed = 0.7,    // Slightly slower for more natural movement
                    silence_padding = 0.2   // Add slight pause between sentences
                }
            };

            if (!string.IsNullOrEmpty(emotion))
            {
                configDict["driver_expressions"] = new { expression = emotion };
            }

            // Only strip the session ID if it's a cookie string
            // var cleanSessionId = sessionId.Contains("AWSALB=") ?
            //     ExtractSessionIdFromCookie(sessionId) :
            //     sessionId;

            var requestData = new
            {
                script = scriptData,
                config = configDict,
                session_id = sessionId
            };

            var authHeader = $"Basic {_config.ApiKey}";

            var jsonContent = JsonSerializer.Serialize(requestData);
            _logger.LogDebug("SendTextToAvatarAsync JSON: {Json}", jsonContent);

            var success = await PostAsync(endpoint, requestData, authHeader);

            if (success)
            {
                _logger.LogInformation("Text sent successfully to D-ID avatar: {StreamId}", streamId);
            }
            else
            {
                _logger.LogWarning("Failed to send text to D-ID avatar: {StreamId}", streamId);
            }

            return success;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error sending text to avatar stream {StreamId}: {Text}", streamId, text);
            return false;
        }
    }

    // public async Task<string> CreateClipStream(string streamId, string sessionId, string textInput)
    // {
    //     using (var client = new HttpClient())
    //     {
    //         // Make sure you're using the stream_id in the URL, not session_id
    //         var url = $"https://api.d-id.com/clips/streams/{streamId}";
    //         // Create the request body
    //         var requestBody = new
    //         {
    //             session_id = sessionId,  // session_id goes in the body
    //             script = new
    //             {
    //                 type = "text",
    //                 input = textInput
    //             },
    //             config = new
    //             {
    //                 stitch = true
    //             }
    //         };
    //         // Debug: Log what you're sending
    //         var jsonContent = Newtonsoft.Json.JsonConvert.SerializeObject(requestBody);
    //         Console.WriteLine($"URL: {url}");
    //         Console.WriteLine($"Request Body: {jsonContent}");
    //         var content = new StringContent(jsonContent, Encoding.UTF8, "application/json");
    //         client.DefaultRequestHeaders.Add("Authorization", $"Basic {_config.ApiKey}");
    //         var response = await client.PostAsync(url, content);
    //         var responseContent = await response.Content.ReadAsStringAsync();
    //         if (!response.IsSuccessStatusCode)
    //         {
    //             Console.WriteLine($"Error Status: {response.StatusCode}");
    //             Console.WriteLine($"Error Response: {responseContent}");
    //         }
    //         return responseContent;
    //     }
    // }

    // Helper method to extract session ID from AWS cookie
    // private string ExtractSessionIdFromCookie(string cookieString)
    // {
    //     try
    //     {
    //         _logger.LogDebug("Extracting session ID from: {CookieString}", cookieString);

    //         // If it's already a simple session ID, return as-is
    //         if (!cookieString.Contains("AWSALB="))
    //         {
    //             _logger.LogDebug("No AWSALB found, returning as-is: {SessionId}", cookieString);
    //             return cookieString;
    //         }

    //         // Extract the AWSALB value from the cookie string
    //         var awsAlbStart = cookieString.IndexOf("AWSALB=") + 7;
    //         var awsAlbEnd = cookieString.IndexOf(";", awsAlbStart);

    //         if (awsAlbEnd == -1)
    //         {
    //             awsAlbEnd = cookieString.Length;
    //         }

    //         var sessionValue = cookieString.Substring(awsAlbStart, awsAlbEnd - awsAlbStart);
    //         _logger.LogInformation("Extracted session ID: '{ExtractedSessionId}' from cookie", sessionValue);
    //         return sessionValue;
    //     }
    //     catch (Exception ex)
    //     {
    //         _logger.LogError(ex, "Failed to extract session ID from cookie: {CookieString}", cookieString);
    //         return cookieString;
    //     }
    // }

    public async Task<bool> CloseStreamAsync(string streamId, string sessionId)
    {
        try
        {
            _logger.LogInformation("Closing D-ID stream: {StreamId}", streamId);

            // // Extract just the session ID value from the cookie string
            // var cleanSessionId = ExtractSessionIdFromCookie(sessionId);

            var endpoint = $"/clips/streams/{streamId}";
            var requestData = new
            {
                session_id = sessionId
            };

            var request = new HttpRequestMessage(HttpMethod.Delete, endpoint);
            request.Headers.Add("Authorization", $"Basic {_config.ApiKey}");

            // if (requestData != null)
            // {
            //     var jsonContent = JsonSerializer.Serialize(requestData);
            //     request.Content = new StringContent(jsonContent, Encoding.UTF8, "application/json");
            // }

            var response = await _httpClient.SendAsync(request);
            var success = response.IsSuccessStatusCode;

            if (success)
            {
                _logger.LogInformation("D-ID stream closed successfully: {StreamId}", streamId);
            }

            return success;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error closing avatar stream {StreamId}", streamId);
            return false;
        }
    }

    public async Task<bool> SendScriptToAvatarAsync(string streamId, SendScriptRequest scriptRequest)
    {
        try
        {
            _logger.LogInformation("Sending text to D-ID avatar stream {StreamId}: {Text}", streamId, scriptRequest.Script.Input);
            _logger.LogInformation("Using TTS voice: {VoiceId}, style: {Style}", scriptRequest.Script.Provider.VoiceId, scriptRequest.Script.Provider.VoiceConfig.Style);

            var endpoint = $"/clips/streams/{streamId}";
            var sessionId = scriptRequest.SessionId;

            var authHeader = $"Basic {_config.ApiKey}";

            var requestData = new
            {
                script = new
                {
                    type = "text",
                    provider = new
                    {
                        type = "microsoft",
                        voice_id = scriptRequest.Script.Provider.VoiceId,
                        voice_config = new
                        {
                            style = scriptRequest.Script.Provider.VoiceConfig.Style,
                            rate = scriptRequest.Script.Provider.VoiceConfig.Rate,
                            pitch = scriptRequest.Script.Provider.VoiceConfig.Pitch
                        }
                    },
                    input = scriptRequest.Script.Input,
                    ssml = scriptRequest.Script.Ssml
                },
                config = new
                {
                    logo = false,  // or omit if you want default
                    result_format = "mp4"
                },
                //presenter_config = scriptRequest.PresenterConfig,
                background = scriptRequest.Background,
                session_id = scriptRequest.SessionId
            };

            var jsonContent = JsonSerializer.Serialize(requestData);
            _logger.LogDebug("SendScriptToAvatarAsync JSON: {Json}", jsonContent);

            var success = await PostAsync(endpoint, requestData, authHeader);

            if (success)
            {
                _logger.LogInformation("Text sent successfully to D-ID avatar: {StreamId}", streamId);
            }
            else
            {
                _logger.LogWarning("Failed to send text to D-ID avatar: {StreamId}", streamId);
            }

            return success;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error sending text to avatar stream {StreamId}: {Text}", streamId, scriptRequest.Script.Input);
            return false;
        }
    }
}
