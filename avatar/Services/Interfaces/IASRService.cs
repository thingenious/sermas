using AliveOnD_ID.Controllers.Responses;

namespace AliveOnD_ID.Services.Interfaces;

public interface IASRService
{
    Task<ASRResponse> ConvertAudioToTextAsync(byte[] audioData, string fileName);
    Task<ASRResponse> ConvertAudioToTextAsync(Stream audioStream, string fileName);
}
