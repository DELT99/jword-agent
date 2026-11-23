# Jword: advanced guide

For people who want the details. **New here? Start with the [README](../README.md).**

- [How Jword works](#how-it-works)
- [Direct feeds and website reading](#direct-feeds-and-website-reading-automatic)
- [Claude Code](#part-b--claude-code-advanced) (parallel subagents)
- [Feature comparison](#part-c--feature-comparison)
- [Repo layout and development](#repo-layout)

---

## How it works
**First, Jword always asks you** (as tap-to-answer options): how recently the jobs should have been posted (24 hours to 60 days, or your own dates), where to search (anywhere, company career pages / ATS, LinkedIn, Indeed, Wellfound, remote job boards, Built In), and what to do with the jobs (just find them / + find recruiter and HR emails / + write an application and email for each job as Gmail drafts). It also asks for your roles, locations and CV if you haven't given them. After that it works through every stage without stopping, except to ask how to handle the emails.

| Stage | What Jword does | You decide |
|---|---|---|
| 1. **Find** | **In Claude Code** it first reads company job boards and remote-job APIs directly, with exact dates ([details](#direct-feeds-and-website-reading-automatic)). **Then (and in Claude chat)** Jword searches like the n8n agent, with no API keys: each search targets one board with a `site:` filter. The boards come from your options: the open web, **LinkedIn hiring posts**, your location's own boards (e.g. Rozee.pk, Hired.pk and Taraki for Pakistan, Bayt, Naukri, Reed), Greenhouse, Workable, Lever and remote boards. Every role × location gets a turn, the board furthest behind its share goes next, and dry boards are skipped. **LinkedIn gets priority** (about one search in three, and up to ~40% of the jobs) but the results are never LinkedIn-only. Drops listing pages, closed or paywalled jobs, duplicates and wrong locations, and **anything outside your posting window or without a verifiable posting date**. Scores each job 1–5 against your CV (with the gaps, honestly) and opens it to confirm it's still accepting applications. | roles, locations, **how recent**, platforms, how many |
| 2. **Contacts** | Finds named recruiters, HR, talent and hiring managers and founders, plus generic hiring inboxes, **only from public pages**, each with its source and a verification status. If the job post has no HR or recruiter email, it **searches the company by name and checks its own website** (careers, contact, about, team pages) before giving up. Never guesses an address. | jobs only / + contacts / + contacts and outreach |
| 3. **Prepare** | Builds your applicant profile from your CV, asks once for anything missing, and writes a cover letter and answers per job. | – |
| 4. **Outreach** | Writes one email per verified contact (own subject, own body), creates Gmail drafts or sends with approval, and records every Gmail id. | contacts only / in chat / **Gmail drafts** / approve each / capped auto |
| 5. **Apply** *(optional)* | Fills application forms in a browser, and hands back to you for logins, CAPTCHAs and uploads. | ask before each submit / auto when covered / fill only |
| 6. **Report** | An Excel tracker (Leads, Contacts, Applications, Run Log, Excluded) plus a status table. | – |

**Clients mode** does the same for agencies and freelancers: companies hiring developers become **sales leads**, with decision-maker contacts and B2B emails. B2B emails are **never** sent automatically.

**What a real run looks like** (live test, 17 Nov 2026: AI Engineer + Flutter Developer, Lahore + Remote, last 7 days, 5 jobs): 3 searches → 37 results → 5 verified open jobs posted in the window, a tailored letter for each, 1 published hiring inbox found (the other companies publish none) → 1 Gmail draft. Opening each page mattered: 6 jobs that looked open in search were expired or closed, including one shown as "5 days ago" that was posted 9 months earlier.

**n8n-style search check** (same day, 7-day window, AI Engineer + Flutter Developer, Lahore + Remote): 6 board searches, 3 jobs saved and page-checked. One came from Hired.pk ("6 hours ago"), one from Remotive and one from Taraki. 14 expired listings and 9 out-of-window listings were dropped, and 7 good matches had no date anywhere. Two changes came out of this test:
- Dated boards are now searched with this month's date words. On Rozee, the plain query had returned 2023–2025 pages; the dated query put this month's listings first.
- Titles like "AI/ML Engineer" now count as *AI Engineer*.

**The guarantees:** the window is never widened to hit a number · no invented jobs, dates, contacts or experience · emails only to verified, published addresses · never the same email twice, even across runs · nothing is sent or submitted outside the mode you chose · Claude never claims an email was sent without Gmail's confirmation.

---

## Direct feeds and website reading (automatic)
`scripts/direct.py` uses only Python's standard library, so there's nothing to install. Where the computer running Jword can reach the internet directly (Claude Code on your computer), the first `next` call reads these sources, with exact posting dates:

| Source | What | Date |
|---|---|---|
| Greenhouse, Lever, Ashby, Workable, SmartRecruiters | The public job feeds behind companies' own careers pages. ~60 boards ship as a starting list, and every board seen in search results is added and read too | ✓ exact (Greenhouse jobs with only an "updated" date are treated as undated) |
| Remotive, RemoteOK, Himalayas, Jobicy | Free public remote-job APIs (for Remote/Anywhere searches) | ✓ exact |
| LinkedIn public job search *(opt-in: `--linkedin-direct`)* | The logged-out job list, with LinkedIn's own "posted in the last N days" filter. LinkedIn's terms forbid automated access, so it's off unless the user agrees | ✓ exact |

These jobs then go through the same filters as web results: role, location, posting window, duplicates and fit review. Jobs from a company's live ATS feed count as open without a page check. In Claude chat the sandbox blocks these sites. The probe notices in under a second, and the run uses web search only.

`jword.py site-emails --id <lead> --url <company site>` reads the company's home, careers, jobs, contact, about and team pages directly. It decodes Cloudflare-protected addresses, and records each email with its page and quoted text, through the same checks as `contacts`. Where it can't connect, it says `unavailable`, and Claude falls back to web search + web fetch.

---

## Part B — Claude Code (advanced)

Use this for big runs (many roles and locations). Claude Code runs **specialized subagents in parallel**, each in its own context.

**Prerequisites:** [Claude Code](https://code.claude.com/docs/en/overview) (signed in), [Git](https://git-scm.com/downloads), Python 3.10+ with `pip install openpyxl`. VS Code is optional.

```bash
git clone https://github.com/DELT99/hiring-signals-leadgen.git
cd hiring-signals-leadgen
code .        # optional: open in VS Code
claude
```
*(Windows: run the same commands in PowerShell or Git Bash. Use `py -m pip install openpyxl` if `pip` isn't found.)*

Claude Code discovers these automatically from the project folder:
| Path | What it is |
|---|---|
| `.claude/skills/jword/SKILL.md` | the Jword skill ([skills docs](https://code.claude.com/docs/en/skills)) |
| `.claude/agents/job-researcher.md` | runs search packets and page checks (Sonnet) |
| `.claude/agents/contact-researcher.md` | finds published contacts (Haiku) |
| `.claude/agents/application-writer.md` | cover letters and answers (Sonnet) |
| `.claude/agents/outreach-writer.md` | one email per contact (Sonnet) |
| `CLAUDE.md` | project notes for Claude |

- **See the agents:** type `/agents` ([subagents docs](https://code.claude.com/docs/en/sub-agents)).
- **Run Jword:** type `/jword`, or just ask: *"Use jword to find 20 Flutter jobs in Germany, UK and remote, posted in the last 7 days."*
- **How it runs:** the main session is the **orchestrator**. It asks you the questions, splits the searches into packets (one per location or role), runs up to 3–4 subagents at once, merges and de-duplicates the results, verifies them, then hands contact research and writing to the other agents. **Only the orchestrator** talks to you, sends Gmail drafts or emails, or submits forms. Subagents have no Gmail, browser or shell access. The same posting window goes to every agent, and the engine enforces it.
- **Models:** set in each agent file (`model: sonnet` / `haiku`). Change one to `inherit` to use your session's model, or set `CLAUDE_CODE_SUBAGENT_MODEL`.
- **Gmail in Claude Code:** the Gmail connector you added in Claude chat isn't automatically available in Claude Code. Add a Gmail MCP server/connector to Claude Code yourself, or let Jword write the emails into the tracker and create the drafts from Claude chat.
- **Cost:** subagents add speed and separate contexts, not guaranteed token savings (each one loads its own instructions). For small runs (one location, ≤10 jobs), Jword stays sequential.

---

## Part C — Feature comparison
| | **Claude chat** | **Claude Code** |
|---|---|---|
| Installation | Upload one zip | Clone the repo, run `claude` |
| Direct job feeds + website reading | – (sandbox blocks them; web search instead) | ✓ automatic (LinkedIn opt-in) |
| Skill support | ✓ | ✓ (`/jword`) |
| Custom subagents | – (one assistant) | ✓ 4 specialized agents |
| Parallel research | – (batched, in order) | ✓ |
| Strict posting-date filter | ✓ | ✓ (same engine) |
| Job verification (open, dated) | ✓ | ✓ |
| Contact research (named + generic) | ✓ | ✓ |
| Application preparation | ✓ | ✓ |
| Gmail drafts / sending | ✓ with the Gmail connector | needs a Gmail connector set up in Claude Code |
| Form filling | ✓ with Claude in Chrome / desktop browser | ✓ with a browser tool |
| Excel tracker | ✓ | ✓ |
| Clients (B2B) mode | ✓ | ✓ |

---

## Repo layout
```
skill/jword/            SOURCE of the skill: SKILL.md, references/, scripts/jword.py + direct.py, tests/
.claude/skills/jword/   generated copy for Claude Code (don't edit)
.claude/agents/         the four Claude Code subagents
dist/jword.zip          generated upload for Claude chat (don't edit)
tools/build_skill.py    builds both copies from the source
CLAUDE.md               notes for Claude Code
examples/               sample output
workflow/ src/ sheets/ scripts/ docs/n8n.md   the n8n edition
tests/                  distribution checks + n8n simulator
```

## Development
```bash
python3 tools/build_skill.py                   # after editing skill/jword/
python3 skill/jword/tests/test_jword.py        # engine: search loop, filters, Excel
python3 skill/jword/tests/test_jword_v3.py     # date window, contacts, outreach, Gmail, reruns, packets
python3 skill/jword/tests/test_direct.py       # direct feeds, LinkedIn opt-in, site-emails (fake internet)
python3 tests/test_distribution.py             # zip + Claude Code copy + agents + n8n regression
node tests/simulate.js                         # n8n workflow simulator
```
More detail on stages, sheets and statuses: **[skill/README.md](../skill/README.md)**.
