"""CLI 入口：子命令与模块一一对应（见 plan/03 §3）。

骨架阶段：profile show / --help 可用；其余子命令为占位桩，
随 M2–M5 里程碑逐个实装。
"""

from __future__ import annotations

import argparse
import sys

import famarchive
from famarchive.profile import load_profile


def _ensure_utf8_stdio() -> None:
    """非 UTF-8 管道（如 Windows cp1252）下打印中文前重配 stdio。

    本机中文控制台 cp936 保持不动；仅探测到非 UTF-8 且支持 reconfigure 时切换。
    """
    for stream in (sys.stdout, sys.stderr):
        encoding = getattr(stream, "encoding", "") or ""
        if encoding.lower().replace("-", "") not in ("utf8", "utf8mb4"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (AttributeError, OSError):
                pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="famarchive",
        description="老照片/家庭档案数字化整理工作台（纯本地单机，零上传）",
    )
    parser.add_argument("--version", action="version", version=famarchive.__version__)
    sub = parser.add_subparsers(dest="command")

    p_import = sub.add_parser("import", help="导入本地文件夹/文件为档案项（M2 实装）")
    p_import.add_argument("path", help="待导入文件或目录")
    p_import.add_argument("--db", default=None, help="SQLite 库路径（默认 ./archive.sqlite3）")
    p_import.add_argument(
        "--media-type",
        required=True,
        help="媒体类型（photo-scan/photo-reprint/letter/document/id-card，见 media-type.yaml）",
    )

    p_validate = sub.add_parser("validate", help="按 DCMI profile 校验著录字段（M3 实装）")
    p_validate.add_argument("--db", default=None, help="SQLite 库路径（默认 ./archive.sqlite3）")
    p_validate.add_argument("--item", default=None, help="只校验指定档案项（默认全部）")
    p_validate.add_argument("--save-history", action="store_true", help="把当前 profile 版本登记进 profile_history")

    p_persons = sub.add_parser("persons", help="人物索引与代际关系（M3 实装）")
    p_persons.add_argument("--db", default=None, help="SQLite 库路径")
    p_persons.add_argument("--add", nargs=2, metavar=("NAME", "RELATION"), help="新增人物")
    p_persons.add_argument("--link", nargs=3, metavar=("PERSON", "ITEM", "ROLE"), help="人物↔档案项链接")
    p_persons.add_argument("--relation", nargs=3, metavar=("FROM", "TO", "TYPE"), help="添加关系边（词表约束）")
    p_persons.add_argument("--merge", nargs=2, metavar=("KEEP", "DROP"), help="同名人工确认合并")

    p_timeline = sub.add_parser("timeline", help="家庭年表视图（M3 实装）")
    p_timeline.add_argument("--db", default=None, help="SQLite 库路径")

    p_gui = sub.add_parser("gui", help="启动桌面 GUI（编目/人物/年表三页；需 .[gui]）")
    p_gui.add_argument("--db", default=None, help="SQLite 库路径")
    p_search = sub.add_parser("search", help="字段/人物/时间/媒体类型组合检索（M5 实装）")
    p_search.add_argument("--db", default=None, help="SQLite 库路径")
    p_search.add_argument("--text", default=None, help="全字段模糊关键词")
    p_search.add_argument("--field", default=None, help="指定著录字段名（配合 --value；单独给=只筛有此字段的条目）")
    p_search.add_argument("--value", default=None, help="字段取值模糊匹配（不配 --field 时按全字段匹配）")
    p_search.add_argument("--person", default=None, help="人物姓名或 person_id")
    p_search.add_argument("--date-from", default=None, help="起始日期（含，W3CDTF）")
    p_search.add_argument("--date-to", default=None, help="结束日期（含，W3CDTF）")
    p_search.add_argument("--media-type", default=None, help="媒体类型过滤")

    p_export = sub.add_parser("export", help="按白名单导出档案包（M5 实装）")
    p_export.add_argument("out", help="导出 JSON 文件路径")
    p_export.add_argument("--db", default=None, help="SQLite 库路径")
    p_export.add_argument("--whitelist", default=None, help="白名单 YAML（默认随包数据文件）")
    p_export.add_argument("--item", action="append", default=None, help="只导出指定条目（可重复；默认全部）")

    sub.add_parser("benchmark", help="合成样例基准断言（M4 实装）")

    p_profile = sub.add_parser("profile", help="查看著录 profile")
    profile_sub = p_profile.add_subparsers(dest="profile_command")
    p_show = profile_sub.add_parser("show", help="显示 profile 版本与规则出处")
    p_show.add_argument(
        "--path",
        default=None,
        help="profile YAML 路径（默认随包数据文件）",
    )
    return parser


