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

FONT = {k: base64.b64encode(open(os.path.join(ROOT, "scripts", "fonts", f), "rb").read()).decode()
        for k, f in (("sans", "geist.woff2"), ("mono", "geist-mono.woff2"))}
SANS = "'Geist', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace"

THEMES = {
    "light": dict(card="#FBF8F2", line="#E7DFD2", fg="#14120F", muted="#6F685E", soft="#A39B8F",
                  accent="#3A2A1F", accent_bg="#E8D5B9", live="#2F8F4E",
                  heat=["#EEE8DE", "#E8D5B9", "#C9AE87", "#8A6E4E", "#3A2A1F"]),
    "dark": dict(card="#15130F", line="#2B2621", fg="#F3EEE5", muted="#9C958A", soft="#6E675E",
                 accent="#E8D5B9", accent_bg="#3A2A1F", live="#3FB950",
                 heat=["#201C17", "#3E3328", "#6E5B45", "#AA906F", "#E8D5B9"]),
}

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

def wrap(text, width, size, weight=400):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if est(t, size, weight=weight) * 1.07 > width and cur:
            lines.append(cur); cur = word
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines

def svg(w, h, body, t, alt, mono=False, bg=True):
    faces = "@font-face{font-family:'Geist';src:url(data:font/woff2;base64,%s) format('woff2');font-weight:100 900}" % FONT["sans"]
    if mono:
        faces += "@font-face{font-family:'Geist Mono';src:url(data:font/woff2;base64,%s) format('woff2');font-weight:100 900}" % FONT["mono"]
    card = '<rect x="0.5" y="0.5" width="%g" height="%g" rx="18" fill="%s" stroke="%s"/>' % (w - 1, h - 1, t["card"], t["line"]) if bg else ""
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-label="%s">'
            '<title>%s</title><style>%s</style>%s%s</svg>') % (w, h, w, h, escape(alt), escape(alt), faces, card, body)

def text(x, y, s, size, t, color="fg", weight=400, mono=False, ls=0, anchor="start", opacity=None):
    fam = MONO if mono else SANS
    op = ' fill-opacity="%s"' % opacity if opacity else ""
    return '<text x="%g" y="%g" font-family="%s" font-size="%g" font-weight="%d" letter-spacing="%g" fill="%s" text-anchor="%s"%s>%s</text>' % (
        x, y, escape(fam), size, weight, ls, t[color], anchor, op, escape(s))

def chip(x, y, s, t, size=12):
    w = est(s, size, mono=True, ls=0.4) + 20
    return ('<rect x="%g" y="%g" width="%g" height="24" rx="12" fill="none" stroke="%s"/>' % (x, y, w, t["line"])
            + text(x + 10, y + 16.5, s, size, t, "muted", 500, True, 0.4)), w

def label(s, t, w):
    """A section label: mono caps, then a hairline to the edge."""
    tw = est(s.upper(), 13, True, 2.2)
    body = text(2, 27, s.upper(), 13, t, "muted", 600, True, 2.2)
    body += '<line x1="%g" y1="22.5" x2="%g" y2="22.5" stroke="%s"/>' % (tw + 18, w - 2, t["line"])
    return svg(w, 40, body, t, s, mono=True, bg=False)

def cross(x, y, s, color):
    """A small Latin cross, drawn (emoji don't render inside SVG fonts)."""
    return ('<g fill="%s"><rect x="%g" y="%g" width="%g" height="%g" rx="0.8"/><rect x="%g" y="%g" width="%g" height="%g" rx="0.8"/></g>' %
            (color, x + s * 0.4, y, s * 0.2, s, x + s * 0.15, y + s * 0.26, s * 0.7, s * 0.2))

def fmt(n):
    return "{:,}".format(n)

# ---------------------------------------------------------------- cards

