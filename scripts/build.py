#!/usr/bin/env python3
"""data/posts.json ও site.json থেকে ওয়েবসাইটের সব পাতা বানায়।

যে ফাইল ও ফোল্ডার এই স্ক্রিপ্ট নিজে বানায় (হাতে বদলাবেন না, প্রতিবার নতুন করে তৈরি হয়):
  index.html, 404.html, sitemap.xml, assets/style.css,
  about/, category/, committee/, contact/, post/, posts/
"""
import hashlib
import html
import json
import os
import re
import shutil
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN_DIRS = ["about", "category", "committee", "contact", "post", "posts"]

MONTHS = ["জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন",
          "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"]
BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def bn(n):
    return str(n).translate(BN_DIGITS)


def bn_date(s):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s or "")
    if not m:
        return ""
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not 1 <= mo <= 12:
        return ""
    return "{} {}, {}".format(bn(d), MONTHS[mo - 1], bn(y))


def img_url(u):
    u = (u or "").strip()
    if not u:
        return ""
    if re.match(r"^https?://", u):
        return u
    if u.startswith("/"):
        return u if re.match(r"^/[\w\-./%]+$", u) else ""
    u = u.lstrip("./")
    return "/" + u if re.match(r"^[\w\-./%]+$", u) else ""


def excerpt(text, n=120):
    t = re.sub(r"\s+", " ", text or "").strip()
    return t if len(t) <= n else t[:n] + "…"


def rich(text):
    t = esc(text)
    return re.sub(
        r"(https?://[^\s<]+)",
        lambda m: '<a href="{0}" target="_blank" rel="noopener noreferrer">{0}</a>'.format(m.group(1)),
        t,
    )


def write(rel, content):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def load_json(rel, default):
    try:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


