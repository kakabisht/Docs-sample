import os
import re
from google import genai
from github import Github

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Regex to detect images without alt text
image_pattern = re.compile(r'!\[\]\(([^)]+)\)')

# Load markdown files from PR changed files
pr_number = int(os.getenv("PR_NUMBER"))
repo_name = os.getenv("GITHUB_REPOSITORY")
gh = Github(os.getenv("GITHUB_TOKEN"))
repo = gh.get_repo(repo_name)
pr = repo.get_pull(pr_number)

# Collect suggestions
suggestion_comment = "### Suggested Alt Text Changes\n\n```diff\n"
has_suggestions = False

for file in pr.get_files():
    if file.filename.endswith(".md"):
        # Read file content from PR patch if possible
        content = file.patch or ""

        def replace(match):
            nonlocal has_suggestions
            has_suggestions = True
            image_path = match.group(1)
            # Generate alt text
            prompt = f"Generate a concise alt text for an image file named {image_path} in developer documentation."
            alt_text = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            ).text.strip()
            # Suggest diff
            return f"+ ![{alt_text}]({image_path})"

        new_content = image_pattern.sub(replace, content)
        if has_suggestions:
            # Add the original line for diff formatting
            for match in image_pattern.findall(content):
                suggestion_comment += f"- ![]({match})\n"
            suggestion_comment += new_content + "\n"

suggestion_comment += "```"

# Post comment if any suggestions
if has_suggestions:
    pr.create_issue_comment(suggestion_comment)
    print("✅ Suggestions posted to PR")
else:
    print("ℹ️ No alt text suggestions needed")
