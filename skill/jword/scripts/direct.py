"""Direct job feeds and company-site email reading, Python standard library only (nothing to install).

Works wherever the script can reach the internet: Claude Code on your computer, or a Claude chat sandbox
that allows these sites. Where the network is blocked, `probe()` says so in a second and Jword carries on
with web search, exactly as before.

Sources (all public, no API keys): Greenhouse, Lever, Ashby, Workable and SmartRecruiters job-board feeds
(the JSON behind companies' own careers pages), and the Remotive, RemoteOK, Himalayas and Jobicy APIs.
Opt-in: LinkedIn's public job search (its terms forbid automated access; personal use, small volumes).
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; Jword/3.4; personal job search; +https://github.com/DELT99/hiring-signals-leadgen)"
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
TIMEOUT = 12

# A starting list of company boards; every run adds the boards it sees in search results.
SEED_BOARDS = {
    "greenhouse": ["gitlab", "anthropic", "vercel", "cloudflare", "databricks", "stripe", "figma", "discord",
                   "dropbox", "airtable", "asana", "duolingo", "grammarly", "elastic", "mongodb", "okta", "twilio",
                   "reddit", "pinterest", "instacart", "coinbase", "robinhood", "gusto", "lyft", "airbnb", "datadog",
                   "verygoodventures", "invertase", "expressvpn", "moovx", "cookunity", "navtechnologies",
                   "gomotive", "turing", "toptal"],
    "lever": ["palantir", "plaid", "mistral", "spotify", "binance", "kraken"],
    "ashby": ["openai", "ramp", "linear", "notion", "supabase", "posthog", "cohere", "replit", "deel", "zapier",
              "elevenlabs", "perplexity"],
    "workable": ["huggingface", "arbisoft", "10pearls"],
    "smartrecruiters": ["Visa", "Bosch", "ServiceNow"],
}


# ------------------------------------------------------------------ http
class Blocked(Exception):
    """The network (or a proxy) refuses connections from here."""


def get(url: str, params: dict | None = None, browser: bool = False, timeout: int = TIMEOUT) -> tuple[int, str, str]:
    """(status, text, final_url).  Raises Blocked for proxy/DNS/connection failures."""
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA if browser else UA,
                                               "Accept": "application/json, text/html;q=0.9, */*;q=0.5",
                                               "Accept-Language": "en"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(4_000_000)
            enc = r.headers.get_content_charset() or "utf-8"
            return r.status, raw.decode(enc, "replace"), r.geturl()
    except urllib.error.HTTPError as e:
        if e.code in (403, 407) and "proxy" in str(e.headers or "").lower():
            raise Blocked(f"proxy refused ({e.code})") from e
        try:
            body = e.read(200_000).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            body = ""
        return e.code, body, url
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise Blocked(f"{type(e).__name__}: {str(e)[:120]}") from e


def probe() -> tuple[bool, str]:
    """Can this machine reach job feeds?  Two quick tries."""
    last = ""
    for url in ("https://boards-api.greenhouse.io/v1/boards/gitlab/jobs", "https://remotive.com/api/remote-jobs?limit=1"):
        try:
            status, _, _ = get(url, timeout=8)
            if status < 500:
                return True, ""
        except Blocked as e:
            last = str(e)
    return False, last or "no response"


def get_json(url, params=None):
    status, text, _ = get(url, params)
    if status != 200:
        return status, None
    try:
        return status, json.loads(text)
    except ValueError:
        return status, None


# ------------------------------------------------------------------ text helpers
def text_of(raw: str, limit: int = 0) -> str:
    if not raw:
        return ""
    s = html.unescape(raw) if "&lt;" in raw[:2000] else raw
    s = re.sub(r"(?is)<(script|style|noscript|svg|head)\b.*?</\1>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>|</(p|div|li|h[1-6]|tr)>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = re.sub(r"[ \t\r\f\v ]+", " ", html.unescape(s))
    s = re.sub(r"\n\s*\n+", "\n", s).strip()
    return s[:limit] if limit else s


def iso(value) -> str:
    """Epoch s/ms, ISO-ish strings -> 'YYYY-MM-DD' ('' if unknown)."""
    if value in (None, "", 0):
        return ""
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
        v = float(value)
        v = v / 1000 if v > 1e11 else v
        try:
            return dt.datetime.fromtimestamp(v, dt.timezone.utc).date().isoformat()
        except (OverflowError, OSError, ValueError):
            return ""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", str(value))
    return m.group(1) if m else ""


def pretty(slug: str) -> str:
    return re.sub(r"[-_]+", " ", slug.split("@")[0]).title()


def result(title, url, company, location, posted="", updated="", desc="", source="", remote=False, apply_url=""):
    """A search-result-shaped record the normal ingest step understands, with an exact date."""
    when = f'"datePosted": "{posted}". ' if posted else (f"Updated {updated}. " if updated else "")
    loc = location or ("Remote" if remote else "")
    if remote and loc and "remote" not in loc.lower():
        loc = f"Remote ({loc})"
    snippet = f"{when}Company: {company}. Location: {loc}. {text_of(desc, 520)}"
    return {"title": title, "url": url, "snippet": re.sub(r"\s+", " ", snippet).strip(), "company": company,
            "location": loc, "feed": source, "apply_url": apply_url}


# ------------------------------------------------------------------ ATS boards
def ats_ref(url: str):
    """Job/board URL -> ('greenhouse', 'gitlab'); EU-hosted boards get '@eu'."""
    try:
        u = urllib.parse.urlparse(url if "://" in url else "https://" + url)
    except ValueError:
        return None
    host, parts = u.netloc.lower(), [p for p in u.path.split("/") if p]
    if host.endswith("greenhouse.io"):
        q = urllib.parse.parse_qs(u.query)
        slug = q["for"][0] if "for" in q else (parts[0] if parts and parts[0] not in ("embed", "v1") else "")
        return ("greenhouse", slug + ("@eu" if ".eu." in host else "")) if slug else None
    if host.endswith("lever.co") and parts:
        return "lever", parts[0] + ("@eu" if ".eu." in host else "")
    if host == "jobs.ashbyhq.com" and parts:
        return "ashby", parts[0]
    if host == "apply.workable.com" and parts and parts[0] not in ("j", "api"):
        return "workable", parts[0]
    if host.endswith(".workable.com") and host.count(".") == 2 and host.split(".")[0] not in ("apply", "jobs", "www"):
        return "workable", host.split(".")[0]
    if host in ("jobs.smartrecruiters.com", "careers.smartrecruiters.com") and parts:
        return "smartrecruiters", parts[0]
    return None


def board_jobs(kind: str, slug: str):
    """(status, [result]) for one company board.  status 404 = board doesn't exist."""
    s, eu = (slug[:-3], True) if slug.endswith("@eu") else (slug, False)
    out = []
    if kind == "greenhouse":
        st, d = get_json(f"https://boards-api{'.eu' if eu else ''}.greenhouse.io/v1/boards/{s}/jobs", {"content": "true"})
        for j in (d or {}).get("jobs", []):
            loc = (j.get("location") or {}).get("name", "")
            first = iso(j.get("first_published"))
            out.append(result(j.get("title", ""), j.get("absolute_url", ""), j.get("company_name") or pretty(s), loc,
                              posted=first, updated="" if first else iso(j.get("updated_at")),
                              desc=j.get("content", ""), source="Greenhouse", remote="remote" in loc.lower()))
    elif kind == "lever":
        st, d = get_json(f"https://api{'.eu' if eu else ''}.lever.co/v0/postings/{s}", {"mode": "json"})
        for j in d or []:
            cat = j.get("categories") or {}
            loc = cat.get("location") or ", ".join(cat.get("allLocations") or [])
            out.append(result(j.get("text", ""), j.get("hostedUrl", ""), pretty(s), loc, posted=iso(j.get("createdAt")),
                              desc=j.get("descriptionPlain", ""), source="Lever",
                              remote=j.get("workplaceType") == "remote" or "remote" in loc.lower(),
                              apply_url=j.get("applyUrl", "")))
    elif kind == "ashby":
        st, d = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{s}")
        for j in (d or {}).get("jobs", []):
            if j.get("isListed") is False:
                continue
            out.append(result(j.get("title", ""), j.get("jobUrl", ""), pretty(s), j.get("location", ""),
                              posted=iso(j.get("publishedAt")), desc=j.get("descriptionPlain", ""), source="Ashby",
                              remote=bool(j.get("isRemote")), apply_url=j.get("applyUrl", "")))
    elif kind == "workable":
        st, d = get_json(f"https://apply.workable.com/api/v1/widget/accounts/{s}")
        company = (d or {}).get("name") or pretty(s)
        for j in (d or {}).get("jobs", []):
            loc = ", ".join(x for x in (j.get("city"), j.get("state"), j.get("country")) if x)
            out.append(result(j.get("title", ""), j.get("url") or j.get("shortlink", ""), company, loc,
                              posted=iso(j.get("published_on")) or iso(j.get("created_at")), source="Workable",
                              remote=bool(j.get("telecommuting")), apply_url=j.get("application_url", "")))
    elif kind == "smartrecruiters":
        st, d = get_json(f"https://api.smartrecruiters.com/v1/companies/{s}/postings", {"limit": "100"})
        for j in (d or {}).get("content", []):
            l = j.get("location") or {}
            loc = l.get("fullLocation") or ", ".join(x for x in (l.get("city"), l.get("country")) if x)
            out.append(result(j.get("name", ""), f"https://jobs.smartrecruiters.com/{s}/{j.get('id')}",
                              (j.get("company") or {}).get("name") or pretty(s), loc,
                              posted=iso(j.get("releasedDate")), source="SmartRecruiters", remote=bool(l.get("remote"))))
    else:
        return 0, []
    return st, out


