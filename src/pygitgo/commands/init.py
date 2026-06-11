import urllib

from pygitgo.commands.git_core import git_init
from pygitgo.exceptions import GitGoError
from pygitgo.utils.colors import *
import os

LANG_ALIASES: dict[str, str] = {
    "py":        "python",
    "rs":        "rust",
    "rb":        "ruby",
    "kt":        "kotlin",
    "cpp":       "c++",
    "cc":        "c++",
    "cplusplus": "c++",
    "cs":        "csharp",

    "js":         "node",
    "ts":         "node",
    "javascript": "node",
    "typescript": "node",
    "golang":     "go",
    "dotnet":     "csharp",
    ".net":       "csharp",
}

PYTHON_REQUIREMENTS = """# Add project dependencies here
"""

NODE_PACKAGE_JSON = """{{
  "name": "{name}",
  "version": "1.0.0",
  "description": "",
  "main": "index.js",
  "scripts": {{
    "start": "node index.js"
  }}
}}
"""

RUST_CARGO_TOML = """[package]
name = "{name}"
version = "0.1.0"
edition = "2021"

[dependencies]
"""

DART_PUBSPEC_YAML = """name: {name}
description: A new Dart project.
version: 1.0.0
environment:
  sdk: '>=3.0.0 <4.0.0'
"""

FLUTTER_PUBSPEC_YAML = """name: {name}
description: A new Flutter project.
version: 1.0.0
environment:
  sdk: '>=3.0.0 <4.0.0'
dependencies:
  flutter:
    sdk: flutter
"""

GO_MOD = """module {name}

go 1.20
"""

README_TEMPLATE = """# {name}

Scaffolded u
"""


def _fetch_available_templates():
    pass

def _fetch_gitignore(language):
    url = (
        f"https://raw.githubusercontent.com/github/gitignore/main/{language}.gitignore"
    )
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "GitGo-CLI"}
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise GitGoError(
                f"Language '{language}' not found in GitHub gitignore templates."
            )
        raise GitGoError(f"Failed to fetch gitignore: HTTP {e.code}")
    except Exception as e:
        raise GitGoError(f"Network error fetching gitignore: {e}")


def _download_and_extract_template():
    pass


def _scaffold_language():
    pass


def _resolved_language(language, available):
    normalized = LANG_ALIASES.get(language.lower(), language.lower())
    if normalized in available:
        return available[normalized]

    suggestions = sorted(
        (
            t for t in available
            if len(normalized) >= 2 and normalized[:2] == t[:2]
        ),
        key=lambda t: abs(len(t) - len(normalized)),
    )[:5]
    hint = f"\n  Similar templates: {', '.join(suggestions)}" if suggestions else ""
    raise GitGoError(f"No .gitignore template found for '{language}'.{hint}")

def _download_and_extract_template(template)


def init_operation(args):
    
    target_dir = args.name

    if os.path.exists(target_dir) and os.listdir(target_dir):
        raise GitGoError(f"Folder '{target_dir}' already exists and is not empty.")
    
    os.makedirs(target_dir, exist_ok=True)

    orig_cwd = os.getcwd()

    try:
        if args.template:
            _download_and_extract_template(args.template, target_dir)
        elif args.lang:
            _scaffold_language(args.lang, target_dir, target_dir)

        os.chdir(target_dir)
        git_init()

        success(f"\nInitialized empty Git repository in {os.path.abspath('.')}")
        info("Next step: Create a remote repo with 'gitgo new <name>'")

    except Exception as e:
        if os.path.exists(target_dir) and not os.listdir(target_dir):
            try:
                os.rmdir(target_dir)
            except Exception:
                pass
        raise e
    finally:
        os.chdir(orig_cwd)