def hero(t, phone):
    w = 440 if phone else 880
    h = 300 if phone else 262
    b = ""
    b += cross(2, 14, 15, t["accent"])
    b += text(26, 27, P["faith"].upper(), 12.5, t, "muted", 600, True, 2)
    if not phone:
        lt = "%s · %s" % (P["now"].upper(), P["place"].upper())
        tw = est(lt, 12.5, True, 2)
        b += '<circle cx="%g" cy="22.5" r="4.5" fill="%s"/><circle cx="%g" cy="22.5" r="8" fill="none" stroke="%s" stroke-opacity=".35"/>' % (w - tw - 18, t["live"], w - tw - 18, t["live"])
        b += text(w, 27, lt, 12.5, t, "muted", 600, True, 2, "end")
    if phone:
        b += text(-2, 96, "Georgi", 50, t, "fg", 650, ls=-2)
        b += text(-2, 146, "Dryanovski", 50, t, "fg", 650, ls=-2)
        y = 190
        for ln in wrap(P["dream"], 400, 22, 500):
            b += text(0, y, ln, 22, t, "accent", 550, ls=-0.4); y += 29
        for ln in wrap(P["role"], 420, 15.5):
            b += text(0, y + 8, ln, 15.5, t, "muted"); y += 22
        b += '<circle cx="5" cy="%g" r="4" fill="%s"/>' % (y + 28, t["live"])
        b += text(17, y + 32, "%s · %s" % (P["now"].upper(), P["place"].upper()), 11, t, "muted", 600, True, 1.6)
    else:
        b += text(-4, 122, P["name"], 76, t, "fg", 650, ls=-3.2)
        b += text(0, 180, P["dream"], 31, t, "accent", 550, ls=-0.7)
        b += text(0, 222, P["role"], 19, t, "muted", 400, ls=-0.2)
    alt = "%s. %s %s %s" % (P["name"], P["faith"] + ".", P["dream"], P["role"])
    return svg(w, h, b, t, alt, mono=True, bg=False)

