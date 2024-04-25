import octokit

def push_to_github(repo_url, token):
    repo = octokit.Repo(repo_url, token)
    repo.init()
    repo.add_all()
    repo.commit("Auto-commit")
    repo.remove_remote("origin")
    repo.add_remote("origin", repo_url)
    repo.unset_credential_helper()
    repo.set_credential_helper("store")
    repo.push("origin", "master")

repo_url = "https://github.com/magentapenguin/my-coding-stuff.git"
token = "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"
push_to_github(repo_url, token)