# ------------------------------------------------------------------ remote-job APIs
def keyword(role: str) -> str:
    w = [x for x in re.findall(r"[a-z][a-z0-9+#.]{2,}", role.lower()) if x not in ("developer", "engineer", "senior", "junior")]
    return w[0] if w else role.lower()


def remote_jobs(api: str, role: str, country: str = ""):
    out = []
    if api == "remotive":
        st, d = get_json("https://remotive.com/api/remote-jobs", {"search": role, "limit": "100"})
        for j in (d or {}).get("jobs", []):
            out.append(result(j.get("title", ""), j.get("url", ""), j.get("company_name", ""),
                              j.get("candidate_required_location") or "Worldwide", posted=iso(j.get("publication_date")),
                              desc=j.get("description", ""), source="Remotive", remote=True))
    elif api == "remoteok":
        status, text, _ = get("https://remoteok.com/api", {"tag": keyword(role)}, browser=True)
        try:
            d = json.loads(text) if status == 200 else []
        except ValueError:
            d = []
        for j in d:
            if isinstance(j, dict) and j.get("position"):
                out.append(result(j["position"], j.get("url", ""), j.get("company", ""), j.get("location") or "Worldwide",
                                  posted=iso(j.get("date") or j.get("epoch")), desc=j.get("description", ""),
                                  source="RemoteOK", remote=True))
    elif api == "himalayas":
        params = {"q": role, "sort": "recent"}
        if country:
            params["country"] = country
        st, d = get_json("https://himalayas.app/jobs/api/search", params)
        for j in (d or {}).get("jobs", []):
            restr = [x.get("name", x) if isinstance(x, dict) else str(x) for x in j.get("locationRestrictions") or []]
            out.append(result(j.get("title", ""), j.get("applicationLink") or j.get("guid", ""), j.get("companyName", ""),
                              ", ".join(restr) or "Worldwide", posted=iso(j.get("pubDate") or j.get("publishedAt")),
                              desc=j.get("excerpt") or j.get("description", ""), source="Himalayas", remote=True))
    elif api == "jobicy":
        st, d = get_json("https://jobicy.com/api/v2/remote-jobs", {"count": "50", "tag": keyword(role)})
        for j in (d or {}).get("jobs", []):
            out.append(result(text_of(j.get("jobTitle", "")), j.get("url", ""), j.get("companyName", ""),
                              j.get("jobGeo") or "Anywhere", posted=iso(j.get("pubDate")),
                              desc=j.get("jobExcerpt", ""), source="Jobicy", remote=True))
    return out


