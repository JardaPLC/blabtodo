# blabtodo

A home task manager for one family: a shared queue of household tasks that any screen in
the house can show.

This is an early version. You can set up your family, rooms and tasks, and mark tasks
done on any allowed device. Tasks are set up in management pages that are made for a PC;
a touch-friendly editor comes later.

## Opening it

After starting the app, select **Open Web UI**, or open this address on any device in
your home network:

    http://homeassistant.local:8000

If that name does not work on a device, use the IP address of your Home Assistant
instead, for example `http://192.168.1.10:8000`.

The app is not shown inside the Home Assistant sidebar. A wall panel or a child's tablet
should be able to open it without a Home Assistant login.

## The first time

A fresh installation greets you with **Vítejte** (Welcome) and asks you to create the
first adult: a name, a PIN of 4 to 8 digits, and a password.

- The **PIN** is for every day. An adult enters it once on each new phone, tablet or PC
  to allow it. After that the device opens the app without asking.
- The **password** is for the management pages, where you add the rest of the family.

Do this on a PC. The page that follows shows a link to the management pages and the user
name to sign in with.

## Home network only

The app answers only to home-network addresses. Do not forward its port on your router.
For access from outside, use a VPN.

## Your data

Everything the app stores (its database and the face photos) is kept by Home Assistant in
the app's private data folder. It survives updates and is included in Home Assistant
backups. During a backup the app is stopped for a few seconds, so the copy is always
consistent.

Uninstalling the app deletes this data. Make a backup first if you want to keep it.

The app also keeps its own copies of the database in the same folder: one per day for
the last two weeks, and one from before each update. They help after a mistake. They do
not replace the Home Assistant backup, because they sit on the same disk.

## Changing the port

On the app's **Configuration** tab, under **Network**, change the host port if 8000 is
already used by something else.

## More

Full documentation and the source code: <https://github.com/JardaPLC/blabtodo>
