using System.Text;

namespace AliveOnD_ID.Services;

public class MessageAccumulator
{
    private readonly StringBuilder _messageBuilder = new();
    public string? LastEmotion { get; set; }

    public void AppendContent(string content)
    {
        if (_messageBuilder.Length > 0 && content.Length > 0)
        {
            char lastChar = _messageBuilder[^1];
            char firstChar = content[0];

            // If last char is punctuation and first is alphanumeric, and no space exists
            if ((lastChar == '.' || lastChar == '!' || lastChar == '?') &&
                char.IsLetterOrDigit(firstChar))
            {
                // Insert a space to fix: "Paris.It ..." -> "Paris. It ..."
                _messageBuilder.Append(' ');
            }
        }

        _messageBuilder.Append(content);
    }

    public string GetFullMessage()
    {
        return _messageBuilder.ToString();
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
