#!/usr/bin/env python3
"""Direct feeds (company job boards, job APIs, opt-in LinkedIn) and company-site email reading, on a fake
internet shaped like the real APIs.   Run:  python3 tests/test_direct.py"""
import datetime as dt
import json
import os
import sys
import tempfile
import time
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "scripts"))
os.environ.pop("JWORD_FEEDS", None)
import direct as D  # noqa: E402
import jword as J  # noqa: E402
from test_jword import run, drive  # noqa: E402
os.environ.pop("JWORD_FEEDS", None)       # test_jword switches feeds off for its own tests

T0 = dt.date.today()
TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


def ago(n):
    return (T0 - dt.timedelta(days=n)).isoformat()


def cf(email, key=0x5A):
    return f"{key:02x}" + "".join(f"{ord(c) ^ key:02x}" for c in email)


def web():
    w = {
        "boards-api.greenhouse.io/v1/boards/gitlab/jobs": {"jobs": []},
        "boards-api.greenhouse.io/v1/boards/acme/jobs": {"jobs": [
            {"id": 1, "title": "Flutter Developer", "first_published": ago(2) + "T09:00:00Z",
             "location": {"name": "Remote"}, "absolute_url": "https://job-boards.greenhouse.io/acme/jobs/1",
             "content": "&lt;p&gt;Flutter, Dart, Firebase&lt;/p&gt;", "company_name": "Acme"},
            {"id": 2, "title": "Flutter Developer", "first_published": ago(40) + "T09:00:00Z",
             "location": {"name": "Remote"}, "absolute_url": "https://job-boards.greenhouse.io/acme/jobs/2",
             "content": "old", "company_name": "Acme"},
            {"id": 3, "title": "Office Manager", "first_published": ago(1), "location": {"name": "Remote"},
             "absolute_url": "https://job-boards.greenhouse.io/acme/jobs/3", "company_name": "Acme"},
            {"id": 4, "title": "Senior Flutter Engineer", "updated_at": ago(1), "location": {"name": "Remote"},
             "absolute_url": "https://job-boards.greenhouse.io/acme/jobs/4", "company_name": "Acme"}]},
        "api.lever.co/v0/postings/beta": [
            {"id": "b1", "text": "Flutter Developer", "createdAt": int(time.mktime(dt.date.fromisoformat(ago(1)).timetuple()) * 1000),
             "categories": {"location": "Remote"}, "hostedUrl": "https://jobs.lever.co/beta/b1",
             "applyUrl": "https://jobs.lever.co/beta/b1/apply", "descriptionPlain": "Flutter apps", "workplaceType": "remote"}],
        "api.ashbyhq.com/posting-api/job-board/gamma": {"jobs": [
            {"id": "g1", "title": "Mobile Engineer (Flutter)", "location": "Remote", "isRemote": True,
             "publishedAt": ago(0) + "T08:00:00Z", "jobUrl": "https://jobs.ashbyhq.com/gamma/g1",
             "descriptionPlain": "Flutter and Dart", "isListed": True}]},
        "remotive.com/api/remote-jobs": {"jobs": [
            {"id": 77, "url": "https://remotive.com/remote/jobs/software-dev/flutter-77", "title": "Flutter Developer",
             "company_name": "Remote People", "publication_date": ago(3) + "T10:00:00",
             "candidate_required_location": "Worldwide", "description": "<p>Flutter. Email jobs@remotepeople.com</p>"}]},
        "remoteok.com/api": [{"legal": "x"}],
        "himalayas.app/jobs/api/search": {"jobs": []},
        "jobicy.com/api/v2/remote-jobs": {"jobs": []},
        "www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search": (
            '<li><div class="base-card relative job-search-card">'
            '<a class="base-card__full-link" href="https://pk.linkedin.com/jobs/view/flutter-developer-at-linkco-4100?trk=x">'
            '</a><h3 class="base-search-card__title">  Flutter Developer </h3>'
            '<h4 class="base-search-card__subtitle"><a href="#">LinkCo</a></h4>'
            '<span class="job-search-card__location">Lahore, Punjab, Pakistan</span>'
            f'<time class="job-search-card__listdate" datetime="{ago(1)}">1 day ago</time></div></li>'),
        "acme.io/": ('<html><title>Acme</title><a href="/careers">Careers</a> <a href="/contact">Contact</a> '
                     f'<a href="/cdn-cgi/l/email-protection#{cf("hr@acme.io")}"><span data-cfemail="{cf("hr@acme.io")}">'
                     '[email&#160;protected]</span></a></html>'),
        "acme.io/careers": "<p>Send your CV to careers@acme.io. Recruiter: Sara Khan (sara.khan@acme.io)</p><img src='a@2x.png'>",
        "acme.io/contact": "<p>info@acme.io · noreply@acme.io · press [at] acme [dot] io</p>",
    }
    return w


