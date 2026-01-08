<div align="center">

# 🚀 GitGo

**A Powerful Git Workflow Automation Tool**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20Termux-lightgrey.svg)](https://github.com/Huerte/GitGo)
[![Git](https://img.shields.io/badge/git-2.x+-orange.svg)](https://git-scm.com/)

*Streamline your Git workflow with intelligent automation and save valuable development time*

</div>

---

## 📋 Table of Contents

- [✨ Features](#-features)
- [🎯 What GitGo Does](#-what-gitgo-does)
- [📋 Prerequisites](#-prerequisites)
- [🛠️ Installation](#️-installation)
- [🚀 Quick Start](#-quick-start)
- [📖 Usage Guide](#-usage-guide)
- [🖼️ Visual Setup Guide](#️-visual-setup-guide)
- [🤝 Contributing](#-contributing)
- [👥 Collaborators](#-collaborators)
- [📄 License](#-license)
- [🆘 Support](#-support)

---

## ✨ Features

<div align="center">

| Feature | Description |
|---------|-------------|
| 🔄 **Automated Push** | Streamlined commit and push operations in one command |
| 🔗 **Repository Linking** | Initialize and link empty projects to GitHub repositories |
| 🌿 **Branch Management** | Create and switch to new branches effortlessly |
| 🎨 **Colored Output** | Beautiful terminal feedback with status indicators |
| ⚡ **Time-Saving** | Reduce repetitive Git operations to single commands |
| 🛡️ **Error Handling** | Robust error detection and user-friendly messages |
| 🎯 **Mission-Style UI** | Engaging command-line interface with tactical feedback |

</div>

## 🎯 What GitGo Does

GitGo transforms complex Git workflows into simple, one-line commands. Instead of running multiple Git commands manually:

```bash
# Traditional way - Setting up a new repository
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/username/repo.git
git branch -M main
git push -u origin main
```

**With GitGo, just run:**
```bash
# Link empty project to GitHub
gitgo link https://github.com/username/repo.git "Initial commit"

# Or push changes to existing repo
gitgo push main "Your commit message"
```

---

## 📋 Prerequisites

Before installing GitGo, ensure you have:

<div align="center">

| Requirement | Version | Download |
|-------------|---------|----------|
| 🐍 **Python** | 3.6+ | [Download Python](https://www.python.org/downloads/) |
| 📦 **Git** | 2.x+ | [Download Git](https://git-scm.com/downloads) |
| 💻 **Operating System** | Windows 10/11, Linux, or Termux | Supported on all major platforms |

</div>

**Platform-Specific Notes:**
- **Windows**: [Windows Terminal](https://aka.ms/terminal) recommended for best experience
- **Linux**: Most distributions come with Python and Git pre-installed
- **Termux**: Install via `pkg install python git`

---

## 🛠️ Installation

Choose the installation method for your platform:

### 🪟 Windows Installation

#### Step 1: Clone the Repository

```powershell
git clone https://github.com/Huerte/GitGo.git
cd GitGo
```

#### Step 2: Run the Installer

```powershell
.\install.bat
```

The installer will:
- ✅ Check for Python and Git
- ✅ Copy files to `%APPDATA%\GitGo`
- ✅ Add GitGo to your system PATH
- ✅ Test the installation

#### Step 3: Restart Your Terminal

Close and reopen your terminal or IDE for PATH changes to take effect.

---

### � Linux Installation

#### Step 1: Clone the Repository

```bash
git clone https://github.com/Huerte/GitGo.git
cd GitGo
```

#### Step 2: Make Installer Executable

```bash
chmod +x install.sh
```

#### Step 3: Run the Installer

```bash
./install.sh
```

The installer will:
- ✅ Detect your Linux distribution
- ✅ Install files to `~/.local/share/gitgo`
- ✅ Create wrapper script in `~/.local/bin`
- ✅ Provide PATH setup instructions if needed

#### Step 4: Update PATH (if needed)

If the installer indicates that `~/.local/bin` is not in your PATH, add this line to your `~/.bashrc` or `~/.zshrc`:

```bash
export PATH="$PATH:$HOME/.local/bin"
```

Then reload your shell configuration:

```bash
source ~/.bashrc  # or source ~/.zshrc
```

---

### 📱 Termux Installation (Android)

#### Step 1: Install Prerequisites

```bash
pkg update
pkg install python git
```

#### Step 2: Clone the Repository

```bash
git clone https://github.com/Huerte/GitGo.git
cd GitGo
```

#### Step 3: Make Installer Executable

```bash
chmod +x install.sh
```

#### Step 4: Run the Installer

```bash
./install.sh
```

The installer will:
- ✅ Detect Termux environment
- ✅ Install files to `$PREFIX/share/gitgo`
- ✅ Create wrapper script in `$PREFIX/bin`
- ✅ Test the installation

**Note**: In Termux, `$PREFIX/bin` is automatically in your PATH, so no additional configuration is needed!

---

## 🚀 Quick Start

Once installed, verify GitGo is working:

```powershell
# Check if GitGo is ready
gitgo -r
# Output: ALL UNITS ONLINE. GitGo STANDING BY. AWAITING COMMANDS...
```

### Your First GitGo Command

**For a new project:**
```powershell
# Link your empty project to GitHub
gitgo link https://github.com/username/your-repo.git "Initial setup"
```

**For existing repositories:**
```powershell
# Make some changes to your project, then:
gitgo push main "Update with GitGo"
```

**GitGo will automatically:**
1. ✅ Initialize git repository (if needed)
2. ✅ Stage all changes (`git add .`)
3. ✅ Commit with your message
4. ✅ Set up remote origin (link command)
5. ✅ Push to the specified branch
6. ✅ Display mission completion status

---

## 📖 Usage Guide

### 🎯 Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `gitgo -r` | Check GitGo status | `gitgo -r` |
| `gitgo link [url] [message]` | Initialize and link project to GitHub | `gitgo link https://github.com/user/repo.git "Initial commit"` |
| `gitgo push [branch] [message]` | Commit and push to existing branch | `gitgo push main "Fix bug"` |
| `gitgo push -n [branch] [message]` | Create new branch and push | `gitgo push -n feature "New feature"` |
| `gitgo update` | Update system PATH to current GitGo location | `gitgo update` |
| `gitgo help` | Show help information | `gitgo help` |

### 💡 Pro Tips

- **New Projects**: Use `gitgo link` to quickly set up new repositories
- **Branch Creation**: Use `-n` or `new` to create and switch to a new branch
- **Commit Messages**: Always include meaningful commit messages
- **Custom Messages**: Link command supports custom commit messages or defaults to "Initial commit"
- **Status Check**: Run `gitgo -r` to ensure everything is configured correctly
- **PATH Issues**: Run `gitgo update` whenever you move GitGo or see PATH warnings

### 🎨 Output Examples

**Successful Push Operation:**
```
✅ MISSION COMPLETE — NO CASUALTIES. ALL TARGETS NEUTRALIZED.
AWAITING FOR YOUR NEXT ORDERS.
```

**Successful Link Operation:**
```
🎯 LINK OPERATION COMPLETE! REPOSITORY LOCKED AND LOADED!
Ready to push with: gitgo push main 'your message'
AWAITING FURTHER ORDERS...
```

**Ready Status:**
```
🔵 ALL UNITS ONLINE. GitGo STANDING BY. AWAITING COMMANDS...
```

### 🔗 Link Command Deep Dive

The `gitgo link` command is perfect for connecting empty projects to GitHub repositories. Here's what it does:

**Step-by-Step Process:**
1. 🔍 **Smart Detection** - Checks if directory is already a git repository
2. 🎯 **Initialize** - Creates git repository if needed
3. 📁 **Stage Files** - Adds all project files (`git add .`)
4. 💾 **Initial Commit** - Creates commit with custom or default message
5. 🔗 **Remote Setup** - Adds GitHub repository as origin
6. ✅ **Connection Test** - Verifies remote repository accessibility
7. 🌿 **Main Branch** - Ensures you're on the 'main' branch

**Usage Examples:**
```bash
# Basic usage with default "Initial commit" message
gitgo link https://github.com/username/my-project.git

# Custom commit message
gitgo link https://github.com/username/my-project.git "Project setup complete"

# Get help for link command
gitgo link --help
```

**What Makes Link Special:**
- 🛡️ **Safe Operation** - Won't overwrite existing git repositories
- 🔄 **Smart Remote Handling** - Updates existing remotes if needed
- 🎨 **Beautiful Feedback** - Clear status updates throughout the process
- ⚡ **One Command Setup** - Replaces 6+ manual git commands

### 🔧 Update Command Deep Dive

The `gitgo update` command fixes PATH issues when GitGo has been moved to a different location. **Now works on Windows, Linux, and Termux!**

**When to Use Update:**
- 🚨 When you see "PATH OUTDATED DETECTED!" warnings
- 📁 After moving GitGo to a new directory
- 🔄 When `gitgo` command stops working from other directories
- 🛠️ During initial setup if PATH configuration fails

**Step-by-Step Process:**
1. 🔍 **Platform Detection** - Automatically detects your operating system
2. 📝 **Wrapper Creation** - Creates/updates wrapper script (`.bat` for Windows, shell script for Linux/Termux)
3. 🎯 **PATH Validation** - Checks if target directory is in system PATH
4. 📋 **Instructions** - Provides platform-specific PATH setup steps if needed
5. ✅ **Verification** - Confirms successful update

**Usage Examples:**
```bash
# Basic update command (works on all platforms)
gitgo update

# Get help for update command
gitgo update --help
```

**What Makes Update Special:**
- 🛡️ **Cross-Platform** - Automatically detects and configures for your OS
- 🔄 **Smart Detection** - Finds the best system directory for your platform
- 📋 **Clear Instructions** - Provides platform-specific PATH setup guide
- ⚡ **Quick Fix** - Resolves PATH issues in seconds

**Platform-Specific Behavior:**
- **Windows**: Creates `gitgo.bat` in `%APPDATA%\Local\Microsoft\WindowsApps` or `%USERPROFILE%\bin`
- **Linux**: Creates `gitgo` shell script in `~/.local/bin`
- **Termux**: Creates `gitgo` shell script in `$PREFIX/bin`

**Common Update Scenarios:**
```bash
# Scenario 1: Moved GitGo folder
# Error: "PATH OUTDATED DETECTED!"
gitgo update

# Scenario 2: Fresh installation
# Error: "'gitgo' is not recognized..." or "command not found"
cd path/to/GitGo/src
python gitgo.py update  # Windows
python3 gitgo.py update # Linux/Termux

# Scenario 3: After system changes
# GitGo stops working from other directories
gitgo update
```

---

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### 🌟 Ways to Contribute

- 🐛 **Report Bugs** - Found an issue? Let us know!
- 💡 **Suggest Features** - Have ideas for improvements?
- 📝 **Improve Documentation** - Help make our docs better
- 🔧 **Submit Code** - Fix bugs or add new features

### 📋 Contribution Process

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

---

## 👥 Collaborators

<div align="center">

### 🚀 Meet the Team Behind GitGo

<table>
<tr>
<td align="center">
<a href="https://github.com/Huerte">
<img src="https://github.com/Huerte.png" width="100px;" alt="Huerte"/>
<br />
<sub><b>Huerte</b></sub>
</a>
<br />
<a href="https://github.com/Huerte" title="Profile">🔗 Profile</a>
</td>
<td align="center">
<a href="https://github.com/Venomous-pie">
<img src="https://github.com/Venomous-pie.png" width="100px;" alt="Venomous-pie"/>
<br />
<sub><b>Venomous-pie</b></sub>
</a>
<br />
<a href="https://github.com/Venomous-pie" title="Profile">🔗 Profile</a>
</td>
</tr>
</table>

*Special thanks to our collaborators for their dedication and expertise in creating this powerful Git automation tool.*

</div>

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License - Feel free to use, modify, and distribute this software.
```

---

## 🆘 Support

<div align="center">

### Need Help? We've Got You Covered!

</div>

If you encounter any issues or have questions:

### 📞 Support Channels

1. **📚 Documentation** - Check this README and inline help (`gitgo help`)
2. **🐛 GitHub Issues** - [Open an issue](https://github.com/Huerte/GitGo/issues) for bugs or feature requests
3. **💬 Discussions** - Join our [GitHub Discussions](https://github.com/Huerte/GitGo/discussions)
4. **📧 Direct Contact** - Reach out to the maintainers

### 🔍 Troubleshooting

**Common Issues:**

| Problem | Solution | Platform |
|---------|----------|----------|
| `gitgo` command not found | Run `gitgo update` from GitGo directory, or restart terminal after installation | All |
| PATH OUTDATED DETECTED warning | Run `gitgo update` to fix PATH configuration | All |
| Dubious Ownership / Security Alert | **Smart Fix:** GitGo will detect this and offer to fix it automatically! | All (Common in Termux) |
| Permission errors (Windows) | Run PowerShell as Administrator | Windows |
| Permission errors (Linux/Termux) | Check file permissions: `chmod +x ~/.local/bin/gitgo` | Linux/Termux |
| Git errors | Verify you're in a Git repository | All |
| GitGo stops working after moving folder | Run `gitgo update` from the new location | All |
| `~/.local/bin` not in PATH | Add `export PATH="$PATH:$HOME/.local/bin"` to `~/.bashrc` | Linux |
| Python not found (Termux) | Run `pkg install python` | Termux |

**Platform-Specific Troubleshooting:**

**Windows:**
```powershell
# If gitgo command not found after installation:
cd "C:\Programs\Git Tools\GitGo\src"
python gitgo.py update

# Then restart your terminal
```

**Linux:**
```bash
# If gitgo command not found:
cd ~/path/to/GitGo
./install.sh

# If still not working, manually add to PATH:
echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bashrc
source ~/.bashrc
```

**Termux:**
```bash
# If gitgo command not found:
cd ~/GitGo
./install.sh

# Verify installation:
which gitgo
gitgo -r
```

---

<div align="center">

### ⭐ Star this repository if GitGo helped streamline your workflow!

**Made with ❤️ by the GitGo Team**

[⬆ Back to Top](#-gitgo)

</div>
