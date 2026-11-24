# X投稿自動化（製造業アカウント）

目的: 製造業の現場アカウントの投稿を、毎日 8:00 / 12:00 / 15:00 に出す。
人間の作業は「候補から選ぶ」と「Xに予約投稿する」だけにする（無料運用。X APIは使わない）。

## 最初に必ず読むもの（毎回）
- `config/profile.md`（本人の考え・好み・禁止事項）
- `config/episodes.md`（実体験ネタ帳。未使用の項目を優先して使う）
- `analytics/log.md`（反応ログ。伸びた型を参考にする）
- `config/character.md`（キャラ設定と発信の柱）

## 構成
- `config/character.md` … アイコンキャラの設定と画像ルール
- `config/products.json` … 楽天アフィリエイト商品リスト
- `queue/candidates/YYYY-MM-DD.json` … 日別の投稿案（各枠5案）
- `queue/selected/YYYY-MM-DD.json` … 選択済み（文・画像パス）
- `queue/images/` … 生成イラスト
- `scripts/generate_image.py` … Geminiで画像生成（`GEMINI_API_KEY` 必須）
- `scripts/build_select_page.py` … 選択ページ `out/select.html` を作る

## 投稿枠
| 時刻 | キー | 内容 | 画像 |
|---|---|---|---|
| 08:00 | aruaru | 製造業あるある（共感・クスッと） | あり |
| 12:00 | affiliate | 楽天アフィリエイト商品のPR | なし |
| 15:00 | question | 真面目なトーンの問いかけ | あり |

## 文面ルール
- 長めに伝える投稿は「メイン投稿＋リプライ1〜2個（スレッド）」にする。各ポストは全角140字以内。docの `replies`（文字列の配列）に入れる
- アフィリエイト投稿: メインに「#PR」と体験・考え、リプライの最後にリンク（リンクはページが自動で付ける）。メイン投稿にURLは入れない
- X Premiumなら1投稿で長文も可能。契約状況は未確認（確認できたら方針を見直す）
- 1投稿は全角120字以内を目安（上限は全角140字）
- アフィリエイト投稿は先頭か末尾に必ず「#PR」を入れる。誇大表現・効果の断定をしない
- あるある・問いかけは、特定の会社・個人が分かる内容や、事故・労災を笑いにする内容を避ける
- 季節ネタは投稿日の3日以内のものだけ
- バズ傾向は「真似」ではなく型（共感の切り口、文の長さ、書き出し）だけ参考にする

## 毎朝のルーティン（定期実行の手順）
1. Web検索で、製造業・現場・季節もののバズ傾向を収集する（X上の話題、関連記事、季節イベント）
2. ユーザーが貼った自分の投稿の数値（インプレッション、いいね等）があれば分析する
3. 朝レポートを作る: 昨日の反応、伸びた型、今日以降に効きそうな切り口
4. ストック確認: `queue/selected/` に今日から数えて3日分なければ、足りない日の候補を3枠×5案で作る
5. 候補ができたら `python3 scripts/build_select_page.py` で選択ページを更新し、ユーザーに知らせる

## 投稿ストックのページ（Artifact）
URL: https://claude.ai/artifact/XbVtetUTEhxY5rAvVSdXeS （ソース: `app/index.html`）
- ユーザーはここで案を選び、コピーし、Xの投稿画面を開き、投稿後に反応（表示・いいね・RP・メモ）を記録する
- データはArtifactのdb（コレクション `posts`、doc id は `日付_スロット_案ID`）。項目: date, slot(aruaru/affiliate/question), cid, text, status(candidate/picked/ready/scheduled/posted), imps, likes, rp, note
- 毎朝: ArtifactData の query で `posts` を読み、status が picked 以降の傾向と posted の反応を `profile.md` と `analytics/log.md` に反映する
- 新しい案は `queue/candidates/` に保存すると同時に、ArtifactData の batch で `posts` に status=candidate で追加する

## 学習の更新（会話のたびに）
- ユーザーが新しい経験・考えを話したら `episodes.md` か `profile.md` に追記してコミット・pushする
- 案を選んだ/選ばなかった傾向は `profile.md` の「選択の傾向ログ」に残す
- 書いていないことを「覚えている」前提で話さない

## 選択後の流れ
ユーザーが「2026-11-25 aruaru=A3 affiliate=F2 question=Q1」の形式で返す。
1. `queue/selected/日付.json` に確定した文を保存する
2. 画像は手動運用（Geminiの画像モデルは無料枠が使えないため）。あるある・問いかけの各案について
   `python3 scripts/make_image_prompt.py "本文"` で出したプロンプトを提示する。
   ユーザーが `assets/icon.png` を添えてGeminiアプリ等で作る。
   （課金を有効にした場合は `scripts/generate_image.py --text 本文 --out queue/images/日付_ID.png` で自動化できる）
3. 完成した「文」を、Xの予約投稿用に日付・時刻つきでまとめて提示する