class Fake:
    def __init__(self, blocked=False):
        self.routes, self.blocked, self.calls = web(), blocked, []

    def get(self, url, params=None, browser=False, timeout=12):
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        self.calls.append(url)
        if self.blocked:
            raise D.Blocked("proxy refused (403)")
        u = urllib.parse.urlparse(url)
        key = u.netloc.removeprefix("www.") + (u.path or "/") if u.path in ("", "/") else u.netloc + u.path
        if u.netloc.endswith("acme.io"):
            key = "acme.io" + (u.path or "/")
        body = self.routes.get(key)
        if body is None:
            return 404, "not found", url
        return 200, body if isinstance(body, str) else json.dumps(body), url


def install(fake, seeds=None):
    D.get = fake.get
    D.SEED_BOARDS = seeds if seeds is not None else {"greenhouse": ["gitlab", "acme", "gone"], "lever": ["beta"],
                                                     "ashby": ["gamma"]}


INIT = ["init", "--mode", "jobs", "--roles", "Flutter Developer", "--locations", "Remote", "--posted-within", "7d",
        "--offer", "Flutter and Dart developer, 2 years, Firebase", "--ranking", "keyword", "--target", "5"]


@test
def feeds_add_dated_live_jobs_before_any_web_search():
    fake = Fake()
    install(fake)
    with tempfile.TemporaryDirectory() as tmp:
        run(tmp, *INIT)
        first = run(tmp, "next")
        note = first["direct_feeds"]
        assert note["available"] and note["boards_checked"] == 5 and note["new_candidates"] >= 4, note
        assert note["outside_window"] == 1                                  # the 40-day-old Acme job
        assert note["by_source"]["Greenhouse"] == 4 and note["by_source"]["Remotive"] == 1
        st = json.loads((Path(tmp) / "state.json").read_text())
        assert "greenhouse:gone" not in st["ats_boards"]                    # dead board dropped
        final, stats = drive(tmp, results_fn=lambda q, n: [])
        st = json.loads((Path(tmp) / "state.json").read_text())
        saved = [c for c in st["candidates"] if c["status"] == "saved"]
        by = {(c["company"], c["url"]): c for c in saved}
        assert ("Acme", "https://job-boards.greenhouse.io/acme/jobs/1") in by
        acme = by[("Acme", "https://job-boards.greenhouse.io/acme/jobs/1")]
        assert acme["open_check"].startswith("Open (listed in the company's live Greenhouse job feed)")
        assert acme["date_verdict"] == "in" and acme["posted"] == ago(2)
        titles = {c["title"] for c in saved}
        assert "Office Manager" not in titles and "Senior Flutter Engineer" not in titles   # wrong role / updated-only
        assert any(c["feed"] == "Remotive" and c["emails"] for c in saved)                 # email printed in post


@test
def blocked_network_falls_back_to_web_search_quickly():
    fake = Fake(blocked=True)
    install(fake)
    with tempfile.TemporaryDirectory() as tmp:
        run(tmp, *INIT)
        t = time.time()
        nxt = run(tmp, "next")
        assert time.time() - t < 3
        assert nxt["action"] == "search" and nxt["direct_feeds"]["available"] is False
        calls = len(fake.calls)
        run(tmp, "next")
        assert len(fake.calls) == calls                                     # never retried in this run


@test
def feeds_can_be_turned_off():
    fake = Fake()
    install(fake)
    with tempfile.TemporaryDirectory() as tmp:
        run(tmp, *INIT, "--feeds", "off")
        nxt = run(tmp, "next")
        assert nxt["action"] == "search" and "direct_feeds" not in nxt and not fake.calls


@test
def boards_seen_in_search_results_are_read_directly():
    fake = Fake()
    install(fake, seeds={})
    fake.routes["remotive.com/api/remote-jobs"] = {"jobs": []}
    for i in range(8):
        fake.routes[f"api.lever.co/v0/postings/co{i}"] = [
            {"id": f"x{i}", "text": "Flutter Developer", "createdAt": int(time.time() * 1000), "categories": {"location": "Remote"},
             "hostedUrl": f"https://jobs.lever.co/co{i}/x{i}", "descriptionPlain": "Flutter", "workplaceType": "remote"}]
    with tempfile.TemporaryDirectory() as tmp:
        run(tmp, *INIT)
        assert run(tmp, "next")["action"] == "search"
        found = [{"title": f"Data Analyst at Co{i}", "url": f"https://jobs.lever.co/co{i}/other-{i}", "snippet": "x"}
                 for i in range(8)]
        f = Path(tmp) / "r.json"
        f.write_text(json.dumps(found))
        out = run(tmp, "ingest", "--results", str(f))
        assert out["next_action"]["direct_feeds"]["boards_checked"] == 8
        st = json.loads((Path(tmp) / "state.json").read_text())
        assert sum(1 for c in st["candidates"] if c.get("feed") == "Lever") == 8


