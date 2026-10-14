# plan/02 — 数据底座与 DCMI profile 设计

> 状态：✅ 初稿 · 2026-10-14 · 对应里程碑 M1/M3
> 上游：plan/01-题目文档.md 模块 2；data/README.md 依据台账
> 纪律：凡引用标准条文的规则，未挂原文核对（✅）不得落库/生效/进入计算路径

## 1. 数据底座清单（M1 落地目标）

| 底座 | 落点 | 状态 | 处置 |
|---|---|---|---|
| DCMI Metadata Terms（15 核心元素 + terms + Type 词汇 + W3CDTF） | `data/raw/dcmi/`（页面快照 + `dublin_core_terms.nt` RDF） | ✅ 可直连，待下载 | M1 下载落库；profile 字段定义引用其元素名 |
| GB/T 11821-2002 全文 | `data/raw/gbt11821/` | ⬜ 预览可得/直连阻断 | 预览人工落地后录入；落地前仅作设计参考，不进计算路径 |
| CIPA EXIF 规范 PDF | `data/raw/cipa/` | ⬜ POST 0 字节阻断 | 扩展项，手动下载后才录入 |
| PIPL 条文 | 台账回填 | ⬜ 待核对 | 核对前仅作设计取向，不引用条文原文 |
| DA/T 54/50 | — | 不可获取 | 降级参考设计，不落库 |

## 2. profile 文件设计（招牌模式：版本化字段方案）

### 2.1 文件布局

```
data/profiles/
├── dcmi-family-profile.yaml        # 当前生效 profile（单一事实来源）
└── archived/                        # 历史版本留档（仅追加，不改历史）
```

### 2.2 profile 结构（YAML，带版本号）

```yaml
profile_id: dcmi-family-profile
version: 0.1.0-draft          # 语义化版本；0.x 期间字段方案可破坏性变更
based_on: DCMI Metadata Terms 2020-01-20   # 依据 + 查证状态挂 data/README.md
rules:
  - id: REQ-TITLE
    field: title               # DCMI term 本地名
    type: required             # required / vocabulary / format
    severity: error
    source: DCMI Terms dcterms:title   # 出处：DCMI spec 条目名（项目自建必填集）
  - id: VOC-TYPE
    field: type
    type: vocabulary
    vocab_source: dcmi-type    # 引用内置受控词表
  - id: FMT-DATE
    field: date
    type: format
    format: W3CDTF             # DCMI 的日期语法编码方案
```

三个规则类型：`required`（必填缺失拦截）、`vocabulary`（词表外取值拦截）、`format`（W3CDTF 格式拦截）。
每条规则必须有 `source` 字段标注出处（DCMI spec 条目名或"项目自建"），无出处不得落库。

### 2.3 受控词表（数据文件，与 profile 分离可复用）

```
data/vocabularies/
├── dcmi-type.yaml          # DCMI Type 词汇（从落库 RDF 提取，挂出处）
├── media-type.yaml         # 本项目媒体类型：photo-scan/letter/document/id-card/reprint
├── relation-type.yaml      # 模块 3 关系边类型：parent-child/spouse/grandparent-grandchild/sibling/other
└──假名白名单.yaml            # 合成样例人物名（data/README.md 第三节纪律）
```

### 2.4 版本史承诺（差异必须真实）

- v0.1.0-draft：最小可用集；后续至少一次实质性变更（如增加必填字段 `relation` 或调整词表）形成 v0.2.0，两个版本的**可选字段集与必填集实质可区分**，作为版本化差异演示；
- profile 加载器记录 `based_on` 与加载时间；导出 manifest 记录来源 profile 版本（模块 4）。

## 3. 档案库 schema（本地、零上传）

- **形态**：SQLite 单文件（`archive.sqlite3`），纯本地，无网络访问代码；
- **表**：
  - `archive_items`（条目 ID、媒体类型、文件 SHA-256 指纹、缩略图路径、EXIF 快照 JSON、录入时间）；
  - `metadata_fields`（条目 ID × 字段名 × 取值，随 profile 版本号）；
  - `persons`（人物 ID、姓名、称谓/代际）；
  - `person_item_links`（人物 × 档案项 × 关系）；
  - `person_relations`（人物 × 人物 × 关系边类型，取值限 relation-type 词表）；
  - `profile_history`（profile 版本变更记录）；
  - `export_manifests`（导出留痕：profile 版本、白名单版本、导出时间）。
- 同件不重复入库：SHA-256 指纹唯一约束；EXIF 仅作预填建议字段，永不自动写入著录字段。

## 4. 校验器设计（模块 2 核心）

- **一处定义多处引用**：校验器只读 profile 数据文件，规则不硬编码；
- 校验结果结构：`{rule_id, field, severity, message, source}`，逐条可回溯；
- 词表引用 vocabularies/ 下数据文件；日期校验实现 W3CDTF（YYYY / YYYY-MM / YYYY-MM-DD / 带时区 datetime，拒绝其他格式）。

## 5. 导出白名单文件（模块 4）

```
data/export-whitelist.yaml
```

- 白名单以数据文件定义、可审计；默认**排除** GPS、证件号类敏感字段（抹除 = 导出文件中字段不出现，而非置空）；
- 导出包内附 manifest：来源 profile 版本、白名单版本、导出时间。

## 6. M1 DoD 对照

| DoD 项 | 本设计的落点 |
|---|---|
| DCMI terms/RDF 落库 | `data/raw/dcmi/` 下载 + vocabularies/dcmi-type.yaml 提取 |
| GB/T 11821 全文获取落地 | data/raw/gbt11821/（人工预览落地） |
| 依据台账三态回填 | data/README.md 表格更新 |
| 每条引用规则挂原文出处 | profile rules[].source 字段 |
