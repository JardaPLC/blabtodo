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
4. Open the **Log** tab. After a few seconds it should end with a line containing
   `Listening at: http://0.0.0.0:8000`.

## 3. Open it

On any device in your home network, open:

    http://homeassistant.local:8000

If that name does not work on a device, use the IP address of your Home Assistant
instead, for example `http://192.168.1.10:8000`.

You should see a page saying "Funguje to!". Try it on a phone, a tablet and a PC:

- The **Čeština** and **English** buttons switch the language on that device only.
- **Screen check** shows how many task cards fit in one row on that screen.
- **Live connection** shows the server's clock. It refreshes by itself every 30 seconds.

If port 8000 is already used by another app, change it on the blabtodo
**Configuration** tab under **Network**.

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

1. Open blabtodo, select **Zobrazit technické podrobnosti** (Show technical details),
   and write down the value under **Instalace** (Installation). It is a fingerprint of
   this installation's data.
2. In Home Assistant, create a backup now and wait until it is finished. Check that the
   file arrived on the NAS.
3. Open the blabtodo app page, select **Uninstall**, and choose to delete its data too.
4. Install and start blabtodo again, as in step 2 above. The **Instalace** value is now
   different: this is a fresh, empty installation.
5. Open **Settings**, **System**, **Backups**, select the backup from step 2, select
   **Restore**, and choose only the blabtodo app.
6. Open blabtodo again. The **Instalace** value is the one you wrote down. The restore
   works.

## 6. Check memory use

Open the blabtodo app page in Home Assistant. It shows the app's current memory and CPU
use. Expect somewhere between 100 and 250 MB of memory and almost no CPU. **Settings**,
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
