"""Build the New Mindset blog into _site/ (standard library only, so GitHub Actions can run it as is).

  posts/<slug>/post.json + 1.jpg … 5.jpg   one article each (written by the studio's blog-publish.py)
  config.json                              site name, categories, links, base path
  static/                                  style.css, site.js (copied as is)

Every post gets its page as soon as it's in posts/ (so the link in a scheduled video works the moment it goes
live), but lists, the feed and the sitemap only show posts whose publishAt has passed; an unpublished page is
marked noindex. Newest first everywhere. Each post has a scrapbook layout (post.json "layout"), cycled so two
posts in a row never share one.

Usage: python3 build.py [--now 2026-10-30T19:00+07:00]   (--now previews the site at another time)
"""
import datetime as dt
import html
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_site")
LAYOUTS = ["pinboard", "folder", "journal", "scatter", "strip", "split"]
KM_DIGITS = str.maketrans("0123456789", "០១២៣៤៥៦៧៨៩")
KM_MONTHS = ["មករា", "កុម្ភៈ", "មីនា", "មេសា", "ឧសភា", "មិថុនា", "កក្កដា", "សីហា", "កញ្ញា", "តុលា", "វិច្ឆិកា", "ធ្នូ"]
ICT = dt.timezone(dt.timedelta(hours=7))

cfg = json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8"))
BASE = cfg.get("base_path", "").rstrip("/")
SITE = (cfg.get("base_url", "").rstrip("/") + BASE) if cfg.get("base_url") else ""
NAME = cfg.get("site_name") or f'{cfg["name_km"]} - {cfg["name_en"]}'


def u(path):
    return f"{BASE}/{path.lstrip('/')}"


def absu(path):
    return f"{SITE}/{path.lstrip('/')}" if SITE else u(path)


def esc(s):
    return html.escape(str(s or ""), quote=True)


def rich(s):
    """Escaped text with ==highlight== marks."""
    return re.sub(r"==(.+?)==", r'<mark>\1</mark>', esc(s))


def plain(s):
    return re.sub(r"==(.+?)==", r"\1", str(s or ""))


def km_date(d):
    return f"{d.day} {KM_MONTHS[d.month - 1]} {d.year}".translate(KM_DIGITS)


def en_date(d):
    return d.strftime("%d %b %Y")


# ---------------------------------------------------------------- doodles (inline SVG, colours from CSS)

SVG = {
    "clip": '<svg class="clip" viewBox="0 0 24 64" aria-hidden="true"><path d="M8 20v28a6 6 0 0 0 12 0V12a9 9 0 0 0-18 0v34a12 12 0 0 0 24 0V22" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>',
    "safety": '<svg class="safety" viewBox="0 0 90 24" aria-hidden="true"><path d="M6 12h70a6 6 0 1 0-6-6M6 12c0 3 2 5 5 5h62" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/><circle cx="8" cy="12" r="3.2" fill="none" stroke="currentColor" stroke-width="2"/><rect x="74" y="4" width="12" height="16" rx="4" fill="currentColor" opacity=".35"/></svg>',
    "star": '<svg class="dd star" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2l2.6 6.6L21 9.3l-5 4.4 1.6 6.8L12 17l-5.6 3.5L8 13.7 3 9.3l6.4-.7z" fill="currentColor"/></svg>',
    "heart": '<svg class="dd heart" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-7.5-4.6-9.4-9.3C1.3 8.4 3.4 4.5 7 4.5c2.1 0 3.6 1.2 5 3 1.4-1.8 2.9-3 5-3 3.6 0 5.7 3.9 4.4 7.2C19.5 16.4 12 21 12 21z" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>',
    "spark": '<svg class="dd spark" viewBox="0 0 40 40" aria-hidden="true"><path d="M20 3v9M20 28v9M3 20h9M28 20h9M8 8l5 5M27 27l5 5M32 8l-5 5M13 27l-5 5" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>',
    "asterisk": '<svg class="dd asterisk" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
    "arrow": '<svg class="dd arrow" viewBox="0 0 120 50" aria-hidden="true"><path d="M4 40c20-2 38-14 60-22 14-5 30-6 48-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M100 6l12 8-13 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "squiggle": '<svg class="dd squiggle" viewBox="0 0 160 16" aria-hidden="true"><path d="M2 10c10-8 18 6 28-1s18 6 28-1 18 6 28-1 18 6 28-1 18 6 28-1" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>',
}
DASHES = [
    '<svg class="dash" viewBox="0 0 800 600" preserveAspectRatio="none" aria-hidden="true"><path d="M-10 90C120 60 200 120 210 230S120 420 260 470 520 360 560 250 700 120 820 170"/></svg>',
    '<svg class="dash" viewBox="0 0 800 600" preserveAspectRatio="none" aria-hidden="true"><path d="M-10 520C90 470 120 360 260 330s180 40 230-40-10-150 60-170 140 60 120 120-90 40-70-10 120-60 290-20"/></svg>',
]


