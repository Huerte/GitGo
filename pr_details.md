### 🌿 Branch Name Suggestion
`refactor/pypi-package-migration`

*(Alternative: `chore/pygitgo-restructure`)*

---

### 📝 Commit Message
```text
refactor: restructure codebase for PyPi distribution as pygitgo

- Migrated source files into standard `src/pygitgo/` package layout
- Configured `pyproject.toml` with entry points and dynamic versioning
- Updated internal module imports to fully qualified `pygitgo.*` paths
- Cleaned up obsolete installation scripts and wrapper logic
- Updated README.md and .gitignore to reflect new installation methodology
```

---

### 🚀 Pull Request Title
**Refactor: Core architecture migration to standard PyPi package (`pygitgo`)**

### 📋 Pull Request Description

#### 🎯 What does this PR do?
This PR completely overhauls the internal directory structure and installation pipeline of GitGo, transitioning it into a standardized, distributable Python package named `pygitgo`. 

#### 🛠️ Changes Made
- **Package Architecture:** Migrated flat `src/` directory to a nested `src/pygitgo/` module structure to prevent namespace collisions.
- **Dependency Management:** Replaced `requirements.txt` and custom install scripts with a modern `pyproject.toml` specification.
- **Entry Points:** The `gitgo` terminal command is now registered natively via PyPi entry points, replacing the need for OS-specific wrappers (`path_manager.py`).
- **Dynamic Versioning:** `main.py` now leverages `importlib.metadata` to retrieve the active version directly from package metadata.
- **Cleanup:** Removed deprecated custom installers (`install.bat`, `install.sh`, `installer/` directory) and updated `.gitignore` to handle Python/PyPi build artifacts correctly.
- **Documentation:** Rewrote `README.md` to guide users on the new `pip install` methodology and explicitly highlight core automation features.

#### 💡 Why is this needed?
This sets the foundational architecture required to officially deploy GitGo to PyPi, greatly improving user adoption, dependency resolution (like `yaspin`), and cross-platform installation stability.

#### ✅ Verification
- `pip install -e .` successfully builds the package
- The entry point `gitgo` commands (`-h`, `-v`, `-r`, `link`, `push`, `state`, `user`) execute successfully and resolve internal imports over the `pygitgo` namespace.
