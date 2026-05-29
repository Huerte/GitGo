---
description: GitGo Writing Rules — Release Notes, Commit Messages, Branch Names, Pull Requests
---

This is the master tone and formatting guide for all written output related to GitGo.
Apply every rule in this document to every piece of content listed below.
These rules exist for three reasons: avoid AI-detection flags, stay readable for non-native
English speakers, and keep the project approachable for beginner contributors.

---

## Voice

GitGo is a student-led open source project. Write like a developer explaining something
to a classmate, not like a company announcing a product update.

- Direct. Say what happened. Skip the setup.
- Honest. If something is small, say it's small. Do not pad it.
- Flat. No enthusiasm, no drama. Let the change speak for itself.
- Human. Vary sentence length. Not every sentence should be the same structure.

---

## Universal Rules (apply to everything)

### Words never to use
powerful, seamless, robust, exciting, significant, notable, comprehensive, clean,
straightforward, frictionless, intuitive, smart, easy, simple (when used as a filler adjective),
streamline, leverage, utilize, facilitate, ensure (when used as filler)

### Patterns never to use
- Em dashes. Use a comma or split into two sentences.
- Emojis. None, anywhere.
- Passive voice when active is possible.
  Wrong: "Files will be stashed before the pull."
  Right: "GitGo stashes your files before pulling."
- AI-pattern openers: "This update brings," "We are pleased to announce,"
  "In this release," "This PR introduces," "This change aims to," "In order to."
- Parenthetical explanations that restate what was just said.
- Two adjectives in a row before a noun.
- Sentences longer than 20 words. If you hit 20, split it.

### Non-native English rule
Write for someone who reads English but is not fluent in it.
No idioms. No phrasal verbs that can be replaced with a single verb.
No nested clauses. One idea per sentence.

---

## Commit Messages

### Format
```
type: short description in lowercase
```

### Types
- `feat` — new command or flag added
- `fix` — bug corrected
- `docs` — documentation only
- `refactor` — code changed, behavior unchanged
- `test` — test files only
- `chore` — CI, config, dependencies, tooling

### Rules
- All lowercase after the colon.
- No period at the end.
- Under 60 characters total if possible. Hard limit: 72.
- The description completes the sentence: "If applied, this commit will ___."
  Write just that blank, not the full sentence.
- If a body is needed, leave one blank line after the subject, then write in plain sentences.
  Body lines wrap at 72 characters.
- No issue numbers in the subject line. Put them in the body: `Closes #12`

### Good examples
```
feat: add gitgo pull with auto-stash and rebase
fix: prevent empty commit when no new files are staged
docs: add missing dates to changelog versions
refactor: move ssh key path logic into platform_utils
chore: add pytest-cov to dev dependencies
```

### Bad examples
```
fix stuff                        (too vague)
Added the new pull command       (capitalized, past tense)
feat: implement robust pull      (filler word)
update                           (no type, no description)
```

---

## Branch Names

### Format
```
type/short-description-in-kebab-case
```

### Types
- `feat/` — new command or user-facing behavior
- `fix/` — bug fix
- `docs/` — documentation only
- `chore/` — maintenance, CI, config
- `test/` — test files only

### Rules
- All lowercase. No uppercase anywhere.
- Hyphens only. No underscores, no slashes inside the description.
- Under 40 characters total including the prefix.
- Description must match what the branch actually does.
  Name it after the change, not the ticket or the person working on it.
- No version numbers in branch names.
- No personal identifiers: not your username, not your initials.

### Good examples
```
feat/gitgo-pull-auto-stash
fix/empty-commit-on-no-changes
docs/add-changelog-dates
chore/add-pytest-cov
feat/gitlab-ssh-support
```

### Bad examples
```
feat/new-stuff              (too vague)
sarge/pull-command             (personal identifier)
fix/bug                        (no description)
feat/gitgo-pull-command-with-auto-stash-and-rebase  (too long)
```

---

## Release Notes

### Format
```
v{{VERSION}} - {{Release Title}}

## What's New
[two to three sentences from the user's point of view]

- `command or flag` — [one to two sentences on what it does]
- `command or flag` — [one to two sentences on what it does]
```

### Rules
- Title line is plain text. No heading marker, no bold.
- Release title keyword names the main thing added: "Auto-Stash Pull", "Selective Staging",
  "Undo Commands". Not "Bug Fixes and Improvements."
- What's New section describes what the user can do now that they could not before.
  Do not describe how the code works internally.
- Each bullet starts with a backtick-wrapped command or flag name if one exists.
- If a flag triggers a specific behavior, show the exact syntax the user types.
- If a behavior has a side effect worth knowing, add it as a second sentence in the same bullet.
- Patch releases (x.x.1) get one or two bullets max. Do not pad them.
- No "thank you to contributors" line unless there is a specific person to name.
- No version comparison ("previously," "before this release," "old behavior was").

### Bad opener examples to never write
```
In this release, we have added...
We are excited to share...
This update brings several improvements...
v1.5.0 is now live with exciting new features...
```

---

## Pull Request Descriptions

### Format
```
[title — plain text, same rules as commit message subject]

## Overview
[two to four sentences: what this PR does, why, what the user can do after merge]

## What was added
- **Label:** [one to two sentences from the user's point of view]
- **Label:** [one to two sentences from the user's point of view]
```

### Rules
- Title follows the same rules as a commit message subject line.
  It can be slightly longer (up to 72 characters) since GitHub displays it with more space.
- Overview does not describe code. It describes the change from the outside.
  If there is a linked issue, reference it as `#NUMBER` in the first or second sentence.
- "What was added" section labels are bold noun phrases, not verbs.
  Wrong: **Added auto-stash before pull**
  Right: **Auto-stash on pull**
- If the PR is a one-line fix, the description can be three sentences total.
  Do not invent structure to fill space.
- Do not list files changed. GitHub already shows the diff.
- Do not explain what the tests do line by line. Say what behavior they cover.
- No "LGTM," "Please review," or "Let me know" anywhere in the body.

---

## Quick Checklist Before Posting Anything

Read your output and ask each question:

1. Does any sentence start with a filler opener? → Rewrite it.
2. Is there an em dash anywhere? → Replace it.
3. Is there a word from the banned list? → Remove it.
4. Is any sentence over 20 words? → Split it.
5. Would a non-native English speaker need a dictionary for any word? → Simplify it.
6. Does it sound like a product announcement? → Flatten the tone.
7. Is there padding in a small change? → Cut it down to match the size of the change.