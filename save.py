from subprocess import run

def push_to_github(repo_url, token):
    run(["git", "init"], cwd="D:/coding")
    run(["git", "add", "."], cwd="D:/coding")
    run(["git", "commit", "-m", "'Auto-commit'"], cwd="D:/coding")
    run(["git", "remote", "add", "origin", repo_url], cwd="D:/coding")
    run(["git", "config", "credential.helper", "store"], cwd="D:/coding")
    run(["git", "push", "-u", "origin", "master"], cwd="D:/coding", env={"GIT_ASKPASS": "echo", "GITHUB_TOKEN": token})

repo_url = "https://github.com/magentapenguin/my-coding-stuff.git"
token = "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"
push_to_github(repo_url, token)