def stat_tiles(t, st, gh, phone):
    tiles = [
        (fmt(st["last12"]), "contributions", "last 12 months"),
        (str(st["active12"]), "active days", "last 12 months"),
        (fmt(st["best"][1]), "on my best day", st["best"][0].strftime("%-d %b %Y")),
        ("%d days" % st["longest"], "longest streak", "in a row"),
        (fmt(st["total"]), "contributions", "since %s" % gh["created"][:4]),
    ]
    alt = "On GitHub: %s contributions in the last 12 months over %d active days, %s on the best day, a longest streak of %d days, %s contributions since %s." % (
        fmt(st["last12"]), st["active12"], fmt(st["best"][1]), st["longest"], fmt(st["total"]), gh["created"][:4])
    if phone:
        w, cols, th = 440, 2, 92
        rows = (len(tiles) + 1) // 2
        h = 24 + rows * th + 8
    else:
        w, cols, th = 880, 5, 0
        h = 128
    b = ""
    for i, (big, l1, l2) in enumerate(tiles):
        if phone:
            if i == len(tiles) - 1 and len(tiles) % 2:
                cw, cx = w - 48, 24
            else:
                cw = (w - 48) / 2; cx = 24 + (i % 2) * cw
            cy = 24 + (i // 2) * th
            b += text(cx, cy + 36, big, 30, t, "accent" if i == 0 else "fg", 650, ls=-1)
            b += text(cx, cy + 58, l1, 13.5, t, "fg", 500)
            if l2: b += text(cx, cy + 76, l2, 12, t, "muted", 500, True, 0.3)
        else:
            cw = (w - 56) / cols; cx = 28 + i * cw
            if i: b += '<line x1="%g" y1="28" x2="%g" y2="100" stroke="%s"/>' % (cx - 14, cx - 14, t["line"])
            b += text(cx, 64, big, 34, t, "accent" if i == 0 else "fg", 650, ls=-1.2)
            b += text(cx, 88, l1, 14, t, "fg", 500)
            if l2: b += text(cx, 106, l2, 12, t, "muted", 500, True, 0.3)
    return svg(w, h, b, t, alt, mono=True)

def heatmap(t, st, phone):
    weeks = 26 if phone else 53
    w = 440 if phone else 880
    cell, gap = (12.5, 3.2) if phone else (12.4, 3)
    end = TODAY
    sunday = end - dt.timedelta(days=(end.weekday() + 1) % 7)  # the Sunday that starts this week
    start = sunday - dt.timedelta(days=(weeks - 1) * 7)
    counts = {d: v for d, v in st["days"]}
    span = [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]
    total = sum(counts.get(d, 0) for d in span)
    nz = sorted(v for v in (counts.get(d, 0) for d in span) if v)
    qs = [nz[int(len(nz) * q)] for q in (0.25, 0.5, 0.75)] if nz else [1, 2, 3]
    def level(v):
        if not v: return 0
        return 1 + sum(v > q for q in qs)
    gw = weeks * (cell + gap) - gap
    x0 = (w - gw) / 2
    y0 = 82
    b = ""
    title = "%s contributions in the last %s" % (fmt(total), "6 months" if phone else "year")
    b += text(x0, 40, title, 18 if phone else 20, t, "fg", 600, ls=-0.3)
    lastm = None
    for i, d in enumerate(span):
        col = (d - start).days // 7
        row = (d.weekday() + 1) % 7
        x = x0 + col * (cell + gap); y = y0 + row * (cell + gap)
        b += '<rect x="%.1f" y="%.1f" width="%g" height="%g" rx="3" fill="%s"/>' % (x, y, cell, cell, t["heat"][level(counts.get(d, 0))])
        if row == 0 and d.month != lastm and d.day <= 7:
            if col < weeks - 2:
                b += text(x, y0 - 10, d.strftime("%b"), 11, t, "muted", 500, True)
            lastm = d.month
    ly = y0 + 7 * (cell + gap) + 18
    lx = x0 + gw
    mw = est("More", 11, True) + 8
    b += text(lx, ly + 9.5, "More", 11, t, "muted", 500, True, anchor="end")
    for k in range(5):
        b += '<rect x="%g" y="%g" width="%g" height="%g" rx="3" fill="%s"/>' % (lx - mw - (5 - k) * (cell + 3) + 3, ly, cell, cell, t["heat"][k])
    b += text(lx - mw - 5 * (cell + 3) - 6, ly + 9.5, "Less", 11, t, "muted", 500, True, anchor="end")
    b += text(x0, ly + 9.5, "private repos included" if phone else "private repos included, as on GitHub", 11, t, "soft", 500, True)
    h = ly + 36
    return svg(w, int(h), b, t, title, mono=True), total

def years_chart(t, st, phone):
    w = 440 if phone else 880
    ys = sorted(st["years"].items())
    top = max(v for _, v in ys) or 1
    pad = 28
    ch = 150
    y0 = 62
    n = len(ys)
    slot = (w - 2 * pad) / n
    bw = min(64, slot * 0.62)
    b = text(pad, 40, "Year by year", 18 if phone else 20, t, "fg", 600, ls=-0.3)
    for i, (y, v) in enumerate(ys):
        hgt = max(3, ch * v / top)
        cx = pad + slot * i + slot / 2
        last = i == n - 1
        b += '<rect x="%g" y="%g" width="%g" height="%g" rx="5" fill="%s"/>' % (cx - bw / 2, y0 + ch - hgt, bw, hgt, t["heat"][4] if last else t["heat"][2])
        b += text(cx, y0 + ch - hgt - 9, fmt(v), 12 if phone else 13, t, "fg" if last else "muted", 600, True, anchor="middle")
        b += text(cx, y0 + ch + 22, ("'" + str(y)[2:]) if phone else str(y), 12, t, "muted", 500, True, anchor="middle")
    alt = "Contributions per year: " + ", ".join("%d: %s" % (y, fmt(v)) for y, v in ys)
    return svg(w, y0 + ch + 44, b, t, alt, mono=True)

def work_card(t, job, phone):
    w = 440 if phone else 880
    pad = 26
    tile = 56
    b = '<rect x="%g" y="%g" width="%g" height="%g" rx="14" fill="%s"/>' % (pad, pad, tile, tile, t["accent_bg"])
    b += text(pad + tile / 2, pad + 38, job["name"][0], 28, t, "accent", 700, anchor="middle")
    tx = pad + tile + 18
    b += text(tx, pad + 24, job["name"], 23, t, "fg", 650, ls=-0.5)
    b += text(tx, pad + 48, "%s · since %s" % (job["role"].upper(), job["since"]), 11.5, t, "muted", 600, True, 1.2)
    if job["url"] and not phone:
        b += text(w - pad, pad + 24, job["url"].replace("https://", "") + " ↗", 13, t, "muted", 500, True, anchor="end")
    y = pad + tile + 34
    width = w - 2 * pad if phone else w - tx - pad
    xx = pad if phone else tx
    for ln in wrap(job["line"], width, 16):
        b += text(xx, y, ln, 16, t, "fg"); y += 23
    y += 4
    for ln in wrap(job["mine"], width, 14.5):
        b += text(xx, y, ln, 14.5, t, "muted"); y += 21
    y += 12
    cx = xx
    for c in job["chips"]:
        cw = est(c, 12, True, 0.4) + 20
        if cx + cw > w - pad:
            cx = xx; y += 32
        s, cw = chip(cx, y, c, t); b += s; cx += cw + 8
    h = y + 24 + pad
    alt = "%s: %s, since %s. %s %s" % (job["name"], job["role"], job["since"], job["line"], job["mine"])
    return svg(w, int(h), b, t, alt, mono=True)

def packages_card(t, npm, phone):
    w = 440 if phone else 880
    pad = 26
    b = ""
    y = pad
    alt = []
    for i, p in enumerate(P["packages"]):
        dl = npm["downloads"].get(p["name"], 0)
        if i:
            b += '<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s"/>' % (pad, y - 14, w - pad, y - 14, t["line"])
        b += text(pad, y + 18, p["name"], 15 if phone else 16, t, "fg", 600, True)
        yy = y + 42
        for ln in wrap(p["line"], (w - 2 * pad) if phone else (w - 2 * pad - 170), 14):
            b += text(pad, yy, ln, 14, t, "muted"); yy += 20
        if phone:
            b += text(pad, yy + 4, "%s downloads this year" % fmt(dl), 12, t, "accent", 600, True); yy += 22
        else:
            b += text(w - pad, y + 22, fmt(dl), 24, t, "accent", 650, anchor="end", ls=-0.6)
            b += text(w - pad, y + 42, "downloads / year", 11, t, "muted", 500, True, anchor="end")
        y = max(yy, y + 52) + 24
        alt.append("%s, %s downloads in the last year" % (p["name"], fmt(dl)))
    return svg(w, int(y - 2), b, t, "Open source on npm: " + "; ".join(alt), mono=True)

def stack_card(t, phone):
    w = 440 if phone else 880
    pad = 26
    b = ""
    y = pad
    for k, items in P["stack"].items():
        b += text(pad, y + 16, k.upper(), 11.5, t, "muted", 600, True, 1.6)
        cx = pad if phone else pad + 90
        if phone: y += 28
        for c in items:
            cw = est(c, 13, True, 0.4) + 22
            if cx + cw > w - pad:
                cx = pad if phone else pad + 90; y += 34
            b += '<rect x="%g" y="%g" width="%g" height="26" rx="13" fill="%s"/>' % (cx, y, cw, t["accent_bg"] if k == "Daily" else t["card"])
            if k != "Daily":
                b += '<rect x="%g" y="%g" width="%g" height="26" rx="13" fill="none" stroke="%s"/>' % (cx, y, cw, t["line"])
            b += text(cx + 11, y + 17.5, c, 13, t, "accent" if k == "Daily" else "muted", 600, True, 0.4)
            cx += cw + 8
        y += 46
    alt = "Stack. " + " ".join("%s: %s." % (k, ", ".join(v)) for k, v in P["stack"].items())
    return svg(w, int(y - 20 + pad), b, t, alt, mono=True)

def badge(t, s):
    w = est(s, 14, False, 0, 500) + 36
    body = '<rect x="0.5" y="0.5" width="%g" height="39" rx="20" fill="%s" stroke="%s"/>' % (w - 1, t["card"], t["line"])
    body += text(18, 25.5, s, 14, t, "fg", 550)
    return svg(int(w), 40, body, t, s, bg=False)

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
    os.makedirs(ASSETS, exist_ok=True)
    for f in os.listdir(ASSETS):
        if f.endswith(".svg"):
            os.remove(os.path.join(ASSETS, f))
    alts = {}
    def put(name, fn, phone=True):
        for th in ("light", "dark"):
            for ph in ((False, True) if phone else (False,)):
                out = fn(THEMES[th], ph)
                if isinstance(out, tuple): out = out[0]
                open(os.path.join(ASSETS, "%s%s-%s.svg" % (name, "-phone" if ph else "", th)), "w", encoding="utf-8").write(out)
    put("hero", hero)
    put("stats", lambda t, ph: stat_tiles(t, st, gh, ph))
    put("year", lambda t, ph: heatmap(t, st, ph))
    put("years", lambda t, ph: years_chart(t, st, ph))
    for job in P["work"]:
        put("work-" + job["id"], lambda t, ph, j=job: work_card(t, j, ph))
    put("packages", lambda t, ph: packages_card(t, npm, ph))
    put("stack", stack_card)
    for s in ("Now", "Open source", "Stack"):
        slug = "label-" + s.lower().replace(" ", "-")
        put(slug, lambda t, ph, s=s: label(s, t, 440 if ph else 880))
    for i, l in enumerate(P["links"]):
        put("link-%d" % i, lambda t, ph, l=l: badge(t, l["label"]), phone=False)

    six = heatmap(THEMES["light"], st, True)[1]
    y12 = st["last12"]
    links = "\n".join('<a href="%s">%s</a>' % (l["url"], picture("link-%d" % i, l["label"], phone=False, height=40)) for i, l in enumerate(P["links"]))
    work = "\n\n".join('%s%s%s' % ('<a href="%s">' % j["url"] if j["url"] else "", picture("work-" + j["id"], "%s, %s" % (j["name"], j["role"])), "</a>" if j["url"] else "") for j in P["work"])
    readme = """{hero}

<p>
{links}
</p>

{stats}

<details open><summary><sub>Activity</sub></summary>

{year}

</details>

{years}

{lnow}

{work}

<p><sub>Earlier: {earlier}</sub></p>

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

<p><sub>Bulgarian, native · English, C1 · German, A2 · <a href="mailto:{email}">{email}</a></sub></p>

<p align="center"><sub>Every card here is drawn by <code>scripts/build.py</code> and redrawn each night from live GitHub and npm data. Updated {asof}.</sub></p>
""".format(
        hero=picture("hero", "%s. %s. %s %s" % (P["name"], P["faith"], P["dream"], P["role"])),
        links=links,
        stats=picture("stats", "%s contributions in the last 12 months over %d active days, %s on the best day, longest streak %d days, %s since %s" % (fmt(y12), st["active12"], fmt(st["best"][1]), st["longest"], fmt(st["total"]), gh["created"][:4])),
        y12=fmt(y12),
        year=picture("year", "%s contributions in the last year (phone: %s in the last 6 months)" % (fmt(y12), fmt(six))),
        years=picture("years", "Contributions per year: " + ", ".join("%d: %s" % (y, fmt(v)) for y, v in sorted(st["years"].items()))),
        lnow=picture("label-now", "Now"),
        work=work,
        earlier=escape(P["earlier"]),
        los=picture("label-open-source", "Open source"),
        packages=picture("packages", "Open source on npm: " + ", ".join("%s (%s downloads this year)" % (p["name"], fmt(npm["downloads"].get(p["name"], 0))) for p in P["packages"])),
        lstack=picture("label-stack", "Stack"),
        stack=picture("stack", "Stack: " + ", ".join(P["stack"]["Daily"] + P["stack"]["Also"])),
        email=P["email"],
        asof=TODAY.strftime("%-d %b %Y"),
    )
    open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
    print("built %d cards; last 12 months %s, streak %d, longest %d, total %s" % (
        len([f for f in os.listdir(ASSETS) if f.endswith(".svg")]), fmt(y12), st["current"], st["longest"], fmt(st["total"])))
    if stale:
        print("stale sources: " + ", ".join(stale), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
