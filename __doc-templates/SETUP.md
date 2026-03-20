# Setup Guide — {{PROJECT_NAME}}

This document provides a complete, step-by-step guide to setting up **{{PROJECT_NAME}}** in your local development environment.

> For a quick start, see the [README](./README.md#getting-started).

---

## Table of Contents

- [System Requirements](#system-requirements)
- [Environment Overview](#environment-overview)
- [Step 1 — Clone the Repository](#step-1--clone-the-repository)
- [Step 2 — Install Dependencies](#step-2--install-dependencies)
- [Step 3 — Environment Variables](#step-3--environment-variables)
- [Step 4 — Database Setup](#step-4--database-setup)
- [Step 5 — Build the Project](#step-5--build-the-project)
- [Step 6 — Run the Development Server](#step-6--run-the-development-server)
- [Step 7 — Verify the Setup](#step-7--verify-the-setup)
- [Platform-Specific Notes](#platform-specific-notes)
- [Common Errors & Fixes](#common-errors--fixes)
- [Resetting Your Environment](#resetting-your-environment)

---

## System Requirements

Ensure your machine meets the following requirements before proceeding.

| Requirement | Minimum Version | Recommended |
|---|---|---|
| **{{Runtime, e.g. Node.js}}** | `{{MIN_VERSION}}` | `{{RECOMMENDED_VERSION}}` |
| **{{Package Manager, e.g. npm}}** | `{{MIN_VERSION}}` | `{{RECOMMENDED_VERSION}}` |
| **{{Database, e.g. PostgreSQL}}** | `{{MIN_VERSION}}` | `{{RECOMMENDED_VERSION}}` |
| **OS** | Windows 10 / macOS 12 / Ubuntu 20.04 | Latest stable |
| **RAM** | {{MIN_RAM, e.g. 4GB}} | {{REC_RAM, e.g. 8GB}} |
| **Disk Space** | {{MIN_DISK, e.g. 1GB}} | {{REC_DISK, e.g. 2GB}} |

### Verify Your Versions

```bash
{{RUNTIME_VERSION_CHECK_COMMAND}}
# Expected: v{{EXPECTED_VERSION}} or higher

{{PACKAGE_MANAGER_VERSION_CHECK_COMMAND}}
# Expected: v{{EXPECTED_VERSION}} or higher
```

---

## Environment Overview

```
{{PROJECT_NAME}}/
│
├── .env.example        ← Template for your local .env file
├── .env                ← Your local config (never commit this)
├── src/                ← Application source code
├── config/             ← Static/shared configuration
└── ...
```

The project uses **`.env`** for environment-specific configuration.  
Never commit your `.env` file — it is already listed in `.gitignore`.

---

## Step 1 — Clone the Repository

```bash
git clone {{REPOSITORY_URL}}
cd {{PROJECT_FOLDER}}
```

If you plan to contribute, fork first and clone your fork:

```bash
git clone https://github.com/{{YOUR_USERNAME}}/{{REPO_NAME}}.git
cd {{REPO_NAME}}

# Add upstream remote to stay in sync
git remote add upstream {{REPOSITORY_URL}}
```

---

## Step 2 — Install Dependencies

<!-- IF project uses Node.js / npm -->
```bash
npm install
```
<!-- ENDIF -->

<!-- IF project uses Python / pip -->
```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```
<!-- ENDIF -->

<!-- IF project uses another package manager, replace accordingly -->
```bash
{{DEPENDENCY_INSTALL_COMMAND}}
```
<!-- ENDIF -->

> If you encounter permission errors, see [Common Errors & Fixes](#common-errors--fixes).

---

## Step 3 — Environment Variables

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

Then open `.env` and configure each variable:

```env
# -----------------------------------------------
# Application
# -----------------------------------------------
APP_NAME={{PROJECT_NAME}}
APP_ENV=development            # development | staging | production
APP_PORT={{DEFAULT_PORT}}
APP_URL=http://localhost:{{DEFAULT_PORT}}

# -----------------------------------------------
# Database
# -----------------------------------------------
DB_HOST=localhost
DB_PORT={{DB_DEFAULT_PORT}}
DB_NAME={{DB_NAME}}
DB_USER={{DB_USER}}
DB_PASSWORD={{DB_PASSWORD}}

# -----------------------------------------------
# Authentication (if applicable)
# -----------------------------------------------
JWT_SECRET={{YOUR_SECRET_KEY}}
JWT_EXPIRES_IN=7d

# -----------------------------------------------
# External Services (if applicable)
# -----------------------------------------------
{{SERVICE_NAME}}_API_KEY={{YOUR_API_KEY}}
{{SERVICE_NAME}}_BASE_URL={{SERVICE_BASE_URL}}
```

### Variable Reference

| Variable | Required | Description | Example |
|---|---|---|---|
| `APP_ENV` | ✅ | Runtime environment | `development` |
| `APP_PORT` | ✅ | Port the server listens on | `3000` |
| `DB_HOST` | ✅ | Database host address | `localhost` |
| `DB_NAME` | ✅ | Name of the database | `myapp_dev` |
| `DB_PASSWORD` | ✅ | Database password | _(your password)_ |
| `JWT_SECRET` | ✅ | Secret key for tokens | _(random string)_ |
| `{{SERVICE_NAME}}_API_KEY` | ⚠️ Optional | API key for {{SERVICE_NAME}} | _(from dashboard)_ |

---

## Step 4 — Database Setup

<!-- IF project uses a database -->

### Create the Database

```bash
# PostgreSQL example
psql -U postgres -c "CREATE DATABASE {{DB_NAME}};"

# MySQL example
mysql -u root -p -e "CREATE DATABASE {{DB_NAME}};"
```

### Run Migrations

```bash
{{MIGRATION_COMMAND}}
```

### Seed Initial Data (Optional)

```bash
{{SEED_COMMAND}}
```

> After seeding, a default admin account is created:
> - **Email:** `{{DEFAULT_ADMIN_EMAIL}}`
> - **Password:** `{{DEFAULT_ADMIN_PASSWORD}}`
>
> ⚠️ Change these credentials immediately in a staging or production environment.

<!-- ELSE -->
_This project does not require a database._
<!-- ENDIF -->

---

## Step 5 — Build the Project

<!-- IF project requires a build step -->

```bash
{{BUILD_COMMAND}}
```

The compiled output will be placed in `./{{BUILD_OUTPUT_FOLDER}}/`.

<!-- ELSE -->
_No build step required for development._
<!-- ENDIF -->

---

## Step 6 — Run the Development Server

```bash
{{DEV_RUN_COMMAND}}
```

The application will be available at:

```
http://localhost:{{DEFAULT_PORT}}
```

<!-- IF project has multiple services (e.g. frontend + backend) -->

### Running Multiple Services

You may need to run services in separate terminal windows:

**Terminal 1 — Backend:**
```bash
{{BACKEND_RUN_COMMAND}}
```

**Terminal 2 — Frontend:**
```bash
{{FRONTEND_RUN_COMMAND}}
```

<!-- ENDIF -->

---

## Step 7 — Verify the Setup

Run the following to confirm everything is working:

```bash
# Run tests
{{TEST_COMMAND}}
```

<!-- IF project has a health check endpoint -->
Or visit the health check endpoint in your browser:

```
http://localhost:{{DEFAULT_PORT}}/{{HEALTH_CHECK_ENDPOINT}}
```

Expected response:

```json
{
  "status": "ok",
  "version": "{{VERSION}}"
}
```
<!-- ENDIF -->

If all tests pass and the server responds correctly, your setup is complete. ✅

---

## Platform-Specific Notes

### macOS

```bash
# Install prerequisites via Homebrew
brew install {{DEPENDENCY_1}} {{DEPENDENCY_2}}
```

### Windows

- Use **Windows Subsystem for Linux (WSL2)** for the best compatibility.
- Alternatively, use **Git Bash** or **PowerShell** as your terminal.
- Replace forward slashes (`/`) with backslashes (`\`) in file paths where needed.

```powershell
# Windows-specific command example (if applicable)
{{WINDOWS_SPECIFIC_COMMAND}}
```

### Linux (Ubuntu/Debian)

```bash
# Install prerequisites via apt
sudo apt update
sudo apt install {{DEPENDENCY_1}} {{DEPENDENCY_2}}
```

---

## Common Errors & Fixes

### ❌ `Permission denied` when installing packages

```bash
# Fix npm global permission issue (macOS/Linux)
sudo chown -R $(whoami) ~/.npm
```

### ❌ `Port {{DEFAULT_PORT}} is already in use`

```bash
# Find the process using the port (macOS/Linux)
lsof -i :{{DEFAULT_PORT}}
kill -9 <PID>

# Windows
netstat -ano | findstr :{{DEFAULT_PORT}}
taskkill /PID <PID> /F
```

### ❌ Database connection refused

- Ensure your database service is running.
- Verify `DB_HOST`, `DB_PORT`, `DB_USER`, and `DB_PASSWORD` in your `.env`.
- Check that the database `{{DB_NAME}}` exists.

### ❌ `Module not found` / missing dependency

```bash
# Clear cache and reinstall
rm -rf node_modules
{{DEPENDENCY_INSTALL_COMMAND}}
```

### ❌ `.env` values not loading

- Ensure the `.env` file is in the **root** of the project, not inside `src/`.
- Do not use quotes around values unless the value itself contains spaces.
- Restart the development server after editing `.env`.

---

## Resetting Your Environment

If something breaks and you want a clean slate:

```bash
# Remove installed dependencies
rm -rf {{DEPENDENCY_FOLDER, e.g. node_modules or venv}}

# Remove build artifacts
rm -rf {{BUILD_OUTPUT_FOLDER}}

# Drop and recreate the database (if applicable)
{{DB_DROP_COMMAND}}
{{DB_CREATE_COMMAND}}
{{MIGRATION_COMMAND}}

# Reinstall everything
{{DEPENDENCY_INSTALL_COMMAND}}
{{BUILD_COMMAND}}
{{DEV_RUN_COMMAND}}
```

---

> Still stuck? [Open an issue](https://github.com/{{USERNAME}}/{{REPO_NAME}}/issues) and include your OS, runtime version, and the full error message.

---

© {{YEAR}} {{AUTHOR_OR_ORGANIZATION}}
