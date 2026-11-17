# Changelog

## 0.7.0

Tasks and rooms are edited in the app, on a phone. No PC needed for everyday changes.

- **Pro dospělé → Upravit úkoly a místnosti** (For adults → Edit tasks and rooms) asks
  for an adult's PIN. Editing then stays unlocked on that device for half an hour after
  the last use, or until **Ukončit** (Finish).
- **Tasks:** a list grouped by room. **Nový úkol** (New task) starts from the catalogue,
  with search, or from your own name. The editor has a picture picker, room, how often,
  for whom, how much work, in use, and under **Další nastavení** (More) the hint, the
  chain, day-only, the end date and the English name. On an existing task: **Zobrazit
  dnes** / **+1**, **Tentokrát přeskočit** (Skip this time), **QR nálepka** (QR sticker),
  and **Smazat** (Delete) for a task never done.
- **Rooms:** a list in order with arrows to move them, new rooms from the catalogue,
  rename, switch off, delete (its tasks stay, without a room).
- Family members, devices and corrections of finished tasks stay in the management pages.

## 0.6.1

Today filtered by room.

- The switch at the start of the filter row chooses between **Lidé** (People) and
  **Místnosti** (Rooms). In room mode the row shows each room in use with the number of
  cards waiting there, plus **Jinde** (Elsewhere) for tasks without a room.
- One filter at a time: choosing a room drops the chosen person, and the other way round.
- The filter is kept in the address. A small display in the kitchen can be left on the
  kitchen's address; the refresh, Done and Undo stay in the kitchen.

## 0.6.0

Rounds: one card for a pile that needs several goes.

- A waiting card can be asked for again. A pile of washing for three loads is one card
  marked **×3**. Add a round with **+1 ještě jednou** on the Done sheet, by scanning the
  task's QR code again, or with **Kolikrát** (Times) in the management pages.
- Done takes one round off; the card goes after the last one. Each round is listed under
  Hotové on its own.
- In a chain, each load asks for one emptying: two loads of the dishwasher leave
  **Vyklidit myčku ×2**.
- The licence texts of the pictures and fonts are now included next to them.

## 0.5.1

Fix: **Done did nothing** for a task that had already been done earlier the same day,
for example "Vyklidit myčku" shown a second time by a chain, or a QR sticker scanned
twice. Such a task can now be done as often as it is asked for.

- If a tap on Today fails for any reason, a red message now says so, instead of nothing
  happening.
- Errors are now written to the app's log in Home Assistant.

## 0.5.0

Chains, finished tasks, and drafts of the pictures and font to choose from.

- **Chains.** In a task's settings, **Potom zobrazit** (Then show) names the task that
  comes next: load the dishwasher, then empty it. When the card is done, the next card
  appears on Today straight away. Undo takes it away again. The next task is best set to
  **Jen na vyžádání** (Only when asked for). A new catalogue picture, **Uklidit prádlo**
  (Put the laundry away), completes the laundry chain.
- **Finished tasks.** The **Hotové** (Finished) button on Today lists what was done, newest
  first and by day, with who did it, when, and the note. Older days load as you scroll.
- **Look.** Under **Pro dospělé** (For adults), **Vzhled** (Look) shows two picture sets
  and three fonts. A choice there changes only that device, so everyone can try them.
  Tell us which you like; the rest will be removed.

## 0.4.0

QR stickers.

- A new way of repeating, **Jen na vyžádání** (Only when asked for): the task never
  appears by itself.
- In the management pages, select tasks and choose **Vytisknout QR nálepky** (Print QR
  stickers) to print a sticker for each.
- Scanning a sticker with a phone's camera opens the task and asks whether to show it on
  Today. This works for repeating tasks too, to bring one forward.
- The codes hold the address the stickers were printed from. If that address changes,
  print them again; the tasks keep their codes.

## 0.3.2

A task that was never done can now be deleted, for example one added by mistake. Once it has been done it can still only be switched off, so that the record of what was done stays whole.

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
