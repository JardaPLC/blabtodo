"""
Compare the texts in the code with a translation file.

Lists texts that are in the code but not in the file, and entries in the file that the
code no longer uses. With --update it adds the missing ones (untranslated, for you to
fill in) and removes the unused ones.

Django's `makemessages` does this job properly, but it needs the GNU gettext programs,
which Windows does not have. This is the pure-Python stand-in for everyday work. The
checks on GitHub still run the real `makemessages`.

    uv run python tools/check_texts.py
    uv run python tools/check_texts.py --update
"""

import ast
import os
import sys
from pathlib import Path

import polib

ROOT = Path(__file__).resolve().parent.parent
PO_FILE = ROOT / "locale" / "cs" / "LC_MESSAGES" / "django.po"

# Folders with no translatable texts of ours.
SKIPPED_FOLDERS = {
    ".django_tailwind_cli",
    ".git",
    ".venv",
    "data",
    "docs",
    "locale",
    "migrations",
    "static",
    "staticfiles",
    "tests",
    "tools",
}

SINGULAR = {"_", "gettext", "gettext_lazy", "gettext_noop"}
PLURAL = {"ngettext", "ngettext_lazy"}
WITH_CONTEXT = {"pgettext", "pgettext_lazy"}
PLURAL_WITH_CONTEXT = {"npgettext", "npgettext_lazy"}
ALL_NAMES = SINGULAR | PLURAL | WITH_CONTEXT | PLURAL_WITH_CONTEXT

# One text: (context or None, the text, its plural form or None).
Text = tuple[str | None, str, str | None]


def _text_from_call(call: ast.Call) -> Text | None:
    if isinstance(call.func, ast.Name):
        name = call.func.id
    elif isinstance(call.func, ast.Attribute):
        name = call.func.attr
    else:
        return None
    if name not in ALL_NAMES:
        return None

    strings = []
    for argument in call.args:
        if not (isinstance(argument, ast.Constant) and isinstance(argument.value, str)):
            break
        strings.append(argument.value)

    if name in SINGULAR and len(strings) >= 1:
        return (None, strings[0], None)
    if name in PLURAL and len(strings) >= 2:
        return (None, strings[0], strings[1])
    if name in WITH_CONTEXT and len(strings) >= 2:
        return (strings[0], strings[1], None)
    if name in PLURAL_WITH_CONTEXT and len(strings) >= 3:
        return (strings[0], strings[1], strings[2])
    return None


def texts_in_python(source: str) -> set[Text]:
    calls = (node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Call))
    return {text for text in map(_text_from_call, calls) if text is not None}


def _calls_in_converted_template(converted: str):
    """
    Yield each `gettext(...)`-style call from Django's converted form of a template.

    The converted form is not valid Python as a whole (everything else is blanked out),
    so the calls are cut out one by one.
    """
    position = 0
    while True:
        hits = [(converted.find(name + "(", position), name) for name in ALL_NAMES]
        hits = [(index, name) for index, name in hits if index != -1]
        if not hits:
            return
        index, _name = min(hits)
        start = index
        while start > 0 and (converted[start - 1].isalnum() or converted[start - 1] == "_"):
            start -= 1
        depth, cursor, quote = 0, converted.index("(", index), None
        while cursor < len(converted):
            char = converted[cursor]
            if quote:
                if char == "\\":
                    cursor += 1
                elif char == quote:
                    quote = None
            elif char in "'\"":
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    break
            cursor += 1
        yield converted[start : cursor + 1]
        position = cursor + 1


def texts_in_template(source: str) -> set[Text]:
    from django.utils.translation.template import templatize

    found = set()
    for call in _calls_in_converted_template(templatize(source)):
        node = ast.parse(call.strip(), mode="eval").body
        if isinstance(node, ast.Call):
            text = _text_from_call(node)
            if text is not None:
                found.add(text)
    return found


def texts_in_code(root: Path = ROOT) -> set[Text]:
    found = set()
    for folder, subfolders, files in os.walk(root):
        subfolders[:] = [name for name in subfolders if name not in SKIPPED_FOLDERS]
        for name in files:
            path = Path(folder) / name
            if path.suffix == ".py":
                found |= texts_in_python(path.read_text(encoding="utf-8"))
            elif path.suffix in {".html", ".txt"} and "templates" in path.parts:
                found |= texts_in_template(path.read_text(encoding="utf-8"))
    return found


def texts_in_file(po_file: Path = PO_FILE) -> set[Text]:
    return {
        (entry.msgctxt, entry.msgid, entry.msgid_plural or None)
        for entry in polib.pofile(str(po_file))
        if not entry.obsolete
    }


def compare(root: Path = ROOT, po_file: Path = PO_FILE) -> tuple[set[Text], set[Text]]:
    """Return (texts missing from the file, entries the code no longer uses)."""
    in_code, in_file = texts_in_code(root), texts_in_file(po_file)
    return in_code - in_file, in_file - in_code


def update(po_file: Path, missing: set[Text], unused: set[Text]) -> None:
    po = polib.pofile(str(po_file))
    plural_forms = int(po.metadata.get("Plural-Forms", "nplurals=2").split("nplurals=")[1][0])
    for entry in list(po):
        if (entry.msgctxt, entry.msgid, entry.msgid_plural or None) in unused:
            po.remove(entry)
    for context, text, plural in sorted(missing, key=lambda item: item[1]):
        entry = polib.POEntry(msgid=text, msgctxt=context)
        if plural:
            entry.msgid_plural = plural
            entry.msgstr_plural = dict.fromkeys(range(plural_forms), "")
        if "%(" in text:
            entry.flags.append("python-format")
        po.append(entry)
    po.save()


def _describe(text: Text) -> str:
    context, singular, plural = text
    described = repr(singular)
    if plural:
        described += f" / {plural!r}"
    if context:
        described += f" (context {context!r})"
    return described


def main(arguments: list[str]) -> int:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    sys.path.insert(0, str(ROOT))
    import django

    django.setup()

    missing, unused = compare()
    if "--update" in arguments:
        update(PO_FILE, missing, unused)
        print(f"added {len(missing)} untranslated, removed {len(unused)} unused")
        print("now fill in the empty translations and run tools/compile_translations.py")
        return 0

    for text in sorted(missing, key=str):
        print("missing from the translation file:", _describe(text))
    for text in sorted(unused, key=str):
        print("no longer used in the code:", _describe(text))
    if missing or unused:
        print("\nrun with --update to add and remove them in", PO_FILE.relative_to(ROOT))
        return 1
    print("the translation file matches the code")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
