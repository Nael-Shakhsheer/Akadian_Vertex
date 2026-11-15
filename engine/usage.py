"""Anonymous usage counts: how much the app is used, with nothing about who used it.

Everything here is a tally. A request adds to counters; it never stores a row, an identifier, a clock
time, a position or anything that could be tied back to a person or put in order. The finest resolution
kept is one UTC day, and the only dimensions are the campus, a fixed list of event names and -- for
indoor views -- which building. That is enough to say how much the app is used and what for, and not
enough to follow anyone around.

Counts live in <engine home>/usage/<YYYY-MM>.json. The engine home is never served by the public app, so
they stay on the machine. They are not encrypted with the vault: the public server runs without the
passphrase, and there is nothing personal in them to protect.

Deliberately not countable from this data:
  * unique people -- nothing identifies a device, so "opens" means opens and must never be called "users"
  * where anyone went -- rooms, routes and coordinates are never sent
  * when, beyond the day -- no clock time, no ordering, no session boundaries

A count can only be wrong in one direction worth knowing about: anything can POST to the collect endpoint,
so these are a floor on real interest, not an audited figure. Say that when you quote them.
"""
import json
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

# The whole vocabulary. Anything not in here is dropped at the door rather than stored and sorted out
# later, so the file can never fill up with something nobody meant to collect.
EVENTS = {
    "open": "App opened",
    "standalone": "Opened from the home screen",
    "offline": "Opened with no network",
    "search": "Searched for something",
    "place": "Opened a place",
    "route": "Got walking directions",
    "navigate": "Started turn-by-turn",
    "arrive": "Arrived",
    "indoor": "Opened a building's inside",
    "study_room": "Routed to a study room",
    "bus": "Checked bus times",
    "parking": "Used a parking lot",
    "car": "Saved where the car is",
}

SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,40}$")
MAX_PER_KEY = 500        # one page visit cannot plausibly do more; caps accidental and deliberate inflation
MAX_KEYS = 40            # distinct building ids in a single report
FLUSH_AFTER = 20.0       # seconds; counts are held in memory this long so a busy day is not a write per hit

DAY = "%Y-%m-%d"


def _today() -> str:
    return datetime.now(timezone.utc).strftime(DAY)


def _clean(counts, allowed=None) -> dict:
    """Keep the pairs that are a known key and a sane positive count; drop everything else silently."""
    out = {}
    if not isinstance(counts, dict):
        return out
    for k, v in list(counts.items())[:MAX_KEYS]:
        if allowed is not None and k not in allowed:
            continue
        if allowed is None and not (isinstance(k, str) and SLUG.match(k)):
            continue
        if isinstance(v, bool) or not isinstance(v, int) or v < 1:
            continue
        out[k] = min(v, MAX_PER_KEY)
    return out


