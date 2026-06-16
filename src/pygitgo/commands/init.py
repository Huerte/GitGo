from pygitgo.commands.git_core import git_init
from pygitgo.utils.colors import info, success
from pygitgo.exceptions import GitGoError
import urllib.request
import urllib.error
import zipfile
import json
import re
import io
import os


LANG_ALIASES = {
    "py":        "python",
    "rs":        "rust",
    "rb":        "ruby",
    "kt":        "kotlin",
    "cpp":       "c++",
    "cc":        "c++",
    "cplusplus": "c++",
    
    "cs":        "visualstudio",
    "csharp":    "visualstudio",

    ".net":      "dotnet",

    "js":         "node",
    "ts":         "node",
    "javascript": "node",
    "typescript": "node",
    "golang":     "go",
}

PYTHON_PYPROJECT = """[project]
name = "{name}"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.8"
dependencies = []
"""

NODE_PACKAGE_JSON = """{{\
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

CSHARP_CSPROJ = """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>
</Project>
"""

README_TEMPLATE = """# {name}

"""

GITIGNORE_API_URL = "https://api.github.com/repos/github/gitignore/contents/"


def _fetch_available_templates():
    req = urllib.request.Request(
        GITIGNORE_API_URL,
        headers={
            "User-Agent": "GitGo-CLI",
            "Accept": "application/vnd.github+json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            entries = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise GitGoError(f"Failed to fetch template list: HTTP {e.code}")
    except Exception as e:
        raise GitGoError(f"Network error fetching template list: {e}")

    suffix = ".gitignore"
    return {
        item["name"][: -len(suffix)].lower(): item["name"][: -len(suffix)]
        for item in entries
        if item.get("type") == "file" and item["name"].endswith(suffix)
    }


def _resolve_lang(lang, available):
    normalized = LANG_ALIASES.get(lang.lower(), lang.lower())
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
    raise GitGoError(f"No .gitignore template found for '{lang}'.{hint}")


def _fetch_gitignore(resolved_lang):
    url = (
        f"https://raw.githubusercontent.com/github/gitignore/main"
        f"/{resolved_lang}.gitignore"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "GitGo-CLI"})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise GitGoError(
                f"Language '{resolved_lang}' not found in GitHub gitignore templates."
            )
        raise GitGoError(f"Failed to fetch gitignore: HTTP {e.code}")
    except Exception as e:
        raise GitGoError(f"Network error fetching gitignore: {e}")


def _parse_template_slug(template):
    # For github url
    match = re.search(r"github\.com[/:]([^/]+/[^/.]+)", template)
    if match:
        return match.group(1)
    # For repo slug
    if re.match(r"^[^/]+/[^/]+$", template):
        return template
    raise GitGoError(
        f"Invalid template format: '{template}'.\n"
        "Expected: owner/repo, https://github.com/owner/repo, or https://github.com/owner/repo.git"
    )


def _download_and_extract_template(template_slug, target_dir):
    from yaspin import yaspin
    import sys
    url = f"https://api.github.com/repos/{template_slug}/zipball"
    req = urllib.request.Request(url, headers={"User-Agent": "GitGo-CLI"})
    kwargs = {"text": f"Downloading template from GitHub: {template_slug}..."}
    if sys.stdout.isatty():
        kwargs["color"] = "cyan"
    spinner = yaspin(**kwargs)
    spinner.start()
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            zip_data = response.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            spinner.text = f"Template '{template_slug}' not found on GitHub."
            spinner.fail("✖")
            raise GitGoError(
                f"Template repository '{template_slug}' not found on GitHub."
            )
        spinner.text = f"Failed to download template: HTTP {e.code}"
        spinner.fail("✖")
        raise GitGoError(f"Failed to download template: HTTP {e.code}")
    except Exception as e:
        spinner.text = f"Network error downloading template: {e}"
        spinner.fail("✖")
        raise GitGoError(f"Network error downloading template: {e}")

    try:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            namelist = zf.namelist()
            if not namelist:
                raise GitGoError("Downloaded ZIP archive is empty.")

            root_dir = namelist[0].split("/")[0] + "/"
            for member in namelist:
                if not member.startswith(root_dir):
                    continue
                rel_path = member[len(root_dir):]
                if not rel_path:
                    continue
                dest = os.path.join(target_dir, rel_path)
                if member.endswith("/"):
                    os.makedirs(dest, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with zf.open(member) as src, open(dest, "wb") as out:
                        out.write(src.read())
        spinner.text = "Template extracted successfully."
        spinner.ok("✔")
    except Exception as e:
        spinner.text = f"Failed to extract template: {e}"
        spinner.fail("✖")
        raise GitGoError(f"Failed to extract template: {e}")


def _scaffold_language(lang, target_dir, name):
    available = _fetch_available_templates()
    resolved_lang = _resolve_lang(lang, available)
    gitignore_content = _fetch_gitignore(resolved_lang)

    with open(os.path.join(target_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(README_TEMPLATE.format(name=name))
    with open(os.path.join(target_dir, ".gitignore"), "w", encoding="utf-8") as f:
        f.write(gitignore_content)

    info("Created README.md and .gitignore")

    canonical = LANG_ALIASES.get(lang.lower(), lang.lower())

    if canonical == "python":
        with open(os.path.join(target_dir, "pyproject.toml"), "w", encoding="utf-8") as f:
            f.write(PYTHON_PYPROJECT.format(name=name))
        with open(os.path.join(target_dir, ".python-version"), "w", encoding="utf-8") as f:
            f.write("3.8\n")
        info("Created pyproject.toml and .python-version")

    elif canonical == "node":
        with open(os.path.join(target_dir, "package.json"), "w", encoding="utf-8") as f:
            f.write(NODE_PACKAGE_JSON.format(name=name))
        info("Created package.json")

    elif canonical == "rust":
        cargo_path = os.path.join(target_dir, "Cargo.toml")
        with open(cargo_path, "w", encoding="utf-8") as f:
            f.write(RUST_CARGO_TOML.format(name=name))
        src_dir = os.path.join(target_dir, "src")
        os.makedirs(src_dir, exist_ok=True)
        with open(os.path.join(src_dir, "main.rs"), "w", encoding="utf-8") as f:
            f.write('fn main() {\n    println!("Hello, world!");\n}\n')
        info("Created Cargo.toml and src/main.rs")

    elif canonical == "dart":
        with open(os.path.join(target_dir, "pubspec.yaml"), "w", encoding="utf-8") as f:
            f.write(DART_PUBSPEC_YAML.format(name=name))
        info("Created pubspec.yaml")

    elif canonical == "flutter":
        with open(os.path.join(target_dir, "pubspec.yaml"), "w", encoding="utf-8") as f:
            f.write(FLUTTER_PUBSPEC_YAML.format(name=name))
        info("Created pubspec.yaml (Flutter)")

    elif canonical == "go":
        with open(os.path.join(target_dir, "go.mod"), "w", encoding="utf-8") as f:
            f.write(GO_MOD.format(name=name))
        with open(os.path.join(target_dir, "main.go"), "w", encoding="utf-8") as f:
            f.write(
                'package main\n\nimport "fmt"\n\n'
                'func main() {\n\tfmt.Println("Hello, World!")\n}\n'
            )
        info("Created go.mod and main.go")

    elif canonical in ("visualstudio", "dotnet"):
        csproj_path = os.path.join(target_dir, f"{name}.csproj")
        with open(csproj_path, "w", encoding="utf-8") as f:
            f.write(CSHARP_CSPROJ)
        with open(os.path.join(target_dir, "Program.cs"), "w", encoding="utf-8") as f:
            f.write('Console.WriteLine("Hello, World!");\n')
        info(f"Created {name}.csproj and Program.cs")


def init_operation(args):
    target_dir = args.name

    if os.path.exists(target_dir) and os.listdir(target_dir):
        raise GitGoError(f"Folder '{target_dir}' already exists and is not empty.")

    os.makedirs(target_dir, exist_ok=True)

    orig_cwd = os.getcwd()
    try:
        if args.template:
            slug = _parse_template_slug(args.template)
            _download_and_extract_template(slug, target_dir)
        elif args.lang:
            _scaffold_language(args.lang, target_dir, target_dir)

        os.chdir(target_dir)
        git_init(ok_text=f"Initialized empty Git repository in {os.path.abspath('.')}")

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