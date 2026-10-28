#!/usr/bin/env python3
"""Build the Satcom Pathways site.

Fetches news RSS feeds and public company job boards (Greenhouse, Lever, Ashby),
tags each item, and writes a static site to ./site:

  site/index.html      the page (news and jobs views, data embedded)
  site/data/news.json  the news items
  site/data/jobs.json  the job items

Only headlines, dates, sources and links are kept for news; articles stay on the
publishers' sites.

Usage:  python build.py            (fetch live data and build)
        python build.py --offline  (rebuild the page from site/data/*.json)
"""
import calendar
import html
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import markdown as md
from email.utils import format_datetime

ROOT = Path(__file__).parent
OUT = ROOT / "site"
UA = "Mozilla/5.0 (compatible; SatcomPathwaysBot/1.0; +https://github.com)"
NOW = datetime.now(timezone.utc)

EARLY_CAREER = re.compile(
    r"\b(intern|internship|co-?op|graduate|new grad|early[- ]career|entry[- ]level|junior|"
    r"apprentice|apprenticeship|trainee|university|student)\b", re.I)
FUNCTIONS = [
    # Checked in order; the first match wins. Patterns match word starts, so "recruit" covers "recruiting".
    ("Program & project management", r"\b(program manager|project manager|programme manager|technical program|tpm\b|"
                                     r"project engineer|pmo|scrum|delivery)"),
    ("Policy, regulatory & spectrum", r"\b(regulatory|licensing|spectrum|policy|government affairs|"
                                      r"public affairs|export control|itar)"),
    ("Corporate", r"\b(financ|cost control|controller|benefits|social media|director of communications|training|accountant|accounting|legal|counsel|paralegal|people|hr\b|human resources|recruit|"
                  r"talent|payroll|tax\b|compliance|executive assistant|office|employee relations|workplace|"
                  r"communications? (manager|specialist|intern)|marketing)"),
    ("Business & sales", r"\b(sales|account|business development|bd\b|partnership|commercial|product manag|"
                         r"product market|customer|pricing|strateg|growth|go-to-market|business)"),
    ("Engineering & technical", r"\b(engineer|technician|scientist|developer|architect|rf\b|antenna|firmware|"
                                r"software|hardware|systems|test|analyst|integration|devops|data|machinist|"
                                r"welder|inspector|design|propulsion|avionics|combustion|materials|electric|"
                                r"mechanic|physicist|research|gnc|thermal|optical|payload)"),
    ("Operations & supply chain", r"\b(operations|operator|supply|sourcing|procurement|buyer|manufactur|"
                                  r"production|logistics|planner|planning|quality|facilit|mission|inventory|"
                                  r"shipping|receiving|warehouse|driver|fulfil|assembl|security|material handler|custodian|cnc|"
                                  r"launch manager|coordinator|ehs|safety)"),
]
IT_RE = re.compile(r"\bIT\b|\b(information security|cyber|ciso|helpdesk|help desk|service desk)", re.I)


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def get_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def terms_regex(terms):
    parts = [re.escape(t.strip()) for t in terms if t.strip()]
    return re.compile(r"\b(" + "|".join(parts) + r")\b", re.I)


