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
    plan = brand.jc_plan()
    campus = brand.campus_counts()
    sw = (brand.ROOT / "app/sw.js").read_text(encoding="utf-8")
    timeout = int(re.search(r"NET_TIMEOUT\s*=\s*(\d+)", sw).group(1))
    indoor = len(brand.json.loads((brand.ROOT / "docs/data/campuses.json")
                                  .read_text(encoding="utf-8"))[0]["indoor"])
    actual = {"study_rooms": plan["n_study"], "jc_rooms": plan["n_rooms"],
              "jc_floors": len(plan["floors"]), "indoor_buildings": indoor,
              "campus_buildings": campus["buildings"], "food": campus["food"],
              "cue_routes": campus["lines"], "cue_stops": campus["stops"],
              "net_timeout_ms": timeout}
    bad = {k: (v, actual[k]) for k, v in T.numbers_claimed().items() if actual[k] != v}
    if bad:
        raise SystemExit("copy claims figures the data does not support: %s" % bad)
    return actual


def check_copy():
    """Every headline and deck in copytext.py, word for word in copy.md."""
    if not COPY_MD.exists():
        raise SystemExit("campaign/copy.md is missing -- the artwork copy has nowhere to come from")
    # compared with whitespace collapsed, so copy.md can wrap its lines where it likes
    md = re.sub(r"\s+", " ", COPY_MD.read_text(encoding="utf-8"))
    missing = []
    for name in dir(T):
        if not re.match(r"^[A-D]_(HEAD|DECK|SHORT|KICKER)$|^FEATURES(_SHORT)?$|^SIGNOFF$", name):
            continue
        val = getattr(T, name)
        strings = ([" ".join(val)] if name.endswith("HEAD") else
                   [t for pair in val for t in pair] if name.startswith("FEATURES") else [val])
        for s in strings:
            if re.sub(r"\s+", " ", s) not in md:
                missing.append("%s: %s" % (name, s[:60]))
    if missing:
        raise SystemExit("copy.md and copytext.py have drifted:\n  " + "\n  ".join(missing))


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
    print("  data   %d study rooms, %d rooms, %d floors in the Johnson Center; %d buildings on campus"
          % (checks["study_rooms"], checks["jc_rooms"], checks["jc_floors"],
             checks["campus_buildings"]))
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
    print("\n  %d pieces. No university mark in any of them; every printed piece carries the "
          "independence line." % len(rows))
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
        print("checks pass")
        sys.exit(0)
    build(only=[a for a in args if not a.startswith("--")], render_only="--render" in args)
