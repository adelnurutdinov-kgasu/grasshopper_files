import math, csv

HOURS = [("5-19", 7), ("6-18", 6), ("7-17", 5), ("8-16", 4), ("9-15", 3), ("10-14", 2), ("11-13", 1), ("12", 0)]
WALL, LOG_D, LOG_W, TOP = 0.51, 1.2, 3.3, 0.4


def hm(t):
    m = int(round(t * 60))
    return "%d:%02d" % (m // 60, m % 60)


def dur(h):
    m = int(round(h * 60))
    return "%d ч %02d мин" % (m // 60, m % 60) if m >= 60 else "%d мин" % m


def parse_t(s):
    h, m = s.split(":")
    return int(h) + int(m) / 60.0


def sun_table(c):
    pts = []
    for key, n in HOURS:
        a, h = c.get("аз_" + key, ""), c.get("выс_" + key, "")
        if a == "" or h == "":
            continue
        a, h = float(a), float(h)
        if n == 0:
            pts.append((12.0, 0.0, h))
        else:
            pts.append((12.0 - n, a, h)); pts.append((12.0 + n, -a, h))
    tr, ts, ar = parse_t(c["восход"]), parse_t(c["закат"]), float(c["аз_восход"])
    pts += [(tr, ar, 0.0), (ts, -ar, 0.0)]
    pts.sort()
    return pts, tr, ts


def _cr(p0, p1, p2, p3, t0, t1, t2, t3, t):
    # Catmull-Rom (non-uniform, centripetal-free, time-parametrised) via Hermite tangents
    m1 = (p2 - p0) / (t2 - t0)
    m2 = (p3 - p1) / (t3 - t1)
    h = t2 - t1; s = (t - t1) / h
    h00 = 2 * s**3 - 3 * s**2 + 1; h10 = s**3 - 2 * s**2 + s
    h01 = -2 * s**3 + 3 * s**2; h11 = s**3 - s**2
    return h00 * p1 + h10 * h * m1 + h01 * p2 + h11 * h * m2


def sun_at(pts, t):
    if t <= pts[0][0] or t >= pts[-1][0]:
        return None
    n = len(pts)
    for i in range(n - 1):
        if pts[i][0] <= t <= pts[i + 1][0]:
            i0, i3 = max(i - 1, 0), min(i + 2, n - 1)
            T = [pts[j][0] for j in (i0, i, i + 1, i3)]
            if T[0] == T[1]: T[0] = T[1] - (T[2] - T[1])
            if T[3] == T[2]: T[3] = T[2] + (T[2] - T[1])
            def comp(k):
                P = [pts[j][k] for j in (i0, i, i + 1, i3)]
                if i0 == i: P[0] = 2 * P[1] - P[2]
                if i3 == i + 1: P[3] = 2 * P[2] - P[1]
                return _cr(P[0], P[1], P[2], P[3], T[0], T[1], T[2], T[3], t)
            return comp(1), max(comp(2), 0.0)


def time_of_az(pts, az):
    lo, hi = pts[0][0] + 1e-6, pts[-1][0] - 1e-6
    f = lambda t: sun_at(pts, t)[0] - az
    if f(lo) * f(hi) > 0:
        return None
    for _ in range(60):
        m = (lo + hi) / 2
        if f(lo) * f(m) <= 0: hi = m
        else: lo = m
    return (lo + hi) / 2


def sdir(az):
    r = math.radians(az)
    return math.sin(r), -math.cos(r)


def rot(p, deg):
    r = math.radians(deg); c, s = math.cos(r), math.sin(r)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def ray_poly(o, d, poly):
    """distance along ray to first entry into convex polygon, or None"""
    tin, tout = -1e9, 1e9
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        nx, ny = ey, -ex
        cx = sum(p[0] for p in poly) / n; cy = sum(p[1] for p in poly) / n
        if (cx - a[0]) * nx + (cy - a[1]) * ny > 0:
            nx, ny = -nx, -ny
        den = d[0] * nx + d[1] * ny
        num = (a[0] - o[0]) * nx + (a[1] - o[1]) * ny
        if abs(den) < 1e-12:
            if num < 0:
                return None
            continue
        t = num / den
        if den < 0:
            tin = max(tin, t)
        else:
            tout = min(tout, t)
    if tin > tout or tout < 0:
        return None
    return max(tin, 0.0)


def shaded(o, az, alt, blds):
    d = sdir(az)
    ta = math.tan(math.radians(alt))
    for poly, H in blds:
        t = ray_poly(o, d, poly)
        if t is not None and t * ta < H:
            return True
    return False


def periods(pred, t0, t1, step=1 / 60.0):
    out, cur = [], None
    n = int(round((t1 - t0) / step))
    for i in range(n + 1):
        t = t0 + i * step
        ok = pred(t)
        if ok and cur is None:
            cur = t
        if not ok and cur is not None:
            out.append((cur, t)); cur = None
    if cur is not None:
        out.append((cur, t1))
    return [(a, b) for a, b in out if b - a > 1e-9]


def r5(t):
    return round(t * 12) / 12.0


def fmt_periods(ps):
    return ", ".join("%s–%s" % (hm(r5(a)), hm(r5(b))) for a, b in ps) if ps else "нет"


def norm_for(lat):
    if lat > 58: return 2.5, 1.5, "северная зона (севернее 58° с.ш.)"
    if lat >= 48: return 2.0, 1.0, "центральная зона (58–48° с.ш.)"
    return 1.5, 1.0, "южная зона (южнее 48° с.ш.)"


def verdict(ps, D):
    tot = sum(b - a for a, b in ps)
    mx = max([b - a for a, b in ps], default=0.0)
    if mx >= D - 1e-6:
        return tot, True, "непрерывно %s ≥ %s — соответствует СанПиН" % (dur(mx), dur(D))
    if len(ps) > 1 and mx >= 1.0 - 1e-6 and tot >= D + 0.5 - 1e-6:
        return tot, True, "прерывисто %s (≥ %s, период ≥ 1 ч) — соответствует СанПиН" % (dur(tot), dur(D + 0.5))
    return tot, False, "не соответствует СанПиН (нужно непрерывно ≥ %s или прерывисто ≥ %s)" % (dur(D), dur(D + 0.5))


def solve(city, var, lat):
    pts, tr, ts = sun_table(city)
    D, excl, zone = norm_for(lat)
    t0, t1 = tr + excl, ts - excl
    A0, L, H, l = (float(var["схема_%d" % k]) for k in range(1, 5))
    H1, H2, H3 = float(var["H1"]), float(var["H2"]), float(var["H3"])
    h_ok, b_ok = float(var["окно_1"]), float(var["окно_2"])
    rotd = float(city["разворот"])
    R = {"город": city["название"], "широта": lat, "норма": D, "зона": zone, "учёт": (t0, t1)}

    # --- задачи 4-5: точка у здания 60x12, схема рис.1
    n = sdir(A0); u = (-math.cos(math.radians(A0)), -math.sin(math.radians(A0)))
    def P(s, q): return (s * u[0] + q * n[0], s * u[1] + q * n[1])
    b1 = [P(l - 60, L), P(l, L), P(l, L + 12), P(l - 60, L + 12)]
    sun = lambda t: sun_at(pts, t)
    def lit(o, blds, extra=None):
        def f(t):
            s = sun(t)
            if s is None or s[1] <= 0: return False
            if extra and not extra(s): return False
            return not shaded(o, s[0], s[1], blds)
        return f
    ps = periods(lit((0, 0), [(b1, H)]), t0, t1)
    sh = periods(lambda t: sun(t) is not None and shaded((0, 0), sun(t)[0], sun(t)[1], [(b1, H)]), t0, t1)
    R["з4"] = dict(shade=sh, lit=ps, total=sum(b - a for a, b in ps))

    # --- схема рис.2 (RT площадки = начало координат), поворот на разворот
    RT = (60.0, 69.0)
    raw = [([(0, 28), (12, 28), (12, 102), (0, 102)], H1),
           ([(12, 0), (108, 0), (108, 12), (12, 12)], H2),
           ([(108, 28), (120, 28), (120, 102), (108, 102)], H3)]
    def place(p, origin): return rot((p[0] - origin[0], p[1] - origin[1]), rotd)
    blds = [([place(p, RT) for p in poly], h) for poly, h in raw]
    ps = periods(lit((0, 0), blds), t0, t1)
    R["з6"] = dict(lit=ps, total=sum(b - a for a, b in ps))

    # --- задачи 8-9: РТ1 (12,92), РТ2 (12,40) на восточном фасаде здания 1
    n_az = 90.0 + rotd
    dw = math.degrees(math.atan((WALL / 2) / b_ok))
    vw = math.degrees(math.atan(h_ok / (WALL / 2)))
    dl = math.degrees(math.atan((LOG_D + WALL / 2) / (LOG_W / 2 + b_ok / 2)))
    vl = math.degrees(math.atan((h_ok + TOP) / (LOG_D + WALL / 2)))
    R["углы"] = dict(окно_г=180 - 2 * dw, окно_в=vw, лоджия_г=180 - 2 * dl, лоджия_в=vl)
    for key, pt in (("РТ1", (12, 92)), ("РТ2", (12, 40))):
        o = place(pt, RT)
        others = [blds[1], blds[2]]
        for kind, dd, vv in (("окно", dw, vw), ("лоджия", dl, vl)):
            win = lambda s, dd=dd, vv=vv: abs(((s[0] - n_az + 180) % 360) - 180) < 90 - dd and s[1] < vv
            p8 = periods(lit(o, others, win), t0, t1)
            tot, okk, txt = verdict(p8, D)
            R["з8_%s_%s" % (key, kind)] = dict(lit=p8, total=tot, ok=okk, txt=txt)

    # --- задача 10: ГИЗ
    ag = dw
    az_B = A0 - 90 + ag
    tB = time_of_az(pts, az_B)
    tV = tB - D if tB is not None else None
    azV = sun_at(pts, tV)[0] if tV is not None and sun_at(pts, tV) else None
    R["з10"] = dict(a_giz=ag, tB=tB, tV=tV, azB=az_B, azV=azV)
    return R


def lines(R, v):
    out = []
    z4 = R["з4"]; z6 = R["з6"]; z10 = R["з10"]
    out.append("ВЫВОДЫ · вариант %s · %s, %.1f° с.ш., %s; норма непрерывной инсоляции %s" % (v, R["город"], R["широта"], R["зона"], dur(R["норма"])))
    out.append("Учётное время: %s–%s (без первого часа после восхода и последнего перед закатом)" % (hm(R["учёт"][0]), hm(R["учёт"][1])))
    out.append("Задачи 4–5 · точка вблизи затеняющего здания: РТ затеняется %s; инсолируется %s, всего %s." % (fmt_periods(z4["shade"]), fmt_periods(z4["lit"]), dur(z4["total"])))
    out.append("Задачи 6–7 · РТ на детской площадке: инсолируется %s, всего %s (для площадок норма — 3 ч на 50 %% площади)." % (fmt_periods(z6["lit"]), dur(z6["total"])))
    a = R["углы"]
    out.append("Задачи 8–9 · инсоляционные углы: окно %.0f° / %.0f°, окно с лоджией %.0f° / %.0f° (гориз. / верт.)." % (a["окно_г"], a["окно_в"], a["лоджия_г"], a["лоджия_в"]))
    for k in ("РТ1", "РТ2"):
        for kind, name in (("окно", "окно без лоджии"), ("лоджия", "окно с лоджией")):
            r = R["з8_%s_%s" % (k, kind)]
            out.append("  %s, %s: %s — %s." % (k, name, fmt_periods(r["lit"]), r["txt"]))
    if z10["tB"] is not None:
        out.append("Задача 10 · ГИЗ: a_гиз = %.0f°; конец инсоляции Б = %s (A₀ = %.1f°), начало В = Б − %s = %s (A₀ = %.1f°)." % (
            z10["a_giz"], hm(r5(z10["tB"])), z10["azB"], dur(R["норма"]), hm(r5(z10["tV"])), z10["azV"] if z10["azV"] is not None else float("nan")))
    return out


if __name__ == "__main__":
    import sys
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig")))
    city = {r["код"]: r for r in rows if r["тип"] == "город"}
    var = {r["код"]: r for r in rows if r["тип"] == "вариант"}
    LAT = {"0": 44.7, "1": 57.6, "2": 55.8, "3": 56.3, "4": 56.8, "5": 54.3, "6": 53.2, "7": 51.5, "8": 48.7, "9": 46.3}
    for v in sys.argv[2:]:
        R = solve(city[v[1]], var[v[2]], LAT[v[1]])
        print("\n".join(lines(R, v))); print()
