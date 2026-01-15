from google import genai
client = genai.Client(api_key="AIzaSyBEGVWc9txUq2zgwr4JTwnOf9eRvOiQIa4")

for i in range(1000):
    response = client.models.generate_content(
        model='gemini-2.5-flash-lite',
        contents='Tell me a story in 30 words.'
    )
    print(i)
    print({response.text})

# print(response.model_dump_json(
#     exclude_none=True, indent=4))