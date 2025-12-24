import os
import re
from datetime import datetime


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VIEWS_DIR = os.path.join(ROOT, "pos_app", "views")
OUT_PATH = os.path.join(ROOT, "POS_FEATURE_CATALOG.md")


RE_STRING = re.compile(r"(?P<q>['\"])(?P<s>(?:\\.|(?!\1).)*)\1")


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _extract_strings_from_args(call_src: str):
    return [m.group("s") for m in RE_STRING.finditer(call_src)]


def _find_all_calls(src: str, call_name: str):
    # Very light regex scanner; returns list of argument strings "(...)".
    # It is not a full parser but works well for cataloging UI labels.
    pat = re.compile(rf"\b{re.escape(call_name)}\s*\(")
    results = []
    i = 0
    while True:
        m = pat.search(src, i)
        if not m:
            break
        start = m.end() - 1  # points at '('
        depth = 0
        in_str = None
        esc = False
        j = start
        while j < len(src):
            ch = src[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == in_str:
                    in_str = None
            else:
                if ch in ("'", '"'):
                    in_str = ch
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        results.append(src[start : j + 1])
                        i = j + 1
                        break
            j += 1
        else:
            break
    return results


def _uniq_keep_order(items):
    out = []
    seen = set()
    for x in items:
        if not x:
            continue
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def _extract_ui_elements(src: str):
    buttons = []
    actions = []
    toolbuttons = []
    icons = []
    shortcuts = []

    for call in _find_all_calls(src, "QPushButton"):
        ss = _extract_strings_from_args(call)
        if ss:
            buttons.append(ss[0])

    for call in _find_all_calls(src, "QToolButton"):
        ss = _extract_strings_from_args(call)
        if ss:
            toolbuttons.append(ss[0])

    for call in _find_all_calls(src, "QAction"):
        ss = _extract_strings_from_args(call)
        if ss:
            actions.append(ss[0])

    # setText("...")
    for call in _find_all_calls(src, "setText"):
        ss = _extract_strings_from_args(call)
        if ss:
            buttons.append(ss[0])

    # Icon references
    for call in _find_all_calls(src, "QIcon"):
        ss = _extract_strings_from_args(call)
        if ss:
            icons.append(ss[0])

    for call in _find_all_calls(src, "setIcon"):
        ss = _extract_strings_from_args(call)
        if ss:
            icons.extend(ss)

    # Shortcuts
    for call in _find_all_calls(src, "setShortcut"):
        ss = _extract_strings_from_args(call)
        if ss:
            shortcuts.append(ss[0])

    # Detect hard-coded Ctrl+ patterns inside key handlers
    for m in re.finditer(r"Ctrl\s*\+\s*[A-Za-z0-9]", src):
        shortcuts.append(m.group(0).replace(" ", ""))

    # Detect Qt.Key_* + ControlModifier patterns (e.g. Ctrl+X implemented in eventFilter)
    for m in re.finditer(r"Qt\.Key_([A-Za-z0-9]+)\s*and\s*\(modifiers\s*&\s*Qt\.ControlModifier\)", src):
        shortcuts.append(f"Ctrl+{m.group(1).upper()}")

    # Common explicit mentions in debug prints
    for m in re.finditer(r"\[SHORTCUT\].*?Ctrl\+([A-Za-z0-9]+)", src):
        shortcuts.append(f"Ctrl+{m.group(1).upper()}")

    return {
        "buttons": _uniq_keep_order([b.strip() for b in buttons if b.strip()]),
        "actions": _uniq_keep_order([a.strip() for a in actions if a.strip()]),
        "toolbuttons": _uniq_keep_order([t.strip() for t in toolbuttons if t.strip()]),
        "icons": _uniq_keep_order([i.strip() for i in icons if i.strip()]),
        "shortcuts": _uniq_keep_order([s.strip() for s in shortcuts if s.strip()]),
    }


def _extract_sidebar_nav(main_window_src: str):
    # Extract tuple list items from nav_buttons = [("Text", ...), ...]
    nav = []
    m = re.search(r"nav_buttons\s*=\s*\[(?P<body>.*?)\]\s*\n\s*self\.nav_buttons", main_window_src, re.S)
    if not m:
        return nav
    body = m.group("body")
    for line in body.splitlines():
        if "(" not in line:
            continue
        ss = _extract_strings_from_args(line)
        if ss:
            nav.append(ss[0])
    return _uniq_keep_order(nav)


def _walk_py_files(base_dir: str):
    for root, _dirs, files in os.walk(base_dir):
        for fn in sorted(files):
            if not fn.endswith(".py"):
                continue
            yield os.path.join(root, fn)


def generate():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    view_files = list(_walk_py_files(VIEWS_DIR))

    main_window_path = os.path.join(VIEWS_DIR, "main_window.py")
    main_window_src = _read_text(main_window_path) if os.path.exists(main_window_path) else ""
    sidebar_nav = _extract_sidebar_nav(main_window_src)

    by_file = []
    all_buttons = []
    all_actions = []
    all_toolbuttons = []
    all_icons = []
    all_shortcuts = []

    for path in view_files:
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        src = _read_text(path)
        elems = _extract_ui_elements(src)
        by_file.append((rel, elems))

        all_buttons.extend(elems["buttons"])
        all_actions.extend(elems["actions"])
        all_toolbuttons.extend(elems["toolbuttons"])
        all_icons.extend(elems["icons"])
        all_shortcuts.extend(elems["shortcuts"])

    all_buttons = _uniq_keep_order(all_buttons)
    all_actions = _uniq_keep_order(all_actions)
    all_toolbuttons = _uniq_keep_order(all_toolbuttons)
    all_icons = _uniq_keep_order(all_icons)
    all_shortcuts = _uniq_keep_order(all_shortcuts)

    lines = []
    lines.append(f"# POS Feature Catalog\n")
    lines.append(f"Generated: `{now}`\n")
    lines.append("This file is generated from the current code in `pos_app/views` by scanning for UI elements (buttons/actions/toolbuttons/icons/shortcuts).")
    lines.append("Because some UI labels are dynamic (built at runtime), this catalog is **best-effort** and may not include 100% of dynamic/translated labels.\n")

    lines.append("## Main Navigation (Sidebar)\n")
    if sidebar_nav:
        for t in sidebar_nav:
            lines.append(f"- **{t}**")
    else:
        lines.append("- **(Not detected)**")
    lines.append("")

    lines.append("## Global Shortcut Inventory (Detected in Code)\n")
    if all_shortcuts:
        for s in all_shortcuts:
            lines.append(f"- **{s}**")
    else:
        lines.append("- **(None detected)**")
    lines.append("")

    lines.append("## Global UI Label Inventory (Detected in Code)\n")
    lines.append("### Buttons (QPushButton / setText)\n")
    if all_buttons:
        for b in all_buttons:
            lines.append(f"- **{b}**")
    else:
        lines.append("- **(None detected)**")

    lines.append("\n### Actions (QAction)\n")
    if all_actions:
        for a in all_actions:
            lines.append(f"- **{a}**")
    else:
        lines.append("- **(None detected)**")

    lines.append("\n### Tool Buttons (QToolButton)\n")
    if all_toolbuttons:
        for t in all_toolbuttons:
            lines.append(f"- **{t}**")
    else:
        lines.append("- **(None detected)**")

    lines.append("\n### Icons (QIcon / setIcon)\n")
    if all_icons:
        for i in all_icons:
            lines.append(f"- **{i}**")
    else:
        lines.append("- **(None detected)**")

    lines.append("\n## Per-File Feature Inventory\n")
    for rel, elems in by_file:
        lines.append(f"### `{rel}`\n")

        if elems["buttons"]:
            lines.append("#### Buttons\n")
            for b in elems["buttons"]:
                lines.append(f"- **{b}**")
            lines.append("")

        if elems["actions"]:
            lines.append("#### Actions\n")
            for a in elems["actions"]:
                lines.append(f"- **{a}**")
            lines.append("")

        if elems["toolbuttons"]:
            lines.append("#### Tool Buttons\n")
            for t in elems["toolbuttons"]:
                lines.append(f"- **{t}**")
            lines.append("")

        if elems["icons"]:
            lines.append("#### Icons\n")
            for i in elems["icons"]:
                lines.append(f"- **{i}**")
            lines.append("")

        if elems["shortcuts"]:
            lines.append("#### Shortcuts\n")
            for s in elems["shortcuts"]:
                lines.append(f"- **{s}**")
            lines.append("")

        if not (elems["buttons"] or elems["actions"] or elems["toolbuttons"] or elems["icons"] or elems["shortcuts"]):
            lines.append("- **(No static UI elements detected by scanner)**\n")

    content = "\n".join(lines).rstrip() + "\n"

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    return OUT_PATH


if __name__ == "__main__":
    out = generate()
    print(out)
