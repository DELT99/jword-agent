# Jword: find jobs and email recruiters, with Claude

![tests](https://github.com/DELT99/hiring-signals-leadgen/actions/workflows/ci.yml/badge.svg) ![no API keys](https://img.shields.io/badge/API%20keys-none-brightgreen) ![license](https://img.shields.io/badge/license-MIT-blue)

Tell Claude what job you want. Jword then:

1. **finds real, open jobs** posted in the time you choose (for example *the last 7 days*),
2. **finds the company's hiring emails** (careers@, hr@, recruiters), only ones the company publishes itself,
3. **writes a personal email and cover letter for each job**, using only what's in your CV,
4. **puts them in your Gmail as drafts**, so you check them and press Send yourself,
5. **gives you an Excel file** listing every job, email and next step.

No coding. No API keys. Nothing to install for Setup 1.

> **Example:** *"Use Jword. Find Flutter Developer jobs in Lahore or remote, posted in the last 7 days. My CV is attached. Find HR emails and make Gmail drafts."*

---

## Which setup should I use?

| | **Setup 1: Claude chat** | **Setup 2: Claude Code (desktop app)** ⭐ more jobs |
|---|---|---|
| Time to set up | 5 minutes | 10 minutes |
| You need | A Claude account | A paid Claude plan (Pro, Max, Team or Enterprise) and the Claude desktop app on Windows or Mac |
| Typing commands | None | None (all clicks) |
| How it finds jobs | Claude's web search | Web search **plus** reading company job boards and remote-job sites directly, so many more jobs with exact dates |
| LinkedIn | LinkedIn hiring posts found by search | Also LinkedIn's job listings, if you say yes |
| Gmail drafts | ✓ | Emails go in the Excel file (Gmail drafts: see [Setup 2, step 6](#step-6-emails-and-gmail)) |

**Not sure? Start with Setup 1.** It takes 5 minutes, and you can add Setup 2 any time.

---

## Setup 1: Claude chat (5 minutes)

### Step 1: Download the Jword file
1. Click **[dist/jword.zip](dist/jword.zip)**.
2. On the page that opens, click the **Download** button (⬇, top right of the file box).
3. You now have `jword.zip` in your Downloads folder. **Don't unzip it.**

### Step 2: Add it to Claude
1. Open **[claude.ai](https://claude.ai)** and sign in, or open the Claude desktop app.
2. Click **Customize** in the left sidebar, then **Skills**.
3. Click **+**, then **Create skill**, then **Upload a skill**.
4. Pick the `jword.zip` file.
5. Check that **Jword** appears in the list and its switch is **on**.

### Step 3: Turn on three settings
1. **Code execution:** click your name (bottom left) → **Settings** → **Capabilities** → turn on **Code execution and file creation**. *(It's usually on already. On a work or school account, an admin may need to allow it.)*
2. **Web search:** in a chat, open the **tools** menu in the message box and turn on **Web search**.
3. **Gmail** (only if you want email drafts): **Settings** → **Connectors** → **Gmail** → **Connect**, then sign in with Google and allow access.

### Step 4: Your first run
1. Click **New chat**.
2. Attach your CV with the **📎** button (PDF or Word).
3. Type:
   ```text
   Use Jword. Find AI Engineer jobs, remote, posted in the last 7 days.
   My CV is attached. Find HR emails and make Gmail drafts.
   ```
4. **Jword asks a few quick questions first.** Tap your answers:
   - *How recently should the jobs have been posted?*
   - *Where should I search?*
   - *What should I do with the jobs?*
5. Wait a few minutes. You get:
   - a numbered list of jobs (company, role, date posted, how well you fit),
   - the emails it found, and where it found each one,
   - drafts in **Gmail → Drafts** (if you chose that),
   - an **Excel file** to download.

✅ **Done.** Want more jobs per run? Add Setup 2.

---

## Setup 2: Claude Code in the desktop app (10 minutes, more jobs)

Claude Code is Claude working in a folder on your own computer. There, Jword can read company job boards (Greenhouse, Lever, Ashby, Workable), remote-job sites (Remotive, RemoteOK, Himalayas, Jobicy) and company websites **directly**, which Claude chat's sandbox can't do. It also splits big searches across helper agents that work in parallel. You use it by clicking, just like chat.

### Step 1: Install what's needed
1. **The Claude desktop app:** [claude.ai/download](https://claude.ai/download). Install it and sign in.
2. **Windows only:**
   - **Git for Windows** ([git-scm.com/downloads/win](https://git-scm.com/downloads/win)): click through the installer with the default options. The Code tab needs it.
   - **Python** ([python.org/downloads](https://www.python.org/downloads/)): run the installer and **tick "Add python.exe to PATH"** on the first screen.
3. **Mac:** nothing else is needed. If Claude later says Python is missing, install it from [python.org/downloads](https://www.python.org/downloads/).
4. **Restart the Claude app** after installing anything.

### Step 2: Download the Jword folder
1. On this GitHub page, click the green **Code** button (top of the page), then **Download ZIP**.
2. **Unzip it** (right-click → *Extract All* on Windows; double-click on Mac).
3. Move the `hiring-signals-leadgen` folder somewhere easy to find, such as **Documents**.

### Step 3: Open the folder in Claude Code
1. Open the Claude desktop app and click the **Code** tab at the top.
2. Under the message box, choose **Local**.
3. Click **Select folder** and pick the `hiring-signals-leadgen` folder.

### Step 4: Your first run
1. Type `/jword`, or say:
   ```text
   Use Jword. Find Flutter Developer jobs in Lahore or remote, posted in the last 7 days.
   My CV is at C:\Users\YourName\Documents\CV.pdf. Find HR emails and write emails for each job.
   ```
   *(Tip: put your CV in the Jword folder and just say "my CV is CV.pdf in this folder".)*
2. Answer the same quick questions as in chat. In Claude Code, Jword also asks whether to read **LinkedIn's job listings directly**. That finds many more LinkedIn jobs with exact dates, but LinkedIn's terms don't allow automated reading, so only say yes for a small personal search.
3. When Claude asks to **run a command** (it runs Jword's script on your computer), click **Allow**. Choose "always allow" for this folder to stop the repeated questions.
4. You'll see a line like *"Read 1,240 listings from 48 company boards and 4 job sites directly; 31 fit your window"* (your numbers will differ), then the usual results.

### Step 5: Find your Excel file
The Excel file is saved in the `hiring-signals-leadgen` folder, named like `jword_2026-11-22.xlsx`. Open it in Excel or Google Sheets.

### Step 6: Emails and Gmail
The Gmail connection you made in Claude chat may not be available in the Code tab. If it isn't, Jword still writes every email and puts them in the Excel file (**Applications** sheet), ready to copy into Gmail. Or do the email step in Claude chat (Setup 1), where Gmail drafts work.

✅ **Done.**

---

## Things you can ask

```text
Use Jword. Find 10 Flutter Developer jobs in Lahore or remote, posted in the last 3 days.
My CV is attached. Find HR and recruiter emails and make Gmail drafts.
```
```text
Use Jword to find 20 AI Engineer jobs in Germany, the UK or remote, posted in the last 14 days.
Just the list and the Excel file, no emails.
```
```text
Run Jword again with the same search, last 3 days. Here's last week's Excel file (attached).
```
```text
Use Jword in clients mode: find companies hiring React developers in Dubai this week.
We're a software agency. Find decision-makers and draft emails in Gmail (don't send).
```

**Tips for better results**
- **Attach your CV every time.** Jword uses it to rank the jobs and write the emails.
- Ask for **2 or 3 job titles** that mean the same thing (*"AI Engineer, LLM Engineer, ML Engineer"*).
- A short window (24 hours, 3 days) gives fewer but fresher jobs. Jword never quietly widens it.
- Say your level (*"I'm a junior developer"*) so senior-only roles get a lower fit score.
- Attach last run's Excel file when you run it again: jobs you've already seen are skipped, and nobody is emailed twice.

---

## Is it safe?

- **It never sends an email unless you choose a sending option.** By default it only creates **drafts**, which you review and send yourself.
- **It never guesses email addresses.** Every address comes from the job post or the company's own website, and the Excel file shows exactly where.
- **It never emails the same address twice**, even across runs (attach your last Excel file).
- **It never makes up** jobs, dates, skills or experience. Your emails use only facts from your CV.
- **It never logs in** to LinkedIn or any other site as you, never solves CAPTCHAs, and never applies on LinkedIn, Indeed or Glassdoor for you.

---

## Help: something's not working

| Problem | Fix |
|---|---|
| Jword doesn't appear under Skills | Upload the **zip file itself**, not an unzipped folder. |
| Claude doesn't use Jword | Check that its switch is on, start a **new chat**, and begin with *"Use Jword"*. |
| It didn't ask me any questions | You may have an old version. Delete Jword (Customize → Skills → ⋯ → Delete) and upload the latest `jword.zip`. |
| "Jword needs web search" | Turn on **Web search** in the chat's tools menu. |
| No Gmail drafts | Connect Gmail: Settings → Connectors → Gmail. Until then, the emails are in the chat and the Excel file. |
| No Excel file | Turn on **Code execution and file creation** (Settings → Capabilities). |
| Code tab asks me to upgrade | Claude Code needs a paid plan. Use Setup 1 instead. |
| Code tab won't start on Windows | Install **Git for Windows**, then restart the Claude app. |
| "Python was not found" (Setup 2) | Install Python from python.org with **"Add python.exe to PATH"** ticked, then restart the Claude app. |
| `/jword` doesn't appear (Setup 2) | Make sure you selected the `hiring-signals-leadgen` folder itself (the one containing `CLAUDE.md`), not a folder inside it or above it. |
| Fewer jobs than I asked for | Normal with a short window. Try 14 or 30 days, or add more job titles or locations. Setup 2 finds more. |
| No emails found for a company | Many companies only accept applications through their website form. Jword never guesses, so apply with the job link; your cover letter is still in the Excel file. |

Still stuck? [Open an issue](https://github.com/DELT99/hiring-signals-leadgen/issues) with what you typed and what happened.

---

## Updating to a new version
- **Setup 1:** download the new [`jword.zip`](dist/jword.zip) → Customize → Skills → on Jword, **⋯ → Delete** → **Upload a skill** with the new file → start a new chat.
- **Setup 2:** download the ZIP from GitHub again and replace your `hiring-signals-leadgen` folder. Move your CV and Excel files out of the old folder first.

---

## For developers and power users
- **[Advanced guide](docs/advanced.md):**
  - how each stage works;
  - the direct feeds and how searches are planned;
  - Claude Code subagents (`git clone`, then `claude` in the folder);
  - repo layout and tests.
- **[n8n workflow](docs/n8n.md):** the original scheduled lead finder (uses your own API keys).

## Responsible use
Jword reads only public pages. It keeps the original link and source on every job (Remotive, RemoteOK, Himalayas and Jobicy ask for this), and reads only a few pages at a time from each site. LinkedIn's direct job listings are off unless you say yes, because LinkedIn's terms forbid automated access; keep those runs small and personal. You're responsible for emails sent in your name, so review the drafts. If you email companies to offer services (clients mode), follow your country's rules for commercial email, such as CAN-SPAM or GDPR.

## License
MIT. See [LICENSE](LICENSE).
