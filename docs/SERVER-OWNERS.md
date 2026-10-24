# Note for KCDC server owners: GOG players

*Deutsche Fassung unten.*

Some players run Kingdom Come: Deliverance II from **GOG.com** (not Steam, not Epic). The KCDC client reports an
empty `steamId` and an empty `epicId` for them, because GOG provides neither. If your server resource kicks players
with an empty `connection.steamId` (for example "SteamID64 fehlt. Bitte über Steam verbinden."), GOG players cannot
join, although they are otherwise able to connect, pass the build verification and load your resources.

If you want to admit them:

* The stock gamemode does not require a Steam ID: `whitelist.ts` accepts `name:<nickname>` entries and only compares
  Steam IDs when `connection.steamId !== ""`. With the whitelist on you can add players by name
  (`whitelist add name:<nickname>`).
* Be aware that nicknames can be typed by anyone and are not verified (the file says so too). Anything that has to
  hold against impersonation or ban evasion needs an identity you issue yourself (e.g. a token handed out via your
  Discord, checked against `connection.ticket`).
* Banning by Steam ID will not work for GOG players; plan for another ban key (nickname, IP, your own token).

Whether to admit GOG players is of course your decision. This note is not a request to change your rules.

---

# Hinweis für KCDC-Server-Betreiber: GOG-Spieler

Manche Spieler nutzen Kingdom Come: Deliverance II von **GOG.com** (weder Steam noch Epic). Der KCDC-Client meldet für
sie eine leere `steamId` und eine leere `epicId`, weil GOG keins von beiden liefert. Wenn deine Server-Ressource Spieler
mit leerer `connection.steamId` rauswirft (z. B. „SteamID64 fehlt. Bitte über Steam verbinden.“), kommen GOG-Spieler nicht
hinein, obwohl sie sich verbinden, die Build-Prüfung bestehen und deine Ressourcen laden.

Wenn du sie zulassen möchtest:

* Der Standard-Gamemode verlangt keine Steam-ID: `whitelist.ts` kennt `name:<Spielername>`-Einträge und vergleicht
  Steam-IDs nur, wenn `connection.steamId !== ""`. Mit eingeschalteter Whitelist: `whitelist add name:<Spielername>`.
* Spielernamen kann jeder frei eingeben, sie werden nicht geprüft (steht auch in der Datei). Was gegen Fälschung oder
  Ban-Umgehung halten muss, braucht eine Identität, die du selbst vergibst (z. B. ein Token über euren Discord, geprüft
  gegen `connection.ticket`).
* Bans per Steam-ID greifen bei GOG-Spielern nicht; ein anderer Ban-Schlüssel (Name, IP, eigenes Token) ist nötig.

Ob du GOG-Spieler zulässt, entscheidest du natürlich selbst. Dieser Hinweis ist keine Aufforderung, deine Regeln zu ändern.
