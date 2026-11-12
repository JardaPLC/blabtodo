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

- [Tailwind CSS](https://tailwindcss.com) (MIT) generates the stylesheet.
- [Django](https://www.djangoproject.com) (BSD-3-Clause) and the other Python packages
  are listed in `pyproject.toml`. They are installed into the image, not copied here.

## Pictures, fonts and sounds

None yet. Each one added later gets a row here with its source and licence.