# ---------------------------------------------------------------- CSS
CSS = r"""
:root{--deep:#083a2c;--green:#0f5c45;--mid:#1d7a5c;--soft:#e6f0ea;--gold:#c99a2e;--gold-l:#f1d98e;--paper:#faf7f0;--card:#fff;--ink:#1b2a24;--muted:#63726b;--line:#e4e0d4;--shadow:0 8px 28px rgba(8,58,44,.10)}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:96px}
body{margin:0;font-family:"Hind Siliguri","Noto Sans Bengali",system-ui,sans-serif;background:var(--paper);color:var(--ink);line-height:1.8}
h1,h2,h3,.serif{font-family:"Tiro Bangla","Hind Siliguri",serif;font-weight:400}
a{color:inherit}img{max-width:100%}
.wrap{max-width:1040px;margin:0 auto;padding:0 18px}.narrow{max-width:760px}
section.block{padding:46px 0 10px}
.sec-head{text-align:center;margin-bottom:26px}.sec-head h2{margin:0;font-size:1.9rem;color:var(--deep)}
.sec-head .bar{width:64px;height:4px;border-radius:4px;margin:8px auto 0;background:linear-gradient(90deg,var(--gold),var(--gold-l))}
.sec-head p{margin:10px 0 0;color:var(--muted)}
.topbar{position:sticky;top:0;z-index:20;background:rgba(8,58,44,.96);backdrop-filter:blur(6px);border-bottom:3px solid var(--gold)}
.topbar .wrap.main-row{display:flex;align-items:center;justify-content:space-between;gap:12px;height:58px}
.clockbar{background:#062c21;color:#cfe3da;font-size:.8rem}
.clockbar .wrap{display:flex;justify-content:flex-end;gap:12px;padding-top:2px;padding-bottom:2px;line-height:1.5}
.clockbar b{color:var(--gold-l);font-weight:500;font-variant-numeric:tabular-nums}
.brand{display:flex;align-items:center;gap:10px;color:#fff;text-decoration:none;font-size:1.25rem;white-space:nowrap}.brand img{height:34px;width:auto}
.menu{display:flex;gap:4px;overflow-x:auto;scrollbar-width:none}.menu::-webkit-scrollbar{display:none}
.menu a{color:#d8ebe2;text-decoration:none;font-size:.95rem;padding:6px 12px;border-radius:18px;white-space:nowrap}
.menu a:hover{background:rgba(255,255,255,.12);color:#fff}.menu a.on{background:var(--gold);color:#2b2106;font-weight:600}
.hero{color:#fff;text-align:center;padding:46px 18px 54px;position:relative;overflow:hidden;background:radial-gradient(circle at 15% 20%,rgba(201,154,46,.28),transparent 38%),radial-gradient(circle at 88% 85%,rgba(29,122,92,.55),transparent 42%),linear-gradient(145deg,var(--deep),var(--green))}
.hero::before{content:"";position:absolute;inset:0;opacity:.07;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='46' height='46'%3E%3Cpath d='M23 3l20 20-20 20L3 23z' fill='none' stroke='%23fff' stroke-width='1.2'/%3E%3C/svg%3E")}
.hero>*{position:relative}
.hero .logo{height:118px;width:auto;display:block;margin:0 auto 12px;filter:drop-shadow(0 6px 14px rgba(0,0,0,.3))}
.hero h1{margin:0;font-size:3rem;letter-spacing:.5px;line-height:1.3}
.hero .branch{margin:2px 0 0;font-size:1.3rem;color:var(--gold-l);font-family:"Tiro Bangla",serif}
.hero .tag{margin:12px auto 0;max-width:560px;opacity:.93}
.partners{display:flex;justify-content:center;gap:14px;flex-wrap:wrap;margin-top:22px}
.partner{display:flex;align-items:center;gap:10px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.28);border-radius:16px;padding:8px 16px 8px 10px;font-size:.88rem;line-height:1.4;text-align:left}
.partner img{height:42px;width:auto;background:#fff;border-radius:10px;padding:3px}
.cta{display:inline-block;margin-top:24px;background:var(--gold);color:#2b2106;text-decoration:none;border-radius:26px;padding:10px 26px;font-weight:600;box-shadow:0 6px 16px rgba(0,0,0,.25)}
.pagehead{background:linear-gradient(145deg,var(--deep),var(--green));color:#fff;text-align:center;padding:34px 18px 30px;border-bottom:4px solid var(--gold)}
.pagehead h1{margin:0;font-size:2.2rem}.pagehead p{margin:6px 0 0;opacity:.9}
.about-text{max-width:760px;margin:0 auto;text-align:center;font-size:1.08rem}.about-text p{margin:0 0 12px}
.more-link{display:block;text-align:center;margin-top:10px;color:var(--green);font-weight:600;text-decoration:none}
.pillars{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-top:26px}
.pillar{background:var(--card);border:1px solid var(--line);border-top:4px solid var(--gold);border-radius:16px;padding:20px 18px;text-align:center;box-shadow:var(--shadow)}
.pillar .ic{font-size:2rem}.pillar h3{margin:6px 0 4px;font-size:1.3rem;color:var(--green)}.pillar p{margin:0;color:var(--muted);font-size:.95rem}
.carousel{position:relative}
.track{display:flex;gap:16px;overflow-x:auto;scroll-snap-type:x mandatory;padding:6px 4px 18px;scrollbar-width:none}.track::-webkit-scrollbar{display:none}
.slide{flex:0 0 min(330px,82%);scroll-snap-align:start}
.arrow{position:absolute;top:42%;z-index:2;width:42px;height:42px;border-radius:50%;border:0;background:var(--deep);color:#fff;font-size:1.5rem;line-height:1;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.28)}
.arrow:hover{background:var(--mid)}.arrow.prev{left:-8px}.arrow.next{right:-8px}
@media(max-width:640px){.arrow{display:none}}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;overflow:hidden;display:flex;flex-direction:column;height:100%;transition:transform .2s,box-shadow .2s}
.card:hover{transform:translateY(-4px);box-shadow:var(--shadow)}
.card .pic{width:100%;height:190px;object-fit:cover;object-position:center top;display:block;background:var(--soft)}
.card .ph{height:190px;display:flex;align-items:center;justify-content:center;font-size:3.2rem;background:linear-gradient(135deg,var(--soft),#fff3d6)}
.card .body{padding:14px 16px 16px;display:flex;flex-direction:column;flex:1}
.chip{display:inline-block;font-size:.78rem;font-weight:600;background:var(--soft);color:var(--green);padding:1px 11px;border-radius:12px;text-decoration:none}
.date{font-size:.8rem;color:var(--muted);margin-left:6px}
.card h3{margin:8px 0 4px;font-size:1.18rem;line-height:1.5}.card h3 a{color:var(--deep);text-decoration:none}
.card p{margin:0;color:var(--muted);font-size:.94rem}
.card .more{margin-top:auto;padding-top:10px;color:var(--green);font-weight:600;font-size:.92rem;text-decoration:none}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:18px}
.empty{text-align:center;color:var(--muted);padding:34px 0;grid-column:1/-1}
.cats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px}
.catcard{text-decoration:none;background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px 12px 16px;text-align:center;position:relative;overflow:hidden;transition:transform .2s,box-shadow .2s,border-color .2s}
.catcard::before{content:"";position:absolute;left:0;right:0;top:0;height:5px;background:var(--c,var(--green))}
.catcard:hover{transform:translateY(-4px);box-shadow:var(--shadow);border-color:var(--c,var(--green))}
.catcard .ico{width:58px;height:58px;margin:0 auto 8px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.7rem;background:color-mix(in srgb,var(--c,var(--green)) 14%,white)}
.catcard .nm{font-size:1.15rem;color:var(--deep);font-family:"Tiro Bangla",serif}.catcard .ct{font-size:.82rem;color:var(--muted)}
.catcard.all{--c:var(--deep)}
.pills{display:flex;gap:8px;overflow-x:auto;padding:18px 0 14px;scrollbar-width:none}.pills::-webkit-scrollbar{display:none}
.pills a{flex:0 0 auto;text-decoration:none;border:1px solid var(--line);background:#fff;padding:5px 16px;border-radius:20px;font-size:.92rem}
.pills a.on{background:var(--green);color:#fff;border-color:var(--green)}
.crumbs{padding:22px 0 8px;font-size:.9rem;color:var(--muted)}.crumbs a{color:var(--green);text-decoration:none}
.post h1{margin:10px 0 14px;font-size:2rem;line-height:1.5;color:var(--deep)}
.ptext{white-space:pre-line;font-size:1.06rem;overflow-wrap:anywhere}.ptext a{color:var(--green)}
.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin:22px 0}
.gallery img{width:100%;border-radius:12px;display:block}
.fblink{display:inline-block;margin:8px 0 6px;color:var(--green);font-weight:600}
.contact{background:linear-gradient(145deg,var(--deep),var(--green));color:#fff;border-radius:22px;padding:34px 20px;text-align:center;box-shadow:var(--shadow)}
.contact h3{margin:0 0 6px;font-size:1.6rem;color:var(--gold-l)}.contact p{margin:0 0 16px;opacity:.92}
.contact .row{display:flex;justify-content:center;gap:12px;flex-wrap:wrap}
.contact a.btn{text-decoration:none;background:#fff;color:var(--deep);padding:10px 22px;border-radius:26px;font-weight:600}
.contact a.btn.alt{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.55)}
.contact .mail{margin-top:14px;font-size:1.05rem;word-break:break-all}.contact .mail a{color:var(--gold-l)}
footer{background:var(--deep);color:#bcd8cc;text-align:center;font-size:.9rem;padding:30px 16px 36px;margin-top:46px;border-top:4px solid var(--gold)}
footer .flogos{display:flex;justify-content:center;align-items:center;gap:16px;margin-bottom:12px;flex-wrap:wrap}
footer .flogos img{height:46px;width:auto;background:#fff;border-radius:10px;padding:4px}footer a{color:var(--gold-l)}
.featured{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px;max-width:760px;margin:0 auto}
.mem{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:18px 14px;text-align:center;box-shadow:var(--shadow)}
.mem .mphoto,.mem .avatar{width:96px;height:96px;border-radius:50%;object-fit:cover;object-position:center top;display:block;margin:0 auto 10px;border:3px solid var(--gold-l)}
.avatar{display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,var(--soft),#fff3d6);color:var(--green);font-size:2.2rem;font-family:"Tiro Bangla",serif}
.mem h3{margin:2px 0 0;font-size:1.15rem;color:var(--deep);line-height:1.5}
.mem .role{display:inline-block;margin-top:4px;background:var(--soft);color:var(--green);font-weight:600;font-size:.84rem;padding:0 12px;border-radius:12px}
.mem .info{margin:6px 0 0;color:var(--muted);font-size:.86rem;line-height:1.6}
.mem.big{padding:26px 16px 22px;border-top:5px solid var(--gold)}
.mem.big .mphoto,.mem.big .avatar{width:170px;height:170px;border-width:5px;font-size:4rem;box-shadow:0 10px 26px rgba(8,58,44,.2)}
.mem.big h3{font-size:1.5rem}.mem.big .role{font-size:1rem;padding:1px 18px}
.mgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:14px}
.sub-head{text-align:center;margin:36px 0 16px;font-size:1.5rem;color:var(--deep)}
@media(max-width:560px){.hero h1{font-size:2.3rem}.hero .logo{height:92px}.brand span{display:none}.post h1{font-size:1.6rem}.clockbar{font-size:.74rem}}
"""

