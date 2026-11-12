"""
Fail when a translation file has texts that are missing, uncertain or no longer used.

Run after Django's `makemessages` has refreshed the files from the code, which is what
the checks on GitHub do. It then catches a text that was added to a page without its
Czech translation.

    uv run python manage.py makemessages --locale cs
    uv run python tools/check_translations.py
"""

import sys
from pathlib import Path

import polib

LOCALE_DIR = Path(__file__).resolve().parent.parent / "locale"


def problems(po_path: Path) -> list[str]:
    po = polib.pofile(str(po_path))
    found = [f"missing translation: {entry.msgid!r}" for entry in po.untranslated_entries()]
    found += [f"uncertain (fuzzy) translation: {entry.msgid!r}" for entry in po.fuzzy_entries()]
    found += [f"no longer used: {entry.msgid!r}" for entry in po.obsolete_entries()]
    return found


def main() -> int:
    exit_code = 0
    for po_path in sorted(LOCALE_DIR.glob("*/LC_MESSAGES/*.po")):
        for problem in problems(po_path):
            print(f"{po_path.relative_to(LOCALE_DIR.parent)}: {problem}")
            exit_code = 1
    if exit_code == 0:
        print("translations are complete")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