def _cmd_profile(args: argparse.Namespace) -> int:
    profile = load_profile(args.path)
    print(f"profile_id : {profile['profile_id']}")
    print(f"version    : {profile['version']}")
    print(f"based_on   : {profile['based_on']}")
    print(f"rules      : {len(profile['rules'])} 条")
    for rule in profile["rules"]:
        print(f"  - {rule['id']:<12} {rule['type']:<10} {rule['field']:<10} [{rule['source']}]")
    return 0


def _cmd_import(args: argparse.Namespace) -> int:
    from pathlib import Path

    from famarchive.importer import import_directory, import_path
    from famarchive.store import DuplicateItemError, Store

    db_path = Path(args.db) if args.db else Path("archive.sqlite3")
    store = Store(db_path)
    try:
        target = Path(args.path)
        if target.is_dir():
            imported, skipped = import_directory(target, store, media_type=args.media_type)
        else:
            try:
                imported, skipped = [import_path(target, store, media_type=args.media_type)], []
            except DuplicateItemError as exc:
                print(f"跳过（重复指纹）: {exc}", file=sys.stderr)
                return 1
        for item in imported:
            print(f"已入库 {item['item_id']}  {item['file_name']}  sha256={item['sha256'][:12]}…")
        for path, reason in skipped:
            print(f"跳过 {path}: {reason}", file=sys.stderr)
        return 0 if imported else 1
    finally:
        store.close()


def _db_path_or_default(db_arg: str | None):
    from pathlib import Path

    return Path(db_arg) if db_arg else Path("archive.sqlite3")


def _cmd_validate(args: argparse.Namespace) -> int:
    from datetime import datetime, timezone

    from famarchive.store import Store
    from famarchive.validator import validate

    profile = load_profile()
    store = Store(_db_path_or_default(args.db))
    try:
        if args.save_history:
            store.record_profile_version(
                version=profile["version"],
                based_on=profile["based_on"],
                recorded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            )
        items = store.list_items()
        if args.item:
            item = store.get_item(args.item)
            items = [item] if item else []
        if not items:
            print("库内无档案项，无可校验对象")
            return 0
        exit_code = 0
        for item in items:
            fields = store.get_metadata_fields(item["item_id"])
            results = validate(fields, profile)
            print(f"{item['item_id']}  {item['file_name']}  著录字段 {len(fields)} 项")
            if not fields:
                print("  （未编目：必填字段全部缺失）")
            for r in results:
                print(f"  [{r['severity']}] {r['rule_id']} {r['field']}: {r['message']}")
                print(f"      出处: {r['source']}")
            if any(r["severity"] == "error" for r in results) or not fields:
                exit_code = 1
        return exit_code
    finally:
        store.close()


def _cmd_persons(args: argparse.Namespace) -> int:
    import uuid

    from famarchive.persons import find_same_name_persons, load_relation_type_ids
    from famarchive.store import Store

    store = Store(_db_path_or_default(args.db))
    try:
        if args.add:
            name, relation = args.add
            person = store.add_person(
                person_id=f"person-{uuid.uuid4().hex[:8]}",
                name=name,
                relation=None if relation == "-" else relation,
            )
            print(f"已登记人物 {person['person_id']}  {person['name']}")
        if args.link:
            pid, item_id, role = args.link
            store.link_person_item(pid, item_id, None if role == "-" else role)
            print(f"已链接 {pid} ↔ {item_id}（role={role}）")
        if args.relation:
            frm, to, rtype = args.relation
            allowed = load_relation_type_ids()
            if rtype not in allowed:
                print(
                    f"relation_type {rtype!r} 不在 relation-type 词表内（允许 {sorted(allowed)}）",
                    file=sys.stderr,
                )
                return 2
            store.add_relation(frm, to, rtype)
            print(f"已添加关系 {frm} → {to} : {rtype}")
        if args.merge:
            keep, drop = args.merge
            store.confirm_same_name_merge(keep, drop)
            print(f"同名合并完成：{drop} → {keep}")

        # 默认动作：列出人物索引与同名报告
        persons = store.list_persons()
        print(f"人物 {len(persons)} 人：")
        for p in persons:
            print(f"  {p['person_id']}  {p['name']}" + (f"（{p['relation']}）" if p["relation"] else ""))
        groups = find_same_name_persons(store)
        if groups:
            print("同名待人工确认（不自动合并）：")
            for g in groups:
                ids = " / ".join(p["person_id"] for p in g)
                print(f"  [{g[0]['name']}] {ids}")
        return 0
    finally:
        store.close()


