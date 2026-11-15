"""Anonymous usage counting.

    python tests/test_usage.py

What matters here is as much what does not get stored as what does: the counters are the one part of the
system that touches every visitor, so the checks below pin down the whitelist, the caps and the fact that
nothing identifying survives a round trip.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.usage import Usage, EVENTS  # noqa: E402

ok = 0


def check(cond, what):
    global ok
    assert cond, f"FAILED: {what}"
    ok += 1


def fresh(tmp, **kw) -> Usage:
    return Usage(Path(tmp), flush_after=kw.pop("flush_after", 1e9))


def main(tmp: Path):
    # ---- a plain round trip ----
    u = fresh(tmp)
    u.add("gmu", {"open": 3, "search": 5}, {"gmu-jc": 2})
    u.add("gmu", {"open": 1}, None)
    r = u.report()
    check(r["totals"]["open"] == 4, "opens add up across reports")
    check(r["totals"]["search"] == 5, "searches add up")
    check(r["buildings"]["gmu-jc"] == 2, "buildings are counted")
    check(r["days"] == 1 and len(r["series"]) == 1, "one day, one row in the series")

    # ---- the whitelist and the caps ----
    u = fresh(tmp / "b")
    check(u.add("gmu", {"not_an_event": 9}, None) is False, "an unknown event name is dropped entirely")
    u.add("gmu", {"open": 10 ** 9, "search": 0, "route": -4, "navigate": True, "arrive": "7", "bus": 2}, None)
    t = u.report()["totals"]
    check(t["open"] == 500, "an absurd count is capped rather than trusted")
    check("search" not in t and "route" not in t, "zero and negative counts are dropped")
    check("navigate" not in t and "arrive" not in t, "a bool and a string are not counts")
    check(t["bus"] == 2, "the good value in a bad report still lands")

    # ---- identifiers cannot sneak in through the keys ----
    u = fresh(tmp / "c")
    u.add("../../etc", {"open": 1}, {"../secret": 1, "Room 320F": 1, "gmu-jc": 1})
    r = u.report()
    check(list(r["campuses"]) == ["unknown"], "a campus that is not a slug becomes 'unknown'")
    check(list(r["buildings"]) == ["gmu-jc"], "only slug-shaped building ids are kept")
    raw = json.loads(next((tmp / "c" / "usage").glob("*.json")).read_text())
    check("secret" not in json.dumps(raw) and "320F" not in json.dumps(raw), "nothing else reached the disk")

    # ---- the file holds counts and nothing else ----
    day = next(iter(raw))
    check(len(day) == 10 and day.count("-") == 2, "the finest resolution stored is one day")
    check(set(raw[day]["unknown"]) == {"events", "buildings"}, "a day holds only events and buildings")

    # ---- ranges ----
    u = fresh(tmp / "d")
    u.add("gmu", {"open": 2}, None)
    u.flush()
    today = next(iter(json.loads(next((tmp / "d" / "usage").glob("*.json")).read_text())))
    check(u.report(start=today)["totals"]["open"] == 2, "a range that includes today finds it")
    check(u.report(end="2000-01-01")["totals"] == {}, "a range that excludes it finds nothing")
    check(u.report(start="2999-01-01")["days"] == 0, "a future range is empty, not an error")

    # ---- csv ----
    lines = u.csv().strip().split("\n")
    check(lines[0].startswith("day,") and len(lines) == 2, "csv has a header and one row per day")
    check(len(lines[0].split(",")) == len(EVENTS) + 1, "every event has a csv column")

    # ---- buffering and durability ----
    u = Usage(tmp / "e", flush_after=1e9)
    u.add("gmu", {"open": 1}, None)
    check(not list((tmp / "e" / "usage").glob("*.json")), "nothing is written while the buffer holds")
    check(Usage(tmp / "e").report()["totals"] == {}, "another reader cannot see an unflushed buffer")
    u.flush()
    check(Usage(tmp / "e").report()["totals"]["open"] == 1, "once flushed, a fresh reader sees it")

    # ---- a damaged file costs that month, not the server ----
    bad = tmp / "f" / "usage"
    bad.mkdir(parents=True)
    (bad / "2027-01.json").write_text("{not json")
    u = fresh(tmp / "f")
    check(u.report()["totals"] == {}, "a truncated month reads as empty instead of raising")
    u.add("gmu", {"open": 1}, None)
    u.flush()
    check(u.report()["totals"]["open"] == 1, "and counting carries on afterwards")

    endpoint(tmp / "g")
    print(f"usage: ok — {ok} checks")


def endpoint(home: Path):
    """The collect route, which is the only part of this that faces the internet."""
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except ImportError:
        print("usage: skipping the endpoint checks (pip install fastapi httpx2)")
        return
    from engine.usage import mount_public

    app = FastAPI()
    usage = mount_public(app, home)
    c = TestClient(app)
    post = lambda body: c.post("/api/public/usage", content=body)  # noqa: E731

    check(post(json.dumps({"campus": "gmu", "events": {"open": 1, "search": 3}})).status_code == 204,
          "a good report is accepted with an empty response")
    check(post("not json at all").status_code == 204, "garbage gets the same empty response, not a 500")
    check(post(json.dumps({"events": "nonsense"})).status_code == 204, "so does a wrongly shaped body")
    check(post("x" * 5000).status_code == 204, "an oversized body is ignored rather than parsed")
    usage.flush()
    t = usage.report()["totals"]
    check(t == {"open": 1, "search": 3}, f"only the good report was counted ({t})")

    # the limit is per address and silent: a flood neither counts nor announces that it was stopped
    before = usage.report()["totals"]["open"]
    codes = {post(json.dumps({"campus": "gmu", "events": {"open": 1}})).status_code for _ in range(60)}
    usage.flush()
    after = usage.report()["totals"]["open"]
    check(codes == {204}, "a rate-limited caller cannot tell it was limited")
    check(after - before < 60, f"the flood was capped ({after - before} of 60 counted)")
    check(not any(p.name.endswith(".tmp") for p in (home / "usage").iterdir()), "no temp files left behind")


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        main(Path(d))
