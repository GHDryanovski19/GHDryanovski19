#!/usr/bin/env python3
"""Draws every card of the profile README from profile.json and live public data.

Standard library only. Run locally with `python3 scripts/build.py` (uses `gh auth token` when
GITHUB_TOKEN is not set) or from the nightly workflow. Every card is drawn three times: light, dark
and phone (narrow, in both themes), and README.md is rewritten so its alt texts carry the numbers.
When a source can't be reached, the last good copy in scripts/state.json is used instead.
"""
import base64, datetime as dt, json, os, subprocess, sys, urllib.parse, urllib.request
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = json.load(open(os.path.join(ROOT, "profile.json"), encoding="utf-8"))
STATE = os.path.join(ROOT, "scripts", "state.json")
ASSETS = os.path.join(ROOT, "assets")
TODAY = dt.date.today()

# ---------------------------------------------------------------- data

def token():
    t = os.environ.get("GITHUB_TOKEN")
    if t:
        return t
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return ""

def http_json(url, body=None, auth=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None)
    req.add_header("User-Agent", "profile-cards")
    if body:
        req.add_header("Content-Type", "application/json")
    if auth:
        req.add_header("Authorization", "bearer " + auth)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def gql(q, tok):
    out = http_json("https://api.github.com/graphql", {"query": q}, tok)
    if "errors" in out:
        raise RuntimeError(out["errors"])
    return out["data"]

def fetch_github(tok):
    u = P["user"]
    head = gql('{user(login:"%s"){createdAt repositories(privacy:PUBLIC,ownerAffiliations:OWNER,isFork:false,first:100){totalCount nodes{stargazerCount}}}}' % u, tok)["user"]
    first = int(head["createdAt"][:4])
    days = {}
    for y in range(first, TODAY.year + 1):
        a = "%d-01-01T00:00:00Z" % y
        b = ("%d-12-31T23:59:59Z" % y) if y < TODAY.year else TODAY.isoformat() + "T23:59:59Z"
        cal = gql('{user(login:"%s"){contributionsCollection(from:"%s",to:"%s"){contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}' % (u, a, b), tok)
        for w in cal["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]
    return {
        "created": head["createdAt"][:10],
        "repos": head["repositories"]["totalCount"],
        "stars": sum(n["stargazerCount"] for n in head["repositories"]["nodes"]),
        "days": days,
        "as_of": TODAY.isoformat(),
    }

def fetch_npm():
    out = {}
    for p in P["packages"]:
        r = http_json("https://api.npmjs.org/downloads/point/last-year/" + urllib.parse.quote(p["name"], safe="@/"))
        out[p["name"]] = r.get("downloads", 0)
    return {"downloads": out, "as_of": TODAY.isoformat()}

def load_data():
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    stale = []
    tok = token()
    for key, fn in (("github", lambda: fetch_github(tok)), ("npm", fetch_npm)):
        try:
            state[key] = fn()
        except Exception as e:  # keep the last good copy
            print("fetch %s failed: %s" % (key, e), file=sys.stderr)
            if key not in state:
                raise
            age = (TODAY - dt.date.fromisoformat(state[key]["as_of"])).days
            if age > 3:
                stale.append(key)
    json.dump(state, open(STATE, "w"), indent=1, sort_keys=True)
    return state, stale

def stats(gh):
    days = sorted((dt.date.fromisoformat(k), v) for k, v in gh["days"].items() if dt.date.fromisoformat(k) <= TODAY)
    total = sum(v for _, v in days)
    year_ago = TODAY - dt.timedelta(days=365)
    last12 = sum(v for d, v in days if d > year_ago)
    longest = run = 0
    for _, v in days:
        run = run + 1 if v else 0
        longest = max(longest, run)
    cur = 0
    for i, (d, v) in enumerate(reversed(days)):
        if v:
            cur += 1
        elif i == 0 and d == TODAY:
            continue  # today isn't over yet
        else:
            break
    years = {}
    for d, v in days:
        years[d.year] = years.get(d.year, 0) + v
    active12 = sum(1 for d, v in days if d > year_ago and v)
    best = max(days, key=lambda x: x[1])
    return {"total": total, "last12": last12, "longest": longest, "current": cur, "years": years, "days": days,
            "active12": active12, "best": best}

# ---------------------------------------------------------------- drawing kit
#
# The look comes from Georgi's own photo: the sand of his shirt, the warm wood of the desk and the
# cyan of the glass wall behind him, on ink. Real marks for Hintora, Inkblot Studio and Citron.

import re

def b64(path):
    return base64.b64encode(open(os.path.join(ROOT, "scripts", path), "rb").read()).decode()

FONT = {"sans": b64("fonts/geist.woff2"), "mono": b64("fonts/geist-mono.woff2")}
PHOTO = {"wide": b64("img/photo-wide.jpg"), "square": b64("img/photo-square.jpg")}
SANS = "'Geist', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace"

# colour, its shadow, the text that sits on it
SWATCH = {
    "cyan":   ("#2AA9DC", "#17769E", "#FFFFFF"),
    "amber":  ("#D98A3D", "#9A5A22", "#FFFFFF"),
    "sand":   ("#E8D5B9", "#B79C76", "#14120F"),
    "orange": ("#F2601C", "#A8400F", "#FFFFFF"),
    "gold":   ("#C9A227", "#8C7119", "#14120F"),
    "ink":    ("#24272E", "#0E1013", "#F3EEE5"),
}
THEMES = {
    "light": dict(panel="#FFFCF6", stroke="#E6DCCB", grid="#F2EADD", fg="#14120F", muted="#6B645A", soft="#A39B8F",
                  heat=["#EFE8DC", "#BFE3F3", "#7CCAEB", "#2AA9DC", "#14678A"], ink_tile=("#14120F", "#000000", "#F3EEE5")),
    "dark": dict(panel="#15171C", stroke="#272B32", grid="#1C1F25", fg="#F3EEE5", muted="#9AA3AE", soft="#5F6670",
                 heat=["#1D2026", "#12384A", "#17769E", "#2AA9DC", "#9BDDF6"], ink_tile=("#2C3038", "#0B0C0F", "#F3EEE5")),
}

def sw(t, name):
    return t["ink_tile"] if name == "ink" else SWATCH[name]

def est(text, size, mono=False, ls=0.0, weight=500):
    """Rough text width (no font metrics in the standard library)."""
    if mono:
        return len(text) * (size * 0.6 + ls)
    w = 0.0
    for ch in text:
        if ch in "il.,:;'|!·": f = 0.27
        elif ch in "frtjI() ": f = 0.34
        elif ch in "mwMW": f = 0.82
        elif ch.isupper() or ch.isdigit(): f = 0.64
        else: f = 0.54
        w += f * size + ls
    return w * (1 + (weight - 500) / 2500)

def wrap(text, width, size, weight=400, mono=False):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if est(t, size, mono, weight=weight) * 1.07 > width and cur:
            lines.append(cur); cur = word
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines

def fmt(n):
    return "{:,}".format(n)

def text(x, y, s, size, fill, weight=400, mono=False, ls=0, anchor="start", extra=""):
    return '<text x="%g" y="%g" font-family="%s" font-size="%g" font-weight="%d" letter-spacing="%g" fill="%s" text-anchor="%s"%s>%s</text>' % (
        x, y, escape(MONO if mono else SANS), size, weight, ls, fill, anchor, extra, escape(s))

def svg(w, h, body, t, alt, panel=True, grid=True):
    faces = ("@font-face{font-family:'Geist';src:url(data:font/woff2;base64,%s) format('woff2');font-weight:100 900}"
             "@font-face{font-family:'Geist Mono';src:url(data:font/woff2;base64,%s) format('woff2');font-weight:100 900}") % (FONT["sans"], FONT["mono"])
    defs = ('<defs><pattern id="g" width="22" height="22" patternUnits="userSpaceOnUse"><path d="M22 0H0V22" fill="none" stroke="%s"/></pattern>'
            '<clipPath id="pc"><rect x="0" y="0" width="%d" height="%d" rx="22"/></clipPath></defs>') % (t["grid"], w, h)
    bg = ""
    if panel:
        bg = '<rect x="0.5" y="0.5" width="%g" height="%g" rx="22" fill="%s" stroke="%s"/>' % (w - 1, h - 1, t["panel"], t["stroke"])
        if grid:
            bg += '<rect x="1" y="1" width="%g" height="%g" rx="21" fill="url(#g)"/>' % (w - 2, h - 2)
            for (cx, cy) in ((14, 14), (w - 14, 14), (14, h - 14), (w - 14, h - 14)):  # blueprint registration marks
                bg += '<path d="M%g %gh8M%g %gv8" stroke="%s" stroke-width="1.2"/>' % (cx - 4, cy, cx, cy - 4, t["soft"])
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-label="%s">'
            '<title>%s</title><style>%s</style>%s%s%s</svg>') % (w, h, w, h, escape(alt), escape(alt), faces, defs, bg, body)

