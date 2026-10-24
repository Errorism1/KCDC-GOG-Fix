"""Findet die Byte-Muster aus KCDCClient.dll, die in einer bestimmten WHGame.dll NICHT vorkommen.

KCDCClient.dll sucht beim Start ca. 980 Signaturen im Spielcode (Funktion RVA 0x6C6900 in KCDC 1.7.1).
Die Muster liegen verschluesselt in der DLL. Dieses Tool fuehrt die Funktion in einem CPU-Emulator (Unicorn)
aus, faengt jede Mustersuche ab und prueft sie selbst gegen die uebergebene WHGame.dll.

Aufruf:
    python find_missing_patterns.py <KCDCClient.dll> <WHGame.dll> [--json out.json] [--ct]

  --json  schreibt alle Muster (Text, Treffer, ...) als JSON
  --ct    ermittelt zusaetzlich, wo der Geheimtext jedes Musters in der DLL liegt (langsamer, mehrere Minuten)

Voraussetzungen:  pip install pefile unicorn
Die Konstanten (FUNC, FUNC_END, CHKSTK, SCAN_CORE, MKSTR) gelten fuer KCDC 1.7.1 und muessen bei anderen
Versionen neu bestimmt werden (siehe docs/TECHNICAL.md).
"""
import json
import struct
import sys

import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_HOOK_CODE, UC_HOOK_MEM_READ, UcError
from unicorn.x86_const import (UC_X86_REG_RAX, UC_X86_REG_RCX, UC_X86_REG_R8, UC_X86_REG_RDX,
                               UC_X86_REG_RIP, UC_X86_REG_RSP)

FUNC, FUNC_END = 0x6C6900, 0x6D5F6D   # Funktion mit allen Mustersuchen
CHKSTK = 0xCE79E0                     # __chkstk (wird uebersprungen)
SCAN_CORE = 0x800B90                  # fuehrt die eigentliche Suche aus (Objekt in RCX)
MKSTR = 0x801040                      # baut den Muster-String (RCX=Objekt, RDX=Zeiger, R8=Laenge)

