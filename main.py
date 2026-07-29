from google import genai

client = genai.Client()
response = client.models.generate_content(
    model="gemini-flash-latest",
    contents="Say hello in French"
)
print(response.text)