def _cmd_timeline(args: argparse.Namespace) -> int:
    from famarchive.persons import build_timeline
    from famarchive.store import Store

    profile = load_profile()
    store = Store(_db_path_or_default(args.db))
    try:
        events = build_timeline(store, profile)
        print(f"家庭年表（编目完成 {len(events)} 件 / 库内 {store.count('archive_items')} 件）：")
        for ev in events:
            persons = "、".join(ev["persons"]) or "—"
            print(f"  {ev['date']}  {ev['title'] or '（无标题）'}  人物：{persons}  [{ev['item_id']}]")
        return 0
    finally:
        store.close()


def _cmd_gui(args: argparse.Namespace) -> int:
    from famarchive.gui import run_gui

    return run_gui(str(_db_path_or_default(args.db)))


def _cmd_search(args: argparse.Namespace) -> int:
    from famarchive.search import Query, search
    from famarchive.store import Store

    query = Query(
        text=args.text,
        field_name=args.field,
        field_value=args.value,
        person=args.person,
        date_from=args.date_from,
        date_to=args.date_to,
        media_type=args.media_type,
    )
    store = Store(_db_path_or_default(args.db))
    try:
        results = search(store, query)
        cond = "、".join(
            f"{k}={v}" for k, v in {
                "关键词": args.text, "字段": args.field, "取值": args.value,
                "人物": args.person, "起": args.date_from, "止": args.date_to,
                "媒体类型": args.media_type,
            }.items() if v
        ) or "无条件（全部条目）"
        print(f"检索条件：{cond}；命中 {len(results)} 件：")
        for r in results:
            f = r["fields"]
            print(f"  {r['item_id']}  {f.get('title') or '（无标题）'}  "
                  f"{f.get('date') or '—'}  {r['media_type']}  "
                  f"人物：{'、'.join(r['persons']) or '—'}")
        return 0
    finally:
        store.close()


def _cmd_export(args: argparse.Namespace) -> int:
    from famarchive.exporter import export_package
    from famarchive.store import Store

    profile = load_profile()
    store = Store(_db_path_or_default(args.db))
    try:
        manifest = export_package(
            store, args.out, profile,
            whitelist_path=args.whitelist,
            item_ids=args.item,
        )
        print(f"导出完成 {args.out}")
        print(f"  export_id={manifest['export_id']}  条目 {manifest['item_count']} 件")
        print(f"  profile v{manifest['profile_version']}  白名单 v{manifest['whitelist_version']}  "
              f"导出时间 {manifest['exported_at']}")
        print(f"  抹除字段（导出文件中键不出现）：{'、'.join(manifest['erased_fields'])}")
        return 0
    finally:
        store.close()


def _cmd_benchmark(args: argparse.Namespace) -> int:
    from famarchive.benchmark import run_benchmark

    report = run_benchmark()
    manifest = report["manifest"]
    print(f"合成样例基准（manifest v{manifest['manifest_version']}，生成器单一来源）")
    print(f"假名白名单 {len(manifest['fake_name_whitelist'])} 人名 | "
          f"证件号占位段 {manifest['placeholders']['id_number'][:6]} | "
          f"电话假号段 {manifest['placeholders']['phone'][:3]}")
    print(f"样例 {len(manifest['samples'])} 件：")
    for s in manifest["samples"]:
        exp = ",".join(s["expected_errors"]) or "—"
        print(f"  {s['sample_id']:<18} {s['media_type']:<14} 预期触发: {exp}")
    print("断言（plan/04 §2 七类异常）：")
    for row in report["assertions"]:
        print(f"  [{row['status']}] {row['category']}: {row['detail']}")
    if not report["passed"]:
        print("基准断言未全部通过", file=sys.stderr)
        return 1
    print("覆盖度口径（写进 manifest，不写硬数字）：")
    for cat, desc in manifest["coverage"].items():
        print(f"  {cat}: {desc}")
    print("基准全部通过")
    return 0


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "import":
        return _cmd_import(args)
    if args.command == "validate":
        return _cmd_validate(args)
    if args.command == "persons":
        return _cmd_persons(args)
    if args.command == "timeline":
        return _cmd_timeline(args)
    if args.command == "gui":
        return _cmd_gui(args)
    if args.command == "search":
        return _cmd_search(args)
    if args.command == "export":
        return _cmd_export(args)
    if args.command == "benchmark":
        return _cmd_benchmark(args)
    if args.command == "profile":
        if args.profile_command == "show":
            return _cmd_profile(args)
        p_profile = parser.parse_args(["profile", "--help"])
        return 0
    if args.command is None:
        parser.print_help()
        return 0
    print(f"子命令 {args.command!r} 尚未实装（见 plan/05 里程碑计划）", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
