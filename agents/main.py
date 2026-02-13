from google import genai
from dotenv import load_dotenv
import os
import sys

load_dotenv()


def main():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    if len(sys.argv) < 2:
        print("Prompt Not Found.")
        sys.exit(1)

    # Verbosity
    verbose_flag = False
    if len(sys.argv) == 3 and sys.argv[2] == "--verbose":
        verbose_flag = True

    prompt = sys.argv[1]

    messages = [
        genai.types.Content(role="user",
                            parts=[genai.types.Part(text=prompt)])
    ]

    response = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=messages
    )

    print(response.text)

    # Fallback
    if response is None or response.usage_metadata is None:
        print("Response is malformed.")
        return

    if verbose_flag:
        print(f"Prompt Tokens: {response.usage_metadata.prompt_token_count}")

if __name__ == "__main__":
    main()