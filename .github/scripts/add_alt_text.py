import os
import re
import openai
from github import Github

# Load OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_alt_text(image_path: str) -> str:
    """
    Generate alt text for an image path using OpenAI GPT-5-nano.
    """
    try:
        prompt = f"Write a short, descriptive alt text for an image file: {image_path}"
        response = openai.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print(f"⚠️ Error generating alt text for {image_path}: {e}")
        return None


def suggest_alt_text_for_file(file_path: str):
    """
    Parse a markdown file and suggest alt text for images without alt text.
    Returns a list of (line_number, old_line, new_line).
    """
    suggestions = []
    image_pattern = re.compile(r'!\[\]\((.*?)\)')

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        match = image_pattern.search(line)
        if match:
            image_path = match.group(1)
            alt_text = generate_alt_text(image_path)
            if alt_text:
                new_line = line.replace(f"![]({image_path})", f"![{alt_text}]({image_path})")
                suggestions.append((i + 1, line.strip(), new_line.strip()))

    return suggestions


def post_suggestions_as_review(repo_name, pr_number, suggestions):
    """
    Post suggestions as a GitHub PR review.
    """
    gh = Github(os.getenv("GITHUB_TOKEN"))
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(int(pr_number))

    comments = []
    for file_path, file_suggestions in suggestions.items():
        for line_number, old_line, new_line in file_suggestions:
            comments.append({
                "path": file_path,
                "position": line_number,
                "body": f"💡 Suggestion: Replace\n```markdown\n{old_line}\n```\nwith\n```markdown\n{new_line}\n```"
            })

    if comments:
        pr.create_review(
            body="🤖 Suggested alt text improvements for images",
            event="COMMENT",
            comments=comments
        )
        print("✅ Posted alt text suggestions as a PR review.")
    else:
        print("ℹ️ No alt text suggestions needed.")


if __name__ == "__main__":
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("PR_NUMBER")

    # Collect suggestions
    suggestions = {}
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                file_suggestions = suggest_alt_text_for_file(file_path)
                if file_suggestions:
                    suggestions[file_path] = file_suggestions

    if suggestions:
        post_suggestions_as_review(repo_name, pr_number, suggestions)
    else:
        print("ℹ️ No alt text suggestions generated.")