def doodle(name, post):
    """History posts stay quiet: no hearts, stars or sparkles."""
    if post.get("tone") == "documentary" and name in ("heart", "star", "spark"):
        return ""
    return SVG[name]


# ---------------------------------------------------------------- pieces

def img_src(post, im):
    return u(f"posts/{post['slug']}/{im['file']}")


def srcset(post, im):
    """Phones get the 540px copy (made by blog-publish.py) when it exists."""
    small = im["file"].replace(".jpg", "-540.jpg")
    if os.path.exists(os.path.join(HERE, "posts", post["slug"], small)):
        small_url = u(f"posts/{post['slug']}/{small}")
        return f' srcset="{small_url} 540w, {img_src(post, im)} 1080w" sizes="(max-width: 760px) 88vw, 400px"'
    return ""


def cover_img(post):
    """The topic thumbnail (blog-article.py picks it); older posts fall back to their first image."""
    return post.get("cover") or (post["images"][0] if post["images"] else None)


def cover_first(post):
    """Images for a cover layout: the topic cover first, then the others."""
    cov = cover_img(post)
    rest = [i for i in post["images"] if not cov or i.get("frame") != cov.get("frame")]
    return ([cov] if cov else []) + rest


def photo(post, im, lang="km", deco="tape", cls="", tilt=0.0, caption=True):
    """A polaroid: deco is tape | pin | clip | safety | none."""
    alt = im.get(f"alt_{lang}") or im.get("alt_en", "")
    cap = im.get(f"caption_{lang}", "") if caption else ""
    deco_html = {"tape": '<span class="tape"></span>', "pin": '<span class="pin"></span>', "clip": SVG["clip"],
                 "safety": SVG["safety"], "none": ""}[deco]
    return (f'<figure class="polaroid {cls}" style="--r:{tilt}deg">{deco_html}'
            f'<img src="{img_src(post, im)}"{srcset(post, im)} alt="{esc(alt)}" loading="lazy" decoding="async" width="1080" height="1350">'
            + (f'<figcaption>{esc(cap)}</figcaption>' if cap else "") + "</figure>")


def cat_chip(cat_id, small=False):
    c = cfg["categories"].get(cat_id, {"km": cat_id, "en": cat_id})
    return f'<a class="chip{" sm" if small else ""}" data-cat="{cat_id}" href="{u(f"category/{cat_id}/")}">{esc(c["km"])} <i>{esc(c["en"])}</i></a>'


def meta_line(post):
    d = post["_date"]
    return f'<p class="typed date">{km_date(d)} · {en_date(d)}</p>'


# ---------------------------------------------------------------- covers (one per layout)

