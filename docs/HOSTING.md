# Hosting your own KCDC server (so GOG players can join)

*Deutsche Fassung unten.* Not tested end to end: this is compiled from the shipped `README.txt`, the gamemode README
and the strings of `KCDCServer`. Where something is not certain it says so.

## Why host yourself

Public servers decide their own rules. Some kick players whose Steam ID is empty (GOG players). On your own server the
stock gamemode does not require a Steam ID.

## Steps (Windows)

1. **Same release everywhere.** Server and all players must run the same KCDC release (1.7.1 here). GOG players use the
   workaround from this repository on their client.
2. **Build the gamemode** (Node.js 22 or newer; `npm ci` downloads packages from the npm registry). In
   `server\resources\kcdc-gamemode`:
   ```
   npm ci
   npm run build
   ```
   Without the build the server answers no commands (README of the download). The server loads `dist\`.
3. **Start** `server\KCDCServer.exe`. If `server.json` is missing it writes a default one. Options (from `--help` strings):

   | Option | Meaning |
   |---|---|
   | `-c`, `--config` | JSON config file to read |
   | `-h`, `--host` / `-p`, `--port` | networking host / port to bind |
   | `-H`, `--apihost` / `-P`, `--apiport` | HTTP API host / port |
   | `--password` | password players must give; empty lets anyone in |
   | `--maxplayers` | player limit (there is a hard cap in the build) |
   | `-t`, `--server-token` | masterlist push token; the server is only announced when this is set |

   `server.json` keys seen in the binary: `bindHost`, `bindPort`, `webBindHost`, `webBindPort`, `maxPlayers`, `password`,
   and `mod.*` entries such as `mod.navmesh` and `mod.required_dlc`. Unknown `mod.` keys are reported and ignored.
4. **Let players in.**
   * Same PC / LAN: join with Quick Connect `127.0.0.1:<bindPort>` / your LAN address.
   * Over the internet: forward the `bindPort` on your router to the PC and allow `KCDCServer.exe` in the firewall. The
     protocol (UDP/TCP) is not documented in the download; forward what the server start log shows or allow both.
   * Players enter `address:port` under Quick Connect, or you give them a line for `client\files\kcdc\servers.tsv`:
     `name<TAB>host<TAB>port<TAB>optional password`.
5. **Whitelist (optional).** Off by default. Console: `whitelist on`, `whitelist add name:<nickname>`,
   `whitelist add <steamid>`, `whitelist list`. Nicknames are not verified.
6. **Optional:** NPC navigation needs `files/<level>/recast.pak` (game data you must supply) or `mod.navmesh` in
   `server.json`.

## Linux

Same options with `server-linux/KCDCServer` (needs `libnode.so.141` beside it, already there) and the same gamemode build.

## Notes

* Do not run the server from inside the archive; keep the folder structure.
* The masterlist (`masterlist.mafiahub.dev`) only lists servers started with a server token. Without it, share address and
  port directly.

---

# Eigenen KCDC-Server hosten (damit GOG-Spieler beitreten können)

Nicht komplett getestet; zusammengestellt aus der `README.txt`, der Gamemode-README und den Strings von `KCDCServer`.

1. **Überall dieselbe Version.** Server und Spieler brauchen dasselbe KCDC-Release (hier 1.7.1). GOG-Spieler nutzen den
   Workaround aus diesem Repository.
2. **Gamemode bauen** (Node.js 22+; `npm ci` lädt Pakete aus dem npm-Netz). In `server\resources\kcdc-gamemode`:
   `npm ci` und `npm run build`. Ohne Build antwortet der Server auf keine Befehle.
3. **Starten:** `server\KCDCServer.exe`. Fehlt `server.json`, schreibt der Server eine Standarddatei. Optionen: `-c` Config,
   `-h`/`-p` Host/Port, `-H`/`-P` API-Host/-Port, `--password`, `--maxplayers`, `-t` Masterlist-Token. Schlüssel in
   `server.json`: `bindHost`, `bindPort`, `webBindHost`, `webBindPort`, `maxPlayers`, `password`, `mod.*`.
4. **Spieler hereinlassen:** lokal `127.0.0.1:<bindPort>`; übers Internet den `bindPort` im Router weiterleiten und
   `KCDCServer.exe` in der Firewall erlauben (UDP/TCP steht nicht in den Unterlagen - lt. Start-Log oder beides). Spieler
   nutzen „Quick Connect“ mit `Adresse:Port` oder eine Zeile in `client\files\kcdc\servers.tsv`
   (`Name<TAB>Host<TAB>Port<TAB>optional Passwort`).
5. **Whitelist (optional):** standardmäßig aus. Konsole: `whitelist on`, `whitelist add name:<Spielername>`,
   `whitelist add <SteamID>`, `whitelist list`.
6. **Linux:** gleiche Optionen mit `server-linux/KCDCServer`.
7. In der Masterlist erscheint der Server nur mit Server-Token; sonst Adresse und Port direkt weitergeben.
