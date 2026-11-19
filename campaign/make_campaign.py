"""Build the launch campaign: SVG masters, then PNG and print-ready PDF from those masters.

    python campaign/make_campaign.py              build everything
    python campaign/make_campaign.py --render     re-render from the .svg files, leaving them alone
    python campaign/make_campaign.py posters      build only pieces whose path matches a word
    python campaign/make_campaign.py --check      run the fact checks and stop
    python campaign/make_campaign.py --qr         print where the real QR code goes in each piece

The .svg files are the masters. By default this script writes them and then renders from what it
just wrote, so the whole set regenerates from the layouts in designs.py. If you have hand-edited a
master in Illustrator or Inkscape, use --render: the masters are left untouched and only the PNG and
PDF are rebuilt from them.

Before anything is drawn, the claims are checked. Every number the copy states is compared against
the app's own data files, and every headline is checked against campaign/copy.md. A figure that
drifts fails the build rather than going quietly onto a poster.
"""
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import brand                        # noqa: E402
import copytext as T                # noqa: E402
import designs                      # noqa: E402
import kit                          # noqa: E402
import render                       # noqa: E402
from svgdoc import parse            # noqa: E402

COPY_MD = HERE / "copy.md"


# ---------------------------------------------------------------- the fact checks
def check_numbers():
    """Every figure in the copy, against the data the app ships."""
    indoor = brand.indoor_counts()
    campus = brand.campus_counts()
    sw = (brand.ROOT / "app/sw.js").read_text(encoding="utf-8")
    timeout = int(re.search(r"NET_TIMEOUT\s*=\s*(\d+)", sw).group(1))
    rsch = brand.building_raw("research")
    room = brand.building_room("research", "423")
    actual = {"indoor_buildings": indoor["buildings"], "indoor_rooms": indoor["rooms"],
              "campus_buildings": campus["buildings"], "food": campus["food"],
              "cue_routes": campus["lines"], "cue_stops": campus["stops"],
              "net_timeout_ms": timeout, "rsch_floors": len(rsch["floors"]),
              "rsch_room_423_floor": room["floor"] if room else None}
    bad = {k: (v, actual[k]) for k, v in T.numbers_claimed().items() if actual[k] != v}
    if bad:
        raise SystemExit("copy claims figures the data does not support (claimed, actual): %s" % bad)
    # the buildings the copy names as mapped inside must be exactly the ones the app maps
    named = {"Research Hall", "Merten Hall", "Johnson Center", "The HUB"}
    if set(indoor["named"]) != named:
        raise SystemExit("copy names %s as mapped indoors; the app maps %s"
                         % (sorted(named), sorted(indoor["named"])))
    # the drawn walks must exist -- building them raises if a room or a route is missing
    for name in ("gps", "find"):
        kit.scene(name)
    return actual


def check_copy():
    """Every string the artwork sets, word for word in copy.md."""
    if not COPY_MD.exists():
        raise SystemExit("campaign/copy.md is missing -- the artwork copy has nowhere to come from")
    # compared with whitespace collapsed, so copy.md can wrap its lines where it likes
    md = re.sub(r"\s+", " ", COPY_MD.read_text(encoding="utf-8"))
    missing = [s[:70] for s in T.on_artwork() if re.sub(r"\s+", " ", s) not in md]
    if missing:
        raise SystemExit("copy.md and copytext.py have drifted:\n  " + "\n  ".join(missing))


def check_claims():
    """Nothing on the artwork may say the app knows where you are inside a building: it does not.
    GPS is used outdoors; indoors the route starts from the door (app/js/main.js, lines 1-2)."""
    banned = re.compile(r"indoor (gps|positioning|location)|where you are inside|"
                        r"knows where you are|gps (inside|indoors)|tracks you inside", re.I)
    for f in sorted(HERE.rglob("*.svg")):
        text = " ".join(re.findall(r">([^<]*)<", f.read_text(encoding="utf-8")))
        hit = banned.search(text)
        if hit:
            raise SystemExit("%s claims indoor positioning (%r) -- the app does not do that"
                             % (f.name, hit.group(0)))


def orphans():
    """Rendered files in the output folders that no piece in designs.PIECES produces any more."""
    keep = {(folder, name) for folder, name, _, _ in designs.PIECES}
    out = []
    for folder in sorted({f for f, _, _, _ in designs.PIECES}):
        for f in sorted((HERE / folder).glob("*")):
            if f.suffix in (".svg", ".png", ".pdf") and (folder, f.stem) not in keep:
                out.append(f)
    return out