GBASE, DUMMY, IMPBASE, HEAP, STK, SENT = 0x300000000, 0x500000000, 0x600000000, 0x700000000, 0x20000000, 0x10000000


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    want_ct = "--ct" in sys.argv
    out_json = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    mod_path, game_path = args

    pe = pefile.PE(mod_path, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    img = pe.get_memory_mapped_image()
    gimg = bytes(pefile.PE(game_path, fast_load=True).get_memory_mapped_image())

    uc = Uc(UC_ARCH_X86, UC_MODE_64)
    uc.mem_map(base, (len(img) + 0xFFF) & ~0xFFF); uc.mem_write(base, img)
    uc.mem_map(GBASE, (len(gimg) + 0xFFF) & ~0xFFF); uc.mem_write(GBASE, gimg)
    uc.mem_map(DUMMY, 0x10000)
    uc.mem_map(STK, 0x400000)
    uc.mem_map(SENT, 0x1000); uc.mem_write(SENT, b"\xf4")
    uc.mem_map(HEAP, 0x4000000)
    uc.mem_map(IMPBASE, 0x100000)
    heap = [HEAP]

    def search(txt):
        tk = [None if t.startswith("?") else int(t, 16) for t in txt.split()]
        best, cur, run = (0, 0), None, 0
        for i, t in enumerate(tk):
            if t is None:
                cur = None
                continue
            if cur is None:
                cur, run = i, 0
            run += 1
            if run > best[0]:
                best = (run, cur)
        n, at = best
        if n == 0:
            return []
        lit, res, p = bytes(tk[at:at + n]), [], gimg.find(bytes(tk[at:at + n]))
        while p != -1:
            s = p - at
            if s >= 0 and s + len(tk) <= len(gimg) and all(t is None or gimg[s + k] == t for k, t in enumerate(tk)):
                res.append(s)
                if len(res) > 5:
                    break
            p = gimg.find(lit, p + 1)
        return res

    def pop_ret():
        rsp = uc.reg_read(UC_X86_REG_RSP)
        uc.reg_write(UC_X86_REG_RIP, struct.unpack("<Q", uc.mem_read(rsp, 8))[0])
        uc.reg_write(UC_X86_REG_RSP, rsp + 8)

    # Importe durch Stubs ersetzen (memset/memcpy/malloc werden nachgebildet)
    pe.parse_data_directories(directories=[1])
    names, i = {}, 0
    for d in pe.DIRECTORY_ENTRY_IMPORT:
        for imp in d.imports:
            fake = IMPBASE + i * 16
            i += 1
            names[fake] = (imp.name or b"ord").decode()
            uc.mem_write(imp.address - pe.OPTIONAL_HEADER.ImageBase + base, struct.pack("<Q", fake))

    def on_import(_uc, addr, size, ud):
        n = names.get(addr, "?")
        rcx, rdx, r8 = (uc.reg_read(r) for r in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8))
        if n == "memset":
            uc.mem_write(rcx, bytes([rdx & 0xFF]) * r8); uc.reg_write(UC_X86_REG_RAX, rcx)
        elif n in ("memcpy", "memmove"):
            uc.mem_write(rcx, bytes(uc.mem_read(rdx, r8))); uc.reg_write(UC_X86_REG_RAX, rcx)
        elif n == "malloc":
            uc.reg_write(UC_X86_REG_RAX, heap[0]); heap[0] += (rcx + 0xF) & ~0xF
        else:
            uc.reg_write(UC_X86_REG_RAX, 0)
        pop_ret()

    results, reads, last_call = [], [], [0]
    rd = [s for s in pe.sections if s.Name.startswith(b".rdata")][0]

    def on_read(_uc, access, addr, size, value, ud):
        reads.append(addr)

    def on_trace(_uc, addr, size, ud):
        if size == 5 and uc.mem_read(addr, 1) == b"\xe8":
            last_call[0] = addr - base

    def on_mkstr(_uc, addr, size, ud):
        obj, src, ln = (uc.reg_read(r) for r in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8))
        data = bytes(uc.mem_read(src, ln))
        if ln < 16:
            uc.mem_write(obj, data + b"\0" * (16 - ln)); cap = 15
        else:
            uc.mem_write(obj, struct.pack("<Q", heap[0])); uc.mem_write(heap[0], data + b"\0")
            heap[0] += (ln + 32) & ~0xF; cap = ln
        uc.mem_write(obj + 0x10, struct.pack("<QQ", ln, cap))
        uc.reg_write(UC_X86_REG_RAX, obj)
        pop_ret()

    def on_scan(_uc, addr, size, ud):
        obj = uc.reg_read(UC_X86_REG_RCX)
        ln, cap = struct.unpack("<QQ", uc.mem_read(obj + 0x10, 16))
        dp = obj if cap < 16 else struct.unpack("<Q", uc.mem_read(obj, 8))[0]
        raw = bytes(uc.mem_read(dp, ln))
        txt = raw.decode("latin1").split("\0")[0].strip()
        m = search(txt)
        arr = heap[0]; heap[0] += 64
        if m:
            uc.mem_write(arr, b"".join(struct.pack("<Q", GBASE + x) for x in m))
        uc.mem_write(obj + 0x48, struct.pack("<QQQ", arr, arr + 8 * len(m), arr + 8 * len(m)))
        entry = dict(site=last_call[0], pat=txt, matches=m, length=ln)
        if want_ct and reads:
            entry["ciphertext_rva"] = max(reads) - base - ln + 1
        reads.clear()
        results.append(entry)
        pop_ret()

    uc.hook_add(UC_HOOK_CODE, on_import, begin=IMPBASE, end=IMPBASE + 0x100000)
    uc.hook_add(UC_HOOK_CODE, lambda u, a, s, d: pop_ret(), begin=base + CHKSTK, end=base + CHKSTK)
    uc.hook_add(UC_HOOK_CODE, on_mkstr, begin=base + MKSTR, end=base + MKSTR)
    uc.hook_add(UC_HOOK_CODE, on_scan, begin=base + SCAN_CORE, end=base + SCAN_CORE)
    uc.hook_add(UC_HOOK_CODE, on_trace, begin=base + FUNC, end=base + FUNC_END)
    if want_ct:
        uc.hook_add(UC_HOOK_MEM_READ, on_read, begin=base + rd.VirtualAddress,
                    end=base + rd.VirtualAddress + rd.Misc_VirtualSize)

    rsp = STK + 0x3F0000
    uc.mem_write(rsp, struct.pack("<Q", SENT))
    uc.reg_write(UC_X86_REG_RSP, rsp)
    try:
        uc.emu_start(base + FUNC, SENT, timeout=900 * 1000000)
    except UcError as e:
        sys.exit("Emulation abgebrochen: %s bei RVA %x (andere KCDC-Version? Konstanten pruefen)"
                 % (e, uc.reg_read(UC_X86_REG_RIP) - base))

    missing = [r for r in results if not r["matches"]]
    print("Mustersuchen: %d, nicht gefunden: %d, mehrdeutig: %d"
          % (len(results), len(missing), len([r for r in results if len(r["matches"]) > 1])))
    for r in missing:
        extra = "  ct=0x%x" % r["ciphertext_rva"] if "ciphertext_rva" in r else ""
        print("  site 0x%X len=%d%s\n    %s" % (r["site"], r["length"], extra, r["pat"]))
    if out_json:
        json.dump(results, open(out_json, "w"), indent=1)


main()