@test
def linkedin_is_read_only_when_switched_on():
    fake = Fake()
    install(fake, seeds={})
    with tempfile.TemporaryDirectory() as tmp:
        run(tmp, *INIT)
        run(tmp, "next")
        assert not any("linkedin" in c for c in fake.calls)
    fake = Fake()
    install(fake, seeds={})
    with tempfile.TemporaryDirectory() as tmp:
        run(tmp, *[a if a != "Remote" else "Lahore" for a in INIT], "--linkedin-direct")
        note = run(tmp, "next")["direct_feeds"]
        li = [c for c in fake.calls if "linkedin" in c]
        assert li and "f_TPR=r604800" in li[0] and "location=Lahore" in li[0]
        assert note["by_source"]["LinkedIn"] == 1
        st = json.loads((Path(tmp) / "state.json").read_text())
        c = next(c for c in st["candidates"] if c.get("feed") == "LinkedIn")
        assert c["company"] == "LinkCo" and c["date_verdict"] == "in" and "?" not in c["url"]


@test
def company_website_emails_are_read_and_recorded_with_evidence():
    fake = Fake()
    install(fake)
    with tempfile.TemporaryDirectory() as tmp:
        run(tmp, *INIT, "--feeds", "off")
        drive(tmp, results_fn=lambda q, n: [{"title": "Flutter Developer at Acme", "url": "https://jobs.lever.co/acme/1",
                                              "snippet": "Posted 2 days ago. Remote. Flutter and Dart."}] if n == 0 else [])
        st = json.loads((Path(tmp) / "state.json").read_text())
        cid = next(c["id"] for c in st["candidates"] if c["status"] == "saved")
        refused = run(tmp, "site-emails", "--id", cid, "--url", "https://jobs.lever.co", ok=False)
        assert "job board" in refused["error"]
        res = run(tmp, "site-emails", "--id", cid, "--url", "acme.io")
        assert set(res["found"]) == {"hr@acme.io", "careers@acme.io", "sara.khan@acme.io", "info@acme.io", "press@acme.io"}
        assert not res["refused"] and not res["incomplete"]
        st = json.loads((Path(tmp) / "state.json").read_text())
        c = next(c for c in st["candidates"] if c["id"] == cid)
        assert c["website"] == "acme.io" and c["contacts_checked"]
        assert any(e["email"] == "careers@acme.io" and e["verification"].startswith("Verified") for e in c["emails"])
    fake.blocked = True
    with tempfile.TemporaryDirectory() as tmp:
        run(tmp, *INIT, "--feeds", "off")
        drive(tmp, results_fn=lambda q, n: [{"title": "Flutter Developer at Acme", "url": "https://jobs.lever.co/acme/1",
                                              "snippet": "Posted 2 days ago. Remote. Flutter and Dart."}] if n == 0 else [])
        st = json.loads((Path(tmp) / "state.json").read_text())
        cid = next(c["id"] for c in st["candidates"] if c["status"] == "saved")
        res = run(tmp, "site-emails", "--id", cid, "--url", "acme.io", ok=False)
        assert res["unavailable"] and "contacts.md" in res["next"]


@test
def ats_links_and_email_extraction():
    assert D.ats_ref("https://boards.greenhouse.io/gitlab/jobs/1") == ("greenhouse", "gitlab")
    assert D.ats_ref("https://job-boards.eu.greenhouse.io/joblogic/jobs/4") == ("greenhouse", "joblogic@eu")
    assert D.ats_ref("https://jobs.lever.co/palantir/u") == ("lever", "palantir")
    assert D.ats_ref("https://jobs.ashbyhq.com/openai/u") == ("ashby", "openai")
    assert D.ats_ref("https://apply.workable.com/huggingface/j/ABC/") == ("workable", "huggingface")
    assert D.ats_ref("https://blueground.workable.com/") == ("workable", "blueground")
    assert D.ats_ref("https://jobs.workable.com/view/x") is None and D.ats_ref("https://www.linkedin.com/jobs/view/1") is None
    got = {e["email"] for e in D.page_emails('<a href="mailto:jobs@x.io?subject=hi">x</a> noreply@x.io img@2x.png '
                                             'talent (at) x (dot) io', "https://x.io")}
    assert got == {"jobs@x.io", "talent@x.io"}
    assert D.decode_cf(cf("hr@x.com")) == "hr@x.com"
    assert D.iso(1763600000) and D.iso("2026-11-20T09:00:00Z") == "2026-11-20" and D.iso(None) == ""


if __name__ == "__main__":
    real_get, real_seeds = D.get, D.SEED_BOARDS
    failed = 0
    for fn in TESTS:
        try:
            fn()
            print(f"ok    {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            import traceback
            traceback.print_exc()
            print(f"FAIL  {fn.__name__}: {e}")
        finally:
            D.get, D.SEED_BOARDS = real_get, real_seeds
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(1 if failed else 0)
