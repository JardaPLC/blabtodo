"""
Fetch the picture and font drafts into static/, at fixed versions.

Run once from the project folder: `uv run python tools/fetch_drafts.py`. The files are
then committed, so the app never loads anything from another site. Sources and licences
are listed in CREDITS.md.
"""

import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tasks import picture_drafts  # noqa: E402

FLUENT = "https://cdn.jsdelivr.net/gh/microsoft/fluentui-emoji@1ffb34c752ecf5d402f04cfb4b392c77f57c54bc/assets/"
MATERIAL = "https://cdn.jsdelivr.net/npm/@material-symbols/svg-400@0.49.0/rounded/"
ANDIKA = "@fontsource/andika@5.3.0/files/andika-"
NUNITO = "@fontsource-variable/nunito@5.3.0/files/nunito-"
ATKINSON = "@fontsource-variable/atkinson-hyperlegible-next@5.3.0/files/atkinson-hyperlegible-next-"
FONTS = {
    "andika-latin-400.woff2": ANDIKA + "latin-400-normal.woff2",
    "andika-latin-ext-400.woff2": ANDIKA + "latin-ext-400-normal.woff2",
    "andika-latin-700.woff2": ANDIKA + "latin-700-normal.woff2",
    "andika-latin-ext-700.woff2": ANDIKA + "latin-ext-700-normal.woff2",
    "nunito-latin.woff2": NUNITO + "latin-wght-normal.woff2",
    "nunito-latin-ext.woff2": NUNITO + "latin-ext-wght-normal.woff2",
    "atkinson-latin.woff2": ATKINSON + "latin-wght-normal.woff2",
    "atkinson-latin-ext.woff2": ATKINSON + "latin-ext-wght-normal.woff2",
}


def fetch(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310 - fixed https sources
        target.write_bytes(response.read())
    print("saved", target.relative_to(ROOT))


def fluent_url(folder: str) -> str:
    snake = folder.lower().replace(" ", "_")
    if folder == "Person in bed":
        # Emoji with skin tones keep the default one in a folder of its own.
        path = f"{folder}/Default/Flat/{snake}_flat_default.svg"
    else:
        path = f"{folder}/Flat/{snake}_flat.svg"
    return FLUENT + urllib.parse.quote(path)


def main() -> None:
    pictures = ROOT / "static" / "pictures"
    tables = {"tasks": picture_drafts.TASKS, "rooms": picture_drafts.ROOMS}
    for kind, table in tables.items():
        for key, (fluent, material, _tile) in table.items():
            fetch(fluent_url(fluent), pictures / "fluent" / kind / f"{key}.svg")
            fetch(f"{MATERIAL}{material}-fill.svg", pictures / "material" / kind / f"{key}.svg")
    fluent, material, _tile = picture_drafts.FALLBACK
    fetch(fluent_url(fluent), pictures / "fluent" / "fallback.svg")
    fetch(f"{MATERIAL}{material}-fill.svg", pictures / "material" / "fallback.svg")
    for name, source in FONTS.items():
        fetch("https://cdn.jsdelivr.net/npm/" + source, ROOT / "static" / "fonts" / name)


if __name__ == "__main__":
    main()
