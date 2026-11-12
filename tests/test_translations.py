"""The translation files are complete, and their compiled form is current."""

from pathlib import Path

import polib
import pytest

from tools.check_translations import problems

LOCALE_DIR = Path(__file__).resolve().parent.parent / "locale"
PO_FILES = sorted(LOCALE_DIR.glob("*/LC_MESSAGES/*.po"))
HOW_TO_FIX = "run: uv run python tools/compile_translations.py"


def _language(po_path: Path) -> str:
    return po_path.parts[-3]


def test_the_translation_file_has_every_text_of_the_code_and_nothing_else():
    # The pure-Python stand-in for Django's makemessages, which GitHub runs for real.
    from tools.check_texts import compare

    missing, unused = compare()

    assert missing == set(), "run: uv run python tools/check_texts.py"
    assert unused == set(), "run: uv run python tools/check_texts.py"


def test_there_is_a_czech_translation():
    assert "cs" in {_language(path) for path in PO_FILES}


@pytest.mark.parametrize("po_path", PO_FILES, ids=_language)
def test_every_text_is_translated(po_path):
    assert problems(po_path) == []


@pytest.mark.parametrize("po_path", PO_FILES, ids=_language)
def test_compiled_file_is_up_to_date(po_path):
    mo_path = po_path.with_suffix(".mo")

    assert mo_path.is_file(), HOW_TO_FIX
    assert mo_path.read_bytes() == polib.pofile(str(po_path)).to_binary(), HOW_TO_FIX
