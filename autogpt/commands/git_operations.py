"""Git operations for autogpt"""
import re
from urllib.parse import quote, urlsplit, urlunsplit

from git.repo import Repo

from autogpt.commands.command import command
from autogpt.config import Config
from autogpt.workspace import path_in_workspace

CFG = Config()


@command(
    "clone_repository",
    "Clone Repositoryy",
    '"repository_url": "<repository_url>", "clone_path": "<clone_path>"',
    CFG.github_username and CFG.github_api_key,
    "Configure github_username and github_api_key.",
)
def clone_repository(repository_url: str, clone_path: str) -> str:
    """Clone a GitHub repository locally

    Args:
        repository_url (str): The URL of the repository to clone
        clone_path (str): The path to clone the repository to

    Returns:
        str: The result of the clone operation"""
    try:
        parsed = urlsplit(repository_url)
        if (
            parsed.scheme != "https"
            or parsed.hostname != "github.com"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port is not None
            or parsed.query
            or parsed.fragment
            or not re.fullmatch(r"/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?", parsed.path)
        ):
            return "Error: Only HTTPS GitHub repository URLs are supported."
        credentials = (
            f"{quote(CFG.github_username, safe='')}:"
            f"{quote(CFG.github_api_key, safe='')}@github.com"
        )
        auth_repo_url = urlunsplit(("https", credentials, parsed.path, "", ""))
        safe_clone_path = path_in_workspace(clone_path)
        Repo.clone_from(auth_repo_url, safe_clone_path)
        return f"""Cloned {repository_url} to {safe_clone_path}"""
    except Exception:
        # Git exceptions can contain the credential-bearing URL or command line.
        return "Error: Repository clone failed. Check the URL, access and workspace path."
