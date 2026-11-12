"""
Compile the translation files (.po) into the binary form that Django reads (.mo).

Django's own `compilemessages` command needs the GNU gettext programs, which Windows
does not have. This script does the same job in pure Python, and the compiled files are
kept in the repository so that nothing has to be compiled when the app is installed.

    uv run python tools/compile_translations.py
"""

from pathlib import Path

import polib

LOCALE_DIR = Path(__file__).resolve().parent.parent / "locale"


def compile_all(locale_dir: Path = LOCALE_DIR) -> list[Path]:
    compiled = []
    for po_path in sorted(locale_dir.glob("*/LC_MESSAGES/*.po")):
        mo_path = po_path.with_suffix(".mo")
        polib.pofile(str(po_path)).save_as_mofile(str(mo_path))
        compiled.append(mo_path)
    return compiled


if __name__ == "__main__":
    for path in compile_all():
        print(f"compiled {path.relative_to(LOCALE_DIR.parent)}")