def tile(x, y, w, h, color, rx=16, depth=5):
    """A coloured block with a solid offset shadow, the chunky 'pressed key' look."""
    return ('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s"/>' % (x, y + depth, w, h, rx, color[1])
            + '<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s"/>' % (x, y, w, h, rx, color[0]))

ICONS = {
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "flame": '<path d="M12 3c1 4 6 6 6 11a6 6 0 0 1-12 0c0-3 2-5 3-6 0 2 1 3 2 3 0-3-1-5 1-8z"/>',
    "trophy": '<path d="M8 4h8v5a4 4 0 0 1-8 0V4zM8 6H4.5v1A3.5 3.5 0 0 0 8 10.5M16 6h3.5v1a3.5 3.5 0 0 1-3.5 3.5M12 13v4M8 21h8M9.5 17h5"/>',
    "chart": '<path d="M4 20h16M7 16v-4M12 16V8M17 16V5"/>',
    "bolt": '<path d="M13 3 5 14h6l-1 7 8-11h-6l1-7z"/>',
    "box": '<path d="M12 3 3 8v8l9 5 9-5V8l-9-5zM3 8l9 5 9-5M12 13v8"/>',
    "code": '<path d="m8 7-5 5 5 5M16 7l5 5-5 5M14 4l-4 16"/>',
    "arrow": '<path d="M7 17 17 7M9 7h8v8"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3.5 3.5 3.5 14.5 0 18M12 3c-3.5 3.5-3.5 14.5 0 18"/>',
    "camera": '<rect x="3" y="3" width="18" height="18" rx="5.5"/><circle cx="12" cy="12" r="4"/><path d="M17.3 6.7h.01"/>',
    "in": '<rect x="3" y="3" width="18" height="18" rx="4"/><path d="M8 10.5V17M8 7.2v.01M12 17v-3.8a2.3 2.3 0 0 1 4.6 0V17M12 10.5V17"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="m3.5 7 8.5 6 8.5-6"/>',
}

