# Ready-to-paste posts

The KCDC Discord has a forum channel for reports with the tags **Bug**, **Idea**, **Fixed**, **Won't fix**,
**Duplicate**. Click **Neuer Post** and pick the tag. Before posting, search the forum for "GOG" to avoid a duplicate.
One topic per post. Message limit is 2000 characters; all posts below are shorter. Discord forum posts here cannot take zip files, so link the GitHub repository instead (scripts and documents only - no modified game or mod binaries): https://github.com/Errorism1/KCDC-GOG-Fix

## 1. Tag: Bug

**Title:** `GOG: client crash in InitClient (3 signatures not found in the GOG build)`

```
Store: GOG, KCD2 1.5.6.0 (build id 59798195747257766, Win64MasterMasterGogPGO), KCDC 1.7.1
WHGame.dll SHA-256: C59754B925C669B26C46723EB6C19C3217ABA2FAC94A1AD2D8BCC229D9363870

Crash: 0xC0000005 at KCDCClient.dll+0x6AFE7B right after "Game module loaded". The signature scan (0x6AFDE0) returns an empty vector and the first element is dereferenced without a check.
3 of 983 patterns are not found in the GOG WHGame.dll:
1) site 0x6CA336 `48 89 5C 24 08 55 56 57 48 83 EC 20 48 8B F1 FF 15 ? ? ? ? 39 05 ? ? ? ? 74 0F 32 C0` -> GOG has `0F 85` instead of `74 0F` (fn at WHGame+0x6C5C90)
2) site 0x6D1E63 `40 55 53 56 57 41 56 48 8B EC 48 81 EC 80 00 00 00 48 8B F9 B2 0B 48 8B 89 30 03 00 00` -> GOG prologue `55 53 57 41 56 41 57 ...` (WHGame+0xF6A295)
3) site 0x6D4495 thunk pattern, result seems unused

With only these 3 patterns changed (local copy via mod_dll_name, original DLL untouched) the client reaches the main menu, connects, passes build verification and loads resources.
Suggestions: null-check + log the failing pattern; add the GOG variants.

Repro: GOG install, select Win64MasterMasterGogPGO\KingdomCome.exe in the launcher, start. Logs: client\logs\KCDC.log. Details, hashes and tools: https://github.com/Errorism1/KCDC-GOG-Fix (docs/TECHNICAL.md)
```

## 2. Tag: Idea

**Title:** `Identity for GOG players (no Steam ID, no Epic ID)`

```
GOG players report an empty steamId and an empty epicId, because GOG provides neither. Server scripts that require a Steam ID kick them right after loading ("SteamID64 fehlt. Bitte über Steam verbinden."), although the client connected, passed build verification and loaded the resources.
Is an identity for GOG players planned (e.g. the GOG Galaxy account id)? Until then a note in the server docs on how owners can admit players without a Steam ID (name: whitelist entries, own tokens via connection.ticket) would help. The stock whitelist already accepts name: entries and only compares Steam IDs when steamId is not empty.
```

## 3. For the community (e.g. in a general / help channel, or on Nexus)

```
**KCDC on GOG: workaround for the startup crash (KCDC 1.7.1 + KCD2 1.5.6.0 GOG)**
The client crashes right after "Game module loaded" because 3 of ~980 signatures do not exist in the GOG build. The attached script builds KCDCClient_gog.dll from YOUR OWN KCDCClient.dll (SHA-256 checked) and points KCDC_launcher.json at it. The original file stays untouched, so the updater keeps saying "up-to-date". No modified binaries are shared.
Status: game starts, main menu, connects, loads server resources. Note: servers that require a Steam ID will still kick GOG players - that is each server's rule.
Unofficial, use at your own risk. Please report whether playing works for you (and say you are on GOG when you report bugs).
Readme (EN/DE), installer and tools: https://github.com/Errorism1/KCDC-GOG-Fix
```
