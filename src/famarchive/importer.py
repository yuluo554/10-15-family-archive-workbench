"""模块 1：档案项导入（混合媒体类型）—— M2 实装。

确定性纪律（plan/01 题目文档）：
- 照片扫描件（JPEG/TIFF/PNG）、家书/文献/证件扫描页同一录入路径；
- EXIF 仅作预填建议（pillow 可选解析），永不自动写入著录字段（K5）；
- 文件指纹（SHA-256）保证同件不重复入库。
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from famarchive.resources import vocabularies_dir
from famarchive.store import Store

# 支持的图像/扫描文件扩展名（照片扫描件与文书/证件扫描页共用录入路径）
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}

THUMBNAIL_SIZE = (256, 256)

# EXIF 键（若存在）→ DCMI 预填建议字段的映射。
# 仅生成"建议"，导入流程任何路径都不会把建议写入 metadata_fields（K5）。
_EXIF_SUGGESTION_MAP = {
    306: "date",      # DateTime
    36867: "date",    # DateTimeOriginal（优先级低于 36867 后写覆盖，仅建议）
    270: "description",  # ImageDescription
}

THUMBNAIL_SUBDIR = "thumbnails"


def _load_media_type_ids() -> set[str]:
    doc = _read_yaml(vocabularies_dir() / "media-type.yaml")
    return {v["id"] for v in doc["values"]}


def _read_yaml(path):
    import yaml

    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_exif(path: Path) -> dict:
    """读取 EXIF（pillow 可选依赖）；无 pillow / 无 EXIF / 非图像返回空 dict。"""
    try:
        from PIL import Image
    except ImportError:  # 优雅降级：缺 pillow 不影响导入主路径
        return {}
    try:
        with Image.open(path) as img:
            raw = img.getexif()
    except Exception:
        return {}
    if not raw:
        return {}
    return {k: str(v) for k, v in raw.items() if isinstance(v, (str, int))}


def exif_to_suggestions(exif: dict) -> list[dict]:
    """把 EXIF 快照转成预填建议队列（供人工确认，不自动落著录字段）。"""
    suggestions: list[dict] = []
    if not exif:
        return suggestions
    if 306 in exif:
        suggestions.append(
            {"field": "date", "suggested_value": exif[306],
             "origin": "EXIF DateTime (tag 306)", "needs_confirmation": True}
        )
    if 36867 in exif:
        suggestions.append(
            {"field": "date", "suggested_value": exif[36867],
             "origin": "EXIF DateTimeOriginal (tag 36867)", "needs_confirmation": True}
        )
    if 270 in exif and exif[270].strip():
        suggestions.append(
            {"field": "description", "suggested_value": exif[270],
             "origin": "EXIF ImageDescription (tag 270)", "needs_confirmation": True}
        )
    return suggestions


def make_thumbnail(path: Path, thumbnails_dir: Path) -> Path | None:
    """生成缩略图；缺 pillow 或非图像时返回 None（不抛错，导入主路径不受阻）。"""
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(path) as img:
            img = img.convert("RGB")
            img.thumbnail(THUMBNAIL_SIZE)
            thumbnails_dir.mkdir(parents=True, exist_ok=True)
            out = thumbnails_dir / f"{path.stem}.jpg"
            img.save(out, "JPEG", quality=85)
            return out
    except Exception:
        return None


def import_path(
    path: str | Path,
    store: Store,
    *,
    media_type: str,
    db_dir: Path | None = None,
    now: datetime | None = None,
) -> dict:
    """导入单个文件为档案项。

    无 EXIF 文件与有 EXIF 文件走完全同一路径；EXIF 结果只进
    exif_suggestions（建议队列），不进 metadata_fields（K5）。
    同 SHA-256 指纹二次导入抛 DuplicateItemError，不入库。
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(p)
    if p.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"不支持的文件类型: {p.suffix}（支持 {' '.join(sorted(SUPPORTED_EXTENSIONS))}）")
    allowed = _load_media_type_ids()
    if media_type not in allowed:
        raise ValueError(f"media_type {media_type!r} 不在 media-type 词表内（{sorted(allowed)}）")

    timestamp = (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")
    digest = sha256_file(p)
    item_id = f"item-{uuid.uuid4().hex[:12]}"

    exif = read_exif(p)
    suggestions = exif_to_suggestions(exif)
    thumb_dir = (db_dir or store.db_path.parent) / THUMBNAIL_SUBDIR
    thumb = make_thumbnail(p, thumb_dir)

    return store.add_item(
        item_id=item_id,
        media_type=media_type,
        sha256=digest,
        file_name=p.name,
        original_path=str(p),
        thumbnail_path=str(thumb) if thumb else None,
        exif_snapshot=exif or None,
        exif_suggestions=suggestions or None,
        imported_at=timestamp,
    )


def import_directory(
    dir_path: str | Path, store: Store, *, media_type: str, db_dir: Path | None = None
) -> tuple[list[dict], list[tuple[str, str]]]:
    """批量导入目录下全部受支持文件；返回 (成功项, [(路径, 失败原因)])。"""
    root = Path(dir_path)
    if not root.is_dir():
        raise NotADirectoryError(root)
    imported: list[dict] = []
    skipped: list[tuple[str, str]] = []
    for f in sorted(root.iterdir()):
        if not f.is_file() or f.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        try:
            imported.append(import_path(f, store, media_type=media_type, db_dir=db_dir))
        except Exception as exc:  # 单文件失败不中断批量
            skipped.append((str(f), str(exc)))
    return imported, skipped