def icon(name, x, y, size, color, sw_=2):
    return ('<g transform="translate(%g %g) scale(%g)" fill="none" stroke="%s" stroke-width="%g" stroke-linecap="round" stroke-linejoin="round">%s</g>'
            % (x, y, size / 24.0, color, sw_, ICONS[name]))

def cross(x, y, s, color):
    return ('<g fill="%s"><rect x="%g" y="%g" width="%g" height="%g" rx="0.8"/><rect x="%g" y="%g" width="%g" height="%g" rx="0.8"/></g>' %
            (color, x + s * 0.4, y, s * 0.2, s, x + s * 0.15, y + s * 0.26, s * 0.7, s * 0.2))

def mark(name, x, y, size, t):
    """Inline one of the real logo marks from scripts/img as a nested SVG."""
    src = open(os.path.join(ROOT, "scripts", "img", name + ".svg"), encoding="utf-8").read()
    src = re.sub(r"<!--.*?-->", "", src, flags=re.S)
    src = re.sub(r"<title>.*?</title>|<style>.*?</style>", "", src, flags=re.S)
    if name == "hintora":
        src = src.replace('class="t" ', "").replace('fill="#EEF0F7"', 'fill="%s"' % ("#EEF0F7" if t is THEMES["light"] else "#24262D"))
    if name == "inkblot":  # white triangles: give them the studio's ink tile
        src = src.replace('<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">',
                          '<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg"><rect width="120" height="120" rx="27" fill="#14120F"/>')
        src = src.replace('id="tri"', 'id="tri-%d"' % (x * 7 + y)).replace('href="#tri"', 'href="#tri-%d"' % (x * 7 + y))
    return src.replace("<svg ", '<svg x="%g" y="%g" width="%g" height="%g" ' % (x, y, size, size), 1)

def pill(x, y, s, fill, color, size=12, h=24, mono=True, weight=600):
    w = est(s, size, mono, 0.3, weight) + 22
    return ('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s"/>' % (x, y, w, h, h / 2, fill)
            + text(x + 11, y + h / 2 + size * 0.36, s, size, color, weight, mono, 0.3)), w

def regular(t):
    return t is THEMES["light"]

# ---------------------------------------------------------------- cards

def hero(t, phone):
    alt = "%s. %s. %s %s" % (P["name"], P["faith"], P["dream"], P["role"])
    if phone:
        w, h = 440, 640
        px, py, pw, ph = 20, 20, 400, 300
    else:
        w, h = 880, 360
        px, py, pw, ph = 532, 24, 324, 312
    b = '<clipPath id="ph"><rect x="%g" y="%g" width="%g" height="%g" rx="18"/></clipPath>' % (px, py, pw, ph)
    b += '<rect x="%g" y="%g" width="%g" height="%g" rx="18" fill="%s"/>' % (px, py + 6, pw, ph, SWATCH["cyan"][1])
    b += '<image href="data:image/jpeg;base64,%s" x="%g" y="%g" width="%g" height="%g" preserveAspectRatio="xMidYMid slice" clip-path="url(#ph)"/>' % (
        PHOTO["square" if phone else "wide"], px, py, pw, ph)
    # the live pill on the photo
    lx, ly = px + 14, py + ph - 46
    pw2 = est("building Hintora", 13, False, 0, 650) + 58
    b += '<rect x="%g" y="%g" width="%g" height="32" rx="16" fill="#14120F" fill-opacity=".82"/>' % (lx, ly, pw2)
    b += mark("hintora", lx + 5, ly + 5, 22, t)
    b += text(lx + 34, ly + 21, "building Hintora", 13, "#F3EEE5", 650)
    b += '<circle cx="%g" cy="%g" r="4" fill="#3FD07A"/>' % (lx + pw2 - 14, ly + 16)
    fg, muted = t["fg"], t["muted"]
    if phone:
        x, y = 24, py + ph + 52
        b += cross(x, y - 13, 14, SWATCH["amber"][0])
        b += text(x + 22, y, P["faith"].upper(), 12, muted, 600, True, 2)
        b += text(x - 2, y + 62, "Georgi", 56, fg, 800, ls=-2.4)
        b += text(x - 2, y + 118, "Dryanovski", 56, fg, 800, ls=-2.4)
        b += text(x, y + 160, "Going to be the", 22, fg, 650, ls=-0.5)
        line2 = "greatest inventor in the world."
        mw = est(line2, 22, False, -0.5, 700) + 16
        b += '<rect x="%g" y="%g" width="%g" height="32" rx="6" fill="%s" transform="rotate(-1.2 %g %g)"/>' % (x - 8, y + 170, mw, SWATCH["sand"][0], x, y + 186)
        b += text(x, y + 193, line2, 22, "#14120F", 700, ls=-0.5)
        b += text(x, y + 230, "SOFTWARE ENGINEER · BURGAS, BG", 11.5, muted, 600, True, 1.6)
    else:
        x = 38
        b += cross(x, 46, 15, SWATCH["amber"][0])
        b += text(x + 24, 59, P["faith"].upper(), 12.5, muted, 600, True, 2.2)
        b += text(x - 3, 132, "Georgi", 70, fg, 800, ls=-3)
        b += text(x - 3, 200, "Dryanovski", 70, fg, 800, ls=-3)
        b += text(x, 248, "Going to be the", 25, fg, 650, ls=-0.6)
        line2 = "greatest inventor in the world."
        mw = est(line2, 25, False, -0.6, 700) + 18
        b += '<rect x="%g" y="%g" width="%g" height="36" rx="7" fill="%s" transform="rotate(-1.2 %g %g)"/>' % (x - 9, 259, mw, SWATCH["sand"][0], x, 277)
        b += text(x, 285, line2, 25, "#14120F", 700, ls=-0.6)
        b += text(x, 322, "SOFTWARE ENGINEER · BURGAS, BULGARIA", 12, muted, 600, True, 1.8)
    return svg(w, h, b, t, alt)

