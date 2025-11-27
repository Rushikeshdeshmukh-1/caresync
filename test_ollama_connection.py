import httpx
import asyncio

async def test_ollama():
    print("Testing Ollama connection...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "gemma:2b",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "stream": False
                }
            )
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                print("Response:", response.json())
            else:
                print("Error:", response.text)
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama())
