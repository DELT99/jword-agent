#!/usr/bin/env python3
"""Live check of the direct sources against the real sites (needs internet).  Prints one line per source.
Run locally (`python3 tools/live_check.py`) or see the `live-check` job on GitHub Actions.
Exit code is always 0: a site being down is information, not a test failure."""
import datetime as dt
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skill" / "jword" / "scripts"))
import direct as D  # noqa: E402

LINKEDIN = "--linkedin" in sys.argv


def line(name, fn):
    t = time.time()
    try:
        res = fn()
        rows = res[1] if isinstance(res, tuple) else res
        status = res[0] if isinstance(res, tuple) else 200
        dated = [r for r in rows if '"datePosted"' in r["snippet"]]
        newest = max((r["snippet"].split('"datePosted": "')[1][:10] for r in dated), default="-")
        ok = "OK " if rows else "-- "
        print(f"{ok} {name:<28} HTTP {status:<4} jobs={len(rows):<5} dated={len(dated):<5} newest={newest}  "
              f"{time.time() - t:4.1f}s")
        return len(rows)
    except Exception as e:  # noqa: BLE001
        print(f"ERR {name:<28} {type(e).__name__}: {str(e)[:120]}")
        return 0


def main():
    ok, why = D.probe()
    print(f"probe: {'reachable' if ok else 'BLOCKED: ' + why}   today={dt.date.today()}\n")
    total = 0
    for kind, slug in [("greenhouse", "gitlab"), ("greenhouse", "anthropic"), ("lever", "palantir"),
                       ("ashby", "openai"), ("ashby", "ramp"), ("workable", "huggingface"),
                       ("smartrecruiters", "Visa")]:
        total += line(f"{kind}:{slug}", lambda k=kind, s=slug: D.board_jobs(k, s))
    for api in ("remotive", "remoteok", "himalayas", "jobicy"):
        total += line(f"{api} (Software Engineer)", lambda a=api: D.remote_jobs(a, "Software Engineer", "pakistan"))
    if LINKEDIN:
        total += line("linkedin (Software Engineer, 7d)", lambda: D.linkedin_jobs("Software Engineer", "Lahore", 7, 1))
    t = time.time()
    try:
        res = D.site_emails("https://remotive.com")
        print(f"\nsite-emails remotive.com: pages={len(res['pages'])} emails={[e['email'] for e in res['emails']][:6]} "
              f"{res['error']} {time.time() - t:4.1f}s")
    except Exception as e:  # noqa: BLE001
        print(f"\nsite-emails ERR {type(e).__name__}: {e}")
    print(f"\nTOTAL listings read: {total}")


if __name__ == "__main__":
    main()
