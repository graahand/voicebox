from ollama import chat

messages = [
  {
    'role': 'user',
    'content': 'What is 10 + 23?',
  },
]

response = chat('qwen3:0.6b', messages=messages, think=False)

# print('Thinking:\n========\n\n' + response.message.thinking)
print('\nResponse:\n========\n\n' + response.message.content)
