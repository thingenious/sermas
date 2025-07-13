namespace AliveOnD_ID.Services.Interfaces;

public interface IStorageService
{
    Task<T?> GetAsync<T>(string key) where T : class;
    Task<bool> SetAsync<T>(string key, T value, TimeSpan? expiry = null) where T : class;
    Task<bool> DeleteAsync(string key);
    Task<bool> ExistsAsync(string key);
    Task<List<string>> GetKeysAsync(string pattern);
}