# ------------------------------------------------------------------ LinkedIn (opt-in)
def linkedin_jobs(role: str, location: str, days: int, pages: int = 2):
    """LinkedIn's public (logged-out) job search with its own 'posted in the last N seconds' filter."""
    out = []
    remote = location.lower() in ("remote", "anywhere", "worldwide", "")
    for page in range(pages):
        params = {"keywords": role, "location": "Worldwide" if remote else location,
                  "f_TPR": f"r{max(1, days) * 86400}", "start": str(page * 25)}
        if remote:
            params["f_WT"] = "2"
        status, text, _ = get("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search", params, browser=True)
        if status != 200 or "base-card" not in text and "job-search-card" not in text:
            break
        for card in re.split(r'(?=<div[^>]+class="[^"]*base-card)', text)[1:]:
            link = re.search(r'href="(https://[^"]*linkedin\.com/jobs/view/[^"?]+)', card)
            title = re.search(r'class="base-search-card__title"[^>]*>(.*?)</h3>', card, re.S)
            comp = re.search(r'class="base-search-card__subtitle"[^>]*>(.*?)</h4>', card, re.S)
            loc = re.search(r'class="job-search-card__location"[^>]*>(.*?)</span>', card, re.S)
            when = re.search(r'<time[^>]+datetime="(\d{4}-\d{2}-\d{2})"', card)
            if link and title:
                out.append(result(text_of(title.group(1)), link.group(1), text_of(comp.group(1)) if comp else "",
                                  text_of(loc.group(1)) if loc else "", posted=when.group(1) if when else "",
                                  source="LinkedIn", remote=remote))
    return out


