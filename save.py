import subprocess

def push_to_github(repo_url, token):
    # Add all changes
    subprocess.run(["git", "add", "D:/coding"])

    # Commit changes
    subprocess.run(["git", "commit", "-m", "backup"])

    # Set the remote URL
    subprocess.run(["git", "remote", "set-url", "origin", repo_url])

    # Authenticate with token
    subprocess.run(["git", "config", "--global", "credential.helper", f'!f() {{ echo "username=magentapenguin"; echo "password={token}"; }}; f'])

    # Push changes to the remote repository
    subprocess.run(["git", "push", "origin", "main"])

repo_url = "https://github.com/magentapenguin/my-coding-stuff"
token = "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"
push_to_github(repo_url, token)
