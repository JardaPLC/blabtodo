# blabtodo — design

A home task manager for one family. Household tasks sit in one shared queue that any screen in the house can show, and marking a task done takes two taps.

- **Status:** draft 0.8, 2026-11-12. Milestone 0 runs on the Pi; its backups and restore rehearsal are still to be done. Milestone 1 is in progress: people and devices are built, and tasks with the Today and Done screens are next.
- **Designed for:** a family with children who cannot read yet and who will grow into it. Czech by default, English as a second language. Used on phones, tablets, PCs and a wall panel. Reachable on the home network only.
- **Not settled:** see [Open questions](#17-open-questions).
- **How to read this:** sections 1–6 describe what the app does, 7–13 how it is built, 14–17 the plan, the decisions and what is still open.

## 1. What we are building

What the app must do:

- Adults set up household tasks, either one-time or repeating.
- Everyone sees one shared queue, oldest task first.
- Tasks can belong to a room, and each room shows what waits there.
- Anyone marks a task done, optionally with a photo or a note. The task then moves to the archive.
- Finished tasks fill one shared family jar that leads to a treat for the whole family.
- It works on a phone, a tablet, a PC and a wall panel, with the same screens everywhere.
- It runs at home on a device that is on all day. Data stays at home, and a backup is a copy of one folder.

Principles. When a later question has no obvious answer, these decide it:

1. **Simple beats complete.** One screen does 90% of the job. A feature that needs explaining waits.
2. **Pictures first.** The kids cannot read yet, so every task is a big picture with large text under it.
3. **Two taps to done.** Tap the card, tap Done. Everything else is optional.
4. **Together, not against each other.** Nothing on any screen compares people.
5. **Nothing is taken away.** No penalties, no red "overdue" warnings, no broken streaks.
6. **One box, one folder, one language.** One container, one SQLite file, one data folder, and Python for everything.

Deliberately left out: projects, subtasks, priorities, deadlines with times, labels, chat, approval of someone's work, pocket-money accounting, calendar sync, several households in one installation, cloud hosting.

## 2. People, views and devices

### Roles

| Role | Who | Can do |
|---|---|---|
| Child | the kids | See the queue, mark tasks done, see the archive and the jar, send thanks |
| Adult | the parents | Everything a child can, plus the admin view |

Adults are the administrators. There is no separate admin account. The first adult created during setup is also the technical owner (Django superuser) and can open Django's own `/admin/` pages for repairs.

### Two views

- **User view:** Today, Rooms, Done, Jar. It is the same for adults and children and has no edit buttons anywhere, so nothing gets changed by accident.
- **Admin view:** Tasks, Rooms, People, Jar goals, Statistics, Devices, Settings, and corrections such as skipping a card or reopening a finished one. It has its own navigation and a differently coloured header, so it is always clear which view is open.
- **The switch:** a lock button in the corner of the user view. Pick your face, enter your PIN, and the admin view opens. "Back to user view" is always visible. On a shared device the admin view closes by itself after a few minutes without a touch. An adult can tell their own phone not to ask for the PIN.

### Devices

Every family member has an account, but nobody types a user name. Small kids cannot type, and a wall panel must show the queue without anyone logging in. So trust is given to devices, and people are picked by face.

- **Trusting a device.** The first time a browser opens the app, an adult enters their PIN once. From then on that device shows the user view with no login. The trust lasts about a year and renews with use. Adults can see the list of trusted devices and remove one.
- **Shared device** (wall panel, family PC). Each time a task is marked done it asks "Who did it?" and shows the faces.
- **Personal device** (a phone). It belongs to one person, and that person is already selected.

Marking a task done under someone's face needs no PIN. The family trusts each other; the protection sits at the device level. Children have no PIN for now. A PIN per child can be added when they are older and have their own devices.

## 3. Screens

### 3.1 Today

```
+----------------------------------------------------------------+
|  Today                        Jar [#######...] (pizza)  [lock] |
|  (All) (face) (face) (face) (face)                             |
|                                                                |
|  +--------------+  +--------------+  +--------------+          |
|  |              |  |              |  |              |          |
|  |  [picture]   |  |  [picture]   |  |  [picture]   |          |
|  |              |  |              |  |              |          |
|  |  Water the   |  |  Load the    |  |  Put the     |          |
|  |  plants      |  |  dishwasher  |  |  toys away   |          |
|  |  Living room |  |  Kitchen     |  |  Playroom    |          |
|  |  since Mon   |  |              |  |      (face)  |          |
|  +--------------+  +--------------+  +--------------+          |
|                                                                |
|  [ Today ]      [ Rooms ]      [ Done ]      [ Jar ]           |
+----------------------------------------------------------------+
```

- Cards are ordered oldest first (first in, first out), by the day each card appeared.
- A card from an earlier day carries a neutral label such as "since Monday". Never red, never "overdue".
- A card shows its room in small type under the title. A task without a room shows none.
- The face buttons at the top filter the queue to "cards with my face on them". This is how a child who cannot read finds their own tasks.
- An empty queue shows a celebration screen.
- The screen refreshes by itself about every 30 seconds, so the wall panel follows what happens on phones.

### 3.2 Rooms

Adults define the rooms of the home, each with a name and a picture, ideally a photo of the real room. A task can belong to one room, or to none ("Go to the shop").

```
+----------------------------------------------------------------+
|  Rooms                        Jar [#######...] (pizza)  [lock] |
|                                                                |
|  +--------------+  +--------------+  +--------------+          |
|  |              |  |              |  |              |          |
|  |  [photo]     |  |  [photo]     |  |  [photo]     |          |
|  |              |  |              |  |              |          |
|  |  Kitchen     |  |  Bathroom    |  |  Playroom    |          |
|  |  (pic) (pic) |  |  all done    |  |  (pic)       |          |
|  +--------------+  +--------------+  +--------------+          |
|                                                                |
|  [ Today ]      [ Rooms ]      [ Done ]      [ Jar ]           |
+----------------------------------------------------------------+
```

- A room tile shows small pictures of the tasks waiting there, or a tick when nothing waits. It says what waits, never how neglected the room is: there is no "dirt" meter.
- Tapping a room shows its waiting cards, oldest first, exactly like Today. Marking done works the same way.
- Rooms keep a fixed order, set by adults. A tile never moves, so a child learns where each room is.
- A last tile, "Elsewhere", collects the waiting tasks that have no room.
- "Room" means any place. The garden, the garage and the cellar are rooms too. There are no floors and no groups of rooms.
- A task has one room or none. "Vacuum the whole flat" is either one task without a room, or one task per room.
- Common rooms come from the starter catalogue with a picture and a name in every language, and a task added from the catalogue suggests its usual room.
- A household that defines no rooms never sees this screen.

Later candidates: a wall panel that opens on its own room, statistics by room, and matching rooms to Home Assistant areas.

### 3.3 Marking a task done

```
+-------------------------------------+
|            [big picture]            |
|          Water the plants           |
|                                     |
|  Who did it?                        |
|  (face) (face) (face) (face)        |   tap one, or several: "we did it together"
|                                     |
|  [ Add photo ]      [ Add note ]    |   both optional
|                                     |
|  [              Done              ] |
+-------------------------------------+
```

- On a shared device you pick the face or faces. On a personal device yours is already picked, so it is two taps.
- After Done the card flies into the jar, with an optional short sound. An "Undo" bar stays for about 10 seconds, because small fingers hit the wrong card. After that only adults can undo, from the admin view.
- Add photo opens the camera directly on a phone, and a file picker on a PC. The photo is shrunk on the device before it is uploaded.

### 3.4 Done (archive)

Newest first, grouped by day. Each entry shows the picture, the title, the faces, the time, the note, a photo thumbnail that opens full size, and a heart for thanks.

### 3.5 Admin view

Tasks (a list and an editor with a picture picker and repeat settings), Rooms, People, Jar goals, Statistics, Devices, Settings. Its own Queue and Archive lists carry the correction buttons: skip a card, reopen a finished one, change who did it. In the first milestone tasks are set up in Django's admin pages; the admin view comes right after.

### 3.6 Rules for every screen

- Every task has a picture: one from the built-in set, or your own photo. A photo of *your* dishwasher is the picture a small child recognises fastest.
- Large type in the user view: at least 20 px on phones, and larger on tablets and the panel, where task titles must be readable from across the room. The admin view uses ordinary sizes, at least 16 px. These are starting values to tune on real devices.
- The font is bundled with the app and must cover Czech letters fully (ě, š, č, ř, ž, ů and the rest).
- Touch targets at least 64 px in the user view and 48 px in the admin view. No actions that need hover, a right-click or a swipe. No nested menus.
- One main action per screen: the big green button, always in the same place.
- Colour is never the only signal. The app respects the system's "reduce motion" setting, and sounds can be switched off.
- Plain words: "Today", "Rooms", "Done", "Jar". Internal terms such as "completion" never appear on screen.
- People are shown as faces and tasks as pictures wherever possible. Thanks, for example, appears as face, heart, face, task picture.
- Reading the task name aloud (a speaker button) is planned for the kids. It depends on which voices the device has for Czech, so it is tested on the real panel first.

### 3.7 Screen sizes

The app is used on phones, tablets, PCs and a wall panel. It is one set of screens that adapts, designed for the phone first and then widened.

| Screen | Cards per row on Today | What else changes |
|---|---|---|
| Phone, upright (from about 360 px wide) | 2 | The Done sheet fills the screen. Navigation and the Done button sit at the bottom, within thumb reach. Faces scroll sideways if they do not fit. |
| Tablet, upright or sideways | 3 or 4 | The Done sheet becomes a centred panel. |
| PC and wall panel | 4 to 6 | Larger type. Mouse and keyboard work as well as touch. |

Today on a phone:

```
+----------------------------+
|  Today              [lock] |
|  Jar [#######...]          |
|  (All) (face) (face) (fa > |
|                            |
| +----------+  +----------+ |
| |  [pic]   |  |  [pic]   | |
| | Water    |  | Load the | |
| | plants   |  | dishes   | |
| | Kitchen  |  | Kitchen  | |
| +----------+  +----------+ |
| +----------+  +----------+ |
| |  [pic]   |  |  [pic]   | |
| | Put toys |  | Go to    | |
| | away     |  | the shop | |
| | Playroom |  |          | |
| +----------+  +----------+ |
|                            |
|[Today] [Rooms] [Done] [Jar]|
+----------------------------+
```

- **Nothing is missing on a small screen.** The admin view works on a phone too: forms are a single column, lists are cards instead of wide tables, and statistics are simple bars.
- **The Done button stays reachable** when the on-screen keyboard is open for a note.
- **Sizes follow the device's own text-size setting.**
- **Browser floor.** The styling tool needs a reasonably recent browser: Chrome 111, Safari 16.4 or Firefox 128, or newer. Current phones are fine. An old tablet reused as a wall panel may be below it, for example an iPad that stopped at iPadOS 15, so this is worth checking before choosing one.
- **Checked on real devices in every milestone:** a small phone, a tablet and a PC.

## 4. Languages

- **Czech is the default; English ships alongside it.** Another language is added by adding one translation file.
- **Chosen per device.** The wall panel can stay Czech while a phone shows English. A device shows Czech until someone changes it there; the browser's own language preference is ignored.
- **Second-language line.** A device can show each task and room name in a second language, in smaller type under the main one. It is off at first and meant for later, when the kids start learning English. The speaker button can then read either line.

  ```
  +--------------+
  |  [picture]   |
  |    Zalít     |
  |   květiny    |    main language, large
  |  Water the   |
  |    plants    |    second language, small
  +--------------+
  ```

- **Task, room and goal names are stored per language.** Only the default language is required. An empty one falls back to the default.
- **Starter catalogue.** Common household tasks and rooms come with a picture and a name in every shipped language. Adding a task or a room usually means picking a card from the catalogue; the names are already filled in and can be changed.
- Dates, weekday names and plural forms follow the language. Czech has three plural forms (1 úkol, 2 úkoly, 5 úkolů), which Django's translation system handles.
- Code, URL paths, commit messages and documentation are in English.

## 5. Tasks and repetition

Two things exist internally. A **task** is the definition (what, which picture, how often) together with one date: the day its next card appears. A **completion** is the record written when a card is done. A card on the Today screen is simply a task whose date has arrived.

### Repeat options in version 1

| Repeat | Settings | Example |
|---|---|---|
| Once | a date | Take the parcel to the post office |
| Every N days | N (1 means daily) | Load the dishwasher |
| Weekly | which weekdays, every N weeks | Vacuum on Wednesday and Saturday; bins every second Tuesday |
| Monthly | day of the month, every N months | Clean the fridge on the 1st |

### Rules

1. A card appears on its scheduled day, at midnight household time, and **waits until someone does it**. The date means "appears on". It is not a deadline.
2. **At most one open card per task.** If Monday's "Water the plants" is still open on Tuesday, no second card is added. Coming back from a holiday shows one card per task, not a pile.
3. **Doing a card today covers today.** The next card appears on the next scheduled day after today, even if the card had been waiting since last week.
4. A task can be marked "only makes sense on the day" (putting the bins out). Its card disappears quietly at the end of the day if nobody did it. No penalty, and no record of it.
5. A task can carry faces (it is meant for one or more people) or none (anyone). The faces are a hint, not a lock: anyone may do the task, and the archive records who really did.
6. Adults can skip a card ("not needed this time"). The task moves on to its next day.
7. Editing a task changes future cards only; a card that is already waiting stays. Deleting a task deactivates it, so the archive stays intact.
8. A monthly task set to the 31st appears on the last day of shorter months.
9. Each task has an effort size, small, medium or big, worth 1, 2 or 3 points for the jar.
10. A task can belong to one room, or to none. The room decides where the card shows on the Rooms screen. It changes nothing about when the card appears.

### How repetition works inside

Nothing is created in advance and nothing runs on a timer.

- **Each task keeps one date:** the day its next card appears.
- **The Today screen is a query:** every active task whose date is today or earlier, oldest date first. For a day-only task the date must be exactly today.
- **Done** writes a completion record (who, when, note, photo, points) and moves the task's date to the next scheduled day after today. A one-time task has no next day and leaves the queue for good.
- **Skip** moves the date the same way and writes nothing.
- **Undo** removes the completion record and puts the date back.
- **The future is calculated, never stored.** One function answers "what is the next scheduled day after this one" from the repeat settings. A preview of the coming week would call it when the page opens.

Example, "Vacuum" on Wednesdays and Saturdays:

| Day | What happens | The task's date |
|---|---|---|
| Wednesday | The card appears | Wednesday |
| Thursday | Nobody did it; still one card, labelled "since Wednesday" | Wednesday |
| Friday | Done: a completion is recorded for Wednesday's card | Moves to Saturday |
| Saturday | The card appears again | Saturday |

Had it been done on Saturday instead, the date would move to the following Wednesday: one vacuuming covers both cards.

"One open card per task" needs no checking, because a task has only one date. A server that was off for a week needs no catching up: the dates are simply in the past and the cards are waiting.

The only step that runs by itself is a small daily housekeeping on the first request of each day. It moves day-only tasks whose day has passed on to their next day, and writes the database snapshot. A real scheduler is added only when timed reminders need one.

### Why this model

There are three usual ways to store repeating things:

| Way | How it works | Where it fits | Why not here |
|---|---|---|---|
| Create ahead | A scheduled job creates a record for each coming occurrence, for example a week ahead | Planning tools, where each future item is assigned or edited on its own | It needs a job that must not fail, and every change of the rule means cleaning up records already created |
| Calculate on read | Only the rule is stored. Occurrences are calculated for whatever period is shown, and records exist only for exceptions | Calendars | "Is last Monday's card still open?" has to be worked out again on every read, and becomes ambiguous once the rule was edited |
| **One live date** (chosen) | The rule plus the date of the next occurrence. A record is written on completion, and the date moves on | To-do and chore lists | — |

What the chosen model gives up: changing one single future card on its own (for example giving only this Saturday's vacuuming to someone else), and any record of cards that were skipped or missed. The first is not needed here; the second is intended.

### Later candidates

"N days after it was last done" as a repeat type, taking turns (the face rotates), several times a day, "I did something extra" for unplanned help, and tasks started by Home Assistant (washing machine finished, so "Hang the laundry" appears). Most of these only change how a task's date moves on, so the model already has room for them.

## 6. Family jar, thanks and statistics

### Why not points per person

Research on motivation is fairly consistent here. When people get an expected, tangible reward for doing a task, their own interest in the task tends to drop once the reward stops (the "overjustification effect": Lepper, Greene & Nisbett 1973; meta-analysis by Deci, Koestner & Ryan 1999). Praise and unexpected rewards do not have that effect. What keeps motivation alive is choosing for yourself, feeling capable, and feeling part of the group (self-determination theory). The design leans on those three and keeps the reward shared, modest and social.

### The design

- **One jar.** Every finished task drops its effort points into a single family jar. A task done together counts once: the task fills the jar, not the person.
- **Goals are shared experiences.** Adults set goals with a picture and a size, such as "Pizza night, 150". One goal is active at a time. When the jar is full, every screen celebrates, and the goal waits in a "to celebrate" list until an adult ticks it off, so the pizza night really happens. The jar then starts on the next goal, and points beyond the goal carry over.
- **Goals have no deadline.** The jar only fills. A goal cannot be missed, so nobody can be blamed for missing it.
- **Thanks.** Anyone can put a heart on a finished task. It is worth no points, because it comes from a person and not from the system.
- **Family counter.** An all-time number, "together we have done 1,240 things for our home", which only grows. It can drive a purely decorative family level.
- **The jar is drawn, not counted.** For small kids it is a jar that visibly fills, with the goal as a picture. Numbers are small and secondary.
- **Children see no personal numbers,** not even their own.
- **Statistics are in the admin view only.** Every adult sees the numbers of every person, kids included: tasks and effort per week and month, and who usually does what. People are listed in a fixed order, with no ranking and no "winner". A task done together counts fully for each person who took part.
- **Rewards can be switched off** in the settings. The app is complete without them.

### What can go wrong

| Risk | Answer |
|---|---|
| One person does little and enjoys the treat anyway | Adults see it in the statistics and talk about it. The app does not police it. |
| Kids start asking "what do I get?" | Keep treats modest and occasional, celebrate the doing, and switch rewards off if it tips over. |
| Someone marks a task they did not do | Adults can undo. Photos are available. A shared jar gives little reason to cheat. |

### Later candidates

Wishes (kids propose goals with a picture), each person's own private view when the kids are older, skill badges such as "plant carer".

## 7. Architecture

The server builds the pages. The browser shows them and asks the server for small pieces when something changes. There is no separate frontend application.

```
 Phone, laptop or wall panel (a browser)
        |  HTTP on the home network: pages, page fragments, photos
        v
 +--------------------------- one container ----------------------------+
 |  Gunicorn -> Django                                                  |
 |    pages and fragments   Django views and templates                  |
 |    /admin/               Django admin, owner only                    |
 |    /media/...            photos, served to trusted devices only      |
 |    /static/...           CSS, scripts, pictures, fonts, sounds       |
 +----------------+-----------------------------------------------------+
                  v
        /data   one folder, kept by the host
          db.sqlite3
          media/      photos, own task pictures, faces
          backups/    daily database snapshots
```

| Layer | Choice | Why |
|---|---|---|
| Backend and pages | Python 3.13, Django 6.1, then 6.2 when it is released | The maintainer already knows Django. Small reusable template pieces ("partials") are built in since 6.0. 6.2 is expected in April 2027 and, by Django's pattern, is the next long-term-support release. |
| Updating parts of a page | htmx | Removes a finished card, opens the Done sheet and refreshes the queue without reloading the page. One small script file, no build step. |
| Behaviour inside a page | Alpine.js | For things that need no server: picking several faces, the PIN pad, the photo preview. One small script file. |
| Styling | Tailwind CSS, built by its standalone program | A modern look, with sizes and colours defined in one place. No Node.js is needed. |
| Database | SQLite in WAL mode | The load is a few writes a day. One file is easy to back up. |
| Languages | Django's translation system | Mature, and it handles Czech plural forms. |
| Images | Pillow | Shrink, make thumbnails, remove location data. |
| Serving | Gunicorn and WhiteNoise | No separate web server such as nginx is needed. |
| Tooling | uv, Ruff, pytest; Playwright for a few end-to-end checks later | All Python, and all of it runs on Windows. |

Points that follow from this:

- **One language.** There is no JavaScript toolchain: no Node.js, no npm, no bundler. htmx and Alpine.js are two files stored in the repository at fixed versions.
- **The look comes from CSS, not from the framework.** Tailwind, CSS animation and the browser's own dialog element give the same app-like result a JavaScript framework would here.
- **Rules live in one place.** Pages contain no business logic. When a card appears and how the jar fills are plain Python functions.
- Screens stay current by asking for the card list again every 30 seconds. Only what changed is redrawn. No WebSockets.
- Timestamps are stored in UTC. "Which day is it" uses the household time zone, and cards are keyed by the local date, so daylight saving changes cannot duplicate or lose a card.
- One installation serves one household. A neighbour runs their own copy.

What this choice gives up, knowingly:

- **No JSON API in version 1.** A native phone app could not be built without adding one. Because the rules are plain functions, an API can be put on top later without rewriting them. Home Assistant integration would need only a couple of small read-only addresses.
- **No use without a connection to the server.** Acceptable for an app that is used at home.

The road to a phone app: (1) a browser shortcut on the home screen works from the first day; (2) the same pages become an installable app (PWA) once HTTPS is set up; (3) a native Android app only if that is still not enough, and that is the moment an API gets added.

## 8. Data model

| Table | Fields | Notes |
|---|---|---|
| **User** | display name, role (adult or child), face (photo, or the initial on a colour), PIN (hashed; required for adults), active | A custom Django user model from the first migration, because Django makes it hard to switch later |
| **Device** | name, kind (shared or personal), owner (personal only), language, second language, "do not ask for PIN" (adult's own device), token (hashed), last seen, active | "Kitchen panel", "Dad's phone". The kind, owner and language fields arrive with milestone 2; until then every device asks who did a task |
| **PinLock** | wrong PINs in a row, paused until | Always exactly one row; see section 13 |
| **Room** | names (one per language), picture (built-in key or own photo), position, active | Any place in or around the home; the garden and the garage count too |
| **Task** | names (one per language), picture (built-in key or uploaded image), hint, room (optional), effort (1–3), repeat type, interval, weekdays, day of month, start date, end date, faces (many users; empty means anyone), day-only switch, active, **next card date** | The definition, plus the one date that says when its next card appears |
| **Completion** | task, card date (the day the card had appeared), done at, done by (many users), recorded on (device), note, points | Written when a card is done. Points are copied from the task at that moment |
| **Photo** | completion, image, thumbnail, created at | None or several per completion |
| **Goal** | names (one per language), picture, target points, position, status (queued, active, reached), reached at, celebrated at | Jar goals |
| **Thanks** | completion, from user | One per person per completion |
| **HouseholdSettings** | family name, rewards on/off, sounds on/off, last housekeeping date | Always exactly one row. The time zone comes from the host, and the languages from the app itself |

Constraints and derived values:

- There is no table of open cards. A card is a task whose next card date has arrived.
- A completion is unique per task and card date. Two people tapping Done on the same card at the same moment therefore produce one record, and the second tap is told the card is already done.
- Jar progress is calculated, not stored: all points ever earned, minus the targets of goals already reached. An undo therefore stays correct without extra bookkeeping.
- Statistics are calculated from completions. There is no separate points ledger.
- The starter catalogue is not a table. It is a data file in the repository, so its translations are maintained with the other texts.
- A room can be removed at any time. Its tasks simply have no room afterwards, and the archive is not affected.

## 9. Pages and actions

Addresses are English and stay the same in every language. Only the visible text is translated. In the card addresses, `<id>` is the task's number, because a task has at most one card.

| Address | What it is | Who |
|---|---|---|
| `/` | Today: the queue | Trusted device |
| `/cards/` | The card grid as a fragment, fetched again every 30 seconds | Trusted device |
| `/cards/<id>/done/` | Opens the Done sheet; submitting it marks the card done (who, note, photo) | Trusted device |
| `/cards/<id>/undo/` | Undo | Anyone within 10 seconds, later the admin view |
| `/cards/<id>/thanks/` | Add or remove a heart | Trusted device |
| `/rooms/` | The rooms, each with what waits there | Trusted device |
| `/rooms/<id>/` | The waiting cards of one room; `/rooms/elsewhere/` for tasks without a room | Trusted device |
| `/done/` | Archive; older days load as you scroll | Trusted device |
| `/jar/` | The jar and its goals | Trusted device |
| `/trust/` | PIN screen for a device that is not trusted yet | Anyone |
| `/switch/` | Enter or leave the admin view (face and PIN) | Adults |
| `/manage/…` | Admin view: tasks, rooms, people, goals, statistics, queue, archive, devices, settings | Adults in the admin view |
| `/setup/` | First run | Only until the first adult exists |
| `/health/` | Health check for the host | Anyone |
| `/admin/` | Django admin | Owner |

## 10. Hosting and deployment

### 10.1 Containers in four sentences

A container image is the app packed together with everything it needs: Python, the libraries, the styles and the pictures. The same image runs unchanged on a Raspberry Pi, a NAS, a mini PC or a neighbour's machine. GitHub builds the image on every release, for Intel/AMD and for 64-bit ARM, and stores it in the GitHub Container Registry, so **Docker is not needed on the Windows development PC**. The host only needs to know which image to run, on which port, and where `/data` lives.

An update is: fetch the new image, restart. The data is not touched, because it lives outside the container.

### 10.2 Hosts considered

| Host | Verdict | Why |
|---|---|---|
| **Raspberry Pi running Home Assistant OS** (reference: Pi 4 with 2 GB) | **Chosen** | Home Assistant OS does not allow installing ordinary programs, but it runs **apps** (called "add-ons" until [release 2026.2](https://www.home-assistant.io/blog/2026/02/04/release-20262/)), and an app is a container that Home Assistant manages. No new hardware is needed, and installing, updating and backing up happen on the Home Assistant screen. The price: the task manager is down whenever that box is. |
| **Entry-level Synology NAS** (for example DS220j with 512 MB) | Stores the backups; not the host | Synology offers [Container Manager](https://www.synology.com/releaseNote/ContainerManager) for this model on DSM 7.2 or newer, but 512 MB is already tight for the NAS itself, and the app needs roughly 150–250 MB. |
| **Low-power x86 mini PC** (Celeron J1900 class) | Fallback and test machine | Debian and Docker run this easily. It would be a third device that is always on (about 10–15 W, around 100 kWh a year) with an operating system to keep updated. |
| **Any other Docker host** | Supported | For people without Home Assistant, through the example `compose.yml`. |

### 10.3 Running as a Home Assistant app

The repository doubles as a [Home Assistant app repository](https://contributors.home-assistant.io/apps/guides/repository/): a `repository.yaml` at the root, and one folder with a [`config.yaml`](https://contributors.home-assistant.io/apps/reference/configuration/) that describes the app (name, version, processor types, image address, port, backup behaviour).

- **Install.** In Home Assistant: Settings > Apps > Install app > menu > Repositories, paste the GitHub address, then install blabtodo and start it.
- **Image.** Home Assistant downloads the image that GitHub built. Nothing is compiled on the Pi. The image tag must equal `version` in `config.yaml`, so a [release](https://contributors.home-assistant.io/apps/guides/publishing/) pushes the image first and changes the version second. The image takes the repository's visibility, so a public repository gives a public image.
- **Data.** Home Assistant gives each app a private `/data` folder that survives updates and is part of Home Assistant backups. The image keeps everything there.
- **Address.** The app listens on its own port, for example `http://homeassistant.local:8000`. It listens on IPv4 and on IPv6: such a name usually resolves to an IPv6 address first, and Home Assistant gives its containers IPv6 addresses. It is not shown inside the Home Assistant sidebar at first: that would put it behind the Home Assistant login, which the wall panel and the kids should not need.
- **Updates.** After a release Home Assistant shows "update available", and one tap installs it.
- **Trying unreleased versions.** Copy the app folder into Home Assistant's `local_apps` folder through the Samba or SSH app ([testing guide](https://contributors.home-assistant.io/apps/guides/testing/)).

One caution: Home Assistant searches the whole repository for app folders, so no other file in it may be called `config.yaml`, `config.yml` or `config.json`.

### 10.4 Network

- Home network only.
- No port forwarding on the router, ever. If access from outside is wanted one day, the answer is a VPN, not a public address.
- Version 1 uses plain HTTP inside the home network. A home-screen shortcut and the phone camera both work that way.
- HTTPS is needed only for the installable phone app (milestone 5). The usual way on a home network is a reverse proxy with a real certificate for a name that points to the local address. Both Home Assistant and the NAS can provide one. That decision waits until then.

### 10.5 Backup and restore

- Everything lives in `/data`: the database, the photos and the snapshots.
- **Home Assistant backups include the app.** The app is configured for "cold" backup, so Home Assistant stops it for the few seconds the backup takes, and the database copy is always consistent.
- **The NAS keeps the copies.** Home Assistant can use a shared folder on the NAS as a backup location, so backups do not stay on the Pi's own storage.
- Daily housekeeping also writes a database snapshot into `/data/backups` and keeps the last 14. A snapshot is taken before every database migration too. These cover mistakes rather than disk failures.
- Restore: restore the Home Assistant backup, or on other hosts stop the container, put the folder back and start it. The restore is rehearsed once in milestone 0.
- The database must sit on the host's own storage, not on a network share. SQLite's file locking is unreliable over a network.
- Every backup contains all photos. When the photo folder passes a couple of gigabytes, either move the photos to a NAS share that Home Assistant mounts, or add a rule that removes old photos.

### 10.6 First run and updates

- No settings are required to start. A first-run screen asks for the first adult: a name, a PIN, and a password for the management pages. The time zone comes from the host. The secret key is generated and kept in `/data`.
- Optional settings: allowed host names, port, time zone.
- Images carry version numbers such as `1.2.0`. Database migrations run automatically at start, after the snapshot.

## 11. Repository layout

One repository holds everything: the app, its Home Assistant packaging and the documentation.

```
blabtodo/
├── README.md                 what it is, how to install, screenshots with invented data
├── LICENSE                   MIT
├── CREDITS.md                sources and licences of pictures, fonts, sounds, htmx, Alpine.js
├── repository.yaml           makes this repository a Home Assistant app repository
├── Dockerfile                builds the single image
├── compose.yml               example for Docker hosts other than Home Assistant
├── pyproject.toml            dependencies (uv), with uv.lock
├── manage.py
├── .github/workflows/
│   ├── ci.yml                checks and tests on every push and pull request
│   └── release.yml           on a version tag: build the image for amd64 and arm64, publish it
├── docs/
│   ├── design.md             this document
│   ├── development.md        running it on a PC, tests, translations, releasing
│   └── deploy/               home-assistant.md, docker.md
├── ha-app/                   the Home Assistant app definition
│   ├── config.yaml           name, version, image, port, backup behaviour
│   └── DOCS.md, CHANGELOG.md, icon.png, logo.png, translations/
├── config/                   Django settings.py, urls.py, wsgi.py; settings come from the environment
├── people/                   User, Device, PIN, trusting a device, the user/admin switch
├── tasks/                    Task, Room, Completion, Photo, repeat rules, Today, Rooms, Done, archive, catalogue
├── jar/                      Goal, Thanks, jar progress, statistics
├── household/                settings row, first-run setup, backup command, health check
├── templates/                base layout and shared pieces: card, face, sheet, PIN pad
├── styles/app.css            the Tailwind input file: sizes, colours, type scale
├── static/
│   ├── vendor/               htmx and Alpine.js at fixed versions
│   ├── js/                   own small scripts: photo, celebrate, speak
│   ├── pictures/             built-in task pictures (SVG)
│   ├── fonts/
│   └── sounds/
├── locale/                   translations: cs (English is the language of the code and needs none)
├── tools/                    small helper scripts for development
└── tests/                    mirrors the apps; the repeat rules get the most tests
```

`people`, `tasks`, `jar` and `household` are Django apps. Each keeps the templates for its own screens in its own `templates/` folder.

Two conventions. The rules (when a card appears, how the jar fills) live in plain functions that can be tested without a web request. The views stay thin and only translate between a request and those functions.

Milestone 0 created everything above except `tasks/` and `jar/`, which arrive with their milestones, and the folders for own scripts, pictures, fonts and sounds, which appear when the first file does.

## 12. Development workflow and GitHub

- **Branches.** `main` always works. Changes go through short branches and pull requests, even when working alone, because that is where the checks run.
- **Checks on every push** (GitHub Actions): Ruff, pytest, a check that no database migration is missing, a check that every text has a Czech translation, Django's deployment checks, and a build and start of the container image.
- **Release.** Pushing a tag such as `v1.2.0` builds the image for both processor types and publishes it to the GitHub Container Registry. The version in `ha-app/config.yaml` is changed after that.
- **Daily development on Windows needs only uv,** which brings the right Python. Django's development server runs the whole app. No Docker, no Node.js. The steps are in [development.md](development.md).
- **Compiled translations are kept in the repository.** Windows has no GNU gettext, so a small Python script compiles them, and installing the app needs no translation tools.
- **Where tests matter most.** The repeat rules, above all the one function that finds the next scheduled day, because date arithmetic is where the bugs are: month ends, leap years, every-second-week counting, daylight saving changes, the change of day at midnight. And the permissions: child, adult, user view, admin view, untrusted device.

### A public repository

- **Nothing personal goes in.** No real names, faces, photos, home network addresses, or screenshots with real data. Examples, tests and screenshots use an invented family.
- **No secrets.** The `/data` folder and `.env` files are ignored by Git from the first commit. An `.env.example` shows the setting names with made-up values. GitHub's secret scanning and push protection stay on.
- **Commit email.** Every commit carries its author's email address, and in a public repository anyone can read it. Before the first commit, set Git to GitHub's private `noreply` address, and switch on "Keep my email addresses private" and "Block command line pushes that expose my email" in GitHub's email settings.
- **Licence.** MIT: short, permissive, and the usual choice for small tools. The copyright line can name "the blabtodo authors" instead of a person.
- **Other people's work keeps its licence.** `CREDITS.md` lists the source and licence of every picture, font and sound.
- **The published image contains code and built-in pictures only,** never data.

## 13. Security and privacy

- The app is for the home network. An untrusted device sees only the "ask an adult" PIN screen, without names or faces.
- Wrong PINs are counted. After five in a row, PIN entry pauses for a minute, and the pause doubles with each further miss, up to an hour. The pause is for the whole household: behind the container's network all devices can look alike, so it cannot be kept per device. Devices that are already allowed keep working during it.
- PINs are stored hashed, with less hashing work than passwords. A PIN is at most eight digits, so what protects it is the pause, not the hash, and a Raspberry Pi should not keep people waiting at the PIN pad.
- The server answers only to home-network addresses, with no configuration needed: IP addresses that are not public, single-word names such as `homeassistant`, and names with a local-only ending such as `.local`. Any other name must be configured. This blocks websites that try to reach home devices through the browser (DNS rebinding).
- Photos are re-encoded on the server, location data is removed, file names are random, and they are served to trusted devices only.
- Django's admin pages need the owner's full password, not a PIN.
- No telemetry and no outside services while running. Scripts, fonts and pictures are bundled, so the app works when the internet is down.

## 14. Roadmap

| Milestone | Contents | Done when |
|---|---|---|
| **0. Skeleton** | Public repository, tooling, checks, a styled "hello" page in Czech and English that fits a phone, a tablet and a PC, the image built by GitHub, installed on the Pi as a Home Assistant app, backups going to the NAS, memory use measured | The page opens from a phone on home Wi-Fi, and a backup has been restored once |
| **1. Core loop** | People, trusted devices, tasks and rooms through Django admin, repeat rules, Today, Done (who and note), archive. The Today screen is shown with both picture sets and the font candidates, to choose from | The family can use it for a week, on a phone and on a PC |
| **2. Family-ready** | Photos, undo, the Rooms screen, the admin view with its switch, task and room editors with catalogue, picture picker and own photos, face filter, shared and personal devices | Nobody needs Django admin for daily use |
| **3. Jar** | Two or three drafts of the jar's look to choose from, effort points, goals, celebration, thanks, statistics | The first goal has been celebrated |
| **4. Kids and panel** | Sounds and animation, read-aloud, second-language line, panel comforts such as returning to Today when idle and dimming at night | A child can mark their own task without help |
| **5. Installable app** | HTTPS, installable PWA | It sits on the phone like an app |
| **Later** | Home Assistant link (sensors, notifications, tasks started by events), the repeat and reward candidates from sections 5 and 6, push notifications, an API and a native app if ever needed | |

Milestone 0 comes first on purpose. Containers and Home Assistant packaging are the unfamiliar part, so they are tried while the app is still trivial.

Milestone 1 is delivered as three releases, each usable on its own: 0.2 with people and allowed devices, 0.3 with tasks, rooms, Today and Done, and 0.4 with the archive and the picture and font drafts.

## 15. Risks to watch

- **Memory on the Pi.** Low risk. The reference Pi 4 with 2 GB idles at about 45% memory and 2% CPU with Home Assistant running, which leaves roughly 1 GB free, and the app needs about 150–250 MB. Milestone 0 confirms it with a measurement.
- **The SD card.** SD cards wear out, mostly from Home Assistant's own constant writing, and tend to fail without warning. This app adds almost no writing. The backups on the NAS are the protection; an SSD is the lasting fix.
- **Date arithmetic.** Small mistakes show up months later. This is covered by tests written before the screens.
- **HTTPS on a home network** is fiddly. It is kept out of the way until milestone 5.
- **Feature creep.** Every "later candidate" is reasonable alone. Principle 1 is the filter.
- **Pictures.** The built-in set decides how the app feels to a child, and each source has licence terms to respect.
- **The limit of server-built pages.** If one screen ever needs heavy behaviour in the browser, that screen gets a richer script. The rest stays as it is.

## 16. Decision log

| # | Decision | Why | Instead of |
|---|---|---|---|
| 1 | Pages built on the server: Django templates with htmx and Alpine.js | One language and one toolchain, both known to the maintainer; the app is about six screens of cards and forms; no Node.js; light on old tablets | React with a REST API: more room for rich interaction and a ready API for a native app, at the price of a second toolchain, roughly twice the code, and upkeep in an unfamiliar stack. Revisit if a native app or offline use becomes a real need |
| 2 | SQLite in WAL mode | Minimal load; a backup is a file copy | PostgreSQL: a second container and no benefit here |
| 3 | One image for amd64 and arm64, built by GitHub | The same package runs on every host; no Docker on the development PC | Installing Python and the app directly on the host |
| 4 | Host: a Home Assistant app on the Pi; the NAS stores the backups | No new hardware; managed from the Home Assistant screen; the NAS has too little memory to host | The NAS as host; a third always-on box |
| 5 | No background worker and no scheduled job. The queue is a query, and a small housekeeping step runs on the first request of the day | Nothing extra to run or to break | Celery, cron, a second container |
| 6 | Refresh every 30 seconds | Simple and enough for a household | WebSockets |
| 7 | A card "appears on" a day, a task has at most one open card, and doing a card today covers today | No piles, no overdue shame | Deadlines and one card per missed day |
| 8 | A small repeat model with four types | The task editor fits on one screen | Full calendar recurrence rules |
| 9 | Trusted devices and picking by face | Small kids cannot type; a wall panel needs no login | A user name and password per person |
| 10 | Two roles, adult and child; two views, user and admin, with a PIN switch | Adults see the same simple screens as everyone until they choose to manage | Separate admin accounts; edit buttons on the everyday screens |
| 11 | One shared jar; statistics for adults only, all people visible to every adult | Cooperative by construction; the family's choice | Personal credits, rankings |
| 12 | A completion records a group of people, and its points count once | "Together" is a normal case, not an exception | One doer plus helpers |
| 13 | One household per installation | A simpler data model and simpler permissions | Multi-household support |
| 14 | Home network only; plain HTTP in version 1 | PIN login is acceptable there; nothing is exposed | Public access |
| 15 | Czech by default, English alongside; language per device; task names stored per language | The kids can meet English on the same cards later; a neighbour can add their language | A single fixed language |
| 16 | Custom user model in the first migration | Django cannot switch painlessly afterwards | Django's default user |
| 17 | Django 6.1 now, 6.2 when released, then long-term-support releases only | Template partials are built in; the step to the long-term release is small | Starting on 5.2 LTS and making a bigger jump before April 2028 |
| 18 | Task pictures from a built-in set plus own photos | Pre-readers need pictures; appliances such as a vacuum cleaner or dishwasher are missing from emoji sets | An icon font only |
| 19 | Public repository, MIT licence | Family and neighbours install by address; Home Assistant can read it without a password | A private repository |
| 20 | "Cold" Home Assistant backup | A consistent database copy with no extra code | Backup while running, with a snapshot command first |
| 21 | A repeating task keeps one date, the day of its next card. A record is written only when a card is done | No cards to create ahead; "one open card" holds by construction; a week of downtime needs no catching up | Creating cards ahead with a scheduled job; calculating every occurrence from the rule on each read (see section 5) |
| 22 | One set of screens that adapts to phone, tablet, PC and wall panel, designed for the phone first | Every device in the house can be used; one thing to build and to test | Separate phone and desktop screens; a native app |
| 23 | Rooms: a task belongs to one room or to none, and a Rooms screen sits next to Today | "What needs doing where I am" is how people tidy; a photo of a room is something a pre-reader recognises | A second row of filter buttons on Today; free tags or categories; several rooms per task; floors and room groups |
| 24 | The host check accepts home-network addresses without configuration | An installation works the moment it starts, and outside websites are still refused | A list of allowed names that every installation must fill in; accepting every name |
| 25 | Compiled translations are kept in the repository | No translation tools are needed on Windows or when installing | Compiling them while the image is built |
| 26 | The pause after wrong PINs is for the whole household | Behind the container's network devices cannot be told apart reliably; a household-wide pause is simple and cannot be sidestepped | A pause per device or per address |
| 27 | The time zone comes from the host, not from a setting in the app | Home Assistant already knows it; one question less at first run | A time zone field on the first-run screen |

## 17. Open questions

Nothing here blocks the first milestones. Each item waits until there is something to look at.

1. **Built-in pictures.** Two candidates: Fluent Emoji (MIT licence, colourful, child-friendly, but no household appliances, so a few would be drawn or sourced separately), or Material Symbols on coloured tiles (Apache 2.0 licence, includes appliances, single colour). Postponed: decided in milestone 1, by looking at both on the real Today screen.
2. **Font.** A rounded, very legible one with full Czech letters. Postponed: chosen together with the pictures.
3. **Wall panel.** Android tablet with a kiosk browser, a Pi with a touchscreen, or a Home Assistant dashboard? Undecided, and not needed before milestone 4. Any candidate must meet the browser floor in section 3.7.
4. **The jar's look.** A jar of marbles, a tree, a garden? And what one point is called in Czech. Postponed: decided in milestone 3, from drafts.
