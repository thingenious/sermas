using Microsoft.Extensions.Options;
using AliveOnD_ID.Services.Interfaces;
using System.Text.Json;
using AliveOnD_ID.Models.Configurations;
using AliveOnD_ID.Controllers.Responses;

namespace AliveOnD_ID.Services;

// Audio to Text Service - Fixed without retry policy
public class ASRService : BaseHttpService, IASRService
{
    private readonly AzureSpeechServicesConfig _config;

    public ASRService(
        HttpClient httpClient,
        IOptions<ServiceConfiguration> config,
        ILogger<ASRService> logger) : base(httpClient, logger)
    {
        _config = config.Value.AzureSpeechServices;
        _httpClient.BaseAddress = new Uri(_config.BaseUrl);
        //_httpClient.Timeout = TimeSpan.FromSeconds(_config.Timeout);
    }

    public async Task<ASRResponse> ConvertAudioToTextAsync(byte[] audioData, string fileName)
    {
        using var stream = new MemoryStream(audioData);
        return await ConvertAudioToTextAsync(stream, fileName);
    }

    public async Task<ASRResponse> ConvertAudioToTextAsync(Stream audioStream, string fileName)
    {
        try
        {
            _logger.LogInformation("Converting audio to text, file: {FileName}", fileName);

            // TODO: Replace with your actual ASR API endpoint and format
            var endpoint = "/api/speech-to-text"; // Replace with actual endpoint

            using var form = new MultipartFormDataContent();
            using var audioContent = new StreamContent(audioStream);
            audioContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue("audio/mpeg");
            form.Add(audioContent, "audio", fileName);

            using var request = new HttpRequestMessage(HttpMethod.Post, endpoint)
            {
                Content = form
            };

            if (!string.IsNullOrEmpty(_config.ApiKey))
            {
                request.Headers.Add("Authorization", $"Bearer {_config.ApiKey}");
            }

            // Direct HTTP call without retry policy
            var response = await _httpClient.SendAsync(request);
            response.EnsureSuccessStatusCode();

            var responseContent = await response.Content.ReadAsStringAsync();

            // TODO: Parse according to your ASR API response format
            // This is a mock response structure
            var result = JsonSerializer.Deserialize<ASRResponse>(responseContent, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });

            _logger.LogInformation("Audio to text conversion completed. Text length: {Length}",
                result?.Text?.Length ?? 0);

            return result ?? new ASRResponse { Text = "", Confidence = 0.0f };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error converting audio to text");
            throw;
        }
    }
}