CLOCK_JS = """<script>
(function(){var d=document.getElementById("clkDate"),t=document.getElementById("clkTime");if(!d||!t)return;
var fd,ft;try{
fd=new Intl.DateTimeFormat("bn-BD",{timeZone:"Asia/Dhaka",weekday:"long",day:"numeric",month:"long",year:"numeric"});
ft=new Intl.DateTimeFormat("bn-BD",{timeZone:"Asia/Dhaka",hour:"2-digit",minute:"2-digit",second:"2-digit",hour12:true});
}catch(e){return;}
function tick(){var n=new Date();d.textContent=fd.format(n);t.textContent=ft.format(n);}
tick();setInterval(tick,1000);})();
</script>"""
CSS_VER = hashlib.sha1(CSS.encode("utf-8")).hexdigest()[:8]

CAROUSEL_JS = """<script>
(function(){
var t=document.getElementById("track");if(!t)return;
var timer=null,rt=null,reduce=window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches;
function step(d){var f=t.firstElementChild;if(!f||!f.offsetWidth)return;var w=f.offsetWidth+16;
 if(d>0){if(t.scrollLeft+t.clientWidth>=t.scrollWidth-8)t.scrollTo({left:0,behavior:"smooth"});else t.scrollBy({left:w,behavior:"smooth"});}
 else{if(t.scrollLeft<=8)t.scrollTo({left:t.scrollWidth,behavior:"smooth"});else t.scrollBy({left:-w,behavior:"smooth"});}}
function stop(){clearInterval(timer);timer=null;clearTimeout(rt);}
function start(){stop();if(reduce||t.children.length<2)return;timer=setInterval(function(){step(1)},4500);}
t.addEventListener("mouseenter",stop);t.addEventListener("mouseleave",start);
t.addEventListener("touchstart",stop,{passive:true});
t.addEventListener("touchend",function(){clearTimeout(rt);rt=setTimeout(start,6000)},{passive:true});
document.getElementById("prev").onclick=function(){step(-1);start()};
document.getElementById("next").onclick=function(){step(1);start()};
start();})();
</script>"""


