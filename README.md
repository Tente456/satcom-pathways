# Satcom Pathways

A news and jobs site for people starting out or working in satellite communications and space.
It refreshes itself every 4 hours:

- **News:** headlines from 17 satcom, space and telecom feeds (SpaceNews, Payload, Via Satellite,
  SpaceWatch.Global, Space in Africa and others). General telecom feeds are filtered to satellite
  stories. Only the headline, source, date and link are shown; readers click through to the publisher.
- **Jobs:** openings pulled from the public careers boards of 21 satellite and space companies
  (AST SpaceMobile, Astranis, Starlink roles at SpaceX, Telesat, E-Space, Kepler, Skylo, Planet,
  ICEYE and others). Roles are tagged by sector, role type, early career and remote.

- **Africa deals:** a hand-curated tracker of African satcom agreements, contracts, licences,
  funding rounds and launches, kept in `deals.json`. Each entry links to its public source, and the
  page also shows the latest Africa headlines from the news feeds.

Hosting is free on GitHub Pages. There is no server to maintain.

## Put it online (about 10 minutes)

1. Create a free GitHub account if you don't have one, then create a new **public** repository,
   for example `satcom-pathways`.
2. Upload everything in this folder to the repository, keeping the `.github` folder.
   (On the repository page: **Add file → Upload files**, then drag the folder contents in.)
3. In the repository go to **Settings → Pages** and set **Source** to **GitHub Actions**.
4. Go to **Settings → Actions → General → Workflow permissions** and choose
   **Read and write permissions**. Save.
5. Go to the **Actions** tab, open **Refresh news and jobs**, and press **Run workflow**.
   After 1–2 minutes the site is live at `https://<your-username>.github.io/satcom-pathways/`.

From then on it rebuilds itself every 4 hours. You can also press **Run workflow** at any time.

To use your own domain (for example `satcompathways.com`), add it under **Settings → Pages → Custom domain**
and follow GitHub's DNS instructions.

## Change things

Everything editable is in `config.json`:

| What | Where in config.json |
|---|---|
| Site name and tagline | `site_name`, `tagline` |
| Add or remove a news feed | `news_sources` (set `"filter": true` for general telecom feeds) |
| Topic tags and their keywords | `news_categories` |
| Add a company's jobs | `job_boards` — needs the company's Greenhouse, Lever or Ashby board name |
| How many roles per company | `jobs_cap_per_company` |
| Links to other job boards | `more_job_boards` |

## Publish research

Each piece in the Research section is a text file in the `research` folder. To publish one:

1. Copy an existing file in `research/` and rename it, for example `2026-11-d2d-spectrum-africa.md`.
2. Edit the top block: `title`, `type` (Analysis, Brief or Report), `date` (YYYY-MM-DD), `author`,
   a one-sentence `summary` and comma-separated `tags`.
3. Write the body below the second `---` line. Use `## Heading` for section titles, `- ` for bullet
   points, `**bold**`, tables, and links written as `[text](https://...)`.
4. Commit the file. It appears on the Research page, gets its own page, and goes into the next
   weekly digest.

You can write and edit these files directly on github.com: open the `research` folder and use
**Add file → Create new file**.

## Weekly digest

Every Monday the build writes a digest of the previous week: new research, the top satcom and Africa
headlines, new Africa deals, and new early-career roles. It is published at `/digest.html` and as an
RSS feed at `/digest.xml`.

To email it, either copy the latest digest from `/digest.html` into a Buttondown email and send it, or
switch on Buttondown's RSS-to-email add-on and point it at `https://satcompathways.com/digest.xml` so
each new digest is sent automatically.

## Turn on the subscribe box

The subscribe box works with Buttondown (free for the first 100 subscribers).

1. Create an account at buttondown.com and choose a username, for example `satcompathways`.
2. In `config.json`, set `"buttondown_username": "satcompathways"` under `newsletter`.
3. Commit the change. New sign-ups appear in Buttondown with the tag `website`, and Buttondown
   sends them a confirmation email.

Until a username is set, the box shows "Sign-up opens soon" and collects nothing.

## The scrolling company band

The band under the header lists the companies whose job boards the site pulls from
(`job_boards` in `config.json`), so it updates itself when you add or remove a company.
Change the wording with `marquee_label`.

## Events

`events.json` holds the conference list. Each entry has `start` and `end` (YYYY-MM-DD), `name`, `organiser`, `where`, `region` (Africa, Europe, Americas, Middle East, Asia), `topic`, `summary`, `url` and `confirmed`. Set `confirmed` to `false` when the dates come from a listing rather than the organiser's own site; the page then shows "Check dates". If only the month is known, add `"dates": "Aug 2027"` and set `start`/`end` to the first and last day of that month. Past events drop off automatically. The next three show on the Home page.

## About page

Edit `about.md` (Markdown). Counts such as `<span data-count="companies"></span>` fill in automatically (`companies`, `deals`, `events`, `research`). The contact line uses `{{CONTACT}}`; it only appears once you set `contact_email` in `config.json`.

## Colours

Two brand colours, set at the top of `template.html`: navy (`--ink`, `--band`) and bright green (`--accent`, `#1fd16a`, also the dot in the logo). Bright green is too light for text on white, so green text uses `--accent-text` (`#0b7a3b`).

## Saved jobs and job alerts

- **Saved jobs.** The star on each role saves it in the visitor's own browser. There are no accounts, and nothing is stored on your side. Saved roles don't move between devices.
- **Email alerts.** The subscribe form has a box, "Also email me new early-career roles". When it's ticked, Buttondown tags the subscriber `early-career-jobs`. To send those people a weekly list, point a Buttondown RSS-to-email automation at `jobs-early.xml` and limit it to that tag (check your Buttondown plan supports this), or send a manual email to that tag. Test the form once after connecting Buttondown to confirm both tags (`website` and `early-career-jobs`) land.
- **Feeds.** Each run writes `jobs.xml` (newest 100 roles) and `jobs-early.xml` (all early-career roles). Both are linked on the Jobs page and in the footer.

## Add a deal

Open `deals.json` and copy an existing entry. Fill in `date` (YYYY-MM-DD, or YYYY-MM if only the month
is known), `title`, `type`, `segment`, `countries`, `parties`, `value_usd` (a number, or `null` if not
disclosed), `value_text`, a one-line `summary` in your own words, and the `source_name` and `source_url`
of the announcement. Commit the change and the site rebuilds within a couple of minutes.

To find a company's board name, open one of its job ads. A link like
`boards.greenhouse.io/astranis/...` means `"ats": "greenhouse", "id": "astranis"`;
`jobs.lever.co/telesat/...` means lever / telesat; `jobs.ashbyhq.com/skylo/...` means ashby / skylo.

Page layout and colours are in `template.html`.

## Run it on your own computer

```
pip install -r requirements.txt
python build.py
```

Then open `site/index.html` in a browser.
