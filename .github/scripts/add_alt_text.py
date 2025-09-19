import os
import re
from openai import OpenAI

# Load API key from environment
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not found in environment")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Function to generate alt text for an image
def generate_alt_text(image_path: str) -> str:
    prompt = f"Generate a concise alt text for an image file named {image_path}. Assume it's part of developer documentation."
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50
    )
    return response.choices[0].message["content"].strip()

# Regex to capture markdown images: ![](image.png)
image_pattern = re.compile(r'!\[\]\(([^)]+)\)')

# Walk through all markdown files
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
