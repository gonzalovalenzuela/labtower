#!/usr/bin/env python3
"""apt-repo.py — build and sign a minimal APT repository for LabTower (stdlib only).

Developer tool: it is NOT part of the .deb. Run it on the machine that holds the GPG key (the Mac).
Herramienta de desarrollo: NO va dentro del .deb. Se ejecuta donde está la clave GPG (el Mac).

  apt-repo.py --repo DIR --key KEYID add labtower_1.2.0_all.deb [...]

What it does / Qué hace:
  1. copies each .deb into DIR/pool/main/p/labtower/
  2. regenerates DIR/dists/stable/main/binary-<arch>/Packages(.gz) for amd64, arm64 and armhf
     (the package is Architecture: all, so the same list is published for each architecture)
  3. writes DIR/dists/stable/Release and signs it: InRelease (clear-signed) + Release.gpg (detached)
  4. exports the public key to DIR/labtower.asc and writes DIR/index.html with install instructions

Package fields come from `dpkg-deb -f` when available; otherwise from debian/control of this repo
(the Version must match the file name). / Los campos salen de `dpkg-deb -f` o, si no existe
(macOS), de debian/control del repo (la versión debe coincidir con el nombre del archivo).
"""
import argparse, gzip, hashlib, re, shutil, subprocess, sys, time
from email.utils import formatdate
from pathlib import Path

ARCHS = ("amd64", "arm64", "armhf")      # the .deb is arch "all": same Packages for every arch
SUITE, COMP = "stable", "main"
ROOT = Path(__file__).resolve().parent.parent


def control_of(deb: Path) -> str:
    """Control fields of a .deb as text (see module docstring for the two sources)."""
    if shutil.which("dpkg-deb"):
        return subprocess.run(["dpkg-deb", "-f", str(deb)], check=True, capture_output=True, text=True).stdout
    txt = (ROOT / "debian" / "control").read_text(encoding="utf-8")
    m = re.search(r"^Version:\s*(\S+)", txt, re.M)
    if not m or f"_{m.group(1)}_" not in deb.name:
        sys.exit(f"{deb.name}: dpkg-deb not found and debian/control version ({m and m.group(1)}) "
                 f"does not match the file name")
    return txt


def parse_fields(text: str) -> list:
    """Control text -> list of (field, value) keeping multi-line values (continuation lines)."""
    out = []
    for line in text.rstrip("\n").split("\n"):
        if line.startswith((" ", "\t")) and out:
            out[-1][1] += "\n" + line
        elif ":" in line:
            k, v = line.split(":", 1)
            out.append([k, v.strip()])
    return out


def hashes(p: Path):
    # MD5 and SHA1 are fields the APT Release format requires; they are not used for security here.
    md5, s1, s256 = hashlib.md5(usedforsecurity=False), hashlib.sha1(usedforsecurity=False), hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            md5.update(blk); s1.update(blk); s256.update(blk)
    return md5.hexdigest(), s1.hexdigest(), s256.hexdigest()


def stanza(deb: Path, repo: Path) -> str:
    """One Packages entry for a .deb already inside the pool."""
    fields = [f for f in parse_fields(control_of(deb)) if f[0] not in ("Installed-Size_", "Filename", "Size")]
    md5, s1, s256 = hashes(deb)
    fields += [["Filename", deb.relative_to(repo).as_posix()], ["Size", str(deb.stat().st_size)],
               ["MD5sum", md5], ["SHA1", s1], ["SHA256", s256]]
    return "\n".join(f"{k}: {v}" for k, v in fields) + "\n"


def write(p: Path, data: bytes):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def gpg(key, *args, data=None):
    return subprocess.run(["gpg", "--batch", "--yes", "--local-user", key, *args], check=True,
                          input=data, capture_output=True)


def build(repo: Path, key: str):
    pool = repo / "pool" / COMP
    debs = sorted(pool.rglob("*.deb"))
    if not debs:
        sys.exit("pool is empty")
    stanzas = "\n".join(stanza(d, repo) for d in debs).encode()
    dist = repo / "dists" / SUITE
    shutil.rmtree(dist, ignore_errors=True)
    files = []
    for arch in ARCHS:
        base = dist / COMP / f"binary-{arch}"
        write(base / "Packages", stanzas)
        write(base / "Packages.gz", gzip.compress(stanzas, mtime=0))
        files += [base / "Packages", base / "Packages.gz"]
    lines = ["Origin: LabTower", "Label: LabTower", f"Suite: {SUITE}", f"Codename: {SUITE}",
             f"Date: {formatdate(time.time(), usegmt=True)}", f"Architectures: {' '.join(ARCHS)}",
             f"Components: {COMP}", "Description: LabTower APT repository"]
    for name, idx in (("MD5Sum", 0), ("SHA1", 1), ("SHA256", 2)):
        lines.append(f"{name}:")
        for f in files:
            lines.append(f" {hashes(f)[idx]} {f.stat().st_size:>8} {f.relative_to(dist).as_posix()}")
    release = ("\n".join(lines) + "\n").encode()
    write(dist / "Release", release)
    write(dist / "InRelease", gpg(key, "--clearsign", data=release).stdout)
    write(dist / "Release.gpg", gpg(key, "--armor", "--detach-sign", data=release).stdout)
    write(repo / "labtower.asc", subprocess.run(["gpg", "--armor", "--export", key], check=True,
                                                  capture_output=True).stdout)
    url = "https://gonzalovalenzuela.github.io/labtower"
    (repo / "index.html").write_text(f"""<!doctype html><meta charset="utf-8"><title>LabTower APT</title>
<h1>LabTower — APT repository</h1>
<pre>sudo install -d -m 0755 /etc/apt/keyrings
sudo wget -O /etc/apt/keyrings/labtower.asc {url}/labtower.asc
echo "deb [signed-by=/etc/apt/keyrings/labtower.asc] {url} {SUITE} {COMP}" | sudo tee /etc/apt/sources.list.d/labtower.list
sudo apt update &amp;&amp; sudo apt install labtower</pre>
""", encoding="utf-8")
    (repo / ".nojekyll").touch()
    print(f"OK: {len(debs)} package file(s), architectures {', '.join(ARCHS)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", required=True, help="repository directory (the gh-pages checkout)")
    ap.add_argument("--key", required=True, help="GPG key id or fingerprint used to sign")
    ap.add_argument("action", choices=["add", "rebuild"])
    ap.add_argument("debs", nargs="*")
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    if a.action == "add":
        if not a.debs:
            sys.exit("add needs at least one .deb")
        dest = repo / "pool" / COMP / "p" / "labtower"
        dest.mkdir(parents=True, exist_ok=True)
        for d in a.debs:
            shutil.copy2(d, dest / Path(d).name)
    build(repo, a.key)


if __name__ == "__main__":
    main()
