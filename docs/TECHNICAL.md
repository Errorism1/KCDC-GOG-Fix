# Technical notes

How the GOG crash was found, what exactly is patched, and how to redo it for another KCDC version.
All addresses are RVAs in KCDC 1.7.1 unless stated otherwise.

## 1. Symptom

```
[Client] Game module loaded at 0x7ffc19f00000 ahead of the engine
[CrashTrail] Unhandled exception 0xC0000005 at KCDCClient.dll+0x6AFE7B
Faulting read of 0x0          RCX = 0
```

The launcher itself works for GOG: its path dialog accepts `Bin\Win64MasterMasterGogPGO\KingdomCome.exe` and writes it
to `KCDC_launcher.json` (`game_path_manual`). The crash is inside the client DLL after it was loaded into the game.

## 2. Cause

`0x6AFDE0` is a signature scanner: it takes a pattern string (`"48 8B ? ? 05 ..."`, `?` = wildcard) and an offset,
runs the search (`0x800B90`) in the game module and returns `first_match + offset`:

```
6afe5f  lea  rcx,[rbp-0x59]     ; pattern string object
6afe63  call 0x801040           ; build the string from (ptr,len)
6afe72  call 0x800b90           ; search -> result vector at [rbp-0x11]
6afe77  mov  rcx,[rbp-0x11]     ; vector.begin
6afe7b  mov  rdi,[rcx]          ; <-- crash when the vector is empty (begin == 0)
```

The result is not checked, so one pattern that is missing in the game kills the client. The table of searches is
one huge function (`0x6C6900`-`0x6D5F6D`, 983 searches). It runs in order and dies at the first miss
(`0x6CA336`, roughly the 140th search), which is why the first 139 look fine.

The patterns are stored **XOR-encrypted** in `.rdata`. Each one has its own unrolled decryptor function (or an inline
loop) with a hard-coded key; plaintext length = the `mov qword [rsp+0x38], LEN` before the call.

## 3. Finding the misses

`tools/find_missing_patterns.py` runs the table function in a CPU emulator (Unicorn):

* the KCDC image and the target `WHGame.dll` are mapped into emulated memory,
* `__chkstk` is skipped, the few CRT imports used (`memset`, `memcpy`, `malloc`) are emulated,
* the string builder (`0x801040`) is replaced (it uses thread-local storage),
* the search core (`0x800B90`) is replaced by a search in the mapped `WHGame.dll`; the result vector is filled so the
  real wrapper code continues normally.

Result against the GOG 1.5.6.0 `WHGame.dll`: **983 searches, 980 found, 3 missing**:

| Site | Pattern (abridged) | What the GOG build has |
|---|---|---|
| `0x6CA336` | `48 89 5C 24 08 55 56 57 48 83 EC 20 48 8B F1 FF 15 ? ? ? ? 39 05 ? ? ? ? 74 0F 32 C0` | same function at `WHGame.dll+0x6C5C90`, but `jz` is `jnz` (`0F 85 ...`): `if (GetCurrentThreadId() != main) return false`-style check, inverted by the compiler (PGO) |
| `0x6D1E63` | `40 55 53 56 57 41 56 48 8B EC 48 81 EC 80 00 00 00 48 8B F9 B2 0B 48 8B 89 30 03 00 00` | same body (`mov rdi,rcx; mov dl,0Bh; mov rcx,[rcx+330h]`) at `WHGame.dll+0xF6A295`, prologue pushes in another order (`55 53 57 41 56 41 57`) |
| `0x6D4495` | tiny thunk followed by 23 wildcards, `CC 40 53` | three candidates in the GOG build (`0x4523A4`, `0x7109A0`, `0x1AB5760`); the result variable (`0x1DCDF60`) is not referenced anywhere else in the client, so the exact choice does not matter |

How the results are used (this is why only the first two matter):

* `0x6CA336` -> `[0x1DCCC80]`, used at `0x2A26D0`: `mov rcx,[g]; lea r8,[orig]; lea rdx,[detour]; jmp 0xC69670` - a hook installer
  (MinHook-style: target, detour, original slot). The detour (`0x2A26F0`) calls the original and post-processes its
  `bool` result, consistent with the thread-check function.
* `0x6D1E63` -> `[0x1DCD7B0]`, used at `0x631BF6`: the same hook installer with detour `0x631D80`, which sets a flag in a
  global object and tail-calls the original.

**The candidates were matched by code structure, not by documentation. They look right and the client runs through
initialisation and connects, but this is inferred.**

