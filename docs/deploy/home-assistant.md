# Installing on Home Assistant

For a Home Assistant OS installation, for example on a Raspberry Pi. You do not need to
know anything about Docker: Home Assistant downloads a ready-made image and runs it as
an app. (Apps were called "add-ons" before Home Assistant 2026.2.)

Menu names below are from Home Assistant 2026. They may differ slightly in your version.

## What you need

- Home Assistant OS on a 64-bit device (Raspberry Pi 3 or newer, or a PC).
- About 250 MB of free memory.

## 1. Add the repository

1. In Home Assistant, open **Settings**, then **Apps**, then **Install app**.
2. Open the menu in the top-right corner and select **Repositories**.
3. Enter `https://github.com/JardaPLC/blabtodo` and select **Add**.
4. Close the dialog. If blabtodo does not appear in the list, reload the page.

## 2. Install and start

1. Select **blabtodo**, then **Install**. Home Assistant downloads the image, which
   takes a minute or two.
2. Turn on **Start on boot** and **Watchdog**. The watchdog restarts the app if it ever
   stops answering.
3. Select **Start**.
4. Open the **Log** tab. After a few seconds it should show a line containing
   `Listening at:`.

## 3. Open it

On any device in your home network, open:

    http://homeassistant.local:8000

If that name does not work on a device, use the IP address of your Home Assistant
instead, for example `http://192.168.1.10:8000`.

The **Čeština** and **English** buttons at the top switch the language on that device
only.

If port 8000 is already used by another app, change it on the blabtodo
**Configuration** tab under **Network**.

### The first time: create the first adult

A fresh installation greets you with **Vítejte** (Welcome). Do this on a PC, because the
management pages you will use next are made for one.

1. Enter your name as the family calls you, for example "Táta".
2. Choose a **PIN** of 4 to 8 digits. It is for every day: an adult enters it once on
   each new phone, tablet or PC to allow it.
3. Choose a **password**. It is for the management pages only. Make it longer and harder
   to guess than the PIN.
4. Select **Vytvořit a začít** (Create and start).

The PC you did this on is now an allowed device, and the page shows your face.

### Add the rest of the family

At the bottom of that page, open **Pro dospělé** (For adults), then the **management
pages**, and sign in with the user name shown there and your password. Under **Členové rodiny**
(People) add each family member: a name, whether they are an adult or a child, and
optionally a photo of the face. Adults need a PIN. Children do not.

### Allow the other devices

Open the same address on a phone or a tablet. It asks for a PIN: any adult enters theirs,
once. From then on that device opens blabtodo without asking.

After five wrong PINs in a row, PIN entry pauses for a minute for everyone, and longer
after each further wrong try. An allowed device is listed under **Zařízení** (Devices) in
the management pages, where you can rename it or remove it.

### Add rooms and tasks

Still in the management pages, on a PC:

1. Under **Místnosti** (Rooms), add the rooms of your home. Choosing a picture is enough;
   its name is filled in for you in Czech and English. Give each room a position number:
   rooms are always shown in that order.
2. Under **Úkoly** (Tasks), add your tasks. Again, choosing a picture is enough. Then say
   when it repeats:
   - **Každý den nebo jednou za několik dní** (Every day, or every few days), with
     "every 1" for daily or "every 3" for every third day.
   - **Ve vybrané dny v týdnu** (On chosen days of the week), and tick the days.
   - **V určitý den v měsíci** (On a day of the month), and give the day.
   - **Jednou** (Once): the start date is its day.
3. Optionally give the task a room, a hint (for example where the watering can is), and
   the faces of the people it is meant for.

A task's card appears on its day and waits until someone does it. There is never more
than one card per task, however long it waits.

To stop using a task, untick **používá se** (in use). A task that was never done can also be deleted, for example one added by mistake; once it has been done it can only be switched off, so that the
record of what was done stays whole.

### QR stickers

A task can be put on Today by scanning a sticker, for example one on the cooker hood for
"change the filter". For such a task choose **Jen na vyžádání** (Only when asked for), so
that it never appears by itself.

1. In the management pages, under **Úkoly** (Tasks), tick the tasks, choose **Vytisknout
   QR nálepky** (Print QR stickers) from the action menu, and confirm with the button
   next to it.