class Usage:
    """Buffered day counters. Safe to call from request handlers; writes are batched and atomic."""

    def __init__(self, home: Path, flush_after: float = FLUSH_AFTER):
        self.dir = home / "usage"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.flush_after = flush_after
        self._lock = threading.Lock()
        self._pending: dict = {}
        self._last = time.monotonic()

    # ----- collecting -----
    def add(self, campus: str, events: dict, buildings: dict | None = None) -> bool:
        """Fold one report into the buffer. Returns False if there was nothing usable in it."""
        campus = campus if isinstance(campus, str) and SLUG.match(campus) else "unknown"
        ev = _clean(events, EVENTS)
        bl = _clean(buildings or {})
        if not ev and not bl:
            return False
        with self._lock:
            day = self._pending.setdefault(_today(), {}).setdefault(campus, {"events": {}, "buildings": {}})
            for k, v in ev.items():
                day["events"][k] = day["events"].get(k, 0) + v
            for k, v in bl.items():
                day["buildings"][k] = day["buildings"].get(k, 0) + v
            due = time.monotonic() - self._last >= self.flush_after
        if due:
            self.flush()
        return True

    def flush(self):
        """Fold the buffer into the month files. Called on a timer, and on shutdown."""
        with self._lock:
            pending, self._pending = self._pending, {}
            self._last = time.monotonic()
        if not pending:
            return
        by_month: dict[str, dict] = {}
        for day, campuses in pending.items():
            by_month.setdefault(day[:7], {})[day] = campuses
        for month, days in by_month.items():
            path = self.dir / f"{month}.json"
            data = _read(path)
            for day, campuses in days.items():
                into_day = data.setdefault(day, {})
                for campus, parts in campuses.items():
                    into = into_day.setdefault(campus, {"events": {}, "buildings": {}})
                    for section in ("events", "buildings"):
                        for k, v in parts[section].items():
                            into[section][k] = into[section].get(k, 0) + v
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")), encoding="utf-8")
            tmp.replace(path)

    # ----- reading -----
    def report(self, start: str | None = None, end: str | None = None) -> dict:
        """Totals, a per-day series and per-campus and per-building breakdowns, over an inclusive range."""
        self.flush()
        days: dict[str, dict] = {}
        for path in sorted(self.dir.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9].json")):
            for day, campuses in _read(path).items():
                if (start and day < start) or (end and day > end):
                    continue
                days[day] = campuses

        totals: dict[str, int] = {}
        by_campus: dict[str, dict] = {}
        by_building: dict[str, int] = {}
        series: list[dict] = []
        for day in sorted(days):
            per_day: dict[str, int] = {}
            for campus, parts in days[day].items():
                seen = by_campus.setdefault(campus, {})
                for k, v in parts.get("events", {}).items():
                    totals[k] = totals.get(k, 0) + v
                    per_day[k] = per_day.get(k, 0) + v
                    seen[k] = seen.get(k, 0) + v
                for k, v in parts.get("buildings", {}).items():
                    by_building[k] = by_building.get(k, 0) + v
            series.append({"day": day, **per_day})
        return {
            "from": min(days) if days else None,
            "to": max(days) if days else None,
            "days": len(days),
            "labels": EVENTS,
            "totals": totals,
            "series": series,
            "campuses": by_campus,
            "buildings": dict(sorted(by_building.items(), key=lambda kv: -kv[1])),
        }

    def csv(self, start: str | None = None, end: str | None = None) -> str:
        """The day series as CSV, for pasting into a spreadsheet or a slide."""
        rep = self.report(start, end)
        cols = list(EVENTS)
        rows = ["day," + ",".join(cols)]
        for row in rep["series"]:
            rows.append(row["day"] + "," + ",".join(str(row.get(c, 0)) for c in cols))
        return "\n".join(rows) + "\n"


def mount_public(app, home: Path) -> Usage:
    """Attach the collect endpoint to a public app, and hand back the Usage it counts into.

    It lives here rather than in server.py so the one route that faces the internet can be imported and
    tested on its own, without the schematic pipeline and everything it needs.

    The rate limit stops a bored person inflating the numbers from one machine. The addresses it counts
    against are held in memory for the length of a window and never written down; nothing else about a
    request is looked at. Every outcome returns the same empty response, so nothing is learned by probing.
    """
    from fastapi import Request, Response

    usage = Usage(home)
    seen: dict[str, list] = {}
    rate, window, max_body = 30, 600, 4096

    @app.post("/api/public/usage")
    async def collect(request: Request):
        now = time.time()
        if len(seen) > 20000:  # a flood, or long uptime: drop stale windows rather than grow without end
            for k in [k for k, (t, _) in seen.items() if now - t > window]:
                seen.pop(k, None)
        ip = request.client.host if request.client else "?"
        win = seen.get(ip)
        if not win or now - win[0] > window:
            win = seen[ip] = [now, 0]
        win[1] += 1
        if win[1] > rate or int(request.headers.get("content-length") or 0) > max_body:
            return Response(status_code=204)
        try:
            body = json.loads(await request.body())
            usage.add(body.get("campus", ""), body.get("events"), body.get("buildings"))
        except (ValueError, TypeError, AttributeError):
            pass  # a malformed beacon is not worth an error the app will never read
        return Response(status_code=204)

    @app.on_event("shutdown")
    def _flush():
        usage.flush()

    return usage


def _read(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (ValueError, OSError):
        return {}  # a truncated file loses that month's counts rather than taking the server down
