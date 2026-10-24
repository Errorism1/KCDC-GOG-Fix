# KCDC mit der GOG-Version von Kingdom Come: Deliverance II

*English version: [README.md](README.md)*

Inoffizieller Workaround, damit **KCDC (Kingdoms Connected) 1.7.1** mit der **GOG**-Version von
Kingdom Come: Deliverance II 1.5.6.0 startet. Ohne ihn stürzt der Client direkt nach dem Laden des
Spielmoduls ab.

> **Stand:** Das Spiel startet, erreicht das KCDC-Hauptmenü, verbindet sich mit Servern, besteht deren
> Build-Prüfung und lädt die Server-Ressourcen. **Server, die eine Steam-ID verlangen, werfen GOG-Spieler raus**
> (siehe [Bekannte Einschränkung](#bekannte-einschränkung-server-die-eine-steam-id-verlangen)); Spielen auf einem
> Server, der Spieler ohne Steam-ID zulässt, ist noch nicht bestätigt. Bitte meldet eure Ergebnisse
> (siehe [Rückmeldung](#rückmeldung)).
>
> **Nur auf einem PC getestet** (Windows 11, Build siehe unten). Auf anderen Systemen oder mit anderem GOG-Build kann es anders sein.
>
> Nicht von den KCDC-/MafiaHub-Entwicklern und nicht mit ihnen verbunden. Nutzung auf eigene Gefahr. Sobald die
> Entwickler offiziell GOG unterstützen, auf deren Version wechseln und diesen Workaround entfernen.
>
> KCDC gehört seinen Autoren; dieses Repository enthält keine Dateien davon. Falls die KCDC-Entwickler wünschen, dass
> dieses Repository geändert oder entfernt wird, geschieht das.

## Das Problem

`KCDCClient.dll` sucht beim Start rund 980 Funktionssignaturen (Byte-Muster) in der `WHGame.dll` des Spiels. Drei
davon gibt es im GOG-Build nicht, weil er etwas anders kompiliert ist als der Steam-Build (andere Befehlswahl und
Registerzuteilung). Der Client prüft nicht, ob die Suche fehlschlug, und liest einen Null-Zeiger:

```
Unhandled exception 0xC0000005 at KCDCClient.dll+0x6AFE7B   (InitClient)
```

## Was der Fix macht

* Erzeugt `KCDCClient_gog.dll` **neben** dem Original und ersetzt diese drei Muster durch die GOG-Varianten.
* Stellt `KCDC_launcher.json` (`mod_dll_name`) auf die neue Datei um.
* Die originale `KCDCClient.dll` bleibt unverändert; der KCDC-Updater meldet deshalb „up-to-date“ und überschreibt
  nichts.
* **Es werden keine veränderten Binärdateien verteilt.** Der Installer baut die Datei aus *deiner eigenen* Kopie und
  läuft nur, wenn diese exakt den SHA-256 von KCDC 1.7.1 hat.

Details: [docs/TECHNICAL.md](docs/TECHNICAL.md) (englisch).

## Getestet mit

| Komponente | Version | SHA-256 |
|---|---|---|
| KCDC-Client | 1.7.1 (`KCDCClient.dll`) | `28949D27AD5FC508B2FAA1FFA430E83A8401445FD3142C1469B936F7A38636FC` |
| Kingdom Come: Deliverance II (GOG) | 1.5.6.0, `Bin\Win64MasterMasterGogPGO`, GOG-Build-ID `59798195747257766` | `KingdomCome.exe`: `2E4C3189F32CC8D2A1A768EAF54754079D3EC90DAC563B392DBD6CAD9EA4E63B` |
| | | `WHGame.dll`: `C59754B925C669B26C46723EB6C19C3217ABA2FAC94A1AD2D8BCC229D9363870` |
| Betriebssystem | Windows 11 | |

Andere GOG-Builds funktionieren eventuell nicht, siehe [Andere Spielversionen](#andere-spielversionen).

## Installation

Voraussetzungen: Windows, PowerShell (die eingebaute reicht), der Download von KCDC 1.7.1.

1. **Archiv entpacken** (nicht einzelne Dateien herauskopieren).
2. **`client\KCDCLauncher.exe` einmal starten.** Der Launcher findet das Spiel nicht über Steam und fragt nach der
   Spiel-EXE. Auswählen:  
   `<dein GOG-Ordner>\Kingdom Come Deliverance II\Bin\Win64MasterMasterGogPGO\KingdomCome.exe`  
   Das Spiel stürzt ab oder schließt sich - das ist erwartet. Danach existiert `client\KCDC_launcher.json`.
3. **Alles schließen** (Launcher, Spiel).
4. **Installer ausführen**, in einem PowerShell-Fenster in diesem Ordner (Pfad zum KCDC-`client`-Ordner anpassen):

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install.ps1 -ClientDir "D:\Games\KCDC-1.7.1\client"
   ```

   Erwartete Ausgabe: `Created KCDCClient_gog.dll (SHA-256 verified).` und `Updated KCDC_launcher.json`.
5. **`client\KCDCLauncher.exe` wie gewohnt starten.** Der Updater sollte „up-to-date“ melden, das Spiel das Hauptmenü
   mit dem KCDC-Serverbrowser erreichen.

Server stehen in `client\files\kcdc\servers.tsv` (Name, Host, Port, optional Passwort, tabgetrennt).

Ohne PowerShell oder mit Python: `python tools\kcdc_gog_patch.py <KCDCClient.dll> <KCDCClient_gog.dll>` und in
`KCDC_launcher.json` von Hand `"mod_dll_name":"KCDCClient_gog.dll"` setzen.

## Deinstallation

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1 -ClientDir "D:\Games\KCDC-1.7.1\client" -RemoveDll
```

Setzt `mod_dll_name` zurück auf `KCDCClient.dll` (Sicherung der ursprünglichen Config: `KCDC_launcher.json.bak`).

## Bekannte Einschränkung: Server, die eine Steam-ID verlangen

Manche Server werfen dich direkt nach dem Laden mit einer Meldung wie dieser hinaus:

```
You have been kicked. Reason: SteamID64 fehlt. Bitte über Steam verbinden.
```

Das ist **kein** Fehler des Clients und wird von diesem Workaround absichtlich nicht umgangen. Der Text gehört nicht
zum Standard-Gamemode von KCDC, sondern kommt aus einem Skript des jeweiligen Servers. KCDC meldet dem Server eine
Steam-ID oder eine Epic-ID; die GOG-Version hat keins von beiden (GOG ist nicht Epic), das Feld ist also leer. Eine ID
vorzutäuschen würde die Zugangskontrolle des Servers umgehen - das macht dieses Projekt nicht.

Was du tun kannst:

* Server wählen, die keine Steam-ID verlangen (der Standard-Gamemode erlaubt eine leere ID).
* Den Server-Betreiber bitten, GOG-Spieler zuzulassen, z. B. mit einem Namenseintrag in der Whitelist
  (`whitelist add name:<Spielername>`) oder ohne die Prüfung. Ein fertiger Text für Betreiber steht in
  [docs/SERVER-OWNERS.md](docs/SERVER-OWNERS.md).
* Die KCDC-Entwickler um eine GOG-Identität bitten (siehe [docs/BUGREPORT.txt](docs/BUGREPORT.txt), Teil 2).

## Nach einem KCDC-Update

Der Updater aktualisiert nur die originale `KCDCClient.dll`. Die `_gog`-Kopie wird **nicht** aktualisiert und passt
dann nicht mehr zur neuen Server-/Launcher-Version. Nach einem Update:

1. `uninstall.ps1` (ohne `-RemoveDll`) ausführen oder `mod_dll_name` auf `KCDCClient.dll` zurücksetzen und testen, ob
   die neue Version GOG schon kann.
2. Stürzt sie noch ab, braucht dieser Fix ein Update für die neue Version
   ([docs/TECHNICAL.md](docs/TECHNICAL.md#adapting-to-a-new-kcdc-version)). Der Installer verweigert den Dienst bei
   einer anderen `KCDCClient.dll`.

## Andere Spielversionen

Prüfer gegen die eigene `WHGame.dll` laufen lassen (braucht `pip install pefile unicorn`):

```powershell
python tools\find_missing_patterns.py "<KCDC>\client\KCDCClient.dll" "<GOG>\Bin\Win64MasterMasterGogPGO\WHGame.dll"
```

Mit der unveränderten 1.7.1-DLL und dem getesteten GOG-Build erscheint `983 Mustersuchen, 3 nicht gefunden`. Mit
`KCDCClient_gog.dll` erscheint `nicht gefunden: 0`. Bei anderer Ausgabe weicht dein Spiel-Build vom getesteten ab,
und die Muster in `install.ps1` passen nicht.

Eigenen Build prüfen:

```powershell
(Get-Item "<GOG>\Bin\Win64MasterMasterGogPGO\KingdomCome.exe").VersionInfo.FileVersion
(Get-FileHash "<GOG>\Bin\Win64MasterMasterGogPGO\WHGame.dll").Hash
```

## Fehlersuche

| Symptom | Ursache / Lösung |
|---|---|
| Absturz `0xC0000005 at KCDCClient.dll+0x6AFE7B` in `client\logs\KCDC.log` | Der Launcher lädt noch die Original-DLL. `"mod_dll_name":"KCDCClient_gog.dll"` in `KCDC_launcher.json` prüfen, `install.ps1` erneut ausführen. Oder dein GOG-Build weicht ab (siehe oben). |
| Launcher meldet „Update fehlgeschlagen“ / ersetzt Dateien | `KCDCClient.dll` selbst wurde verändert. Archiv neu entpacken (oder vom Updater wiederherstellen lassen) und den Installer nutzen, der das Original nie anfasst. |
| `install.ps1`: „does not match KCDC 1.7.1“ | Andere KCDC-Version oder bereits veränderte DLL. Sauberen 1.7.1-Download verwenden. |
| `KCDC_launcher.json` fehlt | `KCDCLauncher.exe` einmal starten und die GOG-`KingdomCome.exe` wählen (Schritt 2). |
| PowerShell: „Skriptausführung deaktiviert“ | Die Form mit `-ExecutionPolicy Bypass` verwenden; sie wirkt nur für diesen einen Aufruf. |

## Rückmeldung

Im KCDC-Download steht keine Bugtracker-Adresse. Laut „Getting Started“-FAQ von KCDC kommen Releases vom offiziellen
**Discord** (Builds-Kanal) und von **Nexus Mods** („Kingdoms Connected Multiplayer“); meldet im Discord-Server, von dem
ihr den Build habt (Forum-Kanal mit den Tags Bug / Idea / Fixed), oder auf der Nexus-Seite. KCDC nur von diesen offiziellen Quellen laden.

Die FAQ verlangt: Mod-Version, Spiele-Store (**GOG angeben - der Support ist als experimentell markiert**), Server,
genaue Fehlermeldung, Schritte zum Nachstellen, Screenshots, die passenden Dateien aus `client\logs` und bei
Update-Problemen `client\.mafiahub\logs\patcher.log`. Erwähnt außerdem, dass ihr den Workaround aus diesem Repository
nutzt (`KCDCClient_gog.dll`), sonst suchen die Entwickler einen Absturz, der schon erklärt ist. Der Text für die
Entwickler steht in [docs/BUGREPORT.txt](docs/BUGREPORT.txt); eigenen Server betreiben: [docs/HOSTING.md](docs/HOSTING.md).

## Dateien

```
install.ps1                      erzeugt KCDCClient_gog.dll und ändert KCDC_launcher.json
uninstall.ps1                    setzt die Config zurück, löscht optional die _gog-DLL
CHECKSUMS.txt                    SHA-256 der getesteten Dateien
docs/TECHNICAL.md                Analyse, Methode, Anpassung an neue Versionen (englisch)
docs/BUGREPORT.txt               englischer Bugreport / Feature-Wunsch für die KCDC-Entwickler
docs/SERVER-OWNERS.md            Hinweis für Server-Betreiber, die GOG-Spieler zulassen wollen
tools/kcdc_gog_patch.py          Python-Alternative zu install.ps1
tools/find_missing_patterns.py   listet Signaturen, die in einer WHGame.dll fehlen (Emulator)
tools/disasm.py                  kleiner x64-Disassembler
```

## Haftungsausschluss

Ohne Gewähr. Die Skripte verändern nur eine Kopie einer Datei, die du bereits hast, und eine Config-Datei; sie laden
nichts herunter und fassen keine Spieldateien an. Server können veränderte Clients ablehnen - bitte die
KCDC-Entwickler nicht um Support bitten, solange dieser Workaround läuft.
