import os
import re
from google import genai
from github import Github, Auth

# --- Initialize Gemini client ---
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- Initialize GitHub client ---
gh = Github(auth=Auth.Token(os.getenv("GITHUB_TOKEN")))
repo_name = os.getenv("GITHUB_REPOSITORY")
pr_number = int(os.getenv("PR_NUMBER"))
repo = gh.get_repo(repo_name)
pr = repo.get_pull(pr_number)

# --- Regex to match all markdown images ---
# group(1) = current alt text (may be empty)
# group(2) = image path
image_pattern = re.compile(r'!\[(.*?)\]\(([^)]+)\)')

# --- Track if we have suggestions ---
has_suggestions = False
suggestion_comment = "### Suggested Alt Text Changes\n\n```diff\n"

# --- Loop through PR files ---
for file in pr.get_files():
    # Only markdown files
    if file.filename.endswith(".md") and file.patch:
        patch_lines = file.patch.split("\n")
        for line in patch_lines:
            # Only consider added lines in PR
            if line.startswith("+") and "!(" in line:
                # Remove leading '+'
                md_line = line[1:]
                matches = image_pattern.findall(md_line)
                for alt_text_current, image_path in matches:
                    has_suggestions = True

                    # --- Generate alt text using Gemini ---
                    prompt = (
                        f"Generate a concise, descriptive alt text for an image file named "
                        f"{image_path}. Assume it is part of developer documentation."
                    )
                    alt_text = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    ).text.strip()

                    # --- Add suggested diff ---
                    suggestion_comment += f"- ![{alt_text_current}]({image_path})\n"
                    suggestion_comment += f"+ ![{alt_text}]({image_path})\n"

suggestion_comment += "```"

# --- Post PR comment if suggestions exist ---
if has_suggestions:
    pr.create_issue_comment(suggestion_comment)
    print("✅ Alt text suggestions posted to PR")
else:
    print("ℹ️ No alt text suggestions needed")
