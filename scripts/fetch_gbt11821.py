"""GB/T 11821-2002 在线预览逐页抓取 → data/raw/gbt11821/（M1 落地脚本）。

来源：openstd.samr.gov.cn 在线预览（WebP 逐页图，非静态全文，须持
showGb 会话 cookie 访问 viewGbImg）。页面图像仅作人工核对底稿，
不做 OCR 转写；条文核对走人工，台账见 data/README.md。

用法：.venv/Scripts/python scripts/fetch_gbt11821.py [最大页数]
"""

from __future__ import annotations

import http.cookiejar
import re
import ssl
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "data" / "raw" / "gbt11821"
HCNO = "6274733E32F53D7C89E868771A13748C"
BASE = "https://openstd.samr.gov.cn"
VIEW_URL = f"{BASE}/bzgk/std/showGb?type=online&hcno={HCNO}&request_locale=zh_CN"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"


def build_opener() -> urllib.request.OpenerDirector:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    cj = http.cookiejar.CookieJar()
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj),
        urllib.request.HTTPSHandler(context=ctx),
    )


def main() -> None:
    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    op = build_opener()
    op.addheaders = [("User-Agent", UA)]

    info_url = f"{BASE}/bzgk/std/newGbInfo?hcno={HCNO}"
    # 服务端校验 Referer：showGb 必须带 newGbInfo 来源，否则 302 回详情页；
    # 偶发连接被服务端直接断开，统一带重试
    def fetch(url: str, referer: str | None = None) -> bytes:
        last_err: Exception | None = None
        for attempt in range(3):
            headers = {"Referer": referer} if referer else {}
            req = urllib.request.Request(url, headers=headers)
            try:
                return op.open(req, timeout=90).read()
            except (urllib.error.URLError, ConnectionError, OSError) as e:
                last_err = e
                time.sleep(2)
        raise SystemExit(f"重试 3 次仍失败：{url}（{last_err}）")

    fetch(info_url)
    html = fetch(VIEW_URL, referer=info_url).decode("utf-8", "ignore")
    bgs = re.findall(r'bg="([^"]+)"', html)
    if not bgs:
        raise SystemExit("预览页无 bg 令牌：页面结构可能已变，拒抓")
    # 同一 bg 令牌对应同一文件，页号由 viewGbImg 302 到 data/.../页码.webp 决定
    # 每页独立 bg 令牌（页级防爬 token），逐页换令牌
    page_tokens: dict[int, str] = {}
    for bg in dict.fromkeys(bgs):
        final_url = None
        for attempt in range(3):
            req = urllib.request.Request(
                f"{BASE}/bzgk/std/viewGbImg?fileName={bg}", headers={"Referer": VIEW_URL}
            )
            try:
                r = op.open(req, timeout=90)
                final_url = r.geturl()
                r.read()
                break
            except (urllib.error.URLError, ConnectionError, OSError) as e:
                print(f"令牌解析第 {attempt + 1} 次失败：{e}")
                time.sleep(2)
        if not final_url:
            raise SystemExit("bg 令牌解析失败（重试耗尽）")
        m = re.search(r"/([0-9-]+)_([A-Za-z0-9]+)\.webp$", final_url)
        if not m:
            raise SystemExit(f"302 目标异常：{final_url}")
        page_no = int(m.group(1).rsplit("-", 1)[-1])
        page_tokens[page_no] = m.group(2)
    if not page_tokens:
        raise SystemExit("未解析出任何页令牌")
    print(f"已解析页令牌：{sorted(page_tokens)}")

    pages = 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for page_no in sorted(page_tokens):
        for attempt in range(3):
            url = f"{BASE}/bzgk/data/2315-3274-{page_no}_{page_tokens[page_no]}.webp"
            try:
                data = fetch(url, referer=VIEW_URL)
                if data:
                    break
            except SystemExit:
                data = b""
                print(f"页 {page_no} 第 {attempt + 1} 次失败")
                time.sleep(2)
        else:
            data = b""
        if not data:
            print(f"页 {page_no}：重试后仍 0 字节，停止")
            break
        out = OUT_DIR / f"page-{page_no:02d}.webp"
        out.write_bytes(data)
        pages += 1
        print(f"页 {page_no}：{len(data)} 字节 ✓")
        time.sleep(1)
    print(f"共抓 {pages} 页 → {OUT_DIR}")
    if pages == 0:
        raise SystemExit("未抓到任何页面")


if __name__ == "__main__":
    main()
