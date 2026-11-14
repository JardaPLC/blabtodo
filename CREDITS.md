# Credits

blabtodo is published under the MIT licence (see [LICENSE](LICENSE)). It includes or
builds on the work of others, listed here with their own licences.

## Files stored in this repository

These are kept at fixed versions in `static/vendor/`, so the app works without an
internet connection and never loads anything from another site.

| File | What | Version | Licence | Source | SHA-256 |
|---|---|---|---|---|---|
| `htmx.min.js` | [htmx](https://htmx.org) | 2.0.11 | 0BSD | `https://unpkg.com/htmx.org@2.0.11/dist/htmx.min.js` | `d6fdc75f204e6bdefa99b69bf1e6d4ac69b8a364f77929f45c13476b4000f717` |
| `alpine.min.js` | [Alpine.js](https://alpinejs.dev) | 3.17.5 | MIT | `https://unpkg.com/alpinejs@3.17.5/dist/cdn.min.js` | `b4036e9e9ac22fa6f6ae1ba292e015e1f3e9c85d0d79e73e4c8eb9bb139b522e` |

To update one of them: download the new version from the same source, replace the file,
and update its row here.

## Used while building

- [segno](https://github.com/heuer/segno) (BSD-3-Clause) draws the QR codes.
- [Tailwind CSS](https://tailwindcss.com) (MIT) generates the stylesheet.
- [Django](https://www.djangoproject.com) (BSD-3-Clause) and the other Python packages
  are listed in `pyproject.toml`. They are installed into the image, not copied here.

## Pictures and fonts (drafts)

These are drafts to choose from on the Look page. Once the family has chosen, the others
are removed. They are fetched at fixed versions by `tools/fetch_drafts.py` and stored in
`static/pictures/` and `static/fonts/`.

| What | Version | Licence | Source |
|---|---|---|---|
| [Fluent Emoji](https://github.com/microsoft/fluentui-emoji), flat style | commit `1ffb34c` | MIT, © Microsoft Corporation | `https://github.com/microsoft/fluentui-emoji` |
| [Material Symbols](https://github.com/google/material-design-icons), rounded, filled | 0.49.0 | Apache 2.0, © Google | npm `@material-symbols/svg-400` |
| [Andika](https://software.sil.org/andika/) | 5.3.0 | SIL Open Font Licence 1.1, © SIL International | npm `@fontsource/andika` |
| [Nunito](https://github.com/googlefonts/nunito) | 5.3.0 | SIL Open Font Licence 1.1, © The Nunito Project Authors | npm `@fontsource-variable/nunito` |
| [Atkinson Hyperlegible Next](https://www.brailleinstitute.org/freefont/) | 5.3.0 | SIL Open Font Licence 1.1, © Braille Institute of America | npm `@fontsource-variable/atkinson-hyperlegible-next` |

Each task's file is named after its picture key; `tasks/picture_drafts.py` says which
emoji or symbol it is.

## Sounds

None yet. Each one added later gets a row here with its source and licence.
