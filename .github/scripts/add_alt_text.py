import os
import re
import requests
from github import Github, Auth

# Pattern for Markdown images without alt text: ![](path/to/image.png)
IMAGE_PATTERN = r'!\[\]\((.*?)\)'

def generate_alt_text(image_path: str) -> str:
    """
    Calls Gemini API to generate alt text for the given image path.
    For simplicity, we'll use the filename as context.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return f"Image of {os.path.basename(image_path)}"

    prompt = f"Generate a short descriptive alt text for an image file named {os.path.basename(image_path)}"
    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
            headers={"Content-Type": "application/json"},
            params={"key": api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"⚠️ Error generating alt text for {image_path}: {e}")
        return f"Image of {os.path.basename(image_path)}"

def suggest_alt_texts_in_file(filepath: str):
    """Scans file for missing alt text and returns suggestions."""
    suggestions = []
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    matches = list(re.finditer(IMAGE_PATTERN, content))
    for match in matches:
        image_path = match.group(1)
        suggestion = generate_alt_text(image_path)
        suggestions.append((match.group(0), f"![{suggestion}]({image_path})"))
    return suggestions

def post_suggestions_as_review(repo_name: str, pr_number: int, suggestions: dict):
    """Posts review comments to the PR with suggested alt text replacements."""
    token = os.getenv("PAT_TOKEN")
    auth = Auth.Token(token)
    gh = Github(auth=auth)
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    if not suggestions:
        print("ℹ️ No alt text suggestions needed")
        return

    body = "### 🖼️ Alt Text Suggestions\n\n"
    for filepath, file_suggestions in suggestions.items():
        body += f"**{filepath}**\n"
        for original, suggested in file_suggestions:
            body += f"- `{original}` → `{suggested}`\n"
        body += "\n"

    pr.create_issue_comment(body)

    print("✅ Suggestions posted to PR review")

if __name__ == "__main__":
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_number = int(os.getenv("PR_NUMBER", "0"))

    if not repo_name or pr_number == 0:
        raise RuntimeError("❌ Missing GITHUB_REPOSITORY or PR_NUMBER in environment variables")

    # Scan repo for markdown files
    suggestions = {}
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith(".md"):
                filepath = os.path.join(root, file)
                file_suggestions = suggest_alt_texts_in_file(filepath)
                if file_suggestions:
                    suggestions[filepath] = file_suggestions

    post_suggestions_as_review(repo_name, pr_number, suggestions)
