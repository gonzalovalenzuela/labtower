#!/usr/bin/env python3
# snmpd "pass" script: fakes the Synology MIB (.1.3.6.1.4.1.6574) for end-to-end tests.
import sys
B = ".1.3.6.1.4.1.6574"
T = {
 "1.1.0": ("integer", 1), "1.2.0": ("integer", 41), "1.3.0": ("integer", 1),
 "1.4.1.0": ("integer", 1), "1.4.2.0": ("integer", 1),
 "1.5.1.0": ("string", "DS920+"), "1.5.2.0": ("string", "SIM0001"), "1.5.3.0": ("string", "DSM 7.2.1-69057 Update 5"), "1.5.4.0": ("integer", 2),
}
for i, (m, st, t, ty) in enumerate([("WD40EFRX", 1, 36, "SATA"), ("WD40EFRX", 1, 38, "SATA"), ("ST4000VN006", 1, 52, "SATA"), ("Samsung 870", 5, 33, "SSD")], 1):
    T[f"2.1.1.1.{i}"] = ("integer", i-1); T[f"2.1.1.2.{i}"] = ("string", f"Disk {i}")
    T[f"2.1.1.3.{i}"] = ("string", m); T[f"2.1.1.4.{i}"] = ("string", ty)
    T[f"2.1.1.5.{i}"] = ("integer", st); T[f"2.1.1.6.{i}"] = ("integer", t)
T["3.1.1.1.1"] = ("integer", 0); T["3.1.1.2.1"] = ("string", "Volume 1"); T["3.1.1.3.1"] = ("integer", 1)
T["3.1.1.4.1"] = ("counter64", 4200000000000); T["3.1.1.5.1"] = ("counter64", 14500000000000)
T["3.1.1.1.2"] = ("integer", 1); T["3.1.1.2.2"] = ("string", "Volume 2"); T["3.1.1.3.2"] = ("integer", 11); T["3.1.1.4.2"] = ("counter64", 100000000000); T["3.1.1.5.2"] = ("counter64", 1000000000000)
T["101.1.1.2.1"] = ("string", "sda"); T["101.1.1.8.1"] = ("integer", 7)
def key(s): return [int(x) for x in s.split(".")]
ks = sorted(T, key=key)
def emit(k):
    ty, v = T[k]; print(B + "." + k); print(ty); print(v)
a = sys.argv[1:]
if len(a) == 2 and a[0] in ("-g", "-n"):
    oid = a[1]
    if not oid.startswith(B): sys.exit(0)
    rel = oid[len(B):].lstrip(".")
    if a[0] == "-g":
        if rel in T: emit(rel)
    else:
        for k in ks:
            if not rel or key(k) > key(rel): emit(k); break
