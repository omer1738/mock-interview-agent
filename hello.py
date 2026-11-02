from dotenv import load_dotenv
from google import genai

load_dotenv()                 
client = genai.Client()        

response = client.models.generate_content(
    model="gemini-3.1-flash-lite",
    contents="Say hello and ask me an interview question.",
)

print(response.text)