def run_feeds(roles, boards, remote_apis, linkedin_locations, days, country="", workers=8):
    """Fetch everything in parallel.  Returns (results, report)."""
    jobs, report = [], {"boards_checked": 0, "boards_live": 0, "boards_gone": [], "errors": {}, "by_source": {}}
    tasks = []
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for kind, slug in boards:
            tasks.append(("board", (kind, slug), ex.submit(board_jobs, kind, slug)))
        for api in remote_apis:
            for role in roles:
                tasks.append(("api", api, ex.submit(remote_jobs, api, role, country)))
        for role in roles:
            for loc in linkedin_locations:
                tasks.append(("linkedin", "LinkedIn", ex.submit(linkedin_jobs, role, loc, days)))
        for kind, key, fut in tasks:
            try:
                res = fut.result()
            except Blocked as e:
                report["errors"][str(key)] = str(e)
                continue
            except Exception as e:  # noqa: BLE001  one bad source never sinks the run
                report["errors"][str(key)] = f"{type(e).__name__}: {str(e)[:100]}"
                continue
            if kind == "board":
                report["boards_checked"] += 1
                status, rows = res
                if status in (404, 410):
                    report["boards_gone"].append(f"{key[0]}:{key[1]}")
                    continue
                if status == 200:
                    report["boards_live"] += 1
                jobs.extend(rows)
            else:
                jobs.extend(res)
    seen, uniq = set(), []
    for j in jobs:
        if j["url"] and j["url"] not in seen:
            seen.add(j["url"])
            uniq.append(j)
            report["by_source"][j["feed"]] = report["by_source"].get(j["feed"], 0) + 1
    return uniq, report


# ------------------------------------------------------------------ emails on a company's own website
EMAIL_RE = re.compile(r"(?<![\w.+-])([A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,24})(?![\w-])")
BAD_EMAIL = re.compile(r"\.(png|jpe?g|gif|svg|webp|css|js)$|@(example|sentry|wixpress|domain|email|yourcompany)\.|"
                       r"^(no-?reply|donotreply|privacy|abuse|postmaster|webmaster|dmca|unsubscribe|bounce)@|@\d+x\.", re.I)