## 4. The patch

Per pattern: `keystream[i] = old_plaintext[i] XOR old_ciphertext[i]`, `new_ciphertext[i] = new_plaintext[i] XOR keystream[i]`.
The keystream does not depend on the plaintext (checked by running the decryptors with zero ciphertext), and the
length constant in the code stays valid because the new text is padded with ` ?` wildcards to the old length.

| Ciphertext RVA | File offset | Length | New pattern |
|---|---|---|---|
| `0x1577480` | `0x1575880` | 84 | `48 89 5C 24 08 55 56 57 48 83 EC 20 48 8B F1 FF 15 ? ? ? ? 39 05 ? ? ? ? 0F 85` + `? ? ?` |
| `0x1583140` | `0x1581540` | 86 | `55 53 57 41 56 41 57 48 8B EC 48 81 EC 80 00 00 00 48 8B F9 B2 0B 48 8B 89 30 03 00 00` |
| `0x1587500` | `0x1585900` | 142 | `48 83 EC 28 48 85 C9 74 12 48 8B 05 ? ? ? ? 33 D2 FF D0 F0 01 05 ? ? ? ? 48 83 C4 28` + wildcards |

(file offset = RVA - `0x1C00`; `.rdata` VA `0xD2D000`, raw `0xD2B400`). Verification: `find_missing_patterns.py` on the
patched DLL reports 983 searches, 0 not found (one ambiguous: pattern 3, unused).

## 5. Why a second DLL instead of editing KCDCClient.dll

The updater (`MafiaHubUpdater` / build patcher) fetches `api.mafiahub.dev` manifests on every launcher start and
compares **SHA-256** of every manifest file (`.mafiahub/build-manifest.json`). A modified `KCDCClient.dll` is replaced
immediately (`status=patched`); locking the file just makes the update fail and the launcher quit. Files that are not in
the manifest are left alone. The launcher reads `mod_dll_name` from `KCDC_launcher.json`, so the patched copy is
`KCDCClient_gog.dll` and the original stays intact and verified.

Consequence: updates to `KCDCClient.dll` are *not* applied to the copy. See README.

## 6. Known limitation: servers that require a Steam id

After the client fix a GOG player gets as far as connecting, passing build verification (`Connection accepted by server,
verifying build`), downloading resources and replicating the world. Some servers then kick:

```
Disconnected: You have been kicked. Reason: SteamID64 fehlt. Bitte über Steam verbinden.
```

That text is **not** in the shipped `kcdc-gamemode`; it comes from a server-side resource (the client log shows
that the server loads its own scripts). The client reports `steamId` and `epicId` (documented as "Authenticated Steam
identifier, or an empty string when unavailable"); GOG gives neither, so both are empty. The stock gamemode accepts that
(`whitelist.ts` has `name:<nickname>` entries), so it is each server's decision. Faking a Steam id would defeat the
server's access control and is deliberately **not** part of this workaround.

What helps: servers that do not require a Steam id, or server owners adding GOG players by name
(`whitelist add name:<nickname>`) / dropping the check. A GOG identity (Galaxy account id) would have to come from the
KCDC developers.

## 7. Adapting to a new KCDC version

1. Keep the new, unmodified `KCDCClient.dll` and your `WHGame.dll`.
2. Check whether the official version already supports GOG (`mod_dll_name` back to `KCDCClient.dll`, start, read
   `client\logs\KCDC.log`). If it does, you are done.
3. Find the new addresses. In `tools/find_missing_patterns.py` the constants `FUNC`, `FUNC_END`, `CHKSTK`, `SCAN_CORE`, `MKSTR`
   are for 1.7.1. Locate them with `tools/disasm.py`: the scan core is the function the pattern wrapper calls with `edx=1`
   after building the string; the table function is the one that contains hundreds of calls to the wrapper.
4. Run `python tools\find_missing_patterns.py KCDCClient.dll WHGame.dll --ct --json out.json`. It prints each missing pattern
   with its ciphertext location (`ciphertext_rva`).
5. Find the equivalent functions in `WHGame.dll` (anchor on the unique tail of the pattern, e.g. the last 10-12
   literal bytes) and write new patterns of at most the old length. Copy the approach of `tools/kcdc_gog_patch.py`
   (needs the old plaintext from the JSON).
6. Re-run step 4 on the generated DLL until nothing is missing; test in game.

Dependencies for the tools: `pip install pefile capstone unicorn`.
