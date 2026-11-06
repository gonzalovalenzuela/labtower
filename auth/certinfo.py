"""
certinfo — lee certificados TLS sin herramientas externas / reads TLS certificates without external tools
"""
# Lo usan Uptime Monitor y NAS Monitor. Recorre el DER del certificado (ASN.1) hasta los campos que interesan:
#   Certificate ::= SEQUENCE { tbsCertificate SEQUENCE { [0] version?, serial, signature, issuer, validity { notBefore, notAfter }, subject, … } … }
# fetch() se conecta, hace el saludo TLS y devuelve el certificado del servidor SIN validarlo: solo se lee, no se confía en él.
# EN: Used by Uptime Monitor and NAS Monitor. Walks the certificate's DER (ASN.1) down to the fields of interest.
#     fetch() connects, does the TLS handshake and returns the server certificate WITHOUT validating it: it is only read, never trusted.
from __future__ import annotations

import calendar
import ipaddress
import socket
import ssl
import time

OID_CN = bytes.fromhex("550403")         # 2.5.4.3  commonName
OID_O = bytes.fromhex("55040a")          # 2.5.4.10 organizationName
_STR_TAGS = {0x0C: "utf-8", 0x13: "ascii", 0x14: "latin-1", 0x16: "ascii", 0x1E: "utf-16-be"}


def _tlv(b: bytes, i: int):
    """(tag, inicio del valor, fin del valor) / (tag, value start, value end)."""
    tag = b[i]; n = b[i + 1]; i += 2
    if n & 0x80:
        k = n & 0x7F
        if not 1 <= k <= 4: raise ValueError("bad length")
        n = int.from_bytes(b[i:i + k], "big"); i += k
    if i + n > len(b): raise ValueError("truncated")
    return tag, i, i + n


def _asn1_time(tag: int, raw: bytes) -> int:
    s = raw.decode("ascii")
    if tag == 0x17:                                                  # UTCTime YYMMDDHHMMSSZ
        yy = int(s[:2]); s = ("19" if yy >= 50 else "20") + s
    elif tag != 0x18: raise ValueError("not a time")                 # GeneralizedTime YYYYMMDDHHMMSSZ
    return calendar.timegm(time.strptime(s[:14], "%Y%m%d%H%M%S"))


def _name(b: bytes, a: int, z: int) -> dict:
    """Name ::= SEQUENCE OF SET OF SEQUENCE { OID, valor }. Devuelve {"cn", "o"} / Returns {"cn", "o"}."""
    out = {}
    i = a
    while i < z:
        _, sa, sz = _tlv(b, i); i = sz                               # SET
        j = sa
        while j < sz:
            _, pa, pz = _tlv(b, j); j = pz                           # SEQUENCE { OID, value }
            _, oa, oz = _tlv(b, pa)
            vt, va, vz = _tlv(b, oz)
            key = {OID_CN: "cn", OID_O: "o"}.get(b[oa:oz])
            if key and key not in out and vt in _STR_TAGS:
                out[key] = b[va:vz].decode(_STR_TAGS[vt], "replace")[:200]
    return out


def parse(der: bytes) -> dict | None:
    """Campos de un certificado DER, o None si no se entiende / Fields of a DER certificate, or None if it cannot be read:
    not_before, not_after (epoch), subject y issuer ({"cn", "o"}), self_signed (emisor = sujeto / issuer == subject)."""
    try:
        _, i, _ = _tlv(der, 0)                                       # Certificate
        _, i, _ = _tlv(der, i)                                       # tbsCertificate
        if der[i] == 0xA0: i = _tlv(der, i)[2]                       # [0] version
        for _ in range(2): i = _tlv(der, i)[2]                       # serial, signature
        _, ia, iz = _tlv(der, i); i = iz                             # issuer
        tag, va, vz = _tlv(der, i); i = vz                           # validity
        if tag != 0x30: return None
        t1, a1, z1 = _tlv(der, va)
        t2, a2, z2 = _tlv(der, z1)
        _, sa, sz = _tlv(der, i)                                     # subject
        return {"not_before": _asn1_time(t1, der[a1:z1]), "not_after": _asn1_time(t2, der[a2:z2]),
                "issuer": _name(der, ia, iz), "subject": _name(der, sa, sz), "self_signed": der[ia:iz] == der[sa:sz]}
    except (ValueError, IndexError, UnicodeDecodeError):
        return None


def not_after(der: bytes) -> int | None:
    """Solo la fecha de vencimiento (epoch) / Only the expiry date (epoch)."""
    p = parse(der)
    return p["not_after"] if p else None


def _is_ip(host: str) -> bool:
    try: ipaddress.ip_address(host.split("%")[0]); return True
    except ValueError: return False


def fetch(addr, host: str, timeout: float, family=socket.AF_INET) -> bytes:
    """Se conecta a addr (sockaddr ya resuelto y revisado), hace el saludo TLS con SNI = host y devuelve el certificado DER.
    EN: Connect to addr (an already resolved and checked sockaddr), do the TLS handshake with SNI = host and return the DER certificate."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE      # nosec B501 - the certificate is only read (expiry), never trusted
    with socket.socket(family, socket.SOCK_STREAM) as raw:
        raw.settimeout(timeout)
        raw.connect(addr)
        with ctx.wrap_socket(raw, server_hostname=None if _is_ip(host) else host) as s:
            return s.getpeercert(True) or b""
