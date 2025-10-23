# Conversation History Feature

## Overview
The Ingage AI Agent now supports conversation history, allowing for more contextual and accurate responses by providing previous conversation context to the Fabric Data Agent API.

## What's New

### API Changes

1. **Updated Request Models**: Both `QueryRequest` models in `main.py` and `main_production.py` now include an optional `conversation_history` field.

2. **Enhanced Client Methods**: The `FabricDataAgentClient` methods `ask()` and `get_run_details()` now accept an optional `conversation_history` parameter.

3. **Automatic Context Passing**: Query endpoints automatically pass conversation history to the Fabric API when provided.

## Usage Examples

### Frontend (JavaScript/TypeScript)

```typescript
// Example: Multi-turn conversation with context
const conversationHistory = [
  {
    role: "user",
    content: "show me top 5 members with open gaps"
  },
  {
    role: "assistant", 
    content: "Here are the top 5 members with the highest number of open HEDIS care gaps..."
  },
  {
    role: "user",
    content: "tell me about the first member?"
  },
  {
    role: "assistant",
    content: "The first member in the dataset is Carlos Doe. Here are some details..."
  }
];

// Query with conversation history
const response = await fetch('/query', {
  method: 'POST',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: "What about the second member?",
    conversation_history: conversationHistory
  })
});
```

### Python Client

```python
from fabric_data_agent_client import FabricDataAgentClient

client = FabricDataAgentClient(
    tenant_id="your-tenant-id",
    data_agent_url="your-data-agent-url"
)

# First query
response1 = client.ask("Show me top 3 members")

# Build conversation history
conversation_history = [
    {"role": "user", "content": "Show me top 3 members"},
    {"role": "assistant", "content": response1}
]

# Follow-up query with context
response2 = client.ask(
    "Tell me more about the first member", 
    conversation_history=conversation_history
)
```

### REST API

```bash
# Simple query without history
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -H "Cookie: fabric_session_id=your-session-id" \
  -d '{
    "query": "Hello, what can you help me with?"
  }'

# Query with conversation history
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -H "Cookie: fabric_session_id=your-session-id" \
  -d '{
    "query": "What about the second member?",
    "conversation_history": [
      {
        "role": "user",
        "content": "show me top 5 members with open gaps"
      },
      {
        "role": "assistant",
        "content": "Here are the top 5 members..."
      }
    ]
  }'
```

## Request Schema

### QueryRequest Model

```python
class ConversationMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str  # Message content

class QueryRequest(BaseModel):
    query: str  # Current question/query
    include_details: bool = False  # Whether to include run details
    conversation_history: Optional[List[ConversationMessage]] = None  # Previous messages
```

### Example Request Payload

```json
{
  "query": "What about the second member?",
  "conversation_history": [
    {
      "role": "user",
      "content": "show me top 5 members with open gaps"
    },
    {
      "role": "assistant", 
      "content": "Here are the top 5 members with the highest number of open HEDIS care gaps (where a care gap is defined as a HEDIS measure with ComplianceFlag = 'N'):\n\n| Member ID | First Name | Last Name | Date of Birth | Open Care Gaps |\n|-----------|------------|-----------|---------------|----------------|\n| 33331857  | Darryl     | Doe       | 1951-06-04    | 12             |\n| 37277786  | Jannie     | Doe       | 1951-06-05    | 11             |\n| C4085507101| A         | Doe       | 1954-04-18    | 10             |\n| 37401443  | Ryan       | Doe       | 1968-01-24    | 10             |\n| 37189239  | Edgar      | Doe       | 1957-10-26    | 10             |"
    },
    {
      "role": "user",
      "content": "tell me about the first member?"
    },
    {
      "role": "assistant",
      "content": "The first member in the dataset is Carlos Doe. Here are some details:\n\n- Date of Birth: April 17, 1945\n- Gender: Male\n- City: Oviedo\n- State: FL\n- Zip Code: 99501\n\nIf you need more information or details about this member's care history, let me know!"
    }
  ]
}
```

## Benefits

