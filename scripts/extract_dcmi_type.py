"""从 dctype.ttl 提取 DCMI Type 词汇 → src/famarchive/data/vocabularies/dcmi-type.yaml。

纪律：脚本转写禁手抄（plan/05 M1）——词表内容一律由本脚本从
data/raw/dcmi/dctype.ttl（DCMI 官方 GitHub dcmi/vocabtool build/dctype.ttl）
程序化生成，人工只维护本脚本不维护词表正文。

用法：.venv/Scripts/python scripts/extract_dcmi_type.py
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
TTL_PATH = REPO / "data" / "raw" / "dcmi" / "dctype.ttl"
OUT_PATH = REPO / "src" / "famarchive" / "data" / "vocabularies" / "dcmi-type.yaml"


def parse_ttl_blocks(text: str) -> list[dict]:
    """按顶层 <subject> 块解析 dctype.ttl（仅依赖本文件出现的谓词形态）。"""
    blocks = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^<(?P<subj>[^>]+)>$", line.strip())
        if m:
            subject = m.group("subj")
            props: dict[str, list[str]] = {}
            i += 1
            while i < len(lines) and not lines[i].strip() in (".", ""):
                prop_line = lines[i].strip()
                if prop_line.endswith("."):
                    prop_line = prop_line[:-1].strip()
                prop_line = prop_line.rstrip(";").strip()
                pm = re.match(r"^(?P<pred>[a-z]+:[A-Za-z]+)\s+(?P<obj>.+?)(?:\s*;)?$", prop_line)
                am = re.match(r"^a\s+(?P<obj>.+?)(?:\s*;)?$", prop_line)
                if pm:
                    props.setdefault(pm.group("pred"), []).append(pm.group("obj"))
                elif am:
                    props.setdefault("a", []).append(am.group("obj"))
                i += 1
            blocks.append({"subject": subject, "props": props})
        i += 1
    return blocks


def unquote(obj: str) -> str:
    """剥引号与 @lang / ^^datatype，取纯字面量值。"""
    obj = obj.strip()
    m = re.match(r'^"(.*)"(?:@[a-z-]+|\^\^<[^>]+>)?$', obj)
    return m.group(1) if m else obj


def main() -> None:
    text = TTL_PATH.read_text(encoding="utf-8")
    blocks = parse_ttl_blocks(text)

    ns_modified = None
    for b in blocks:
        if b["subject"] == "http://purl.org/dc/dcmitype/":
            ns_modified = unquote(b["props"]["dcterms:modified"][0])
    if not ns_modified:
        raise SystemExit("dctype.ttl 缺 namespace dcterms:modified，拒绝生成")

    values = []
    for b in blocks:
        if not b["subject"].startswith("http://purl.org/dc/dcmitype/"):
            continue
        local = b["subject"].rsplit("/", 1)[-1]
        if not b["props"].get("a") or "rdfs:Class" not in b["props"]["a"]:
            continue
        label = unquote(b["props"]["rdfs:label"][0])
        definition = unquote(b["props"]["rdfs:comment"][0])
        issued = unquote(b["props"]["dcterms:issued"][0])
        modified = unquote(b["props"]["dcterms:modified"][0])
        has_version = b["props"]["dcterms:hasVersion"][0].strip().strip("<>")
        values.append(
            {
                "id": local,
                "label": label,
                "definition": definition,
                "source": (
                    f"DCMI Type Vocabulary <{b['subject']}>（issued {issued}，"
                    f"modified {modified}，history {has_version}；"
                    f"转写自 data/raw/dcmi/dctype.ttl）"
                ),
            }
        )
    values.sort(key=lambda v: v["id"])

    doc = {
        "vocabulary_id": "dcmi-type",
        "title": "DCMI Type 受控词表（脚本转写）",
        "version": ns_modified,
        "source_document": "data/raw/dcmi/dctype.ttl（DCMI 官方 GitHub dcmi/vocabtool build/dctype.ttl）",
        "provenance_note": "本文件由 scripts/extract_dcmi_type.py 从 dctype.ttl 程序化生成，禁手抄；改动须改脚本重跑",
        "values": values,
    }
    OUT_PATH.write_text(
        yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )
    print(f"写入 {OUT_PATH}：{len(values)} 个词条，namespace modified={ns_modified}")


if __name__ == "__main__":
    main()
