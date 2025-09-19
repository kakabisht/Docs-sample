import os
import re
from google import genai

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_alt_text(image_path):
    prompt = f"Generate a concise alt text for an image file named {image_path}. Assume it's part of developer documentation."
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text.strip()

# Regex to capture markdown image syntax ![](image.png) or [](image.png)
image_pattern = re.compile(r'!\[\]\(([^)]+)\)')

for root, _, files in os.walk("."):
    for file in files:
        if file.endswith(".md"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            def replace(match):
                image_path = match.group(1)
                alt_text = generate_alt_text(image_path)
                return f'![{alt_text}]({image_path})'

            new_content = image_pattern.sub(replace, content)

            if new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated {path}")
