#!/usr/bin/env python3
"""アイコンキャラを参照画像にして、投稿文に合うイラストをGeminiで生成する。

使い方:
  python3 scripts/generate_image.py --text "投稿文" --out queue/images/2026-11-25_A3.png

環境変数:
  GEMINI_API_KEY      Gemini APIキー（必須）
  GEMINI_IMAGE_MODEL  画像モデル名（既定: gemini-2.5-flash-image）
標準ライブラリのみ使用。
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

STYLE = (
    "添付した画像の人物を主人公にしたイラストを描いてください。"
    "人物の特徴: オレンジ色のふんわりした髪、にこやかな笑顔、頬に淡いピンクの丸、白シャツに紺のネクタイ、青い作業着（胸に小さな名札、胸ポケットにペン）。"
    "絵柄は添付画像と同じ、やわらかい水彩風、線は細め、正方形の構図。製造業の現場が舞台。"
    "画像の中に文字や数字は入れないこと（名札は無地のまま）。安全に関わる場面では保護具を着用させること。"
)


def build_prompt(text: str, scene: str | None) -> str:
    body = scene or f"次のX投稿の内容を、見た人が思わずクスッと・ハッとする1場面で表現する: 「{text}」"
    return f"{STYLE}\n\n場面: {body}"


def generate(text: str, scene: str | None, out: Path) -> None:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY が設定されていません")
    icon = base64.b64encode((ROOT / "assets" / "character_ref.png").read_bytes()).decode()
    payload = {
        "contents": [{
            "parts": [
                {"text": build_prompt(text, scene)},
                {"inline_data": {"mime_type": "image/png", "data": icon}},
            ]
        }]
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Gemini API エラー {e.code}: {e.read().decode(errors='replace')[:500]}")
    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            blob = part.get("inlineData") or part.get("inline_data")
            if blob:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(base64.b64decode(blob["data"]))
                print(f"saved: {out}")
                return
    sys.exit(f"画像が返りませんでした: {json.dumps(data, ensure_ascii=False)[:500]}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True, help="投稿文")
    ap.add_argument("--scene", help="場面を直接指定したい場合")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    generate(a.text, a.scene, a.out)