PAGE_HINT = re.compile(r"career|jobs?\b|join|hiring|work-with-us|vacanc|opening|recruit|contact|about|team|people|reach", re.I)
STANDARD_PATHS = ["/careers", "/jobs", "/contact", "/contact-us", "/about", "/about-us", "/team", "/join-us"]


def decode_cf(hexstr: str) -> str:
    try:
        key = int(hexstr[:2], 16)
        return "".join(chr(int(hexstr[i:i + 2], 16) ^ key) for i in range(2, len(hexstr), 2))
    except ValueError:
        return ""


def page_emails(raw: str, url: str) -> list[dict]:
    """[{email, source_url, evidence}] from mailto links, page text, Cloudflare-hidden and 'x [at] y [dot] com'."""
    text = text_of(raw)
    for m in re.finditer(r'(?:data-cfemail="|/cdn-cgi/l/email-protection#)([0-9a-fA-F]{4,})', raw):
        dec = decode_cf(m.group(1))
        if dec and EMAIL_RE.fullmatch(dec):
            text = text.replace("[email protected]", dec, 1)
            if dec not in text:
                text += f"\n(Cloudflare-protected address on this page: {dec})"
    for m in re.finditer(r'(?i)href=["\']mailto:([^"\'?]+)', raw):
        addr = urllib.parse.unquote(m.group(1)).strip()
        if addr.lower() not in text.lower():
            text += f"\n(email link on this page: {addr})"
    for m in re.finditer(r"\b([A-Za-z0-9._%+-]{1,64})\s*(?:\[\s*at\s*\]|\(\s*at\s*\))\s*([A-Za-z0-9-]+)\s*(?:\[\s*dot\s*\]|\(\s*dot\s*\))\s*([A-Za-z]{2,10})\b", text, re.I):
        addr = f"{m.group(1)}@{m.group(2)}.{m.group(3)}"
        text += f"\n(written on this page as '{m.group(0)}': {addr})"
    found = {}
    for m in EMAIL_RE.finditer(text):
        e = m.group(1).strip(".").lower()
        if BAD_EMAIL.search(e) or e in found:
            continue
        i = m.start()
        found[e] = {"email": e, "source_url": url,
                    "evidence": re.sub(r"\s+", " ", text[max(0, i - 110): i + len(e) + 110]).strip()}
    return list(found.values())


def site_emails(website: str, max_pages: int = 10) -> dict:
    """Read a company's own home, careers, jobs, contact, about and team pages for published emails."""
    base = website if "://" in website else "https://" + website
    status, raw, final = get(base, browser=True)
    if status != 200:
        return {"website": base, "pages": [], "emails": [], "error": f"homepage returned HTTP {status}"}
    host = urllib.parse.urlparse(final).netloc.lower().removeprefix("www.")
    links = []
    for m in re.finditer(r'(?is)<a\b[^>]*href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', raw):
        u = urllib.parse.urljoin(final, m.group(1)).split("#")[0]
        if urllib.parse.urlparse(u).netloc.lower().removeprefix("www.") == host and PAGE_HINT.search(m.group(1) + " " + text_of(m.group(2))):
            if u not in links and u != final:
                links.append(u)
    for p in STANDARD_PATHS:
        u = urllib.parse.urljoin(final, p)
        if u not in links:
            links.append(u)
    pages, emails = [final], {e["email"]: e for e in page_emails(raw, final)}

    def fetch(u):
        try:
            s, t, f = get(u, browser=True)
            return (f, t) if s == 200 else None
        except Blocked:
            return None
    with cf.ThreadPoolExecutor(max_workers=5) as ex:
        for res in ex.map(fetch, links[: max_pages - 1]):
            if res and res[0] not in pages:
                pages.append(res[0])
                for e in page_emails(res[1], res[0]):
                    emails.setdefault(e["email"], e)
    return {"website": final, "pages": pages, "emails": list(emails.values()), "error": ""}
