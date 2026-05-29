<!-- If you are unsure how to fill this out, see CONTRIBUTING.md: https://github.com/Huerte/GitGo/blob/main/CONTRIBUTING.md -->

<!-- Note: These hidden comments guide you while typing. GitHub hides them automatically when you submit. -->

## Type

<!-- Check the one that fits. Put an 'x' inside the brackets: [x] -->

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactor / internal

## Overview

<!-- Describe what you changed and why. 2-3 sentences is enough. -->



## Changes

<!-- One bullet per change. Say what changed and what effect it has.
     Examples:
     - `gitgo push`: no longer stops mid-run after a branch jump. It now completes the commit and push automatically.
     - `gitgo jump`: revert prompt now shows the target branch name before asking for confirmation.
     - README: added missing flag description for `gitgo push -s`.
-->

-

## Breaking Changes

<!-- Does this change the behavior of an existing command, flag, or output in a way
     that could break someone's workflow? If yes, describe what breaks and what they
     should do instead. If no, write: None -->

**Breaking changes:** None

## How to Test

<!-- Write the exact steps a reviewer should run to verify your change works.
     Be specific — include the exact commands and what output to expect.
     If this PR only updates documentation, you can skip this section.
-->

1. `pip install -e ".[dev]"`
2.
3. Expected result:

## Checklist

<!-- Put an 'x' inside the brackets to check a box: [x] -->

- [ ] I tested my changes locally and they work
- [ ] I updated `CHANGELOG.md` under the [`[Unreleased]`](https://github.com/Huerte/GitGo/blob/main/CHANGELOG.md) section
- [ ] I updated `README.md` (if I added or changed a command)
- [ ] I added or updated tests for my change (if applicable)
- [ ] My change does not break any existing commands