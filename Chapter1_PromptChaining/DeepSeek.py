# Please install OpenAI SDK first: `pip3 install openai`
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv('DEEPSEEK_API_KEY')
openai_base_url = os.getenv('DEEPSEEK_BASE_URL')

client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_base_url)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ],
    stream=False
)

print(response.choices[0].message.content)