def cover(post, linked=False):
    km, en, ims = post["km"], post["en"], cover_first(post)
    href = u(f"posts/{post['slug']}/")
    title = f'<a href="{href}">{rich(km["title"])}</a>' if linked else rich(km["title"])
    t = f'<h1 class="title">{title}</h1><p class="title-en">{esc(plain(en["title"]))}</p>'
    lay = post["layout"]
    im = lambda i: ims[i % len(ims)] if ims else None
    if lay == "pinboard":
        return f'''<header class="cover cv-pinboard">{DASHES[0]}
  <div class="note kraft"><p class="hand">{esc(plain(km["excerpt"]))}</p></div>
  <div class="cv-title">{cat_chip(post["category"])}{t}{meta_line(post)}</div>
  <div class="board">
    {photo(post, im(0), deco="none", cls="hero", tilt=-1.5, caption=False)}
    {photo(post, im(1), deco="pin", cls="mini m1", tilt=-4, caption=False)}
    {photo(post, im(2), deco="pin", cls="mini m2", tilt=3, caption=False)}
    {photo(post, im(3), deco="pin", cls="mini m3", tilt=-2, caption=False)}
  </div>{doodle("star", post)}</header>'''
    if lay == "folder":
        return f'''<header class="cover cv-folder"><div class="folder">
  <span class="tab typed">{esc(cfg["categories"].get(post["category"], {}).get("en", ""))}</span>
  <div class="sheet s1"></div><div class="sheet s2"></div>
  <div class="folder-body">
    {photo(post, im(0), deco="clip", cls="hero", tilt=-2.5, caption=False)}
    <div class="side"><p class="hand big">{esc(plain(km["excerpt"]))}</p>{doodle("arrow", post)}</div>
    <div class="cv-title">{t}{meta_line(post)}</div>
  </div></div></header>'''
    if lay == "journal":
        strip = "".join(f'<img src="{img_src(post, ims[i])}" alt="{esc(ims[i].get("alt_km", ""))}" loading="lazy">' for i in range(min(4, len(ims))))
        return f'''<header class="cover cv-journal"><div class="page holes">
  <div class="corners typed"><span>VOL. {post["_n"]}</span><span>{post["_date"]:%d.%m}</span></div>
  <h1 class="title bracket">[ {title} ]</h1><p class="title-en">{esc(plain(en["title"]))}</p>
  <p class="lede">{rich(km["excerpt"])}</p>
  <div class="booth"><span class="tape wide"></span>{strip}</div>
  <p class="hand note-red">{"អនុស្សាវរីយ៍តូចមួយ" if post.get("tone") == "documentary" else "រឿងតូចមួយ"}</p>{doodle("arrow", post)}{doodle("heart", post)}
  <div class="corners bottom typed"><span>{esc(cfg["categories"].get(post["category"], {}).get("en", ""))}</span><span>{km_date(post["_date"])}</span></div>
  </div><span class="binder-clip"></span></header>'''
    if lay == "scatter":
        return f'''<header class="cover cv-scatter">
  {photo(post, im(0), deco="none", cls="sc a", tilt=-8, caption=False)}{photo(post, im(1), deco="none", cls="sc b", tilt=7, caption=False)}
  {photo(post, im(2), deco="none", cls="sc c", tilt=6, caption=False)}{photo(post, im(3), deco="none", cls="sc d", tilt=-6, caption=False)}
  <div class="torn note-card"><span class="tape t-top"></span><span class="tape t-bot"></span>
    <p class="typed small">{esc(cfg["categories"].get(post["category"], {}).get("en", ""))}</p>
    <h1 class="title hand-title">{title}</h1><p class="title-en">{esc(plain(en["title"]))}</p>
    <p class="lede">{rich(km["excerpt"])}</p>{meta_line(post)}
  </div></header>'''
    if lay == "strip":
        cards = "".join(
            f'<div class="num-card n{i + 1}"><span class="num typed">0{i + 1}.</span>'
            f'{photo(post, ims[i], deco="safety", cls="strip-photo", tilt=(-2, 1.5, -1)[i], caption=False)}'
            f'<p class="nc-title">{esc(post["km"]["sections"][i]["heading"] if i < len(post["km"]["sections"]) else "")}</p></div>'
            for i in range(min(3, len(ims))))
        word = cfg["categories"].get(post["category"], {}).get("en", "").split(" ")[0].lower()
        return f'''<header class="cover cv-strip"><span class="ghost-word">{esc(word)}</span>
  <div class="cv-title">{cat_chip(post["category"])}{t}{meta_line(post)}</div>
  <div class="nums">{cards}</div></header>'''
    # split
    return f'''<header class="cover cv-split"><div class="left">
    <h1 class="title hand-title"><span class="bar"></span>{title}</h1><p class="title-en">{esc(plain(en["title"]))}</p>
    <p class="lede">{rich(km["excerpt"])}</p>
    {photo(post, im(0), deco="none", cls="flat", tilt=0, caption=False)}
  </div><div class="right">
    <span class="sticker yellow">{esc(cfg["categories"].get(post["category"], {}).get("km", ""))}</span>
    <span class="sticker blue typed">{post["_date"].year}</span>{doodle("asterisk", post)}
    {photo(post, im(1), deco="none", cls="flat r1", tilt=0, caption=False)}
    {photo(post, im(2), deco="none", cls="flat r2", tilt=0, caption=False)}
    {meta_line(post)}
  </div></header>'''


# Inline photo framing per layout (inside the article body).
FRAME = {"pinboard": ("pin", (-3, 2.5)), "folder": ("clip", (-2, 2)), "journal": ("tape", (-1.5, 1.5)),
         "scatter": ("tape", (-4, 3.5)), "strip": ("safety", (-1.5, 1.5)), "split": ("none", (0, 0))}