2. Print the page, cut out the stickers and put them where the task is done.
3. Scan a sticker with a phone's camera app and open the link. blabtodo asks **Zobrazit
   tento úkol v Dnes?** (Show this task on Today?).

Print the stickers from the address the family uses, because that address is in the
codes. A fixed IP address for the Pi, reserved in your router, is the safest choice. If
the address changes, print the stickers again; each task keeps its code.

The phone must open the link in the browser that was allowed with the PIN. If its camera
app opens a different browser, that browser asks for the PIN once.

### Every day

Open blabtodo on any allowed device. **Dnes** (Today) shows the cards that are waiting,
the oldest first.

- Tap a card, tap the face of whoever did it (several faces if you did it together), and
  tap **Hotovo** (Done).
- A bar with **Vrátit zpět** (Undo) stays for ten seconds, in case the wrong card was
  tapped.
- Tap a face at the top to see only the cards with that face on them.
- The screen refreshes by itself every 30 seconds, so a wall panel follows what happens
  on phones.

What was done is listed under **Hotové úkoly** (Finished tasks) in the management pages.
From there a finished card can also be put back.

### Check a device

**Kontrola zařízení** (Device check), under **Pro dospělé** (For adults) at the bottom of
the first page, shows how a screen will lay out the task cards and whether the page keeps
itself up to date.

## 4. Send backups to a NAS

Home Assistant backups include the blabtodo data. A backup that stays on the same SD card
as Home Assistant protects against mistakes, but not against the card failing. Store
the backups on another device.

On the NAS (the steps are for Synology; other brands are similar):

1. Create a shared folder for the backups, for example `ha-backups`.
2. Create a user that can read and write that folder and nothing else.
3. Make sure the SMB file service is on (**Control Panel**, **File Services**).

In Home Assistant:

1. Open **Settings**, **System**, **Storage**, then **Add network storage**.
2. Give it a name, choose **Backup** as the usage, enter the NAS address, choose
   **Samba/Windows (CIFS)**, and enter the shared folder name and the user from above.
3. Open **Settings**, **System**, **Backups**, then the backup settings.
4. Turn on automatic backups, include apps, and select the NAS as a backup location.

While a backup runs, blabtodo is stopped for a few seconds. That is deliberate: it makes
sure the copy of the database is consistent.

## 5. Rehearse a restore once

A backup you have never restored is only a hope. This takes ten minutes and is worth
doing while the app holds nothing important.

1. Make sure blabtodo is set up and shows your family.
2. In Home Assistant, create a backup now and wait until it is finished. Check that the
   file arrived on the NAS.
3. Open the blabtodo app page, select **Uninstall**, and choose to delete its data too.
4. Install and start blabtodo again, as in step 2 above, and open it. It greets you with
   **Vítejte** again: this is a fresh, empty installation. Do not fill it in.
5. Open **Settings**, **System**, **Backups**, select the backup from step 2, select
   **Restore**, and choose only the blabtodo app.
6. Open blabtodo again. Your family is back, and the device you are using is still
   allowed. The restore works.

## 6. Check memory use

Open the blabtodo app page in Home Assistant. It shows the app's current memory and CPU
use. Expect roughly 70 to 150 MB of memory and almost no CPU. **Settings**,
**System**, **Hardware** shows the totals for the whole device.

## Updating

When a new version is released, Home Assistant shows an update for blabtodo. Select
**Update**. Your data is kept. To be asked less often, turn on **Auto update** on the
app page.

## If something does not work

| What you see | What to do |
|---|---|
| The page does not open | Check that the app is started and look at its **Log** tab. Try the IP address instead of `homeassistant.local`. |
| "blabtodo answers only to home-network addresses" | You opened it under a name the app does not recognise as local. Use the IP address or `homeassistant.local`. |
| Install fails with an image error | The image for this version may not be published yet. Try again in a few minutes. |
| The app keeps restarting | Open the **Log** tab and look at the last lines before the restart. |

## Good to know

- blabtodo is for the home network only. Do not forward its port on your router. For
  access from outside, use a VPN.
- The app is not shown inside the Home Assistant sidebar. A wall panel or a child's
  tablet should be able to open it without a Home Assistant login.
- Uninstalling the app deletes its data unless you choose to keep it.