def check_marks():
    """No university mark anywhere in the campaign, and the independence line on every print piece."""
    banned = re.compile(r"\bmason\b", re.I)
    for f in sorted(HERE.rglob("*.svg")):
        text = " ".join(re.findall(r">([^<]*)<", f.read_text(encoding="utf-8")))
        for hit in banned.finditer(text):
            around = text[max(0, hit.start() - 110):hit.end() + 110].lower()
            if "not affiliated" not in around and "for george mason" not in around:
                raise SystemExit("%s names the university outside the independence line: %r"
                                 % (f.name, around))


def qr_report():
    """Where the real QR code goes, in every piece: the exact box, in points, inches and pixels.

    Read straight out of the built masters rather than from the layout code, so it stays true even
    if a master has been nudged by hand.
    """
    print("%-38s %-18s %-16s %s" % ("piece", "box (pt)", "box (in)", "box (px in the PNG)"))
    for folder, name, _fn, spec in designs.PIECES:
        svg = HERE / folder / (name + ".svg")
        if not svg.exists():
            continue
        w, h, els = parse(svg.read_text(encoding="utf-8"))
        marks = [e for e in els if e["t"] == "text" and e["s"] == "QR"]
        rects = [e for e in els if e["t"] == "rect" and (e["fill"] or "").lower() == "#ffffff"]
        for m in marks:
            inside = [r for r in rects
                      if r["x"] <= m["x"] <= r["x"] + r["width"]
                      and r["y"] - r["height"] <= m["y"] <= r["y"] + r["height"]]
            if not inside:
                continue
            r = min(inside, key=lambda r: r["width"] * r["height"])
            scale = (spec.get("dpi") or 72) / 72.0
            unit = "pt" if spec.get("pdf") else "px"
            print("%-38s %-18s %-16s %s"
                  % (folder + "/" + name,
                     "%.0f,%.0f %.0f%s" % (r["x"], r["y"], r["width"], unit),
                     ("%.2f x %.2f" % (r["width"] / 72, r["width"] / 72)) if spec.get("pdf") else "-",
                     "%.0f,%.0f %.0f px" % (r["x"] * scale, r["y"] * scale, r["width"] * scale)))


# ---------------------------------------------------------------- the build
def build(only=None, render_only=False):
    checks = check_numbers()
    check_copy()
    fonts = render.font_report()
    print("Akadian Vertex - launch campaign")
    print("  data   %d rooms mapped inside %d buildings; %d buildings on campus; walks: %s"
          % (checks["indoor_rooms"], checks["indoor_buildings"], checks["campus_buildings"],
             ", ".join("%s %s %d m" % (kit.scene(n).plan["name"], kit.scene(n).room_id,
                                       round(kit.scene(n).metres)) for n in ("gps", "find"))))
    print("  fonts  " + ", ".join("%s: %s / %s (pdf)" % (k, a, b) for k, (a, b) in fonts.items()))
    print()

    rows = []
    for folder, name, fn, spec in designs.PIECES:
        if only and not any(o.lower() in ("%s/%s" % (folder, name)).lower() for o in only):
            continue
        out = HERE / folder
        svg = out / (name + ".svg")
        t0 = time.time()
        if render_only:
            if not svg.exists():
                raise SystemExit("%s does not exist -- build it without --render first" % svg)
        else:
            fn().save(svg)
        size = render.render_png(svg, out / (name + ".png"),
                                 dpi=spec.get("dpi"), supersample=spec.get("supersample", 1))
        made = ["svg"] if not render_only else []
        made.append("png %dx%d" % size)
        if spec.get("pdf"):
            render.render_pdf(svg, out / (name + ".pdf"))
            made.append("pdf")
        rows.append((folder + "/" + name, ", ".join(made), time.time() - t0))
        print("  %-42s %-26s %4.1fs" % rows[-1])

    check_marks()
    check_claims()
    stale = orphans()
    if stale:
        print("\n  not made by any piece any more (delete them):")
        for f in stale:
            print("    " + str(f.relative_to(HERE)))
    print("\n  %d pieces. No university mark in any of them; every printed piece carries the "
          "independence line; nothing claims indoor positioning." % len(rows))
    print("  QR squares are placeholders -- see campaign/README.md before printing.")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    if "--qr" in args:
        qr_report()
        sys.exit(0)
    if "--check" in args:
        check_numbers()
        check_copy()
        check_marks()
        check_claims()
        print("checks pass")
        sys.exit(0)
    build(only=[a for a in args if not a.startswith("--")], render_only="--render" in args)