def body(post, lang):
    a = post[lang]
    deco, tilts = FRAME[post["layout"]]
    after = post.get("image_after") or list(range(len(post["images"])))
    out = []
    for i, s in enumerate(a["sections"]):
        num = f'<span class="sec-num typed">0{i + 1}.</span>' if post["layout"] in ("strip", "journal") else ""
        out.append(f'<section class="sec">{num}<h2>{rich(s["heading"])}</h2>' + "".join(f"<p>{rich(p)}</p>" for p in s["paragraphs"]) + "</section>")
        for k, im in enumerate(post["images"]):
            if (after[k] if k < len(after) else k) == i:
                side = "left" if k % 2 == 0 else "right"
                sticker = f'<span class="sticker yellow">{k + 1:02d}</span>' if post["layout"] == "split" else ""
                out.append(f'<div class="inline-photo {side}">{sticker}{photo(post, im, lang=lang, deco=deco, tilt=tilts[k % 2])}</div>')
    tk = a.get("takeaways") or []
    if tk:
        head = "ចំណុចសំខាន់ៗ" if lang == "km" else "Takeaways"
        out.append(f'<aside class="takeaways torn"><span class="tape t-top"></span><h3 class="hand-title">{head}</h3><ul>'
                   + "".join(f"<li>{rich(t)}</li>" for t in tk) + "</ul></aside>")
    return "\n".join(out)


def video_block(post):
    v = post.get("video") or {}
    if not v.get("youtube_id"):
        return ""
    poster = cover_img(post)
    # Our own clean still as the poster (YouTube's auto thumbnail carries burned-in captions); the real player
    # loads only when tapped, which keeps the page light on phones.
    return f'''<div class="watch"><figure class="polaroid phone" style="--r:2deg"><span class="tape"></span>
  <a class="yt-lite" href="{esc(v.get("url", ""))}" data-id="{esc(v["youtube_id"])}" aria-label="Play the Short">
    {f'<img src="{img_src(post, poster)}" alt="" loading="lazy">' if poster else ""}<span class="play" aria-hidden="true"></span></a></figure>
  <div class="watch-note"><p class="hand big">មើលវីដេអូខ្លី</p><p class="typed">Watch the Short</p>
  <a class="btn" href="{esc(v.get("url", ""))}">YouTube ↗</a>{doodle("spark", post)}</div></div>'''


def sources_block(post):
    src = post.get("sources") or []
    fic = '<p class="typed small">រឿងនេះជារឿងប្រឌិត · This story is fiction.</p>' if post.get("fiction") else ""
    if not src:
        return fic
    items = "".join(f'<li><a href="{esc(s["url"])}" rel="noopener">{esc(s["claim"][:140] or s["url"])}</a></li>' for s in src)
    return f'<section class="sources"><h3 class="typed">ប្រភព · Sources</h3><ol>{items}</ol>{fic}</section>'


# ---------------------------------------------------------------- page shell

def page(title, content, desc="", image="", path="", noindex=False, body_cls=""):
    og_img = f'<meta property="og:image" content="{esc(absu(image))}">' if image else ""
    return f'''<!doctype html><html lang="km"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#f4f0e8">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
{'<meta name="robots" content="noindex">' if noindex else ''}
<meta property="og:type" content="article"><meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(absu(path))}">{og_img}
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{u("static/icon-32.png")}" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="{u("static/icon-180.png")}"><link rel="manifest" href="{u("static/site.webmanifest")}">
<meta property="og:site_name" content="{esc(NAME)}"><meta name="application-name" content="{esc(NAME)}"><meta name="apple-mobile-web-app-title" content="{esc(NAME)}">
<link rel="alternate" type="application/rss+xml" title="{esc(NAME)}" href="{u("feed.xml")}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Kantumruy+Pro:wght@400;500;700&family=Hanuman:wght@700;900&family=Fasthand&family=Caveat:wght@500;700&family=Courier+Prime&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,700;1,9..40,400&display=swap">
<link rel="stylesheet" href="{u("static/style.css")}">
<script>document.documentElement.classList.add("js")</script>
</head><body class="{body_cls}">
<header class="mast"><a class="logo" href="{u("")}" aria-label="{esc(NAME)}"><img class="logo-icon" src="{u("static/icon-180.png")}" alt="" width="44" height="44"><span class="logo-km">{esc(cfg["name_km"])}</span><span class="logo-en">- {esc(cfg["name_en"])}</span></a>
<nav class="cats">{"".join(cat_chip(k, small=True) for k in cfg["categories"])}</nav></header>
<main>{content}</main>
<footer class="foot"><div class="squig">{SVG["squiggle"]}</div>
<p class="hand">{esc(cfg["tagline_km"])}</p>
<p class="links"><span class="follow">{esc(NAME)} on</span> <a href="{esc(cfg["links"]["youtube"])}">YouTube</a> · <a href="{esc(cfg["links"]["facebook"])}">Facebook</a> · <a href="{esc(cfg["links"]["instagram"])}">Instagram</a> · <a href="{u("feed.xml")}">RSS</a> · <a href="{esc(cfg["policies"])}">Privacy</a></p>
<p class="typed small">© {dt.date.today().year} {esc(NAME)}</p></footer>
<script src="{u("static/site.js")}"></script></body></html>'''


