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
- `scripts/build_select_page.py` … 選択ページ `out/select.html` を作る（旧。今は Artifact のページを使う）
- `scripts/fetch_news.py` … Google ニュースRSSから毎朝10記事を集める → `news/`
- 環境 `haru-x-posts`: news.google.com / rss.itmedia.co.jp / newswitch.jp / 楽天3ホストを許可済み

## 投稿枠
| 時刻 | キー | 内容 | 画像 |
|---|---|---|---|
| 08:00 | news | ニュース記事にコメント（メイン＋リプライ2：意見／元記事リンク） | あり |
| 予備 | aruaru | 製造業あるある（共感・クスッと）。ニュースが弱い日や夕方用 | あり |
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
前提: 作業ブランチは `claude/x-post-automation-jwzmvs`。投稿は絶対に自動で出さない（X APIは使わない）。
1. `python3 scripts/fetch_news.py --days 2` で、キーワード（製造、自動車、働き方、管理職、中小企業、AI、溶接、プロジェクション溶接、スポット溶接、プレス、ロボット）の記事を10件集める → `news/日付.md`
2. 10件から、あなたの軸（仕組み化・属人化・電気制御・溶接/プレス/ロボット）に合う5件を選び、当日 `news` 枠（08:00）の候補N1〜N5を作る
   - メイン: 記事の見出しの範囲で内容に触れ、一言の意見を添える（記事に書いていない事実を作らない・断定しない）
   - リプライ1: 意見の続き（profile.md と episodes.md の事実だけを使う）
   - リプライ2: `元記事：タイトル（媒体名）` ＋ URL
   - 各ポスト全角140字以内。事件・訃報・誹謗は選ばない
3. ArtifactData の `posts` を読み、選択・投稿済みの傾向と反応（imps/likes/rp/note）を `profile.md` と `analytics/log.md` に反映する
4. ストック確認: 今日から3日分で、question・affiliate 枠が未選択のまま不足していれば、足りない日の候補を作る（各枠5案、メイン＋リプライ2）
5. 候補は `queue/candidates/` に保存し、同時に ArtifactData の batch（status=candidate）で `posts` に追加する。既存の文書は上書きしない
6. 朝レポートを返す: 昨日の反応、今日の10記事、作った候補、ユーザーにしてほしいこと（選ぶ・商品確認など）

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
