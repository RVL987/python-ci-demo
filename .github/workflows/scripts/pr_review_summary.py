import json
import os
import subprocess
import urllib.request

repo = os.environ["REPO"]
pr_number = os.environ["PR_NUMBER"]
token = os.environ["GITHUB_TOKEN"]
base_sha = os.environ["BASE_SHA"]
head_sha = os.environ["HEAD_SHA"]

# Changed files

files = subprocess.check_output(
["git", "diff", "--name-only", base_sha, head_sha],
text=True
).splitlines()

# Diff stats

diff_stat = subprocess.check_output(
["git", "diff", "--stat", base_sha, head_sha],
text=True
)

# Added / Removed lines

numstat = subprocess.check_output(
["git", "diff", "--numstat", base_sha, head_sha],
text=True
).splitlines()

added = 0
removed = 0

for line in numstat:
parts = line.split("\t")
if len(parts) >= 2:
try:
added += int(parts[0])
removed += int(parts[1])
except:
pass

# TODO / FIXME search

todos = []

for file in files:
if os.path.exists(file):
try:
with open(file, "r", encoding="utf-8") as f:
for idx, line in enumerate(f, start=1):
if "TODO" in line or "FIXME" in line:
todos.append(
f"{file}:{idx} → {line.strip()}"
)
except:
pass

# Markdown table

table = "| Metric | Value |\n|---|---|\n"
table += f"| Files Changed | {len(files)} |\n"
table += f"| Lines Added | {added} |\n"
table += f"| Lines Removed | {removed} |\n"

comment_body = f"""

<!-- PR_REVIEW_SUMMARY -->

## Automated PR Review Summary

{table}

### Diff Statistics

```text
{diff_stat}
```

### TODO / FIXME Findings

"""

if todos:
comment_body += "\n".join(
f"- {item}" for item in todos
)
else:
comment_body += "\nNo TODO/FIXME comments found."

# GitHub API headers

headers = {
"Authorization": f"Bearer {token}",
"Accept": "application/vnd.github+json",
"Content-Type": "application/json"
}

# Find existing bot comment

comments_url = (
f"https://api.github.com/repos/"
f"{repo}/issues/{pr_number}/comments"
)

req = urllib.request.Request(
comments_url,
headers=headers
)

comments = json.loads(
urllib.request.urlopen(req).read().decode()
)

existing_comment = None

for comment in comments:
if "<!-- PR_REVIEW_SUMMARY -->" in comment["body"]:
existing_comment = comment["id"]
break

payload = json.dumps(
{"body": comment_body}
).encode()

if existing_comment:
update_url = (
f"https://api.github.com/repos/"
f"{repo}/issues/comments/"
f"{existing_comment}"
)

```
req = urllib.request.Request(
    update_url,
    data=payload,
    headers=headers,
    method="PATCH"
)

urllib.request.urlopen(req)
```

else:
req = urllib.request.Request(
comments_url,
data=payload,
headers=headers,
method="POST"
)

```
urllib.request.urlopen(req)
```

print("PR review summary updated.")
