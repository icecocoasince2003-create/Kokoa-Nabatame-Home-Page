"""researchmap のエクスポートデータから data/researchmap.yaml を作り直すスクリプト。

使い方（どちらでもOK）:
    python update_researchmap.py ダウンロードしたzipファイル.zip
    python update_researchmap.py rm_researchers20261018.jsonl

zip にパスワードが付いている場合は、実行中に入力を求められます。
researchmap で「公開」になっている項目だけがホームページに載ります
（「研究者のみ」「非公開」の項目は書き出されません）。
"""

import getpass
import json
import os
import sys
import zipfile
from datetime import date

import yaml

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "researchmap.yaml")

MY_NAMES = ("生田目", "nabatame")  # 著者リストで自分の名前を太字にするための目印

PRESENTATION_TYPES = {
    "oral_presentation": "口頭発表",
    "poster_presentation": "ポスター発表",
    "invited_oral_presentation": "招待講演",
    "keynote_oral_presentation": "基調講演",
    "public_symposium": "シンポジウム",
    "nominated_symposium": "シンポジウム",
}
PAPER_TYPES = {
    "scientific_journal": "学術雑誌",
    "international_conference_proceedings": "国際会議プロシーディングス",
    "research_institution": "研究機関紀要",
    "in_book": "論文集（書籍）内論文",
}


# ---------- 読み込み ----------

def read_lines(path):
    if path.lower().endswith(".zip"):
        with zipfile.ZipFile(path) as zf:
            name = next(n for n in zf.namelist() if n.endswith(".jsonl"))
            try:
                data = zf.read(name)
            except RuntimeError:  # パスワード付き
                pwd = os.environ.get("RM_ZIP_PASSWORD") or getpass.getpass("zip のパスワード: ")
                data = zf.read(name, pwd=pwd.encode())
        text = data.decode("utf-8")
    else:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    return [json.loads(line) for line in text.splitlines() if line.strip()]


# ---------- 小さな整形ヘルパー ----------

def ja(value):
    """{"ja": ..., "en": ...} から日本語（なければ英語）を取り出す。"""
    if isinstance(value, dict):
        return value.get("ja") or value.get("en") or ""
    return value or ""


def names(value):
    people = ja(value) or []
    result = []
    for p in people:
        name = p.get("name", "")
        result.append({"name": name, "me": any(m in name.lower() for m in MY_NAMES)})
    return result


def period(start, end):
    """'2025-04', '9999' → '2025年4月 〜 現在' のような表示用文字列。"""
    def fmt(d):
        if not d:
            return ""
        if d.startswith("9999"):
            return "現在"
        parts = d.split("-")
        s = f"{parts[0]}年"
        if len(parts) > 1:
            s += f"{int(parts[1])}月"
        return s
    if end and end != start:
        return f"{fmt(start)} 〜 {fmt(end)}"
    return fmt(start)


def pages(m):
    s, e = m.get("starting_page"), m.get("ending_page")
    if s and e:
        return f"pp. {s}–{e}"
    return f"p. {s}" if s else ""


def journal_info(m):
    bits = [ja(m.get("publication_name"))]
    vol = m.get("volume")
    if vol:
        bits.append(f"{vol}({m['number']})" if m.get("number") else str(vol))
    if pages(m):
        bits.append(pages(m))
    return " ".join(b for b in bits if b)


# ---------- 種類ごとの変換 ----------

