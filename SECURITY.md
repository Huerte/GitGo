# Security Policy

## Supported Versions

We only fix security problems in the latest release of GitGo.

| Version | Supported |
| ------- | --------- |
| Latest  | Yes       |
| Older   | No        |

## Reporting a Vulnerability

Do not open a public issue for a security problem. 

Report security problems using GitHub Private Vulnerability Reporting. Follow these steps:

1. Go to the "Security" tab in this repository.
2. Click "Advisories" on the left side.
3. Click the "Report a vulnerability" button.
4. Fill in the form with details about the problem.
5. Click "Submit report".

## What to Expect After Reporting

We read every report. We will reply to you within 5 to 7 days. We will ask you if we need more details. We will update you as we work on a fix. When we fix the problem, we will release a new version. We will give you credit for finding the problem if you want.

## Scope

This policy covers the GitGo code. 

A real security problem must affect one of these sensitive parts:
- SSH key generation and commit signing.
- How we store the GitHub Personal Access Token in the git config.
- How we rewrite remote URLs.
- How we run git subprocess commands.

Examples of valid security problems:
- Someone can read your GitHub Personal Access Token.
- Someone can run dangerous commands through git subprocess calls.
- Someone can steal your SSH keys.

These are NOT security problems:
- A bug that crashes the tool but does not expose data.
- Feature requests.
- Questions about how to use the tool.

For normal bugs, please open a regular public issue.
