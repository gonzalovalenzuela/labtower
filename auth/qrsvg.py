"""Minimal QR code generator (byte mode, error correction M, versions 1-10) that returns an SVG string. Standard library only.
ES: Lo usa el Admin Panel para mostrar el código QR del 2FA sin depender de librerías externas ni de servicios de internet.
EN: Used by the Admin Panel to show the 2FA QR code without external libraries or internet services. Algorithm after the public QR spec (ISO/IEC 18004)."""

_ECC_PER_BLOCK = [10, 16, 26, 18, 24, 16, 18, 22, 22, 26]    # level M, versions 1..10
_NUM_BLOCKS    = [1, 1, 1, 2, 2, 4, 4, 4, 5, 5]
MAX_VERSION = 10

def _mul(x, y):
    z = 0
    for i in range(7, -1, -1):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z

def _divisor(deg):
    res = [0] * (deg - 1) + [1]
    root = 1
    for _ in range(deg):
        for j in range(deg):
            res[j] = _mul(res[j], root)
            if j + 1 < deg: res[j] ^= res[j + 1]
        root = _mul(root, 2)
    return res

def _remainder(data, div):
    res = [0] * len(div)
    for b in data:
        f = b ^ res.pop(0); res.append(0)
        for i, c in enumerate(div): res[i] ^= _mul(c, f)
    return res

def _raw_modules(ver):
    r = (16 * ver + 128) * ver + 64
    if ver >= 2:
        n = ver // 7 + 2
        r -= (25 * n - 10) * n - 55
        if ver >= 7: r -= 36
    return r

def _data_codewords(ver): return _raw_modules(ver) // 8 - _ECC_PER_BLOCK[ver - 1] * _NUM_BLOCKS[ver - 1]

def _align_positions(ver):
    if ver == 1: return []
    n = ver // 7 + 2
    step = (ver * 4 + n * 2 + 1) // (n * 2 - 2) * 2
    size = ver * 4 + 17
    return list(reversed([size - 7 - i * step for i in range(n - 1)] + [6]))

def encode(text: str) -> list:
    """Return the module matrix (list of rows of bools; True = dark)."""
    data = text.encode("utf-8")
    for ver in range(1, MAX_VERSION + 1):
        cc = 8 if ver < 10 else 16
        if 4 + cc + len(data) * 8 <= _data_codewords(ver) * 8: break
    else:
        raise ValueError("text too long for this QR generator")
    bits = [0, 1, 0, 0] + [(len(data) >> i) & 1 for i in range(cc - 1, -1, -1)]
    for b in data: bits += [(b >> i) & 1 for i in range(7, -1, -1)]
    cap = _data_codewords(ver) * 8
    bits += [0] * min(4, cap - len(bits))
    bits += [0] * (-len(bits) % 8)
    cw = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    pad = 0xEC
    while len(cw) < cap // 8: cw.append(pad); pad ^= 0xEC ^ 0x11
    # error correction + interleaving
    nb, el = _NUM_BLOCKS[ver - 1], _ECC_PER_BLOCK[ver - 1]
    raw = _raw_modules(ver) // 8
    nshort, slen = nb - raw % nb, raw // nb
    div, blocks, k = _divisor(el), [], 0
    for i in range(nb):
        d = cw[k:k + slen - el + (0 if i < nshort else 1)]; k += len(d)
        ecc = _remainder(d, div)
        if i < nshort: d = d + [0]
        blocks.append(d + ecc)
    out = []
    for i in range(len(blocks[0])):
        for j, b in enumerate(blocks):
            if i != slen - el or j >= nshort: out.append(b[i])
    return _matrix(ver, out)