def article_page(post, now):
    km = post["km"]
    content = f'''<article class="post lay-{post["layout"]}" data-cat="{post["category"]}">
{cover(post)}
<div class="lang-switch" role="group" aria-label="Language"><button data-lang="km" aria-pressed="true">ខ្មែរ</button><button data-lang="en" aria-pressed="false">English</button></div>
<div class="body" lang="km">{body(post, "km")}</div>
<div class="body" lang="en">{body(post, "en")}</div>
{video_block(post)}
{sources_block(post)}
<nav class="more"><a class="btn ghost" href="{u(f"category/{post['category']}/")}">← {esc(cfg["categories"].get(post["category"], {}).get("km", ""))}</a><a class="btn ghost" href="{u("")}">ទំព័រដើម · Home</a></nav>
</article>'''
    return page(f'{plain(km["title"])} · {NAME}', content, desc=plain(km["excerpt"]),
                image=f'posts/{post["slug"]}/{cover_img(post)["file"]}' if cover_img(post) else "",
                path=f'posts/{post["slug"]}/', noindex=post["_date"] > now, body_cls=f"cat-{post['category']}")


def card(post, i):
    deco = ("pin", "tape", "clip")[i % 3]
    tilt = (-2.2, 1.8, -1.2, 2.4)[i % 4]
    im = cover_img(post)
    pic = photo(post, im, deco=deco, cls="card-photo", tilt=tilt, caption=False) if im else ""
    return f'''<a class="card" href="{u(f"posts/{post['slug']}/")}" data-cat="{post["category"]}">{pic}
  <span class="chip sm" data-cat="{post["category"]}">{esc(cfg["categories"].get(post["category"], {}).get("km", ""))}</span>
  <h3>{rich(post["km"]["title"])}</h3><p class="title-en">{esc(plain(post["en"]["title"]))}</p>
  <p class="typed date">{km_date(post["_date"])}</p></a>'''


def folders(published):
    out = []
    for cid, c in cfg["categories"].items():
        posts = [p for p in published if p["category"] == cid]
        thumbs = "".join(f'<img src="{img_src(p, cover_img(p))}" alt="" loading="lazy" style="--i:{k}">' for k, p in enumerate(posts[:3]) if cover_img(p))
        out.append(f'''<a class="folder-link" href="{u(f"category/{cid}/")}" style="--fc:{c["color"]};--fi:{c["ink"]}">
  <span class="peek">{thumbs}</span><span class="f-back"></span><span class="f-front"><b>{len(posts)}</b></span>
  <span class="f-label"><span class="km">{esc(c["km"])}</span> <i>{esc(c["en"])}</i></span></a>''')
    return '<section class="folders">' + "".join(out) + "</section>"


def home(published):
    if not published:
        hero = '<section class="empty torn"><p class="hand big">អត្ថបទដំបូងនឹងមកដល់ឆាប់ៗនេះ</p><p class="typed">The first story is on its way.</p></section>'
        rest = ""
    else:
        hero = f'<section class="featured"><p class="typed kicker">ថ្មីបំផុត · Latest</p>{cover(published[0], linked=True)}<p class="read-on"><a class="btn" href="{u(f"posts/{published[0]["slug"]}/")}">អានបន្ត · Read →</a></p></section>'
        rest = ('<section class="recent"><h2 class="hand-title">រឿងមុនៗ <i>Earlier stories</i></h2><div class="cards">'
                + "".join(card(p, i) for i, p in enumerate(published[1:])) + "</div></section>") if len(published) > 1 else ""
    intro = f'<section class="intro"><p class="hand big">{esc(cfg["tagline_km"])}</p><p class="typed">{esc(cfg["tagline_en"])}</p>{SVG["arrow"]}</section>'
    return page(NAME, intro + hero + folders(published) + rest, desc=cfg["tagline_en"], path="")


