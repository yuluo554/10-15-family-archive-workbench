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

    sub.add_parser("import", help="导入本地文件夹/文件为档案项（M2 实装）")
    sub.add_parser("validate", help="按 DCMI profile 校验著录字段（M3 实装）")
    sub.add_parser("persons", help="人物索引与代际关系（M3 实装）")
    sub.add_parser("timeline", help="家庭年表视图（M3 实装）")
    sub.add_parser("search", help="字段/人物/时间/媒体类型组合检索（M5 实装）")
    sub.add_parser("export", help="按白名单导出档案包（M5 实装）")
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


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
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
