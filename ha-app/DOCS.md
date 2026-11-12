# blabtodo

A home task manager for one family: a shared queue of household tasks that any screen in
the house can show.

This is an early version. It shows a test page that confirms the installation works.

## Opening it

After starting the app, select **Open Web UI**, or open this address on any device in
your home network:

    http://homeassistant.local:8000

If that name does not work on a device, use the IP address of your Home Assistant
instead, for example `http://192.168.1.10:8000`.

The app is not shown inside the Home Assistant sidebar. A wall panel or a child's tablet
should be able to open it without a Home Assistant login.

## Home network only

The app answers only to home-network addresses. Do not forward its port on your router.
For access from outside, use a VPN.

## Your data

Everything the app stores (its database, and later photos) is kept by Home Assistant in
the app's private data folder. It survives updates and is included in Home Assistant
backups. During a backup the app is stopped for a few seconds, so the copy is always
consistent.

Uninstalling the app deletes this data. Make a backup first if you want to keep it.

## Changing the port

On the app's **Configuration** tab, under **Network**, change the host port if 8000 is
already used by something else.

## More

Full documentation and the source code: <https://github.com/JardaPLC/blabtodo>