def clean_text(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


# ---------------------------------------------------------------- news

def fetch_feed(src):
    try:
        parsed = feedparser.parse(get_bytes(src["url"]))
        return src, parsed.entries
    except Exception as e:  # one bad feed must not stop the build
        log(f"  news FAIL {src['name']}: {e}")
        return src, []


def entry_date(e):
    for key in ("published_parsed", "updated_parsed"):
        t = e.get(key)
        if t:
            return datetime.fromtimestamp(calendar.timegm(t), tz=timezone.utc)
    return None


def build_news(cfg):
    space_re = terms_regex(cfg["space_filter_terms"])
    cat_res = {c: terms_regex(t) for c, t in cfg["news_categories"].items()}
    cutoff = NOW - timedelta(days=cfg["news_max_age_days"])
    items, seen = [], set()
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(fetch_feed, cfg["news_sources"]))
    for src, entries in results:
        kept = 0
        for e in entries:
            title = clean_text(e.get("title"))
            link = (e.get("link") or "").strip()
            if not title or not link:
                continue
            key = re.sub(r"\W+", "", title.lower())
            if link in seen or key in seen:
                continue
            when = entry_date(e)
            if when is None or when < cutoff or when > NOW + timedelta(days=1):
                continue
            when = min(when, NOW)  # some feeds stamp items a few hours ahead
            text = f"{title} {clean_text(e.get('summary'))[:600]}"
            if src.get("filter") and not space_re.search(text):
                continue
            cats = [c for c, rx in cat_res.items() if rx.search(text)]
            seen.update((link, key))
            items.append({"title": title, "url": link, "source": src["name"],
                          "date": when.isoformat(timespec="minutes"), "categories": cats})
            kept += 1
        log(f"  news {src['name']}: {kept} kept of {len(entries)}")
    # Feeds only carry their latest items, so keep earlier items from the previous build.
    prev = OUT / "data/news.json"
    if prev.exists():
        for old in json.loads(prev.read_text(encoding="utf-8")):
            key = re.sub(r"\W+", "", old["title"].lower())
            if old["url"] in seen or key in seen:
                continue
            if datetime.fromisoformat(old["date"]) < cutoff:
                continue
            seen.update((old["url"], key))
            items.append(old)
    items.sort(key=lambda x: x["date"], reverse=True)
    return items[: cfg["news_max_items"]]


# ---------------------------------------------------------------- jobs

def norm_job(board, title, url, location, posted, team=""):
    title = clean_text(title)
    location = clean_text(location) or "Not stated"
    text = f"{title} {team}"
    function = next((name for name, rx in FUNCTIONS if re.search(rx, text, re.I)), None)
    if function is None or (function == "Corporate" and re.search(r"\bIT\b", title)):
        function = "IT & security" if re.search(r"\bIT\b", title) or IT_RE.search(title) else (function or "Other")
    return {
        "title": title, "url": url, "company": board["company"], "sector": board["sector"],
        "location": location, "posted": posted, "function": function,
        "early": bool(EARLY_CAREER.search(title)),
        "remote": bool(re.search(r"\bremote\b", f"{location} {title}", re.I)),
    }


def iso_from_ms(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat(timespec="minutes") if ms else ""


def iso_norm(s):
    if not s:
        return ""
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat(timespec="minutes")
    except ValueError:
        return ""


def fetch_board(board):
    ats, bid = board["ats"], board["id"]
    try:
        if ats == "greenhouse":
            data = get_json(f"https://boards-api.greenhouse.io/v1/boards/{bid}/jobs")["jobs"]
            jobs = [norm_job(board, j["title"], j["absolute_url"], (j.get("location") or {}).get("name", ""),
                             iso_norm(j.get("first_published") or j.get("updated_at"))) for j in data]
        elif ats == "lever":
            data = get_json(f"https://api.lever.co/v0/postings/{bid}?mode=json")
            jobs = [norm_job(board, j["text"], j["hostedUrl"], (j.get("categories") or {}).get("location", ""),
                             iso_from_ms(j.get("createdAt")),
                             " ".join(filter(None, [(j.get("categories") or {}).get(k, "") for k in ("team", "department")])))
                    for j in data]
        elif ats == "ashby":
            data = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{bid}")["jobs"]
            jobs = [norm_job(board, j["title"], j["jobUrl"], j.get("location", ""), iso_norm(j.get("publishedAt")),
                             f"{j.get('department', '')} {j.get('team', '')}")
                    for j in data if j.get("isListed", True)]
        else:
            raise ValueError(f"unknown ats {ats}")
    except Exception as e:
        log(f"  jobs FAIL {board['company']}: {e}")
        return board, []
    must = [t.lower() for t in board.get("title_must_include", [])]
    if must:
        jobs = [j for j in jobs if any(t in j["title"].lower() for t in must)]
    return board, jobs


def build_jobs(cfg):
    out = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(fetch_board, cfg["job_boards"]))
    for board, jobs in results:
        seen, uniq = set(), []
        for j in sorted(jobs, key=lambda x: x["posted"], reverse=True):
            k = (j["title"].lower(), j["location"].lower())
            if k not in seen:
                seen.add(k)
                uniq.append(j)
        kept = uniq[: cfg["jobs_cap_per_company"]]
        log(f"  jobs {board['company']}: {len(kept)} kept of {len(jobs)}")
        out.extend(kept)
    out.sort(key=lambda x: x["posted"], reverse=True)
    return out



