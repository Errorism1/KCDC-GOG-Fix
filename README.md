# KCDC on the GOG version of Kingdom Come: Deliverance II

*Deutsche Version: [README.de.md](README.de.md)*

Unofficial workaround that lets **KCDC (Kingdoms Connected) 1.7.1** start with the **GOG** build of
Kingdom Come: Deliverance II 1.5.6.0. Without it the client crashes right after the game module is loaded.

> **Status:** the game starts, reaches the KCDC main menu, connects to servers, passes the server's build
> verification and loads the server's resources. **Servers that require a Steam ID kick GOG players** (see
> [Known limitation](#known-limitation-servers-that-require-a-steam-id)); playing on a server that admits
> players without one has not been confirmed yet. Please report your results (see
> [Reporting](#reporting-results)).
>
> This is not made by or affiliated with the KCDC / MafiaHub developers. Use at your own risk. When the
> developers ship official GOG support, switch back to their version and delete this workaround.

## The problem

`KCDCClient.dll` looks for ~980 function signatures (byte patterns) in the game's `WHGame.dll`. Three of them
do not exist in the GOG build, because the GOG build is compiled slightly differently from the Steam build
(different instruction choices and register allocation). The client does not check for a failed search and
dereferences a null pointer:

```
Unhandled exception 0xC0000005 at KCDCClient.dll+0x6AFE7B   (InitClient)
```

## What this fix does

* Creates `KCDCClient_gog.dll` **next to** the original and replaces those three patterns with the GOG variants.
* Points `KCDC_launcher.json` (`mod_dll_name`) at the new file.
* The original `KCDCClient.dll` stays untouched, so the KCDC updater reports "up-to-date" and does not
  overwrite anything.
* **No modified binaries are distributed.** The installer builds the file from *your own* copy and refuses to
  run unless that copy has the exact SHA-256 of KCDC 1.7.1.

Details: [docs/TECHNICAL.md](docs/TECHNICAL.md).

## Tested with

| Component | Version | SHA-256 |
|---|---|---|
| KCDC client | 1.7.1 (`KCDCClient.dll`) | `28949D27AD5FC508B2FAA1FFA430E83A8401445FD3142C1469B936F7A38636FC` |
| Kingdom Come: Deliverance II (GOG) | 1.5.6.0, `Bin\Win64MasterMasterGogPGO`, GOG build id `59798195747257766` | `KingdomCome.exe`: `2E4C3189F32CC8D2A1A768EAF54754079D3EC90DAC563B392DBD6CAD9EA4E63B` |
| | | `WHGame.dll`: `C59754B925C669B26C46723EB6C19C3217ABA2FAC94A1AD2D8BCC229D9363870` |
| OS | Windows 11 | |

Other GOG builds may work or not; see [Other game versions](#other-game-versions).

## Installation

Requirements: Windows, PowerShell (the one built into Windows is enough), the KCDC 1.7.1 download.

1. **Unpack** the KCDC 1.7.1 archive (do not copy single files out of it).
2. **Start `client\KCDCLauncher.exe` once.** It cannot find the game through Steam and asks for the game
   executable. Select  
   `<your GOG folder>\Kingdom Come Deliverance II\Bin\Win64MasterMasterGogPGO\KingdomCome.exe`  
   The game will crash or close - that is expected. Afterwards `client\KCDC_launcher.json` exists.
3. **Close everything** (launcher, game).
4. **Run the installer** from a PowerShell window in this folder (adjust the path to your KCDC `client` folder):

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install.ps1 -ClientDir "D:\Games\KCDC-1.7.1\client"
   ```

   Expected output: `Created KCDCClient_gog.dll (SHA-256 verified).` and `Updated KCDC_launcher.json`.
5. **Start `client\KCDCLauncher.exe` as usual.** The updater should say "up-to-date" and the game should
   reach the main menu with the KCDC server browser.

Servers are listed from `client\files\kcdc\servers.tsv` (name, host, port, optional password, tab separated).

Without PowerShell, or if you prefer Python: `python tools\kcdc_gog_patch.py <KCDCClient.dll> <KCDCClient_gog.dll>`
and set `"mod_dll_name":"KCDCClient_gog.dll"` in `KCDC_launcher.json` by hand.

## Uninstall

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1 -ClientDir "D:\Games\KCDC-1.7.1\client" -RemoveDll
```

This sets `mod_dll_name` back to `KCDCClient.dll` (a backup of the original config is
`KCDC_launcher.json.bak`).

## Known limitation: servers that require a Steam ID

Some servers kick you right after loading with a message like:

```
You have been kicked. Reason: SteamID64 fehlt. Bitte über Steam verbinden.
```

This is **not** a bug of the client and not fixed by this workaround on purpose. The text is not part of the stock
KCDC gamemode; it comes from a script of that particular server. KCDC reports a Steam ID or an Epic ID to the
server, and the GOG version has neither (GOG is not Epic), so the field is empty. Faking an ID would circumvent the
server's access control, so this repository does not do that.

What you can do:

* Join servers that do not require a Steam ID (the stock gamemode allows an empty ID).
* Ask the server owner to admit GOG players, e.g. with a name entry on the whitelist (`whitelist add name:<nickname>`)
  or by dropping the check. A ready-to-send note for server owners is in [docs/SERVER-OWNERS.md](docs/SERVER-OWNERS.md).
* Ask the KCDC developers for a GOG identity (see [docs/BUGREPORT.txt](docs/BUGREPORT.txt), part 2).

## After a KCDC update

The updater only updates the original `KCDCClient.dll`; the `_gog` copy is **not** updated and will not match
the new server/launcher version. After an update:

1. Run `uninstall.ps1` (without `-RemoveDll`) or set `mod_dll_name` back to `KCDCClient.dll` and test whether the
   new version already supports GOG.
2. If it still crashes, this fix needs an update for the new version
   ([docs/TECHNICAL.md](docs/TECHNICAL.md#adapting-to-a-new-kcdc-version)). The installer will refuse to run
   on a different `KCDCClient.dll`.

## Other game versions

Run the checker against your own `WHGame.dll` (needs `pip install pefile unicorn`):

```powershell
python tools\find_missing_patterns.py "<KCDC>\client\KCDCClient.dll" "<GOG>\Bin\Win64MasterMasterGogPGO\WHGame.dll"
```

With the unmodified 1.7.1 DLL and the tested GOG build it prints `983 searches, 3 not found`. With
`KCDCClient_gog.dll` it prints `not found: 0`. If you get a different list, your game build differs from the
tested one and the patterns in `install.ps1` will not fit.

Check your build:

```powershell
(Get-Item "<GOG>\Bin\Win64MasterMasterGogPGO\KingdomCome.exe").VersionInfo.FileVersion
(Get-FileHash "<GOG>\Bin\Win64MasterMasterGogPGO\WHGame.dll").Hash
```

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Crash `0xC0000005 at KCDCClient.dll+0x6AFE7B` in `client\logs\KCDC.log` | The launcher still loads the original DLL. Check `"mod_dll_name":"KCDCClient_gog.dll"` in `KCDC_launcher.json`; re-run `install.ps1`. Or your GOG build differs (see above). |
| Launcher shows "update failed" / replaces files | You edited `KCDCClient.dll` itself. Re-extract the archive (or let the updater restore it) and use the installer instead - it never touches the original. |
| `install.ps1`: "does not match KCDC 1.7.1" | You have another KCDC version, or an already-modified DLL. Use a clean 1.7.1 download. |
| `KCDC_launcher.json` missing | Start `KCDCLauncher.exe` once and select the GOG `KingdomCome.exe` (step 2). |
| PowerShell: "running scripts is disabled" | Use the `-ExecutionPolicy Bypass` form shown above; it only affects that one call. |

## Reporting results

The KCDC download ships no bug tracker address. According to the KCDC "Getting Started" FAQ, releases come from the
official **Discord** (builds channel) and from **Nexus Mods** ("Kingdoms Connected Multiplayer"); report in the
Discord server you got the build from (forum channel with the tags Bug / Idea / Fixed), or on that Nexus page. Only download KCDC from those official sources.

The FAQ asks for: mod version, game store (**say that you use GOG - support is marked experimental**), the server,
the exact error, steps to reproduce, screenshots, the relevant files from `client\logs`, and for update problems
`client\.mafiahub\logs\patcher.log`. Also tell them that you use the workaround from this repository
(`KCDCClient_gog.dll`), otherwise they may chase a crash that is already explained. The text for the KCDC developers
is in [docs/BUGREPORT.txt](docs/BUGREPORT.txt); hosting your own server: [docs/HOSTING.md](docs/HOSTING.md).

## Files

```
install.ps1                      creates KCDCClient_gog.dll and edits KCDC_launcher.json
uninstall.ps1                    reverts the config, optionally deletes the _gog DLL
CHECKSUMS.txt                    SHA-256 of the tested files
docs/TECHNICAL.md                analysis, method, how to adapt to new versions
docs/BUGREPORT.txt               English bug report / feature request for the KCDC developers
docs/SERVER-OWNERS.md            note for server owners who want to admit GOG players
tools/kcdc_gog_patch.py          Python alternative to install.ps1
tools/find_missing_patterns.py   lists signatures missing in a given WHGame.dll (emulator based)
tools/disasm.py                  small x64 disassembler helper
```

## Disclaimer

Provided as is, without warranty. The scripts only modify a copy of a file you already have and a config file;
they do not download anything and do not touch the game files. Servers may refuse modified clients - do not ask
the KCDC developers for support while running this workaround.
