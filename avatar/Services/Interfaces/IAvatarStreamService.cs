using AliveOnD_ID.Controllers.Requests;
using AliveOnD_ID.Controllers.Responses;

namespace AliveOnD_ID.Services.Interfaces;

public interface IAvatarStreamService
{
    Task<DIDStreamResponse> CreateStreamAsync(string? presenterId = null, string? driverId = null);
    Task<bool> StartStreamAsync(string streamId, string sessionId, object sdpAnswer);
    Task<bool> SendIceCandidateAsync(string streamId, string sessionId, string candidate, string mid, int lineIndex);
    Task<bool> SendTextToAvatarAsync(string streamId, string sessionId, string text, string? emotion = null);

    Task<bool> CloseStreamAsync(string streamId, string sessionId);
    // Task<string> CreateClipStream(string streamId, string sessionId, string textInput);
    Task<bool> SendScriptToAvatarAsync(string streamId, SendScriptRequest scriptRequest);
}