class Site:
    def __init__(self):
        self.cfg = load_json("site.json", {})
        c = self.cfg
        self.url = (c.get("url") or "").rstrip("/")
        self.name = c.get("name", "পাঠকবন্ধু")
        self.branch = c.get("branch", "")
        self.tagline = c.get("tagline", "")
        self.email = c.get("email", "")
        self.fb = c.get("facebook", "")
        self.about = c.get("about") or []
        self.pillars = c.get("pillars") or []
        self.cats = c.get("categories") or [{"name": "সাধারণ", "slug": "general", "icon": "📌", "color": "#5b6b66"}]
        self.recent_count = int(c.get("recent_count", 8))
        self.full_name = (self.name + ", " + self.branch).strip(", ")
        self.cat_by_name = {x["name"]: x for x in self.cats}
        self.default_cat = self.cat_by_name.get("সাধারণ") or self.cats[-1]

        raw = load_json("data/posts.json", [])
        posts = [p for p in raw if isinstance(p, dict) and not p.get("hidden")]
        posts.sort(key=lambda p: str(p.get("date", ""))[:19], reverse=True)
        used = set()
        for p in posts:
            slug = re.sub(r"[^0-9A-Za-z_-]", "-", str(p.get("id", "post"))) or "post"
            base, i = slug, 2
            while slug in used:
                slug = "{}-{}".format(base, i)
                i += 1
            used.add(slug)
            p["_slug"] = slug
            p["_cat"] = self.cat_by_name.get(p.get("category"), self.default_cat)
        self.posts = posts

        cm = load_json("data/committee.json", {})
        if not isinstance(cm, dict):
            cm = {}
        self.cm_term = cm.get("term", "")
        self.members = [m for m in (cm.get("members") or []) if isinstance(m, dict) and m.get("name")]

    def cat_posts(self, cat):
        return [p for p in self.posts if p["_cat"]["slug"] == cat["slug"]]

    # ------------------------------------------------------------ layout
    def layout(self, title, desc, body, active, path, image=None, scripts=""):
        full_title = title if title == self.full_name else "{} | {}".format(title, self.full_name)
        canon = self.url + path if self.url else path
        og_img = ""
        if image:
            absu = image if image.startswith("http") else (self.url + image)
            og_img = '<meta property="og:image" content="{}">'.format(esc(absu))
        items = [("home", "/", "হোম"), ("about", "/about/", "আমাদের কথা"), ("committee", "/committee/", "কমিটি"),
                 ("posts", "/posts/", "সব পোস্ট"), ("cats", "/category/", "ক্যাটাগরি"), ("contact", "/contact/", "যোগাযোগ")]
        menu = "".join('<a href="{}"{}>{}</a>'.format(h, ' class="on"' if k == active else "", t) for k, h, t in items)
        mail = "mailto:" + self.email
        return """<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#083a2c">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website">
<meta property="og:locale" content="bn_BD">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
{og_img}
<link rel="icon" href="/images/pathakbondhu-logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700&family=Tiro+Bangla:ital@0;1&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/style.css?v={ver}">
</head>
<body>
<div class="topbar">
<div class="clockbar"><div class="wrap"><span id="clkDate"></span><b id="clkTime"></b></div></div>
<div class="wrap main-row">
  <a class="brand serif" href="/"><img src="/images/pathakbondhu-logo.png" alt="" onerror="this.style.display='none'"><span>{name}</span></a>
  <nav class="menu">{menu}</nav>
</div></div>
{body}
<footer>
  <div class="flogos">
    <img src="/images/pathakbondhu-logo.png" alt="" onerror="this.style.display='none'">
    <img src="/images/iu-logo.png" alt="" onerror="this.style.display='none'">
    <img src="/images/ajkerpatrika-logo.png" alt="" onerror="this.style.display='none'">
  </div>
  &copy; {full}<br>
  দৈনিক আজকের পত্রিকার সহযোগী সংগঠন<br>
  <a href="{mail}">{email}</a> &nbsp;|&nbsp; <a href="{fb}" target="_blank" rel="noopener">ফেসবুক পেইজ</a>
</footer>
{scripts}{clock}
</body>
</html>
""".format(title=esc(full_title), desc=esc(desc), canon=esc(canon), og_img=og_img, ver=CSS_VER,
           name=esc(self.name), menu=menu, body=body, full=esc(self.full_name), mail=esc(mail),
           email=esc(self.email), fb=esc(self.fb), scripts=scripts, clock=CLOCK_JS)

    # ------------------------------------------------------------ parts
    def card(self, p):
        href = "/post/{}/".format(p["_slug"])
        cat = p["_cat"]
        img = img_url((p.get("images") or [None])[0])
        icon = cat.get("icon", "📌")
        ph = '<div class="ph">{}</div>'.format(esc(icon))
        safe_icon = re.sub(r"[^\w\u0080-\U0010ffff]", "", str(icon)) or "📌"
        # onerror-এ শুধু একক উদ্ধৃতি ব্যবহার হয়, যাতে HTML না ভাঙে
        fallback = ("this.onerror=null;this.replaceWith(Object.assign(document.createElement('div'),"
                    "{className:'ph',textContent:'" + safe_icon + "'}))")
        pic = ('<a href="{}"><img class="pic" src="{}" alt="{}" loading="lazy" onerror="{}"></a>'.format(
            esc(href), esc(img), esc(p.get("title")), esc(fallback))
               if img else '<a href="{}">{}</a>'.format(esc(href), ph))
        return ('<article class="card">{pic}<div class="body"><div><a class="chip" href="/category/{slug}/">{cat}</a>'
                '<span class="date">{date}</span></div><h3><a href="{href}">{title}</a></h3><p>{ex}</p>'
                '<a class="more" href="{href}">বিস্তারিত পড়ুন →</a></div></article>').format(
            pic=pic, slug=esc(cat["slug"]), cat=esc(cat["name"]), date=esc(bn_date(p.get("date"))),
            href=esc(href), title=esc(p.get("title")), ex=esc(excerpt(p.get("text"))))

    def cat_cards(self):
        out = ['<a class="catcard all" href="/posts/"><div class="ico">🗂️</div><div class="nm">সব পোস্ট</div>'
               '<div class="ct">{}টি পোস্ট</div></a>'.format(bn(len(self.posts)))]
        for c in self.cats:
            out.append('<a class="catcard" href="/category/{}/" style="--c:{}"><div class="ico">{}</div>'
                       '<div class="nm">{}</div><div class="ct">{}টি পোস্ট</div></a>'.format(
                           esc(c["slug"]), esc(c.get("color", "#0f5c45")), c.get("icon", "📌"),
                           esc(c["name"]), bn(len(self.cat_posts(c)))))
        return "".join(out)

    def pills(self, active_slug):
        out = ['<a href="/posts/"{}>সব</a>'.format(' class="on"' if active_slug == "all" else "")]
        for c in self.cats:
            out.append('<a href="/category/{}/"{}>{}</a>'.format(
                esc(c["slug"]), ' class="on"' if c["slug"] == active_slug else "", esc(c["name"])))
        return '<div class="pills">{}</div>'.format("".join(out))

    def pillars_html(self):
        return '<div class="pillars">{}</div>'.format("".join(
            '<div class="pillar"><div class="ic">{}</div><h3>{}</h3><p>{}</p></div>'.format(
                esc(x.get("icon", "")), esc(x.get("title", "")), esc(x.get("text", ""))) for x in self.pillars))

    def avatar(self, m):
        initial = re.sub(r"[^\w]", "", str(m.get("name", "")))[:1] or "•"
        photo = img_url(m.get("photo"))
        if not photo:
            return '<div class="avatar">{}</div>'.format(esc(initial))
        fallback = ("this.onerror=null;this.replaceWith(Object.assign(document.createElement('div'),"
                    "{className:'avatar',textContent:'" + initial.replace("'", "").replace("\\", "") + "'}))")
        return '<img class="mphoto" src="{}" alt="{}" loading="lazy" onerror="{}">'.format(
            esc(photo), esc(m.get("name")), esc(fallback))

    def member_card(self, m, big=False):
        return '<div class="mem{}">{}<h3>{}</h3><div class="role">{}</div>{}</div>'.format(
            " big" if big else "", self.avatar(m), esc(m.get("name")), esc(m.get("title")),
            '<p class="info">{}</p>'.format(esc(m.get("info"))) if m.get("info") else "")

    def featured_members(self):
        feat = [m for m in self.members if m.get("featured")]
        return feat or self.members[:2]

    def featured_html(self):
        return '<div class="featured">{}</div>'.format("".join(self.member_card(m, True) for m in self.featured_members()))

    def contact_box(self):
        return ('<div class="contact"><h3>আমাদের সাথে যোগাযোগ করুন</h3><p>যেকোনো প্রশ্ন, পরামর্শ বা সহযোগিতার জন্য লিখুন।</p>'
                '<div class="row"><a class="btn" href="mailto:{m}">ইমেইল পাঠান</a>'
                '<a class="btn alt" href="{fb}" target="_blank" rel="noopener">ফেসবুক পেইজ</a></div>'
                '<div class="mail">ইমেইল: <a href="mailto:{m}">{m}</a></div></div>').format(m=esc(self.email), fb=esc(self.fb))

    def head(self, title, sub=""):
        return '<div class="pagehead"><h1 class="serif">{}</h1>{}</div>'.format(
            title, "<p>{}</p>".format(sub) if sub else "")

    def grid(self, posts):
        if not posts:
            return '<div class="grid"><div class="empty">এখানে এখনো কোনো পোস্ট নেই।</div></div>'
        return '<div class="grid">{}</div>'.format("".join(self.card(p) for p in posts))

    # ------------------------------------------------------------ pages
    def build(self):
        for d in GEN_DIRS:
            shutil.rmtree(os.path.join(ROOT, d), ignore_errors=True)
        write("assets/style.css", CSS)
        desc = "{}: {}। দৈনিক আজকের পত্রিকার সহযোগী সংগঠন।".format(self.full_name, self.tagline)
        urls = ["/", "/about/", "/posts/", "/category/", "/contact/"]

        # হোমের কমিটি অংশ
        committee_home = ""
        if self.members:
            committee_home = ('<section class="block"><div class="sec-head"><h2>আমাদের কমিটি</h2><div class="bar"></div>{}</div>{}'
                              '<a class="more-link" href="/committee/">পুরো কমিটি দেখুন →</a></section>').format(
                "<p>{}</p>".format(esc(self.cm_term)) if self.cm_term else "", self.featured_html())
            urls.append("/committee/")

        # কমিটির পাতা
        feat = [m for m in self.members if m.get("featured")]
        rest = [m for m in self.members if not m.get("featured")]
        order, groups = [], {}
        for m in rest:
            g = m.get("group") or "সদস্যবৃন্দ"
            if g not in groups:
                groups[g] = []
                order.append(g)
            groups[g].append(m)
        parts = []
        if feat:
            parts.append('<section class="block">{}</section>'.format(
                '<div class="featured">{}</div>'.format("".join(self.member_card(m, True) for m in feat))))
        for g in order:
            parts.append('<h2 class="sub-head serif">{}</h2><div class="mgrid">{}</div>'.format(
                esc(g), "".join(self.member_card(m) for m in groups[g])))
        if not parts:
            parts.append('<div class="empty">কমিটির তথ্য শীঘ্রই যোগ করা হবে।</div>')
        body = self.head("আমাদের কমিটি", esc(self.cm_term)) + '<div class="wrap">{}</div>'.format("".join(parts))
        write("committee/index.html", self.layout("আমাদের কমিটি", "{} — {}".format(self.full_name, self.cm_term or "কমিটি"),
                                                  body, "committee", "/committee/"))

        # হোম
        about_first = "<p>{}</p>".format(esc(self.about[0])) if self.about else ""
        slides = "".join('<div class="slide">{}</div>'.format(self.card(p)) for p in self.posts[:self.recent_count])
        if not slides:
            slides = '<div class="empty" style="width:100%">শীঘ্রই নতুন পোস্ট আসছে।</div>'
        body = """
<header class="hero">
  <img class="logo" src="/images/pathakbondhu-logo.png" alt="লোগো" onerror="this.style.display='none'">
  <h1>{name}</h1>
  <p class="branch">{branch}</p>
  <p class="tag">{tag}</p>
  <div class="partners">
    <div class="partner"><img src="/images/iu-logo.png" alt="ইসলামী বিশ্ববিদ্যালয় লোগো" onerror="this.style.display='none'"><span>ইসলামী বিশ্ববিদ্যালয়</span></div>
    <div class="partner"><img src="/images/ajkerpatrika-logo.png" alt="দৈনিক আজকের পত্রিকা লোগো" onerror="this.style.display='none'"><span>দৈনিক আজকের পত্রিকার<br>সহযোগী সংগঠন</span></div>
  </div>
  <a class="cta" href="#recent">সাম্প্রতিক পোস্ট দেখুন</a>
</header>
<div class="wrap">
  <section class="block"><div class="sec-head"><h2>আমাদের কথা</h2><div class="bar"></div></div>
    <div class="about-text">{about}</div>{pillars}
    <a class="more-link" href="/about/">আরও জানুন →</a></section>
  {committee}
  <section class="block" id="recent"><div class="sec-head"><h2>সাম্প্রতিক পোস্ট</h2><div class="bar"></div><p>আমাদের সর্বশেষ কার্যক্রম</p></div>
    <div class="carousel"><button class="arrow prev" id="prev" aria-label="আগেরটি">‹</button>
    <div class="track" id="track">{slides}</div>
    <button class="arrow next" id="next" aria-label="পরেরটি">›</button></div>
    <a class="more-link" href="/posts/">সব পোস্ট দেখুন →</a></section>
  <section class="block"><div class="sec-head"><h2>ক্যাটাগরি অনুযায়ী দেখুন</h2><div class="bar"></div><p>আপনার পছন্দের বিষয়ে ক্লিক করুন</p></div>
    <div class="cats">{cats}</div></section>
  <section class="block"><div class="sec-head"><h2>যোগাযোগ</h2><div class="bar"></div></div>{contact}</section>
</div>""".format(name=esc(self.name), branch=esc(self.branch), tag=esc(self.tagline), about=about_first,
                 pillars=self.pillars_html(), slides=slides, cats=self.cat_cards(), contact=self.contact_box(),
                 committee=committee_home)
        first_img = next((img_url((p.get("images") or [None])[0]) for p in self.posts if (p.get("images") or [None])[0]), None)
        write("index.html", self.layout(self.full_name, desc, body, "home", "/", image="/images/pathakbondhu-logo.png",
                                        scripts=CAROUSEL_JS))

        # আমাদের কথা
        about_html = "".join("<p>{}</p>".format(esc(t)) for t in self.about)
        body = self.head("আমাদের কথা", esc(self.full_name)) + '<div class="wrap"><section class="block">' \
            '<div class="about-text">{}</div>{}</section><section class="block">{}</section></div>'.format(
                about_html, self.pillars_html(), self.contact_box())
        write("about/index.html", self.layout("আমাদের কথা", desc, body, "about", "/about/"))

        # যোগাযোগ
        body = self.head("যোগাযোগ") + '<div class="wrap"><section class="block">{}</section></div>'.format(self.contact_box())
        write("contact/index.html", self.layout("যোগাযোগ", "যোগাযোগ: " + self.email, body, "contact", "/contact/"))

        # সব পোস্ট
        body = self.head("সব পোস্ট", "মোট {}টি পোস্ট".format(bn(len(self.posts)))) + \
            '<div class="wrap">{}{}</div>'.format(self.pills("all"), self.grid(self.posts))
        write("posts/index.html", self.layout("সব পোস্ট", "আমাদের সব পোস্ট ও কার্যক্রম", body, "posts", "/posts/"))

        # ক্যাটাগরির তালিকা
        body = self.head("ক্যাটাগরি", "পছন্দের বিষয়ে ক্লিক করুন") + \
            '<div class="wrap"><section class="block"><div class="cats">{}</div></section></div>'.format(self.cat_cards())
        write("category/index.html", self.layout("ক্যাটাগরি", "ক্যাটাগরি অনুযায়ী পোস্ট", body, "cats", "/category/"))

        # প্রতিটি ক্যাটাগরি
        for c in self.cats:
            lst = self.cat_posts(c)
            path = "/category/{}/".format(c["slug"])
            body = self.head("{} {}".format(c.get("icon", ""), esc(c["name"])), "{}টি পোস্ট".format(bn(len(lst)))) + \
                '<div class="wrap">{}{}</div>'.format(self.pills(c["slug"]), self.grid(lst))
            write("category/{}/index.html".format(c["slug"]),
                  self.layout(c["name"], "{} ক্যাটাগরির পোস্টসমূহ".format(c["name"]), body, "cats", path))
            urls.append(path)

        # প্রতিটি পোস্ট
        for p in self.posts:
            cat = p["_cat"]
            path = "/post/{}/".format(p["_slug"])
            imgs = [u for u in (img_url(x) for x in (p.get("images") or [])) if u]
            gallery = ('<div class="gallery">{}</div>'.format("".join(
                '<a href="{0}" target="_blank" rel="noopener"><img src="{0}" alt="" loading="lazy" '
                'onerror="this.parentNode.style.display=\'none\'"></a>'.format(esc(u)) for u in imgs)) if imgs else "")
            fb = p.get("fb_url") or ""
            fb_html = ('<a class="fblink" href="{}" target="_blank" rel="noopener">ফেসবুকে দেখুন →</a>'.format(esc(fb))
                       if re.match(r"^https?://", fb) else "")
            related = [x for x in self.cat_posts(cat) if x is not p][:3]
            rel_html = ('<section class="block"><div class="sec-head"><h2>আরও পোস্ট</h2><div class="bar"></div></div>{}</section>'.format(
                self.grid(related)) if related else "")
            body = ('<div class="wrap narrow"><nav class="crumbs"><a href="/">হোম</a> › <a href="/posts/">সব পোস্ট</a> › '
                    '<a href="/category/{slug}/">{cat}</a></nav><article class="post"><div><a class="chip" href="/category/{slug}/">{cat}</a>'
                    '<span class="date">{date}</span></div><h1 class="serif">{title}</h1><div class="ptext">{text}</div>{gallery}{fb}</article></div>'
                    '<div class="wrap">{rel}</div>').format(
                slug=esc(cat["slug"]), cat=esc(cat["name"]), date=esc(bn_date(p.get("date"))), title=esc(p.get("title")),
                text=rich(p.get("text")), gallery=gallery, fb=fb_html, rel=rel_html)
            write("post/{}/index.html".format(p["_slug"]),
                  self.layout(p.get("title") or "পোস্ট", excerpt(p.get("text"), 160) or desc, body, "posts", path,
                              image=imgs[0] if imgs else None))
            urls.append(path)

        # ৪০৪ ও সাইটম্যাপ
        body = ('<div class="wrap narrow"><section class="block" style="text-align:center"><h2 class="serif">পাতাটি পাওয়া যায়নি</h2>'
                '<p>আপনি যে পাতাটি খুঁজছেন সেটি নেই বা সরানো হয়েছে।</p><a class="cta" href="/">হোমে ফিরুন</a></section></div>')
        write("404.html", self.layout("পাতা পাওয়া যায়নি", desc, body, "", "/404.html"))
        if self.url:
            sm = "".join("<url><loc>{}{}</loc></url>".format(esc(self.url), esc(u)) for u in urls)
            write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
                  '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{}</urlset>\n'.format(sm))
        print("তৈরি হয়েছে: {}টি পোস্ট, {}টি ক্যাটাগরি, মোট {}টি পাতা".format(len(self.posts), len(self.cats), len(urls) + 1))


if __name__ == "__main__":
    Site().build()
