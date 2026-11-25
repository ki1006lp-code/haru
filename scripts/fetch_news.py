#!/usr/bin/env python3
"""Google ニュースのRSSから、指定キーワードの直近記事を集めて10件に絞る。

使い方: python3 scripts/fetch_news.py [--days 2] [--top 10]
出力:   news/YYYY-MM-DD.json と news/YYYY-MM-DD.md（日付はJST）
標準ライブラリのみ。取得に失敗したキーワードは飛ばして続行する。
"""
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JST = timezone(timedelta(hours=9))

# (ラベル, 検索語, 重み)。重みが大きいほど、少ない話題として優先する。
QUERIES = [
    ("製造", "製造業", 1.0),
    ("自動車", "自動車 部品 メーカー", 1.0),
    ("働き方", "働き方 製造業 現場", 1.2),
    ("管理職", "管理職 中小企業", 1.2),
    ("中小企業", "中小企業 製造業", 1.0),
    ("AI", "AI 製造業 工場", 1.0),
    ("溶接", "溶接", 2.0),
    ("プロジェクション溶接", "プロジェクション溶接", 3.0),
    ("スポット溶接", "スポット溶接", 3.0),
    ("プレス", "プレス加工 金型", 2.0),
    ("ロボット", "ロボット 工場 自動化", 1.0),
]
PER_LABEL_CAP = 2
# 話題として使えない記事（事件・訃報・市場調査の宣伝など）を除く
EXCLUDE = ["逮捕", "容疑", "死亡", "遺体", "市場分析", "市場規模", "市場予測", "市場調査", "年までの予測", "百万米ドル", "CAGR", "セミナー開催のお知らせ"]


def fetch(query: str, days: int):
    q = urllib.parse.quote(f"{query} when:{days}d")
    url = f"https://news.google.com/rss/search?q={q}&hl=ja&gl=JP&ceid=JP:ja"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        root = ET.fromstring(r.read())
    out = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        src = (it.findtext("source") or "").strip()
        if src and title.endswith(" - " + src):
            title = title[: -len(src) - 3]
        try:
            pub = parsedate_to_datetime(it.findtext("pubDate")).astimezone(JST)
        except Exception:
            pub = None
        out.append({"title": title, "source": src, "url": (it.findtext("link") or "").strip(), "published": pub})
    return out


def norm(t: str) -> str:
    return re.sub(r"[\s　「」『』【】\[\]（）()、。・!！?？:：\-―]", "", t)[:24]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=2)
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args()
    now = datetime.now(JST)
    pool = {}
    failed = []
    for label, query, weight in QUERIES:
        try:
            items = fetch(query, a.days)
        except Exception as e:  # noqa: BLE001
            failed.append(f"{label}: {e}")
            continue
        for rank, it in enumerate(items[:15]):
            key = norm(it["title"])
            if not key or any(w in it["title"] for w in EXCLUDE):
                continue
            rec = pool.setdefault(key, {**it, "labels": [], "score": 0.0})
            if label not in rec["labels"]:
                rec["labels"].append(label)
                rec["score"] += weight + max(0, 3 - rank) * 0.1
    ranked = sorted(
        pool.values(),
        key=lambda r: (r["score"] + (1.0 if r["published"] and now - r["published"] < timedelta(hours=24) else 0)),
        reverse=True,
    )
    picked, cnt = [], {}
    for r in ranked:
        main = r["labels"][0]
        if sum(cnt.get(l, 0) for l in r["labels"][:1]) >= PER_LABEL_CAP:
            continue
        picked.append(r)
        cnt[main] = cnt.get(main, 0) + 1
        if len(picked) >= a.top:
            break
    for r in picked:
        r["published"] = r["published"].strftime("%Y-%m-%d %H:%M") if r["published"] else ""
    date = now.strftime("%Y-%m-%d")
    outdir = ROOT / "news"
    outdir.mkdir(exist_ok=True)
    (outdir / f"{date}.json").write_text(json.dumps({"date": date, "failed": failed, "articles": picked}, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"# ニュース {date}", ""]
    for i, r in enumerate(picked, 1):
        lines += [f"{i}. [{r['title']}]({r['url']})", f"   - {r['source']} / {r['published']} / {', '.join(r['labels'])}"]
    if failed:
        lines += ["", "取得失敗: " + "; ".join(failed)]
    (outdir / f"{date}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    if len(picked) < a.top:
        print(f"\n注意: {len(picked)}件しか集まりませんでした", file=sys.stderr)


if __name__ == "__main__":
    main()
