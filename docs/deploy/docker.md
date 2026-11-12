# Installing on a Docker host

For any machine that runs Docker and is on all day: a NAS with a container app, a mini
PC, a Linux box. If you use Home Assistant OS, follow
[home-assistant.md](home-assistant.md) instead; it is easier.

## What you need

- Docker with the Compose plugin, on a 64-bit Intel/AMD or ARM machine.
- About 250 MB of free memory. On a NAS with 512 MB in total, expect it to be slow.

## Install

1. Create a folder for blabtodo, for example `blabtodo`, on the machine's own disk.
   Do not use a network share: the database does not work reliably on one.
2. Copy [compose.yml](../../compose.yml) into that folder. Change `TZ` if you are not
   in the Czech time zone.
3. In that folder, run:

   ```
   docker compose up -d
   ```

4. Open `http://<address of the machine>:8000` on any device in your home network.
   You should see a page saying "Funguje to!".

On a Synology NAS with Container Manager: open **Project**, select **Create**, choose
the folder, and paste the contents of `compose.yml`.

## Your data

Everything the app stores is in the `data` folder next to `compose.yml`. To back up:

```
docker compose stop
```

then copy the `data` folder, then:

```
docker compose start
```

Stopping first makes sure the copy of the database is consistent. To restore, stop the
app, put the folder back, and start it.

## Update

```
docker compose pull
docker compose up -d
```

Your data is kept.

## Settings

All settings are optional. Add them under `environment:` in `compose.yml`.

| Setting | Meaning |
|---|---|
| `TZ` | Time zone, for example `Europe/Prague` |
| `BLABTODO_ALLOWED_HOSTS` | Extra names the app should answer to, separated by commas. Home-network IP addresses, single-word names and names ending in `.local` work without it |
| `BLABTODO_TRUSTED_ORIGINS` | Needed only behind an HTTPS reverse proxy, for example `https://tasks.example.org` |

To use another port, change the first number in `"8000:8000"`.

## Good to know

blabtodo is for the home network only. Do not forward its port on your router. For
access from outside, use a VPN.
