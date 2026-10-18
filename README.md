# Kokoa Nabatame Home Page

生田目心愛のホームページ（Flask / Vercel）。

## どこを直せばいい？

| 変えたいもの | 編集する場所 |
| --- | --- |
| 自己紹介・関心・研究テーマ・学歴・資格・連絡先・リンク | `data/profile.yaml` |
| 業績（論文・発表・受賞）・所属学会・研究費・社会貢献・TA など | researchmap を更新 → 下の「researchmap の反映」 |
| ブログ記事 | `posts/` に Markdown を1つ追加（`posts/README.md` 参照） |
| プロフィール写真 | `public/images/` に画像を置き、`profile.yaml` の `photo` を変更 |
| 見た目（色・余白など） | `public/style.css` の冒頭 |
| 夜空の動き（星の数・回る速さ・流れ星） | `public/sky.js` の冒頭「調整できる値」 |

`app.py` と `templates/` は、ふだん触る必要はありません。

## researchmap の反映

1. researchmap の「エクスポート」で zip をダウンロード
2. このフォルダで次を実行（パスワードを聞かれたら入力）

   ```bash
   python update_researchmap.py ~/Downloads/rm_researchers20261018.zip
   ```

3. `data/researchmap.yaml` が新しくなるので、そのまま commit & push

- researchmap で **「公開」** になっている項目だけがサイトに載ります（「研究者のみ」「非公開」は載りません）。
- 自分の名前（生田目 / Nabatame）は著者リストで自動的に太字になります。
- 学会の公式サイトへのリンクは `profile.yaml` の `society_urls` に追記します。
- zip や `.jsonl` はリポジトリに入れないでください（`.gitignore` 済み）。

## 手元で確認する

```bash
pip install -r requirements.txt
python app.py
# → http://127.0.0.1:5000 を開く
```

GitHub の `main` に push すると Vercel に自動で公開されます。
