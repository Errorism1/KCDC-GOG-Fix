"""GOG-Fix fuer KCDC 1.7.1 (Kingdom Come: Deliverance II 1.5.6.0, GOG-Build Win64MasterMasterGogPGO).

Erzeugt aus der unveraenderten KCDCClient.dll eine Kopie KCDCClient_gog.dll, in der drei Byte-Muster
(Signaturen zum Finden von Spielfunktionen) auf die GOG-Variante angepasst sind. Die Muster liegen in der
DLL XOR-verschluesselt; der Schluesselstrom ergibt sich aus altem Klartext XOR altem Geheimtext.

Aufruf:  python kcdc_gog_patch.py <KCDCClient.dll> <KCDCClient_gog.dll>
Die Quelldatei muss exakt der Mod-Version 1.7.1 entsprechen (SHA-256 wird geprueft).
"""
import hashlib
import struct
import sys

SRC_SHA256 = "28949d27ad5fc508b2faa1ffa430e83a8401445fd3142c1469b936f7a38636fc"

# (Geheimtext-RVA, Laenge, alter Klartext, neuer Klartext ohne Auffuellung)
PATCHES = [
    (0x1577480, 84,
     "48 89 5C 24 08 55 56 57 48 83 EC 20 48 8B F1 FF 15 ? ? ? ? 39 05 ? ? ? ? 74 0F 32 C0",
     "48 89 5C 24 08 55 56 57 48 83 EC 20 48 8B F1 FF 15 ? ? ? ? 39 05 ? ? ? ? 0F 85"),
    (0x1583140, 86,
     "40 55 53 56 57 41 56 48 8B EC 48 81 EC 80 00 00 00 48 8B F9 B2 0B 48 8B 89 30 03 00 00",
     "55 53 57 41 56 41 57 48 8B EC 48 81 EC 80 00 00 00 48 8B F9 B2 0B 48 8B 89 30 03 00 00"),
    (0x1587500, 142,
     "48 83 EC 28 48 85 C9 74 12 48 8B 05 ? ? ? ? 33 D2 FF D0 F0 01 05 ? ? ? ? 48 83 C4 28 C3 "
     "? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? CC 40 53",
     "48 83 EC 28 48 85 C9 74 12 48 8B 05 ? ? ? ? 33 D2 FF D0 F0 01 05 ? ? ? ? 48 83 C4 28"),
]


def rva_to_offset(data, rva):
    """RVA -> Dateioffset ueber die PE-Sektionstabelle."""
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    sec = pe + 24 + opt
    for i in range(nsec):
        vsize, va, rsize, raw = struct.unpack_from("<IIII", data, sec + 40 * i + 8)
        if va <= rva < va + max(vsize, rsize):
            return raw + rva - va
    raise ValueError("RVA %x liegt in keiner Sektion" % rva)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    data = bytearray(open(sys.argv[1], "rb").read())
    if hashlib.sha256(data).hexdigest() != SRC_SHA256:
        sys.exit("Abbruch: Quelldatei ist nicht KCDCClient.dll aus KCDC 1.7.1 (SHA-256 passt nicht).")
    for rva, ln, old, new in PATCHES:
        off = rva_to_offset(data, rva)
        ct_old = bytes(data[off:off + ln])
        old_pt = old.encode("ascii")
        assert len(old_pt) == ln, (hex(rva), len(old_pt), ln)
        keystream = bytes(a ^ b for a, b in zip(old_pt, ct_old))
        # Neuen Text mit " ?" auf die Originallaenge auffuellen (Paritaet ggf. durch Weglassen des letzten Tokens)
        txt = new
        if (ln - len(txt)) % 2:
            txt = " ".join(txt.split()[:-1])
        txt += " ?" * ((ln - len(txt)) // 2)
        assert len(txt) == ln, (hex(rva), len(txt), ln)
        data[off:off + ln] = bytes(a ^ b for a, b in zip(txt.encode("ascii"), keystream))
    open(sys.argv[2], "wb").write(bytes(data))
    print("OK:", sys.argv[2], hashlib.sha256(data).hexdigest())


main()