def category_page(cid, posts):
    c = cfg["categories"][cid]
    head = f'''<section class="cat-head" style="--fc:{c["color"]};--fi:{c["ink"]}"><span class="tab typed">{esc(c["en"])}</span>
  <h1 class="title">{esc(c["km"])}</h1><p class="typed">{len(posts)} stories · newest first</p></section>'''
    cards = '<div class="cards">' + "".join(card(p, i) for i, p in enumerate(posts)) + "</div>" if posts else \
        '<p class="hand big empty-cat">មិនទាន់មានអត្ថបទទេ</p>'
    return page(f'{c["km"]} · {NAME}', head + cards, desc=f'{c["en"]} — {cfg["name_en"]}', path=f"category/{cid}/",
                body_cls=f"cat-{cid}")


def feed(published):
    items = "".join(f'''<item><title>{esc(plain(p["km"]["title"]))} — {esc(plain(p["en"]["title"]))}</title>
<link>{esc(absu(f"posts/{p['slug']}/"))}</link><guid>{esc(absu(f"posts/{p['slug']}/"))}</guid>
<pubDate>{p["_date"].strftime("%a, %d %b %Y %H:%M:%S %z")}</pubDate><description>{esc(plain(p["km"]["excerpt"]))}</description></item>'''
                    for p in published[:30])
    return f'''<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{esc(NAME)}</title>
<link>{esc(absu(""))}</link><description>{esc(cfg["tagline_en"])}</description><language>km</language>{items}</channel></rss>'''


def sitemap(published):
    urls = [absu("")] + [absu(f"category/{c}/") for c in cfg["categories"]] + [absu(f"posts/{p['slug']}/") for p in published]
    return '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + \
        "".join(f"<url><loc>{esc(x)}</loc></url>" for x in urls) + "</urlset>"


def write(rel, text):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(text)


def load_posts():
    posts = []
    root = os.path.join(HERE, "posts")
    for slug in sorted(os.listdir(root)) if os.path.isdir(root) else []:
        f = os.path.join(root, slug, "post.json")
        if os.path.exists(f):
            p = json.load(open(f, encoding="utf-8"))
            p["slug"] = slug
            p["_date"] = dt.datetime.fromisoformat(p["publishAt"]).astimezone(ICT)
            p.setdefault("layout", "pinboard")
            posts.append(p)
    posts.sort(key=lambda p: p["_date"], reverse=True)
    for n, p in enumerate(reversed(posts), 1):
        p["_n"] = n
    return posts


def main():
    now = dt.datetime.now(ICT)
    if "--now" in sys.argv:
        now = dt.datetime.fromisoformat(sys.argv[sys.argv.index("--now") + 1]).astimezone(ICT)
    posts = load_posts()
    published = [p for p in posts if p["_date"] <= now]
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(os.path.join(HERE, "static"), os.path.join(OUT, "static"))
    for p in posts:
        src = os.path.join(HERE, "posts", p["slug"])
        for f in os.listdir(src):
            if f.endswith((".jpg", ".png", ".webp")):
                os.makedirs(os.path.join(OUT, "posts", p["slug"]), exist_ok=True)
                shutil.copy2(os.path.join(src, f), os.path.join(OUT, "posts", p["slug"], f))
        write(f"posts/{p['slug']}/index.html", article_page(p, now))
    write("index.html", home(published))
    for cid in cfg["categories"]:
        write(f"category/{cid}/index.html", category_page(cid, [p for p in published if p["category"] == cid]))
    write("feed.xml", feed(published))
    write("sitemap.xml", sitemap(published))
    write("404.html", page("404", '<section class="empty torn"><p class="hand big">រកមិនឃើញទំព័រនេះទេ</p><p class="typed">Page not found.</p></section>'))
    write(".nojekyll", "")
    print(f"built {len(posts)} post page(s), {len(published)} listed (now {now:%Y-%m-%d %H:%M} ICT) → _site/")


if __name__ == "__main__":
    main()