# ---------------------------------------------------------------- research

def load_research():
    """Read research/*.md. Front matter is simple 'key: value' lines between --- markers."""
    items = []
    for path in sorted((ROOT / "research").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta, body = {}, text
        if text.startswith("---"):
            _, head, body = text.split("---", 2)
            for line in head.strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
        html_body = md.markdown(body, extensions=["tables", "sane_lists"])
        html_body = html_body.replace("<a href=\"http", "<a target=\"_blank\" rel=\"noopener\" href=\"http")
        words = len(re.findall(r"\w+", body))
        items.append({
            "slug": re.sub(r"[^a-z0-9-]", "-", path.stem.lower()),
            "title": meta.get("title", path.stem),
            "type": meta.get("type", "Analysis"),
            "date": meta.get("date", ""),
            "author": meta.get("author", ""),
            "summary": meta.get("summary", ""),
            "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
            "minutes": max(1, round(words / 220)),
            "html": html_body,
        })
    items.sort(key=lambda x: x["date"], reverse=True)
    return items


# ---------------------------------------------------------------- weekly digest

def week_key(d):
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def build_digest(cfg, news, jobs, deals, research):
    """Create the digest for the last completed Monday-Sunday week if it does not exist yet."""
    store = OUT / "data/digests.json"
    digests = json.loads(store.read_text(encoding="utf-8")) if store.exists() else []
    monday = (NOW - timedelta(days=NOW.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    start, end = monday - timedelta(days=7), monday
    key = week_key(start)
    if any(d["week"] == key for d in digests):
        return digests

    def in_week(iso):
        if not iso:
            return False
        try:
            t = datetime.fromisoformat(iso if "T" in iso else iso + "T00:00+00:00")
        except ValueError:
            return False
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return start <= t < end

    week_news = [n for n in news if in_week(n["date"])]
    def score(n):
        c = n["categories"]
        return (("Satcom & connectivity" in c) * 2 + ("Africa" in c) * 2 + ("Business & funding" in c))
    top = sorted(week_news, key=lambda n: (score(n), n["date"]), reverse=True)[:8]
    week_jobs = [j for j in jobs if in_week(j["posted"])]
    early, seen_co = [], set()
    for j in week_jobs:
        if j["early"] and j["company"] not in seen_co:
            seen_co.add(j["company"]); early.append(j)
    early = early[:5]
    week_deals = [d for d in deals if len(d["date"]) == 10 and in_week(d["date"])]
    week_research = [r for r in research if in_week(r["date"])]
    url = cfg.get("site_url", "").rstrip("/")
    esc = html.escape

    parts = [f"<p>Highlights from {start:%d %B} to {(end - timedelta(days=1)):%d %B %Y}.</p>"]
    if week_research:
        parts.append("<h2>New research</h2><ul>" + "".join(
            f'<li><a href="{url}/#research-{r["slug"]}">{esc(r["title"])}</a>: {esc(r["summary"])}</li>' for r in week_research) + "</ul>")
    if top:
        parts.append("<h2>Top headlines</h2><ul>" + "".join(
            f'<li><a href="{esc(n["url"])}">{esc(n["title"])}</a> ({esc(n["source"])})</li>' for n in top) + "</ul>")
    if week_deals:
        parts.append("<h2>Africa deals</h2><ul>" + "".join(
            f'<li><a href="{esc(d["source_url"])}">{esc(d["title"])}</a></li>' for d in week_deals) + "</ul>")
    parts.append(f"<h2>Jobs</h2><p>{len(week_jobs)} of the roles listed on the site were posted this week"
                 + (", including these early-career openings:" if early else ".") + "</p>")
    if early:
        parts.append("<ul>" + "".join(
            f'<li><a href="{esc(j["url"])}">{esc(j["title"])}</a>, {esc(j["company"])}, {esc(j["location"])}</li>' for j in early) + "</ul>")
    parts.append(f'<p><a href="{url}/#jobs">See all jobs</a> · <a href="{url}/#deals">Deals tracker</a> · <a href="{url}/#research">Research</a></p>')

    digests.insert(0, {"week": key, "title": f"{cfg['site_name']} weekly: {start:%d %b} to {(end - timedelta(days=1)):%d %b %Y}",
                       "published": end.isoformat(timespec="minutes"), "html": "".join(parts)})
    digests = digests[:26]
    store.write_text(json.dumps(digests, ensure_ascii=False, indent=1), encoding="utf-8")
    return digests


def write_job_feeds(cfg, jobs):
    """jobs.xml (newest 100 roles) and jobs-early.xml (every early-career role), for feed readers and email tools."""
    url = cfg.get("site_url", "").rstrip("/")
    esc = html.escape

    def feed(name, title, desc, items):
        body = ""
        for j in items:
            try:
                pub = format_datetime(datetime.fromisoformat(j["posted"]))
            except (KeyError, ValueError):
                pub = format_datetime(NOW)
            body += (f"<item><title>{esc(j['title'])} at {esc(j['company'])}</title><link>{esc(j['url'])}</link>"
                     f"<guid isPermaLink=\"true\">{esc(j['url'])}</guid><pubDate>{pub}</pubDate>"
                     f"<description>{esc(j['location'])} · {esc(j['function'])}</description></item>")
        rss = (f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{esc(title)}</title>'
               f"<link>{url}/#jobs</link><description>{esc(desc)}</description>"
               f"<lastBuildDate>{format_datetime(NOW)}</lastBuildDate>{body}</channel></rss>")
        (OUT / name).write_text(rss, encoding="utf-8")

    newest = sorted(jobs, key=lambda j: j.get("posted", ""), reverse=True)
    feed("jobs.xml", f"{cfg['site_name']}: new satellite and space jobs",
         "The newest roles from the careers boards we track.", newest[:100])
    feed("jobs-early.xml", f"{cfg['site_name']}: early-career roles",
         "Internships, graduate schemes and other early-career roles.", [j for j in newest if j.get("early")])


def write_digest_files(cfg, digests):
    url = cfg.get("site_url", "").rstrip("/")
    esc = html.escape
    items = "".join(
        f"<item><title>{esc(d['title'])}</title><link>{url}/digest.html#{d['week']}</link>"
        f"<guid isPermaLink=\"false\">{d['week']}</guid>"
        f"<pubDate>{format_datetime(datetime.fromisoformat(d['published']))}</pubDate>"
        f"<description><![CDATA[{d['html']}]]></description></item>" for d in digests)
    rss = (f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
           f"<title>{esc(cfg['site_name'])} weekly</title><link>{url}/</link>"
           f"<description>{esc(cfg.get('newsletter', {}).get('blurb', ''))}</description>{items}</channel></rss>")
    (OUT / "digest.xml").write_text(rss, encoding="utf-8")
    body = "".join(f'<article id="{d["week"]}"><h1>{esc(d["title"])}</h1>{d["html"]}</article><hr>' for d in digests) \
        or "<p>The first weekly digest appears after the site has run for one full week.</p>"
    page = (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{esc(cfg['site_name'])} weekly digests</title><style>body{{font-family:Arial,sans-serif;max-width:680px;margin:30px auto;padding:0 16px;line-height:1.5;color:#18202b}}"
            f"h1{{font-size:22px}}h2{{font-size:17px;margin-top:22px}}a{{color:#174ea6}}hr{{border:0;border-top:1px solid #ddd;margin:30px 0}}</style></head><body>{body}</body></html>")
    (OUT / "digest.html").write_text(page, encoding="utf-8")

# ---------------------------------------------------------------- page

def load_json_list(name):
    """Hand-kept lists (events.json). Missing file means an empty list."""
    f = ROOT / name
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


def load_about(cfg):
    """about.md becomes the About page. {{CONTACT}} becomes a mailto link when contact_email is set."""
    f = ROOT / "about.md"
    if not f.exists():
        return ""
    text = f.read_text(encoding="utf-8")
    email = cfg.get("contact_email", "").strip()
    if email:
        text = text.replace("{{CONTACT}}", f'<a href="mailto:{html.escape(email)}">{html.escape(email)}</a>')
    else:  # drop any line that needs the contact address
        text = "\n".join(l for l in text.splitlines() if "{{CONTACT}}" not in l)
    # The part above the first "---" line is the dark "why" panel; the rest is the page body.
    parts = re.split(r"\n-{3,}\n", text, maxsplit=1)
    why, body = (parts[0], parts[1]) if len(parts) == 2 else ("", parts[0])
    out = ""
    if why.strip():
        out += '<section class="why">' + md.markdown(why, extensions=["sane_lists"]) + "</section>"
    return out + '<div class="prose">' + md.markdown(body, extensions=["sane_lists"]) + "</div>"


def render(cfg, news, jobs, updated, research):
    template = (ROOT / "template.html").read_text(encoding="utf-8")
    payload = {
        "site": {"name": cfg["site_name"], "tagline": cfg["tagline"], "updated": updated},
        "newsCategories": list(cfg["news_categories"].keys()),
        "news": news, "jobs": jobs, "moreBoards": cfg["more_job_boards"],
        "newsSources": [s["name"] for s in cfg["news_sources"]],
        "newsletter": cfg.get("newsletter", {}),
        "research": research,
        "researchTagline": cfg.get("research_tagline", ""),
        "marqueeLabel": cfg.get("marquee_label", "Live job listings from"),
        "deals": sorted(json.loads((ROOT / "deals.json").read_text(encoding="utf-8")),
                        key=lambda d: d["date"], reverse=True),
        "events": load_json_list("events.json"),
        "aboutHtml": load_about(cfg),
    }
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = (template.replace("{{SITE_NAME}}", html.escape(cfg["site_name"]))
                    .replace("{{TAGLINE}}", html.escape(cfg["tagline"]))
                    .replace("{{DATA}}", data))
    return page


def main():
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    (OUT / "data").mkdir(parents=True, exist_ok=True)
    if "--offline" in sys.argv:
        news = json.loads((OUT / "data/news.json").read_text())
        jobs = json.loads((OUT / "data/jobs.json").read_text())
        updated = json.loads((OUT / "data/meta.json").read_text())["updated"]
    else:
        log("Fetching news…")
        news = build_news(cfg)
        log("Fetching jobs…")
        jobs = build_jobs(cfg)
        updated = NOW.isoformat(timespec="minutes")
        if not news and not jobs:
            sys.exit("No data fetched; keeping the previous site.")
        (OUT / "data/news.json").write_text(json.dumps(news, ensure_ascii=False, indent=1))
        (OUT / "data/jobs.json").write_text(json.dumps(jobs, ensure_ascii=False, indent=1))
        (OUT / "data/meta.json").write_text(json.dumps({"updated": updated}))
    research = load_research()
    deals = json.loads((ROOT / "deals.json").read_text(encoding="utf-8"))
    digests = build_digest(cfg, news, jobs, deals, research)
    write_digest_files(cfg, digests)
    write_job_feeds(cfg, jobs)
    (OUT / "index.html").write_text(render(cfg, news, jobs, updated, research), encoding="utf-8")
    log(f"Built site: {len(news)} news items, {len(jobs)} jobs, {len(research)} research pieces, {len(digests)} digests")


if __name__ == "__main__":
    main()
