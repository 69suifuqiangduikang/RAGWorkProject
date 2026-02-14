from openai import OpenAI
client = OpenAI(
    base_url="https://openrouter.ai/api/v1/",
    api_key="sk-xxx"
)

response = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello, world!"}],
    stream=False
)
print(response)