def _matrix(ver, codewords):
    size = ver * 4 + 17
    m = [[False] * size for _ in range(size)]
    fn = [[False] * size for _ in range(size)]
    def put(x, y, dark):
        m[y][x] = bool(dark); fn[y][x] = True
    for i in range(size):
        put(6, i, i % 2 == 0); put(i, 6, i % 2 == 0)
    for cx, cy in ((3, 3), (size - 4, 3), (3, size - 4)):
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                x, y = cx + dx, cy + dy
                if 0 <= x < size and 0 <= y < size: put(x, y, max(abs(dx), abs(dy)) not in (2, 4))
    ap = _align_positions(ver)
    for i, cx in enumerate(ap):
        for j, cy in enumerate(ap):
            if (i == 0 and j == 0) or (i == 0 and j == len(ap) - 1) or (i == len(ap) - 1 and j == 0): continue
            for dy in range(-2, 3):
                for dx in range(-2, 3): put(cx + dx, cy + dy, max(abs(dx), abs(dy)) != 1)
    def fmt(mask):
        d = (0 << 3) | mask                                   # level M = 00
        r = d
        for _ in range(10): r = (r << 1) ^ ((r >> 9) * 0x537)
        bits = ((d << 10) | r) ^ 0x5412
        g = lambda i: (bits >> i) & 1
        for i in range(6): put(8, i, g(i))
        put(8, 7, g(6)); put(8, 8, g(7)); put(7, 8, g(8))
        for i in range(9, 15): put(14 - i, 8, g(i))
        for i in range(8): put(size - 1 - i, 8, g(i))
        for i in range(8, 15): put(8, size - 15 + i, g(i))
        put(8, size - 8, True)
    fmt(0)
    if ver >= 7:
        r = ver
        for _ in range(12): r = (r << 1) ^ ((r >> 11) * 0x1F25)
        bits = (ver << 12) | r
        for i in range(18):
            b = (bits >> i) & 1; a, c = size - 11 + i % 3, i // 3
            put(a, c, b); put(c, a, b)
    i = 0
    for right in range(size - 1, 0, -2):
        if right == 6: right = 5
        for vert in range(size):
            for j in range(2):
                x = right - j
                y = size - 1 - vert if ((right + 1) & 2) == 0 else vert
                if not fn[y][x] and i < len(codewords) * 8:
                    m[y][x] = bool((codewords[i >> 3] >> (7 - (i & 7))) & 1); i += 1
    masks = [lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0, lambda x, y: x % 3 == 0, lambda x, y: (x + y) % 3 == 0,
             lambda x, y: (x // 3 + y // 2) % 2 == 0, lambda x, y: x * y % 2 + x * y % 3 == 0,
             lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0, lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0]
    best = None
    for mk in range(8):
        t = [row[:] for row in m]
        for y in range(size):
            for x in range(size):
                if not fn[y][x] and masks[mk](x, y): t[y][x] = not t[y][x]
        s = _penalty(t)
        if best is None or s < best[0]: best = (s, mk, t)
    _, mk, t = best
    m = t; fmt(mk)
    return m

def _penalty(t):
    n, p = len(t), 0
    for rows in (t, [list(c) for c in zip(*t)]):
        for row in rows:
            run = 1
            for i in range(1, n):
                if row[i] == row[i - 1]: run += 1
                else:
                    if run >= 5: p += run - 2
                    run = 1
            if run >= 5: p += run - 2
    for y in range(n - 1):
        for x in range(n - 1):
            if t[y][x] == t[y][x + 1] == t[y + 1][x] == t[y + 1][x + 1]: p += 3
    dark = sum(map(sum, t)) * 100 // (n * n)
    return p + abs(dark - 50) // 5 * 10

def svg(text: str, border: int = 4) -> str:
    m = encode(text); n = len(m) + border * 2
    path = "".join(f"M{x + border},{y + border}h1v1h-1z" for y, row in enumerate(m) for x, d in enumerate(row) if d)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" shape-rendering="crispEdges" role="img" aria-label="QR">'
            f'<rect width="{n}" height="{n}" fill="#fff"/><path d="{path}" fill="#000"/></svg>')