### 1. **Contextual Understanding**
The AI agent can now reference previous conversations, enabling more natural follow-up questions like:
- "What about the second member?" (references previous member list)
- "Show me more details about that" (references previous query results)
- "Can you explain that calculation?" (references previous analysis)

### 2. **Improved Accuracy** 
With conversation context, the agent can:
- Better understand ambiguous references
- Maintain consistency across multiple queries
- Provide more relevant responses based on conversation flow

### 3. **Enhanced User Experience**
Users can have natural, flowing conversations without having to repeat context or be overly specific in each query.

## Implementation Details

### Backend Processing

1. **History Validation**: The API validates conversation history format and content.
2. **Context Preparation**: Messages are added to the OpenAI thread in chronological order before the current query.
3. **Thread Management**: Each conversation creates a new thread with full history for proper context.

### Thread Structure

```
OpenAI Thread:
├── Message 1 (user): "show me top 5 members with open gaps"
├── Message 2 (assistant): "Here are the top 5 members..."  
├── Message 3 (user): "tell me about the first member?"
├── Message 4 (assistant): "The first member in the dataset..."
└── Message 5 (user): "What about the second member?" (current query)
```

### Performance Considerations

- **Token Usage**: Longer conversation histories consume more tokens
- **Processing Time**: Including history may increase response time slightly
- **Memory**: Conversation context is processed in memory for each request

## Best Practices

### 1. **Conversation Length**
- Keep conversation history relevant and concise
- Consider limiting to last 10-20 messages for performance
- Remove very old or irrelevant messages

### 2. **Message Quality**
- Ensure accurate role assignment ("user" vs "assistant")
- Include complete assistant responses for better context
- Maintain chronological order

### 3. **Error Handling**
- Handle cases where conversation history is malformed
- Gracefully degrade to no-context mode if history processing fails
- Validate message content before including in history

## Testing

### Manual Testing

```bash
# Run the test script
python test_conversation_history.py
```

### Integration Testing

```python
# Test conversation flow
def test_conversation_flow():
    # Initial query
    response1 = client.ask("Show me member statistics")
    
    # Build history
    history = [
        {"role": "user", "content": "Show me member statistics"},
        {"role": "assistant", "content": response1}
    ]
    
    # Follow-up with context
    response2 = client.ask("What about the top member?", conversation_history=history)
    
    assert "member" in response2.lower()
```

## Troubleshooting

### Common Issues

1. **Missing Context**: If the agent doesn't seem to understand references, check that:
   - Conversation history is properly formatted
   - Messages are in correct chronological order
   - Role assignments are correct ("user"/"assistant")

2. **Performance Issues**: If requests are slow:
   - Reduce conversation history length
   - Check for very long message content
   - Monitor token usage

3. **Validation Errors**: If requests fail validation:
   - Ensure all required fields are present
   - Check message content for proper encoding
   - Verify role values are "user" or "assistant"

### Debug Logging

The application logs conversation history processing:

```
📚 Including 4 messages from conversation history
📚 Added 4 previous messages to thread
```

Monitor these logs to verify history is being processed correctly.

## Migration Guide

### Existing Applications

No breaking changes! The `conversation_history` field is optional:

```python
# This still works (no history)
response = client.ask("What data do you have?")

# This is the new feature (with history)
response = client.ask("What about the second member?", conversation_history=history)
```

### Frontend Updates

Add conversation history to your existing queries:

```typescript
// Before
const requestBody = {
  query: userInput
};

// After  
const requestBody = {
  query: userInput,
  conversation_history: conversationState  // Optional
};
```

## Future Enhancements

### Planned Features

1. **Automatic History Management**: Backend could automatically track conversation history per session
2. **Smart Context Pruning**: Intelligent removal of irrelevant old messages
3. **Conversation Summarization**: Compress long conversations into summaries
4. **Context Relevance Scoring**: Score message relevance to current query

### Feedback

This feature enhances the conversational experience significantly. Users can now have natural, flowing conversations with the AI agent, making it much more intuitive and powerful for complex data analysis workflows.

---

*Feature implemented: October 23, 2025*
*Version: 2.0.0*