def stat_tiles(t, st, gh, npm_total, phone):
    big = [
        ("cyan", "calendar", fmt(st["last12"]), "contributions", "in the last year"),
        ("amber", "flame", fmt(st["best"][1]), "on my best day,", st["best"][0].strftime("%-d %b %Y")),
        ("sand", "trophy", "%d days" % st["longest"], "longest streak", "in a row"),
        ("ink", "chart", fmt(st["total"]), "contributions", "since %s" % gh["created"][:4]),
    ]
    small = [
        ("cyan", "bolt", str(st["active12"]), "active days"),
        ("amber", "box", fmt(npm_total), "npm downloads"),
        ("sand", "code", "6", "years shipping"),
    ]
    alt = "On GitHub: %s contributions in the last year, %s on the best day, a %d-day longest streak, %s since %s, %d active days, %s npm downloads this year." % (
        fmt(st["last12"]), fmt(st["best"][1]), st["longest"], fmt(st["total"]), gh["created"][:4], st["active12"], fmt(npm_total))
    w = 440 if phone else 880
    pad = 24
    b = text(pad, 50, "On GitHub", 26, t["fg"], 800, ls=-0.8)
    if not phone:
        b += text(w - pad, 48, "redrawn every night · %s" % TODAY.strftime("%-d %b %Y"), 12, t["muted"], 500, True, anchor="end")
    else:
        b += text(pad, 72, "redrawn every night · %s" % TODAY.strftime("%-d %b %Y"), 11, t["muted"], 500, True)
    cols = 2 if phone else 4
    gap = 14
    tw = (w - 2 * pad - (cols - 1) * gap) / cols
    th = 124
    y0 = 92 if phone else 74
    for i, (c, ic, num, l1, l2) in enumerate(big):
        x = pad + (i % cols) * (tw + gap); y = y0 + (i // cols) * (th + gap + 4)
        col = sw(t, c)
        b += tile(x, y, tw, th, col)
        b += icon(ic, x + tw - 38, y + 14, 22, col[2])
        b += text(x + 16, y + 62, num, 30 if phone else 34, col[2], 800, ls=-1.2)
        b += text(x + 16, y + 88, l1, 13.5, col[2], 600)
        b += text(x + 16, y + 106, l2, 13.5, col[2], 600, extra=' fill-opacity=".78"')
    y = y0 + ((len(big) - 1) // cols + 1) * (th + gap + 4) + 4
    scol = 1 if phone else 3
    sw_w = (w - 2 * pad - (scol - 1) * gap) / scol
    for i, (c, ic, num, lab) in enumerate(small):
        x = pad + (i % scol) * (sw_w + gap); yy = y + (i // scol) * 70
        col = sw(t, c)
        b += tile(x, yy, sw_w, 56, col, rx=14, depth=4)
        b += icon(ic, x + 16, yy + 16, 22, col[2])
        nw = est(num, 22, False, -0.6, 800)
        b += text(x + 50, yy + 36, num, 22, col[2], 800, ls=-0.6)
        b += text(x + 58 + nw, yy + 35, lab, 13.5, col[2], 600)
    h = y + ((len(small) - 1) // scol + 1) * 70 + 14
    return svg(w, int(h), b, t, alt)

def heatmap(t, st, phone):
    weeks = 26 if phone else 53
    w = 440 if phone else 880
    cell, gap = (12.5, 3.2) if phone else (12.4, 3)
    end = TODAY
    sunday = end - dt.timedelta(days=(end.weekday() + 1) % 7)
    start = sunday - dt.timedelta(days=(weeks - 1) * 7)
    counts = dict(st["days"])
    span = [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]
    total = sum(counts.get(d, 0) for d in span)
    nz = sorted(v for v in (counts.get(d, 0) for d in span) if v)
    qs = [nz[int(len(nz) * q)] for q in (0.25, 0.5, 0.75)] if nz else [1, 2, 3]
    level = lambda v: 0 if not v else 1 + sum(v > q for q in qs)
    gw = weeks * (cell + gap) - gap
    x0 = (w - gw) / 2
    y0 = 96
    title = "%s contributions" % fmt(total)
    b = text(x0, 50, title, 24 if phone else 26, t["fg"], 800, ls=-0.8)
    b += text(x0, 72, "every day of the last %s, private repos included" % ("6 months" if phone else "year"), 12, t["muted"], 500, True)
    lastm = None
    for d in span:
        col = (d - start).days // 7
        row = (d.weekday() + 1) % 7
        x = x0 + col * (cell + gap); y = y0 + row * (cell + gap)
        lv = level(counts.get(d, 0))
        b += '<rect x="%.1f" y="%.1f" width="%g" height="%g" rx="3.2" fill="%s"/>' % (x, y, cell, cell, t["heat"][lv])
        if d == st["best"][0]:
            b += '<rect x="%.1f" y="%.1f" width="%g" height="%g" rx="3.2" fill="none" stroke="%s" stroke-width="2"/>' % (x - 1.5, y - 1.5, cell + 3, cell + 3, SWATCH["amber"][0])
        if row == 0 and d.month != lastm and d.day <= 7:
            if col < weeks - 2:
                b += text(x, y0 - 10, d.strftime("%b"), 11, t["muted"], 500, True)
            lastm = d.month
    ly = y0 + 7 * (cell + gap) + 16
    lx = x0 + gw
    mw = est("More", 11, True) + 8
    b += text(lx, ly + 9.5, "More", 11, t["muted"], 500, True, anchor="end")
    for k in range(5):
        b += '<rect x="%g" y="%g" width="%g" height="%g" rx="3" fill="%s"/>' % (lx - mw - (5 - k) * (cell + 3) + 3, ly, cell, cell, t["heat"][k])
    b += text(lx - mw - 5 * (cell + 3) - 6, ly + 9.5, "Less", 11, t["muted"], 500, True, anchor="end")
    b += '<rect x="%g" y="%g" width="11" height="11" rx="3" fill="none" stroke="%s" stroke-width="2"/>' % (x0 + 1, ly + 1, SWATCH["amber"][0])
    b += text(x0 + 20, ly + 10, "best day: %s" % fmt(st["best"][1]), 11, t["muted"], 500, True)
    return svg(w, int(ly + 40), b, t, "%s contributions in the last %s" % (fmt(total), "6 months" if phone else "year")), total

def month_line(t, st, phone):
    w = 440 if phone else 880
    days = [(d, v) for d, v in st["days"] if d > TODAY - dt.timedelta(days=30)]
    total = sum(v for _, v in days)
    top = max([v for _, v in days] + [1])
    step = 50 if top <= 300 else 100 if top <= 600 else 200
    ymax = ((top // step) + 1) * step
    pad, x0, y0, ch = 24, 58 if not phone else 50, 96, 150
    cw = w - x0 - pad - 6
    b = text(pad, 50, "%s in the last 30 days" % fmt(total), 24 if phone else 26, t["fg"], 800, ls=-0.8)
    b += text(pad, 72, "contributions per day", 12, t["muted"], 500, True)
    for k in range(0, ymax + 1, step):
        y = y0 + ch - ch * k / ymax
        b += '<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-dasharray="3 5"/>' % (x0, y, x0 + cw, y, t["stroke"])
        b += text(x0 - 10, y + 4, str(k), 11, t["muted"], 500, True, anchor="end")
    n = len(days)
    pts = [(x0 + cw * i / max(n - 1, 1), y0 + ch - ch * v / ymax) for i, (_, v) in enumerate(days)]
    line = " ".join(("M" if i == 0 else "L") + "%.1f %.1f" % p for i, p in enumerate(pts))
    amber = SWATCH["amber"][0]
    b += '<defs><linearGradient id="fa" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s" stop-opacity=".38"/><stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient></defs>' % (amber, amber)
    b += '<path d="%s L%.1f %.1f L%.1f %.1f Z" fill="url(#fa)"/>' % (line, pts[-1][0], y0 + ch, pts[0][0], y0 + ch)
    b += '<path d="%s" fill="none" stroke="%s" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>' % (line, amber)
    for (x, y) in pts:
        b += '<circle cx="%.1f" cy="%.1f" r="3.6" fill="%s" stroke="%s" stroke-width="2"/>' % (x, y, t["panel"], amber)
    pk = max(range(n), key=lambda i: days[i][1])
    b += '<circle cx="%.1f" cy="%.1f" r="6" fill="%s"/>' % (pts[pk][0], pts[pk][1], amber)
    b += text(pts[pk][0], pts[pk][1] - 14, fmt(days[pk][1]), 12, t["fg"], 700, True, anchor="middle")
    b += text(x0, y0 + ch + 24, days[0][0].strftime("%-d %b"), 11, t["muted"], 500, True)
    b += text(x0 + cw, y0 + ch + 24, "today", 11, t["muted"], 500, True, anchor="end")
    return svg(w, y0 + ch + 46, b, t, "%s contributions in the last 30 days" % fmt(total)), total

def years_chart(t, st, phone):
    w = 440 if phone else 880
    ys = sorted(st["years"].items())
    top = max(v for _, v in ys) or 1
    pad, ch, y0 = 24, 150, 100
    slot = (w - 2 * pad) / len(ys)
    bw = min(70, slot * 0.64)
    b = text(pad, 50, "Year by year", 24 if phone else 26, t["fg"], 800, ls=-0.8)
    b += text(pad, 72, "the year it clicked: %d" % ys[-1][0], 12, t["muted"], 500, True)
    for i, (y, v) in enumerate(ys):
        hgt = max(6, ch * v / top)
        cx = pad + slot * i + slot / 2
        col = SWATCH["cyan"] if i == len(ys) - 1 else sw(t, "sand")
        b += tile(cx - bw / 2, y0 + ch - hgt, bw, hgt, col, rx=6, depth=4)
        b += text(cx, y0 + ch - hgt - 10, fmt(v), 12 if phone else 13, t["fg"], 700, True, anchor="middle")
        b += text(cx, y0 + ch + 26, ("'" + str(y)[2:]) if phone else str(y), 12, t["muted"], 500, True, anchor="middle")
    return svg(w, y0 + ch + 44, b, t, "Contributions per year: " + ", ".join("%d: %s" % (y, fmt(v)) for y, v in ys))

def terminal(t, st, phone):
    w = 440 if phone else 880
    size = 13 if phone else 15.5
    lh = size * 1.75
    lines = [
        ("$", "whoami"),
        ("", "georgi · software engineer · %s" % P["place"]),
        ("", "disciple of Jesus Christ"),
        ("$", "cat dream.txt"),
        (">", "going to be the greatest inventor in the world"),
        ("$", "cat now.txt"),
        (">", "founding engineer at Hintora: an assistant that sees your screen"),
        (">", "co-owner of Inkblot Studio: Citron, CRM + ERP + POS in one"),
        (">", "%s contributions this year, most in private repos" % fmt(st["last12"])),
        ("$", "cat rule.txt"),
        (">", "He leads. I only row."),
        ("$", ""),
    ]
    maxw = w - 56
    rows = []
    for k, s in lines:
        parts = wrap(s, maxw - (22 if k == ">" else 0), size, 400, True) or [""]
        for j, p in enumerate(parts):
            rows.append((k if j == 0 else ("" if k != ">" else " "), p, k))
    h = 64 + len(rows) * lh + 24
    ink = "#101215"
    b = '<rect x="0" y="0" width="%d" height="%d" rx="22" fill="%s"/>' % (w, h, ink)
    b += '<rect x="0" y="0" width="%d" height="44" rx="22" fill="#191C21"/><rect x="0" y="30" width="%d" height="14" fill="#191C21"/>' % (w, w)
    for i, c in enumerate(("#F2601C", "#E8D5B9", "#2AA9DC")):
        b += '<circle cx="%d" cy="22" r="6.5" fill="%s"/>' % (24 + i * 22, c)
    b += text(w / 2, 27, "georgi@burgas: ~", 12.5, "#7E8792", 500, True, anchor="middle")
    y = 64 + size
    for k, s, kind in rows:
        x = 26
        if k == "$":
            b += text(x, y, "$", size, "#F2601C", 700, True)
            if s:
                b += text(x + size * 1.3, y, s, size, "#F3EEE5", 700, True)
            else:
                b += '<rect x="%g" y="%g" width="%g" height="%g" fill="#2AA9DC"/>' % (x + size * 1.3, y - size * 0.85, size * 0.6, size * 1.05)
        elif kind == ">":
            if k == ">":
                b += text(x, y, "→", size, "#3FD07A", 700, True)
            color = "#E8D5B9" if ("inventor" in s or "row" in s) else "#C9CED6"
            b += text(x + 22, y, s, size, color, 600 if color == "#E8D5B9" else 400, True)
        else:
            b += text(x, y, s, size, "#C9CED6", 400, True)
        y += lh
    return svg(w, int(h), b, t, "whoami: " + "; ".join(s for _, s in lines if s), panel=False)

def sticker(t, s, color, note, phone):
    w = 440 if phone else 880
    col = sw(t, color)
    size = 20 if phone else 22
    tw = est(s, size, False, -0.4, 800) + 36
    b = '<g transform="rotate(-2 %g 36)">%s%s</g>' % (tw / 2 + 6, tile(6, 12, tw, 44, col, rx=12, depth=5),
                                                      text(24, 12 + 22 + size * 0.36, s, size, col[2], 800, ls=-0.4))
    if note:
        nx = tw + 26
        nw = est(note, 12, True, 0.3) + 22
        b += '<rect x="%g" y="21" width="%g" height="26" rx="8" fill="%s" stroke="%s"/>' % (nx, nw, t["panel"], t["stroke"])
        b += text(nx + 11, 38.5, note, 12, t["muted"], 600, True, 0.3)
    return svg(w, 72, b, t, s, panel=False)

def work_card(t, job, phone):
    w = 440 if phone else 880
    pad = 26
    logo = 72
    colors = {"hintora": "orange", "inkblot": "ink", "verasoft": "cyan"}
    col = sw(t, colors[job["id"]])
    b = ""
    # logo tile with depth
    b += '<rect x="%g" y="%g" width="%g" height="%g" rx="18" fill="%s"/>' % (pad, pad + 5, logo, logo, col[1])
    if job["id"] in ("hintora", "inkblot"):
        b += mark(job["id"], pad, pad, logo, t)
    else:
        b += '<rect x="%g" y="%g" width="%g" height="%g" rx="18" fill="%s"/>' % (pad, pad, logo, logo, col[0])
        b += text(pad + logo / 2, pad + 49, job["name"][0], 38, col[2], 800, anchor="middle")
    tx = pad + logo + 20
    b += text(tx, pad + 30, job["name"], 26 if phone else 30, t["fg"], 800, ls=-0.9)
    s, pw = pill(tx, pad + 44, "%s · since %s" % (job["role"].lower(), job["since"]), col[0], col[2], 11.5)
    b += s
    if job["url"]:
        if phone:
            pass
        else:
            dom = job["url"].replace("https://", "")
            dw = est(dom, 12.5, True, 0) + 52
            bx = w - pad - dw
            b += tile(bx, pad + 2, dw, 34, sw(t, "sand"), rx=10, depth=4)
            b += text(bx + 14, pad + 24, dom, 12.5, "#14120F", 600, True)
            b += icon("arrow", bx + dw - 28, pad + 10, 18, "#14120F", 2.4)
    y = pad + logo + 36
    xx = pad if phone else tx
    width = w - xx - pad
    for ln in wrap(job["line"], width, 16.5, 500):
        b += text(xx, y, ln, 16.5, t["fg"], 500); y += 24
    y += 2
    for ln in wrap(job["mine"], width, 14.5):
        b += text(xx, y, ln, 14.5, t["muted"]); y += 21
    y += 12
    cx = xx
    for c in job["chips"]:
        if c == "Citron":
            cw = est(c, 12, True, 0.3) + 46
            b += '<rect x="%g" y="%g" width="%g" height="26" rx="13" fill="none" stroke="%s"/>' % (cx, y, cw, t["stroke"])
            b += mark("citron", cx + 4, y + 3, 20, t)
            b += text(cx + 32, y + 17.5, c, 12, t["fg"], 600, True, 0.3)
        else:
            cw = est(c, 12, True, 0.3) + 22
            if cx + cw > w - pad:
                cx = xx; y += 34
            b += '<rect x="%g" y="%g" width="%g" height="26" rx="13" fill="none" stroke="%s"/>' % (cx, y, cw, t["stroke"])
            b += text(cx + 11, y + 17.5, c, 12, t["muted"], 600, True, 0.3)
        cx += cw + 8
    h = y + 26 + pad
    alt = "%s: %s, since %s. %s %s" % (job["name"], job["role"], job["since"], job["line"], job["mine"])
    return svg(w, int(h), b, t, alt)

def packages_card(t, npm, phone):
    w = 440 if phone else 880
    pad = 24
    gap = 14
    cols = 1 if phone else 3
    cw = (w - 2 * pad - (cols - 1) * gap) / cols
    b = ""
    y = pad
    rowh = 0
    alt = []
    tiles = ["cyan", "amber", "sand"]
    for i, p in enumerate(P["packages"]):
        dl = npm["downloads"].get(p["name"], 0)
        x = pad + (i % cols) * (cw + gap)
        yy = y + (i // cols) * (186 + gap) if not phone else pad + i * (172 + gap)
        col = sw(t, tiles[i])
        b += '<rect x="%g" y="%g" width="%g" height="%g" rx="16" fill="%s" stroke="%s"/>' % (x, yy, cw, 172 if phone else 186, t["panel"], t["stroke"])
        b += tile(x + 16, yy + 16, 40, 40, col, rx=11, depth=3)
        b += icon("box", x + 24, yy + 24, 24, col[2])
        scope, _, nm = p["name"].rpartition("/")
        b += text(x + 68, yy + 32, scope + "/", 12, t["muted"], 500, True)
        b += text(x + 68, yy + 51, nm, 15.5, t["fg"], 700, True)
        ty = yy + 84
        for ln in wrap(p["line"], cw - 32, 13.5)[:2]:
            b += text(x + 16, ty, ln, 13.5, t["muted"]); ty += 19
        b += text(x + 16, yy + (150 if phone else 162), fmt(dl), 28, t["fg"], 800, ls=-1)
        b += text(x + 22 + est(fmt(dl), 28, False, -1, 800), yy + (150 if phone else 162), "downloads this year", 12, t["muted"], 500, True)
        alt.append("%s, %s downloads in the last year" % (p["name"], fmt(dl)))
    h = (pad + 3 * (172 + gap) - gap + pad) if phone else (pad + 186 + pad)
    return svg(w, int(h), b, t, "Open source on npm: " + "; ".join(alt), grid=False)

def stack_card(t, phone):
    w = 440 if phone else 880
    pad = 26
    b = ""
    y = pad
    for k, items in P["stack"].items():
        b += text(pad, y + 17, k.upper(), 11.5, t["muted"], 600, True, 1.8)
        cx0 = pad if phone else pad + 90
        cx = cx0
        if phone: y += 28
        for c in items:
            cw = est(c, 13.5, True, 0.3) + 26
            if cx + cw > w - pad:
                cx = cx0; y += 40
            if k == "Daily":
                b += tile(cx, y, cw, 30, sw(t, "sand"), rx=10, depth=3)
                b += text(cx + 13, y + 20, c, 13.5, "#14120F", 700, True, 0.3)
            else:
                b += '<rect x="%g" y="%g" width="%g" height="30" rx="10" fill="none" stroke="%s"/>' % (cx, y, cw, t["stroke"])
                b += text(cx + 13, y + 20, c, 13.5, t["muted"], 600, True, 0.3)
            cx += cw + 9
        y += 52
    alt = "Stack. " + " ".join("%s: %s." % (k, ", ".join(v)) for k, v in P["stack"].items())
    return svg(w, int(y - 26 + pad), b, t, alt, grid=False)

LINK_LOOK = {"hintora.ai": ("orange", "globe"), "inkblotstudio.eu": ("ink", "globe"), "LinkedIn": ("cyan", "in"), "Instagram": ("amber", "camera")}

def badge(t, s):
    c, ic = LINK_LOOK.get(s, ("sand", "globe"))
    col = sw(t, c)
    w = est(s, 14.5, False, 0, 700) + 56
    body = tile(1, 1, w - 2, 38, col, rx=12, depth=4)
    body += icon(ic, 14, 10, 20, col[2])
    body += text(42, 26, s, 14.5, col[2], 700)
    return svg(int(w), 44, body, t, s, panel=False)

# ---------------------------------------------------------------- write

def picture(name, alt, width="100%", phone=True, height=None):
    size = ('height="%d"' % height) if height else ('width="%s"' % width)
    src = []
    if phone:
        src += ['<source media="(prefers-color-scheme: dark) and (max-width: 600px)" srcset="assets/%s-phone-dark.svg">' % name,
                '<source media="(max-width: 600px)" srcset="assets/%s-phone-light.svg">' % name]
    src.append('<source media="(prefers-color-scheme: dark)" srcset="assets/%s-dark.svg">' % name)
    return '<picture>%s<img src="assets/%s-light.svg" %s alt="%s"></picture>' % ("".join(src), name, size, escape(alt))

def main():
    state, stale = load_data()
    gh, npm = state["github"], state["npm"]
    st = stats(gh)
    npm_total = sum(npm["downloads"].values())
    os.makedirs(ASSETS, exist_ok=True)
    for f in os.listdir(ASSETS):
        if f.endswith(".svg"):
            os.remove(os.path.join(ASSETS, f))
    def put(name, fn, phone=True):
        for th in ("light", "dark"):
            for ph in ((False, True) if phone else (False,)):
                out = fn(THEMES[th], ph)
                if isinstance(out, tuple): out = out[0]
                open(os.path.join(ASSETS, "%s%s-%s.svg" % (name, "-phone" if ph else "", th)), "w", encoding="utf-8").write(out)
    put("hero", hero)
    put("stats", lambda t, ph: stat_tiles(t, st, gh, npm_total, ph))
    put("year", lambda t, ph: heatmap(t, st, ph))
    put("month", lambda t, ph: month_line(t, st, ph))
    put("years", lambda t, ph: years_chart(t, st, ph))
    put("whoami", lambda t, ph: terminal(t, st, ph))
    for job in P["work"]:
        put("work-" + job["id"], lambda t, ph, j=job: work_card(t, j, ph))
    put("packages", lambda t, ph: packages_card(t, npm, ph))
    put("stack", stack_card)
    labels = [("label-build", "What I'm building", "amber", "%d roles" % len(P["work"])),
              ("label-os", "Open source", "cyan", "on npm"),
              ("label-stack", "Stack", "sand", "")]
    for slug, s, c, note in labels:
        put(slug, lambda t, ph, s=s, c=c, n=note: sticker(t, s, c, n, ph))
    for i, l in enumerate(P["links"]):
        put("link-%d" % i, lambda t, ph, l=l: badge(t, l["label"]), phone=False)

    six = heatmap(THEMES["light"], st, True)[1]
    m30 = month_line(THEMES["light"], st, False)[1]
    y12 = st["last12"]
    links = "\n".join('<a href="%s">%s</a>' % (l["url"], picture("link-%d" % i, l["label"], phone=False, height=44)) for i, l in enumerate(P["links"]))
    work = "\n\n".join('%s%s%s' % ('<a href="%s">' % j["url"] if j["url"] else "", picture("work-" + j["id"], "%s, %s since %s. %s" % (j["name"], j["role"], j["since"], j["line"])), "</a>" if j["url"] else "") for j in P["work"])
    readme = """{hero}

<p align="center">
{links}
</p>

{stats}

{year}

{month}

{years}

{whoami}

{lbuild}

{work}

<p align="center"><sub>Earlier: {earlier}</sub></p>

{los}

{packages}

{lstack}

{stack}

<details>
<summary><b>Education and certificates</b></summary>

<br>

**B.Sc. Software Engineering** <sub>(in progress)</sub> · Burgas Free University<br>
**Vocational School of Computer Programming and Innovation** · Burgas, 2024

Microsoft Technology Associate in HTML and CSS (2020) and JavaScript (2021) ·
Adobe Certified Professional in Visual Design, Photoshop and Illustrator (2022) ·
Microsoft Office Specialist, Word (2020) · <sub>verifiable at certiport.com</sub>

</details>

<p align="center"><sub>Bulgarian, native · English, C1 · German, A2 · <a href="mailto:{email}">{email}</a></sub></p>

<p align="center"><sub>Every card is drawn by <code>scripts/build.py</code> and redrawn each night from live GitHub and npm data · Burgas, {asof}</sub></p>
""".format(
        hero=picture("hero", "%s. %s. %s %s" % (P["name"], P["faith"], P["dream"], P["role"])),
        links=links,
        stats=picture("stats", "On GitHub: %s contributions in the last year, %s on the best day, longest streak %d days, %s since %s, %d active days, %s npm downloads this year" % (
            fmt(y12), fmt(st["best"][1]), st["longest"], fmt(st["total"]), gh["created"][:4], st["active12"], fmt(npm_total))),
        year=picture("year", "%s contributions in the last year (phone: %s in the last 6 months)" % (fmt(y12), fmt(six))),
        m30=fmt(m30),
        month=picture("month", "%s contributions in the last 30 days" % fmt(m30)),
        years=picture("years", "Contributions per year: " + ", ".join("%d: %s" % (y, fmt(v)) for y, v in sorted(st["years"].items()))),
        whoami=picture("whoami", "whoami: georgi, software engineer, Burgas. Disciple of Jesus Christ. Dream: going to be the greatest inventor in the world. Rule: He leads. I only row."),
        lbuild=picture("label-build", "What I'm building"),
        work=work,
        earlier=escape(P["earlier"]),
        los=picture("label-os", "Open source"),
        packages=picture("packages", "Open source on npm: " + ", ".join("%s (%s downloads this year)" % (p["name"], fmt(npm["downloads"].get(p["name"], 0))) for p in P["packages"])),
        lstack=picture("label-stack", "Stack"),
        stack=picture("stack", "Stack: " + ", ".join(P["stack"]["Daily"] + P["stack"]["Also"])),
        email=P["email"],
        asof=TODAY.strftime("%-d %b %Y"),
    )
    open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
    print("built %d cards; last 12 months %s, best %s, longest %d, total %s, 30d %s" % (
        len([f for f in os.listdir(ASSETS) if f.endswith(".svg")]), fmt(y12), fmt(st["best"][1]), st["longest"], fmt(st["total"]), fmt(m30)))
    if stale:
        print("stale sources: " + ", ".join(stale), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