def convert(records):
    out = {
        "updated": date.today().isoformat(),
        "keywords": [],
        "fields": [],
        "achievements": [],
        "projects": [],
        "experience": [],
        "memberships": [],
        "outreach": [],
    }

    for rec in records:
        kind = rec["insert"]["type"]
        m = rec.get("merge", {})
        if kind != "researchers" and m.get("display") != "disclosed":
            continue  # 公開設定の項目だけ使う

        if kind == "research_interests":
            out["keywords"].append(ja(m.get("keyword")))

        elif kind == "research_areas":
            out["fields"].append(
                {"field": ja(m.get("research_field")), "keyword": ja(m.get("research_keyword"))}
            )

        elif kind == "published_papers":
            out["achievements"].append({
                "date": m.get("publication_date", ""),
                "type": "論文",
                "title": ja(m.get("paper_title")),
                "authors": names(m.get("authors")),
                "venue": journal_info(m),
                "note": PAPER_TYPES.get(m.get("published_paper_type"), ""),
                "url": (m.get("see_also") or [{}])[0].get("@id", ""),
            })

        elif kind == "misc":
            out["achievements"].append({
                "date": m.get("publication_date", ""),
                "type": "著作",
                "title": ja(m.get("paper_title")),
                "authors": names(m.get("authors")),
                "venue": journal_info(m),
                "note": "",
                "url": "",
            })

        elif kind == "presentations":
            out["achievements"].append({
                "date": m.get("from_event_date") or m.get("publication_date", ""),
                "type": "発表",
                "title": ja(m.get("presentation_title")),
                "authors": names(m.get("presenters")),
                "venue": ja(m.get("event")),
                "note": PRESENTATION_TYPES.get(m.get("presentation_type"), ""),
                "url": "",
            })

        elif kind == "awards":
            title = ja(m.get("award_name"))
            subject = ja(m.get("award_title"))
            out["achievements"].append({
                "date": m.get("award_date", ""),
                "type": "受賞",
                "title": f"{title}（{subject}）" if subject else title,
                "authors": names(m.get("winners")),
                "venue": ja(m.get("association")),
                "note": "",
                "url": "",
            })

        elif kind == "research_projects":
            out["projects"].append({
                "title": ja(m.get("research_project_title")),
                "funder": ja(m.get("offer_organization")),
                "program": ja(m.get("system_name")),
                "period": period(m.get("from_date"), m.get("to_date")),
                "start": m.get("from_date", ""),
                "role": "研究代表者" if m.get("research_project_owner_role") == "principal_investigator" else "",
            })

        elif kind == "research_experience":
            org = ja(m.get("affiliation"))
            section = ja(m.get("section"))
            out["experience"].append({
                "job": ja(m.get("job")),
                "org": f"{org} {section}".strip(),
                "period": period(m.get("from_date"), m.get("to_date")),
                "start": m.get("from_date", ""),
                "note": ja(m.get("note")),
            })

        elif kind == "association_memberships":
            out["memberships"].append({
                "name": ja(m.get("academic_society_name")),
                "since": (m.get("from_date") or "")[:4],
            })

        elif kind == "social_contribution":
            ds = m.get("dataset") or {}
            out["outreach"].append({
                "title": ja(m.get("social_contribution_title")),
                "event": ja(m.get("event")),
                "organizer": ja(m.get("promoter")),
                "date": m.get("from_event_date", ""),
                "url": ds.get("access_url", ""),
            })

    # 新しい順に並べる
    out["achievements"].sort(key=lambda a: a["date"], reverse=True)
    out["projects"].sort(key=lambda a: a["start"], reverse=True)
    out["experience"].sort(key=lambda a: a["start"], reverse=True)
    out["memberships"].sort(key=lambda a: a["since"])
    out["outreach"].sort(key=lambda a: a["date"], reverse=True)
    return out


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    data = convert(read_lines(sys.argv[1]))
    header = (
        "# このファイルは update_researchmap.py が自動で作ります。手で編集しないでください。\n"
        "# 内容を変えたいときは researchmap 側を直して、もう一度エクスポート → スクリプト実行。\n"
    )
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(header)
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, width=1000)
    print(f"更新しました: {OUTPUT}")
    print(f"  業績 {len(data['achievements'])} 件 / 所属学会 {len(data['memberships'])} 件 / "
          f"研究費 {len(data['projects'])} 件 / 社会貢献 {len(data['outreach'])} 件")


if __name__ == "__main__":
    main()
