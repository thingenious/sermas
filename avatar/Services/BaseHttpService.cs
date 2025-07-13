using System.Text;
using System.Text.Json;

namespace AliveOnD_ID.Services;

// Simplified base service without retry logic
public abstract class BaseHttpService
{
    protected readonly HttpClient _httpClient;
    protected readonly ILogger _logger;

    protected BaseHttpService(HttpClient httpClient, ILogger logger)
    {
        _httpClient = httpClient;
        _logger = logger;
    }

    protected async Task<T?> PostJsonAsync<T>(string endpoint, object data, string? authHeader = null)
    {
        try
        {
            using var request = new HttpRequestMessage(HttpMethod.Post, endpoint);

            if (!string.IsNullOrEmpty(authHeader))
            {
                request.Headers.Add("Authorization", authHeader);
            }

            if (data != null)
            {
                var jsonContent = JsonSerializer.Serialize(data);
                request.Content = new StringContent(jsonContent, Encoding.UTF8, "application/json");

                _logger.LogDebug("POST {Endpoint}: {Json}", endpoint, jsonContent);
            }

            var response = await _httpClient.SendAsync(request);
            var responseContent = await response.Content.ReadAsStringAsync();

            _logger.LogDebug("Response {StatusCode}: {Content}", response.StatusCode, responseContent);

            response.EnsureSuccessStatusCode();

            return JsonSerializer.Deserialize<T>(responseContent, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error calling API endpoint: {Endpoint}", endpoint);
            throw;
        }
    }

    protected async Task<bool> PostAsync(string endpoint, object data, string? authHeader = null)
    {
        try
        {
            using var request = new HttpRequestMessage(HttpMethod.Post, endpoint);

            if (!string.IsNullOrEmpty(authHeader))
            {
                request.Headers.Add("Authorization", authHeader);
            }

            if (data != null)
            {
                var jsonContent = JsonSerializer.Serialize(data);
                request.Content = new StringContent(jsonContent, Encoding.UTF8, "application/json");

                _logger.LogDebug("POST {Endpoint}: {Json}", endpoint, jsonContent);
            }

            var response = await _httpClient.SendAsync(request);
            var responseContent = await response.Content.ReadAsStringAsync();

            _logger.LogDebug("Response {StatusCode}: {Content}", response.StatusCode, responseContent);

            if (!response.IsSuccessStatusCode)
            {
                _logger.LogWarning("API call failed with status {StatusCode}: {Endpoint}, Response: {Response}",
                    response.StatusCode, endpoint, responseContent);
            }

            return response.IsSuccessStatusCode;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error calling API endpoint: {Endpoint}", endpoint);
            return false;
        }
    }
}
