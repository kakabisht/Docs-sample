import os
import re
from google import genai  # Gemini API
from github import Github, Auth

# --- Initialize Gemini client ---
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- Initialize GitHub client ---
gh = Github(auth=Auth.Token(os.getenv("GITHUB_TOKEN")))
repo_name = os.getenv("GITHUB_REPOSITORY")
pr_number = int(os.getenv("PR_NUMBER"))
repo = gh.get_repo(repo_name)
pr = repo.get_pull(pr_number)

# --- Regex to find images without alt text ---
image_pattern = re.compile(r'!\[\]\(([^)]+)\)')

# --- Track if we have suggestions ---
has_suggestions = False
suggestion_comment = "### Suggested Alt Text Changes\n\n```diff\n"

# --- Process markdown files in PR branch ---
for root, _, files in os.walk("."):
    for file in files:
        if file.endswith(".md"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # --- Replace function for regex ---
            def replace(match):
                has_suggestions = True
                image_path = match.group(1)

                # --- Call Gemini to generate alt text ---
                prompt = f"Generate a concise alt text for an image file named {image_path} in developer documentation."
                alt_text = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                ).text.strip()

                # --- Suggest diff formatting ---
                suggestion_comment_lines = f"- ![]({image_path})\n+ ![{alt_text}]({image_path})\n"
                return suggestion_comment_lines

            new_content = image_pattern.sub(replace, content)

            # Append to suggestion comment
            if has_suggestions:
                suggestion_comment += new_content

suggestion_comment += "```"

# --- Post comment if suggestions exist ---
if has_suggestions:
    pr.create_issue_comment(suggestion_comment)
    print("✅ Alt text suggestions posted to PR")
else:
    print("ℹ️ No alt text suggestions needed")
