"""Kleiner Disassembler fuer eine RVA-Spanne einer PE-Datei (x64), mit Strings bei RIP-relativen Zugriffen.

Aufruf:  python disasm.py <datei.dll> <start-rva-hex> <ende-rva-hex>
Beispiel: python disasm.py KCDCClient.dll 6afde0 6aff72      (die Mustersuch-Funktion in KCDC 1.7.1)

Voraussetzungen:  pip install pefile capstone
Achtung: Der Name dieser Datei darf nicht 'dis.py' sein (kollidiert mit dem Python-Standardmodul).
"""
import re
import sys

import capstone
import pefile

if len(sys.argv) != 4:
    sys.exit(__doc__)
pe = pefile.PE(sys.argv[1], fast_load=True)
beg, end = int(sys.argv[2], 16), int(sys.argv[3], 16)
data = pe.get_data(beg, end - beg)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)


def cstr(rva):
    try:
        s = pe.get_data(rva, 80).split(b"\0")[0]
        if len(s) >= 3 and all(32 <= c < 127 for c in s):
            return s.decode()
    except Exception:
        pass


for i in md.disasm(data, beg):
    extra = ""
    m = re.search(r"rip ([+-]) (0x[0-9a-f]+)", i.op_str)
    if m and i.mnemonic in ("lea", "mov"):
        t = i.address + i.size + int(m.group(2), 16) * (1 if m.group(1) == "+" else -1)
        s = cstr(t)
        extra = "  ; -> %x %s" % (t, ('"%s"' % s) if s else "")
    print("%x  %-6s %s%s" % (i.address, i.mnemonic, i.op_str, extra))
