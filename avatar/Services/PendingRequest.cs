using AliveOnD_ID.Controllers.Responses;

namespace AliveOnD_ID.Services;

    public class PendingRequest
{
    public string Id { get; }
    public TaskCompletionSource<LLMResponse> TaskCompletionSource { get; }
    public DateTime CreatedAt { get; }
    public bool IsActive => !TaskCompletionSource.Task.IsCompleted;

    public PendingRequest(string id)
    {
        Id = id;
        TaskCompletionSource = new TaskCompletionSource<LLMResponse>();
        CreatedAt = DateTime.UtcNow;
    }
}

// EVE API Message Formats:
/*
// Start conversation:
{
  "type": "start_conversation"
}

// Continue existing conversation:
{
  "type": "start_conversation",
  "conversation_id": "existing-conversation-id"
}

// User message:
{
  "type": "user_message",
  "content": "Hello, how are you?"
}

// Response: conversation_started
{
  "type": "conversation_started",
  "conversation_id": "unique-conversation-id"
}

// Response: message segment
{
  "type": "message",
  "content": "I'm doing well, ",
  "emotion": "happy",
  "is_final": false
}

// Response: final message segment
{
  "type": "message",
  "content": "thank you for asking!",
  "emotion": "happy",
  "is_final": true
}

// Error response:
{
  "type": "error",
  "content": "Error description here"
}
*/
