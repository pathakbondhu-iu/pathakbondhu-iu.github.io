#!/usr/bin/env python3
"""ফেসবুক পেইজের পোস্ট এনে data/posts.json-এ যোগ করে।
- শুধু নতুন পোস্ট যোগ হয়। আগে থেকে থাকা পোস্ট কখনো বদলানো হয় না,
  তাই আপনার করা এডিট নিরাপদ।
- ছবি নামিয়ে images/posts/ ফোল্ডারে রাখে।
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

PAGE_ID = os.environ.get("FB_PAGE_ID", "").strip()
TOKEN = os.environ.get("FB_PAGE_TOKEN", "").strip()
API = "https://graph.facebook.com/v21.0"
DATA_FILE = "data/posts.json"
IMG_DIR = "images/posts"
MAX_IMAGES = 6

# ক্যাটাগরি ঠিক করার নিয়ম। আগে হ্যাশট্যাগ, তারপর কীওয়ার্ড দেখা হয়।
# ওপরের ক্যাটাগরির অগ্রাধিকার বেশি। নিজের মতো বদলাতে পারবেন।
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


def main():
    if not PAGE_ID or not TOKEN:
        print("FB_PAGE_ID বা FB_PAGE_TOKEN পাওয়া যায়নি। GitHub Secrets ঠিক আছে কিনা দেখুন।")
        sys.exit(1)

    os.makedirs("data", exist_ok=True)
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            posts = json.load(f)
    except FileNotFoundError:
        posts = []
    known = {p.get("id") for p in posts}

    fields = (
        "id,message,created_time,permalink_url,full_picture,"
        "attachments{subattachments{media{image{src}}},media{image{src}}}"
    )
    query = urllib.parse.urlencode({"fields": fields, "limit": 50, "access_token": TOKEN})
    url = "{}/{}/posts?{}".format(API, PAGE_ID, query)

    new_posts = []
    pages = 0
    while url and pages < 200:
        data = api_get(url)
        pages += 1
        batch = data.get("data", [])
        if batch and all(p["id"] in known for p in batch):
            break  # এই পাতার সব পোস্ট আগে থেকেই আছে
        for p in batch:
            if p["id"] in known:
                continue
            urls = collect_image_urls(p)
            images = download_images(p["id"], urls)
            text = p.get("message", "")
            new_posts.append({
                "id": p["id"],
                "title": make_title(text),
                "date": to_iso(p.get("created_time", "")),
                "category": pick_category(text, len(images)),
                "text": text,
                "images": images,
                "fb_url": p.get("permalink_url", ""),
                "edited": False,
            })
            known.add(p["id"])
        url = (data.get("paging") or {}).get("next")

    if new_posts:
        posts = [p for p in posts if not str(p.get("id", "")).startswith("demo-")]
        posts.extend(new_posts)
        posts.sort(key=lambda p: p.get("date", ""), reverse=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
    print("নতুন পোস্ট যোগ হয়েছে: {}টি".format(len(new_posts)))


if __name__ == "__main__":
    main()
