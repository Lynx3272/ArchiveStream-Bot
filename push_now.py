import subprocess
from pathlib import Path

pat = Path('.git-pat').read_text().strip()
url = f"https://Lynx3272:{pat}@github.com/Lynx3272/ArchiveStream-Bot.git"
r = subprocess.run(["git", "push", url, "HEAD:refs/heads/main", "refs/heads/builds:refs/heads/builds"],
                   capture_output=True, text=True, shell=False)
out = (r.stdout + r.stderr).replace(pat, "***")
print(out)
print("exit:", r.returncode)
