# Changelog

## 0.3.1

Fixes found by trying the screens in a real browser at phone, tablet and PC sizes.

- On a small phone the PIN pad and its button now fit without scrolling.
- On a small phone the Done and Not yet buttons stay at the bottom edge of the sheet,
  always in view.
- On a tablet or PC the Done panel is as tall as its content instead of nearly filling
  the screen.

## 0.3.0

Tasks.

- Tasks and rooms are set up in the management pages. Choosing a picture is enough: its
  name comes with it, in Czech and English.
- A task repeats every few days, on chosen days of the week, on a day of the month, or
  happens once.
- **Today** shows the waiting cards, oldest first. A card waits until someone does it,
  and there is never more than one card per task.
- Tap a card, tap who did it, tap Done. Undo is offered for ten seconds.
- Tapping a face shows only the cards meant for that person.
- The app keeps a copy of its database once a day and before each update.

The pictures are stand-ins for now. The real picture set is chosen in the next version.

## 0.2.0

The family and its devices.

- A first-run screen creates the first adult, with a PIN and a password.
- The rest of the family is added in the management pages, each with a face photo or a
  coloured initial.
- A new phone, tablet or PC is allowed once by an adult's PIN and then opens the app
  without asking. Devices can be renamed and removed in the management pages.
- After five wrong PINs in a row, PIN entry pauses, longer after each further wrong try.

After updating, the app shows the first-run screen once. Tasks arrive with the next
version.

## 0.1.1

Fixed: the page did not open under a name such as `homeassistant.local`, only under the
numeric IPv4 address. The app now answers over IPv6 as well.

## 0.1.0

First installable version. It shows a test page in Czech and English that confirms the
whole chain works: the page, its styles, live refresh, and the database.
