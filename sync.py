#!/usr/bin/env python3
"""ফেসবুক পেইজের সাথে ওয়েবসাইটের পোস্ট মিলিয়ে রাখে।

- নতুন পোস্ট যোগ করে।
- ফেসবুকে এডিট করা পোস্টের লেখা সাইটেও বদলে দেয়।
- ফেসবুক থেকে মুছে ফেলা পোস্ট সাইট থেকেও সরিয়ে দেয়।
- আপনি Pages CMS-এ যে পোস্ট নিজে এডিট করেছেন, সেটা কখনো বদলায় বা মুছে না।
- হাতে বানানো পোস্ট (আইডিতে '_' নেই) কখনো বদলায় বা মুছে না।
- ফেসবুক থেকে তথ্য আনতে ত্রুটি হলে কিছুই মুছে না।
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime


def _clean(value):
    # ফাঁকা জায়গা, নতুন লাইন ও উদ্ধৃতি চিহ্ন সরিয়ে ফেলে
    return re.sub(r"[\s\"'`]+", "", value or "")


PAGE_ID = _clean(os.environ.get("FB_PAGE_ID"))
TOKEN = _clean(os.environ.get("FB_PAGE_TOKEN"))
API = "https://graph.facebook.com/v21.0"
DATA_FILE = "data/posts.json"
IMG_DIR = "images/posts"
MAX_IMAGES = 6

# ক্যাটাগরি ঠিক করার নিয়ম। ওপরের ক্যাটাগরির অগ্রাধিকার বেশি।
RULES = [
    ("সেবামূলক কাজ", ["#সেবা", "#রক্তদান", "রক্তদান", "রক্ত", "বিতরণ", "ত্রাণ", "শীতবস্ত্র", "কম্বল", "সহায়তা", "অনুদান", "সেবা"]),
    ("ইভেন্ট", ["#ইভেন্ট", "অনুষ্ঠান", "আয়োজন", "ইভেন্ট", "সেমিনার", "কর্মশালা", "প্রতিযোগিতা", "বইমেলা", "আলোচনা সভা", "র‍্যালি"]),
    ("ঘোষণা", ["#ঘোষণা", "ঘোষণা", "বিজ্ঞপ্তি", "নোটিশ", "নিয়োগ", "আবেদন", "নিবন্ধন", "রেজিস্ট্রেশন"]),
    ("শিক্ষামূলক", ["#শিক্ষা", "শিক্ষা", "পাঠচক্র", "পাঠাগার", "লাইব্রেরি", "বই", "পাঠ", "রিভিউ"]),
    ("খবর", ["#খবর", "সংবাদ", "প্রতিবেদন", "খবর", "আজকের পত্রিকা"]),
    ("গ্যালারি", ["#গ্যালারি", "#ছবি"]),
]
DEFAULT_CATEGORY = "সাধারণ"


def api_get(url, retries=3):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            try:
                msg = json.loads(body)["error"]["message"]
            except Exception:
                msg = body[:200]
            print("ফেসবুক ত্রুটি ({}): {}".format(e.code, msg))
            if e.code in (400, 401, 403):
                sys.exit(1)
        except Exception as e:  # নেটওয়ার্ক সমস্যা
            print("নেটওয়ার্ক সমস্যা:", type(e).__name__)
        time.sleep(3 * (attempt + 1))
    sys.exit(1)


def sig(title, category, text):
    raw = "\n".join([title or "", category or "", text or ""])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def pick_category(text, n_images):
    t = (text or "").strip()
    if not t:
        return "গ্যালারি" if n_images else DEFAULT_CATEGORY
    for cat, words in RULES:
        for w in words:
            if w in t:
                return cat
    return DEFAULT_CATEGORY


def make_title(text):
    t = (text or "").strip()
    if not t:
        return "ফটো পোস্ট"
    first = t.splitlines()[0].strip()
    first = re.sub(r"#\S+", "", first).strip() or t[:60]
    return first if len(first) <= 70 else first[:67] + "…"


def collect_image_urls(post):
    urls = []
    att = (post.get("attachments") or {}).get("data") or []
    if att:
        subs = (att[0].get("subattachments") or {}).get("data") or []
        for s in subs:
            u = ((s.get("media") or {}).get("image") or {}).get("src")
            if u:
                urls.append(u)
        if not urls:
            u = ((att[0].get("media") or {}).get("image") or {}).get("src")
            if u:
                urls.append(u)
    if not urls and post.get("full_picture"):
        urls.append(post["full_picture"])
    return urls[:MAX_IMAGES]


def download_images(post_id, urls):
    os.makedirs(IMG_DIR, exist_ok=True)
    saved = []
    safe = re.sub(r"[^0-9A-Za-z_-]", "_", post_id)
    for i, u in enumerate(urls, 1):
        path = "{}/{}_{}.jpg".format(IMG_DIR, safe, i)
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            with open(path, "wb") as f:
                f.write(data)
            saved.append(path)
        except Exception as e:
            print("ছবি নামানো যায়নি:", type(e).__name__)
    return saved


def to_iso(s):
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z").isoformat()
    except Exception:
        return s


def is_fb_post(p):
    return "_" in str(p.get("id", ""))


def hand_edited(p):
    """Pages CMS-এ এডিট করা পোস্ট কিনা।"""
    if p.get("edited"):
        return True
    auto = p.get("auto")
    cur = sig(p.get("title"), p.get("category"), p.get("text"))
    return auto is not None and auto != cur


def merge(posts, fb_posts, download):
    """posts তালিকা বদলে দেয় এবং (যোগ, আপডেট, মোছা) সংখ্যা ফেরত দেয়।"""
    by_id = {p.get("id"): p for p in posts}
    fb_ids = {f["id"] for f in fb_posts}
    added = updated = removed = 0

    for f in fb_posts:
        text = f.get("message", "")
        p = by_id.get(f["id"])
        if p is None:
            images = download(f["id"], collect_image_urls(f))
            title = make_title(text)
            cat = pick_category(text, len(images))
            posts.append({
                "id": f["id"],
                "title": title,
                "date": to_iso(f.get("created_time", "")),
                "category": cat,
                "text": text,
                "images": images,
                "fb_url": f.get("permalink_url", ""),
                "edited": False,
                "auto": sig(title, cat, text),
            })
            added += 1
            continue

        if p.get("edited"):
            continue
        cur = sig(p.get("title"), p.get("category"), p.get("text"))
        if p.get("auto") is None:
            p["auto"] = cur  # পুরনো পোস্ট: এডিট হয়নি ধরে নেওয়া হলো
        if p["auto"] != cur:
            continue  # আপনি নিজে এডিট করেছেন, তাই ছোঁয়া হবে না

        changed = False
        title = make_title(text)
        cat = pick_category(text, len(p.get("images") or []))
        new_sig = sig(title, cat, text)
        if new_sig != cur:
            p["title"], p["category"], p["text"] = title, cat, text
            p["auto"] = new_sig
            changed = True
        if not p.get("images"):
            urls = collect_image_urls(f)
            if urls:
                imgs = download(f["id"], urls)
                if imgs:
                    p["images"] = imgs
                    changed = True
        link = f.get("permalink_url", "")
        if link and p.get("fb_url") != link:
            p["fb_url"] = link
            changed = True
        if changed:
            updated += 1

    # ফেসবুকে নেই এমন পোস্ট সরানো
    to_remove = [
        p for p in posts
        if is_fb_post(p) and p.get("id") not in fb_ids and not hand_edited(p)
    ]
    total_fb = len([p for p in posts if is_fb_post(p)])
    if to_remove and (not fb_posts or len(to_remove) > max(5, total_fb // 2)):
        print("সতর্কতা: {}টি পোস্ট মুছতে হতো, কিন্তু সংখ্যাটি সন্দেহজনক বেশি। নিরাপত্তার জন্য কিছুই মোছা হয়নি।".format(len(to_remove)))
        to_remove = []
    for p in to_remove:
        for img in p.get("images") or []:
            if str(img).startswith(IMG_DIR + "/") and os.path.exists(img):
                try:
                    os.remove(img)
                except OSError:
                    pass
        posts.remove(p)
        removed += 1

    if fb_posts:
        posts[:] = [p for p in posts if not str(p.get("id", "")).startswith("demo-")]
    posts.sort(key=lambda p: p.get("date", ""), reverse=True)
    return added, updated, removed


def fetch_all_fb_posts():
    fields = (
        "id,message,created_time,permalink_url,full_picture,"
        "attachments{subattachments{media{image{src}}},media{image{src}}}"
    )
    query = urllib.parse.urlencode({"fields": fields, "limit": 50, "access_token": TOKEN})
    url = "{}/{}/posts?{}".format(API, PAGE_ID, query)
    result = []
    pages = 0
    while url and pages < 200:
        data = api_get(url)  # ত্রুটি হলে এখানেই প্রোগ্রাম থেমে যায়, কিছু মোছা হয় না
        pages += 1
        result.extend(data.get("data", []))
        url = (data.get("paging") or {}).get("next")
    return result


def main():
    if not PAGE_ID or not TOKEN:
        print("FB_PAGE_ID বা FB_PAGE_TOKEN পাওয়া যায়নি। GitHub Secrets ঠিক আছে কিনা দেখুন।")
        sys.exit(1)
    if not PAGE_ID.isascii() or not PAGE_ID.isdigit():
        print("FB_PAGE_ID ভুল: এতে শুধু ইংরেজি সংখ্যা থাকতে হবে (যেমন 1234567890123)। "
              "বর্তমানে {} অক্ষর আছে এবং সবগুলো ইংরেজি সংখ্যা নয়।".format(len(PAGE_ID)))
        sys.exit(1)
    if not TOKEN.isascii() or not TOKEN.startswith("EAA"):
        print("FB_PAGE_TOKEN ভুল: টোকেন ইংরেজি অক্ষরে এবং সাধারণত EAA দিয়ে শুরু হয়। "
              "বর্তমানে {} অক্ষর আছে।".format(len(TOKEN)))
        sys.exit(1)

    os.makedirs("data", exist_ok=True)
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            posts = json.load(f)
    except FileNotFoundError:
        posts = []
    before = json.dumps(posts, ensure_ascii=False, sort_keys=True)

    fb_posts = fetch_all_fb_posts()
    added, updated, removed = merge(posts, fb_posts, download_images)

    after = json.dumps(posts, ensure_ascii=False, sort_keys=True)
    if after != before:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
    print("যোগ: {}টি, আপডেট: {}টি, মোছা: {}টি".format(added, updated, removed))


if __name__ == "__main__":
    main()
