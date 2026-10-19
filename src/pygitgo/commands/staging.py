from pygitgo.utils.executor import run_command
from pygitgo.exceptions import GitCommandError
from pygitgo.utils.cli_io import success



STATUS_LABELS = {
    "M": "modified",
    "A": "added",
    "D": "deleted",
    "R": "renamed",
    "??": "new file",
}


def parse_porcelain_z(raw):
    """Parse `git status --porcelain -z` output.

    Entries are NUL-separated as 'XY path'. Paths are never quoted in -z mode,
    and renames/copies are followed by an extra entry holding the original path.
    """
    files = []
    entries = raw.split("\0")
    i = 0
    while i < len(entries):
        entry = entries[i]
        i += 1
        if len(entry) < 4 or entry[2] != " ":
            continue
        xy, path = entry[:2], entry[3:]
        if "R" in xy or "C" in xy:
            i += 1  # skip the original path of a rename/copy
        code = xy.strip()
        label = STATUS_LABELS.get(code, "changed")
        files.append({"status": code, "label": label, "path": path, "index": xy[0]})
    return files


def get_changed_files():
    # Don't use the stripped string form: stripping removes the leading space of
    # the first entry (' M file') and shifts every path in that entry by one char.
    try:
        result = run_command(["git", "status", "--porcelain", "-z"], return_complete=True)
    except GitCommandError:
        return []

    raw = result.stdout if hasattr(result, "stdout") else str(result)
    return parse_porcelain_z(raw)


def display_file_picker(files):
    from pick import pick
    options = [f"({f['label']}) {f['path']}" for f in files]

    selected = pick(
        options,
        "Select files to stage (SPACE to toggle, ENTER to confirm):",
        multiselect=True,
        min_selection_count=0
    )

    return [files[idx]["path"] for _, idx in selected]


def selective_stage(selected_files):
    for filepath in selected_files:
        run_command(["git", "add", "--", filepath])
    success(f"\n{len(selected_files)} file(s) staged for commit.")
