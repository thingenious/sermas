using Microsoft.Extensions.Caching.Memory;
using Microsoft.Extensions.Options;
using AliveOnD_ID.Services.Interfaces;
using AliveOnD_ID.Models.Configurations;

namespace AliveOnD_ID.Services;

public class InMemoryStorageService : IStorageService
{
    private readonly IMemoryCache _cache;
    private readonly RedisConfig _config;
    private readonly ILogger<InMemoryStorageService> _logger;

    public InMemoryStorageService(
        IMemoryCache cache,
        IOptions<RedisConfig> config,
        ILogger<InMemoryStorageService> logger)
    {
        _cache = cache;
        _config = config.Value;
        _logger = logger;
    }

    public Task<T?> GetAsync<T>(string key) where T : class
    {
        try
        {
            var fullKey = GetFullKey(key);
            var value = _cache.Get<T>(fullKey);
            _logger.LogDebug("Retrieved key: {Key}, Found: {Found}", fullKey, value != null);
            return Task.FromResult(value);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving key: {Key}", key);
            return Task.FromResult<T?>(null);
        }
    }

    public Task<bool> SetAsync<T>(string key, T value, TimeSpan? expiry = null) where T : class
    {
        try
        {
            var fullKey = GetFullKey(key);
            var options = new MemoryCacheEntryOptions();

            if (expiry.HasValue)
            {
                options.AbsoluteExpirationRelativeToNow = expiry.Value;
            }
            else
            {
                // Default expiration of 1 hour for session data
                options.AbsoluteExpirationRelativeToNow = TimeSpan.FromHours(1);
            }

            _cache.Set(fullKey, value, options);
            _logger.LogDebug("Stored key: {Key}, Expiry: {Expiry}", fullKey, expiry);
            return Task.FromResult(true);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error storing key: {Key}", key);
            return Task.FromResult(false);
        }
    }

    public Task<bool> DeleteAsync(string key)
    {
        try
        {
            var fullKey = GetFullKey(key);
            _cache.Remove(fullKey);
            _logger.LogDebug("Deleted key: {Key}", fullKey);
            return Task.FromResult(true);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting key: {Key}", key);
            return Task.FromResult(false);
        }
    }

    public Task<bool> ExistsAsync(string key)
    {
        try
        {
            var fullKey = GetFullKey(key);
            var exists = _cache.TryGetValue(fullKey, out _);
            return Task.FromResult(exists);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error checking existence of key: {Key}", key);
            return Task.FromResult(false);
        }
    }

    public Task<List<string>> GetKeysAsync(string pattern)
    {
        try
        {
            // Note: In-memory cache doesn't support pattern matching like Redis
            // This is a limitation we'll address when moving to Redis
            _logger.LogWarning("Pattern matching not supported in in-memory cache: {Pattern}", pattern);
            return Task.FromResult(new List<string>());
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting keys with pattern: {Pattern}", pattern);
            return Task.FromResult(new List<string>());
        }
    }

    private string GetFullKey(string key)
    {
        return $"{_config.KeyPrefix}{key}";
    }
}
