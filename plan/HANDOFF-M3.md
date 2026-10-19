# plan/HANDOFF-M3.md — 下一阶段交接快照

> 状态：M2 导入解析已收尾 · 2026-10-14 · 下一棒：M3 著录规则与人物（模块 2/3）
> 续接提示词：`/goal 读取 <项目绝对路径>\plan\HANDOFF-M3.md 继续完成任务`（绝对路径只出现在用户侧启动命令，本文件库内一律相对路径）

## 1. 当前进度与证据

- **M2 全部收尾**：
  - `store.py`：SQLite 单文件库（`Store` 类），plan/02 §3 七表全落齐（archive_items / metadata_fields / persons / person_item_links / person_relations / profile_history / export_manifests）；`archive_items.sha256 UNIQUE` 约束在**库层**生效（`add_item` 遇同指纹抛 `DuplicateItemError`，`find_by_sha256` 可查重）；`set_metadata_fields/get_metadata_fields` 供 M3 校验器与录入使用。
  - `importer.py`：`import_path`（单文件）/`import_directory`（批量，单文件失败不中断）同一录入路径；支持 jpg/jpeg/png/tif/tiff/bmp；`media_type` 强制校验在 media-type 词表内；缩略图 256px JPEG（pillow 可选，缺 pillow / 非图像优雅降级返回 None）；EXIF 读出进 `exif_snapshot` + `exif_suggestions` 建议队列（每条 `needs_confirmation: true`），**永不写 metadata_fields（K5）**。
  - CLI `import` 子命令实装：`famarchive import <path> --media-type <id> [--db <sqlite>]`，目录批量时重复指纹逐条跳过并 exit 1。
  - pillow 12.3.0 已装入 venv（开发态验证用；运行时缺失也不崩）。
- 证据：`pytest` **21 passed**（原 9 项烟囱 + M2 新增 12 项：指纹唯一/重复拒绝/K5 断言/无 EXIF 同路径/批量去重/词表越界拒绝/库层直插同指纹拒绝等）；CLI 端到端冒烟（导入 2 件 → 重导全跳 → `metadata_fields` 0 行）通过。

## 2. 下一里程碑待办（M3 著录规则与人物，plan/05）

- [ ] `validator.py`：profile 驱动的必填/词表/W3CDTF 校验，逐条挂出处（结果结构 `{rule_id, field, severity, message, source}`，见 plan/02 §4；W3CDTF = YYYY / YYYY-MM / YYYY-MM-DD / 带时区 datetime）
- [ ] `persons.py`：人物标注、关系边（取值限 relation-type 词表）、同名人工确认、家庭年表
- [ ] GUI 编目页/人物页/年表页（PySide6，可选依赖 `.[gui]`）
- [ ] profile v0.2.0 实质变更演示：必填/可选集与 v0.1.0 **实质可区分**（K6），历史版本进 `src/famarchive/data/profiles/archived/`
- [ ] DoD：校验规则逐条标出处；profile 版本化成立

## 3. 既定口径清单（动了会打挂测试）

- **K1 profile 规则出处强制**：`profile.py` 对缺 `source` 的规则抛 ValueError（`test_profile_rejects_rule_without_source` 锁死）；新规则必须带出处。
- **K2 必备键集**：profile 必备键 = `profile_id / version / based_on / rules`，规则必备键 = `id / field / type / severity / source`，规则类型枚举 = `required / vocabulary / format`——改口径须同步 loader + 测试 + plan/02 三处。
- **K3 词表文件名**：`src/famarchive/data/vocabularies/{media-type,relation-type,假名白名单,dcmi-type}.yaml`，测试按名断言——改名须同步测试；dcmi-type.yaml 改内容须改 `scripts/extract_dcmi_type.py` 重跑（禁手抄）。
- **K4 抹除语义**：白名单外字段导出时**不出现**（非置空）——M5 exporter 实装时不得偏离。
- **K5 EXIF 纪律（M2 已实装锁定）**：`test_exif_goes_to_suggestions_only` 断言导入后 `metadata_fields` 表 0 行；后续任何路径（含 GUI 预填）都只能把建议值经**人工确认**后写入著录字段。
- **K6 版本化承诺**：profile v0.2.0 必须与 v0.1.0 必填/可选集实质可区分（M3 DoD）。
- **K7 CI 矩阵**：ubuntu+windows × py3.10/3.12，env 带 `PYTHONUTF8=1`，checkout `fetch-depth: 0`。
- **K8 DCMI 词表**：转写只认 `scripts/extract_dcmi_type.py` 单一来源；data/raw/dcmi 快照与 data/README.md 登记绑定（`test_dcmi_raw_snapshot_registered` 同时断言 README 含 `dcmi/vocabtool` 与 `CC-BY`）。
- **K9 M2 新增**：`media_type` 取值必须校验在 media-type 词表内（`importer._load_media_type_ids`）；指纹唯一约束在**库层**（`archive_items.sha256 UNIQUE` + `store.add_item` 主动查重双重防护），不要只靠导入层；`metadata_fields.value` 以 JSON 字符串存储（`set/get_metadata_fields` 已封装序列化）。

## 4. 本机环境坑（只写实测过的）

- `python` 命令不可用（商店占位符）；**项目开发统一走 `py -3.12` 建的 `.venv`**。
- venv 内命令一律用 `.venv/Scripts/python.exe` / `.venv/Scripts/famarchive.exe`（Git Bash 相对路径可跑）；venv 内安装/运行一律 `python -m pip`。
- 网络坑（M1 实测，M2 期间无新增）：
  - `purl.archive.org` TCP 直连阻断 → DCMI RDF 走 dublincore.org 主站 + `api.github.com`（带 `Accept: application/vnd.github.raw` 头）。
  - `openstd.samr.gov.cn` 站点级封锁（showGb 302 至拦截页）：封锁解除或换网络后重跑 `scripts/fetch_gbt11821.py`，被拦截时勿重试。
  - `flk.npc.gov.cn` 检索 API 须人机验证码，无头脚本死路。
- Windows Git Bash 下 `filter-branch` 输出接管道有杀进程风险——重写直跑 + 重定向文件。

## 5. DoD 逐项 checklist（M3）

- [ ] `validator.py`：校验结果逐条含 `{rule_id, field, severity, message, source}`；必填缺失/词表越界/W3CDTF 格式三类规则全部可触发并被测试锁定
- [ ] `persons.py`：人物标注 + 关系边限 relation-type 词表 + 同名人工确认路径 + 家庭年表
- [ ] GUI 三页（编目/人物/年表）可达（CLI 全链路先行可用，GUI 按 plan/05 增量补齐）
- [ ] profile v0.2.0：与 v0.1.0 必填/可选集实质可区分；旧版进 `src/famarchive/data/profiles/archived/`
- [ ] 收尾：pytest 复跑全绿 → plan/00/05 状态回写 → **写 plan/HANDOFF-M4.md（本对话内，先落盘再结束）** → commit

## 6. 关键命令速查

```bash
cd <项目根>                                            # 仓库根（用户侧拼绝对路径）
.venv/Scripts/python -m pytest -v                      # 全量测试（M2 后 21 项）
.venv/Scripts/famarchive.exe import <文件或目录> --media-type photo-scan --db archive.sqlite3
.venv/Scripts/famarchive.exe profile show              # profile 版本与规则出处
.venv/Scripts/python scripts/extract_dcmi_type.py      # 重转写 dcmi-type.yaml（改脚本后跑）
.venv/Scripts/python scripts/fetch_gbt11821.py         # GB/T 页图抓取（封锁解除后重跑）
.venv/Scripts/python -m pip install -e .[dev]          # 依赖变更后重装
.venv/Scripts/python -m pip install -e .[exif,gui]     # pillow / PySide6 可选依赖
git log --format="%ae %ce" --all | sort -u             # 提交元数据核验（应仅 noreply）
```

## 7. 里程碑收尾出口纪律（对下一棒同样生效）

每个里程碑 DoD 达成后，**必须在本对话内写完下一阶段 HANDOFF-M<next> 才允许结束对话**（六节齐：进度证据/待办/既定口径/环境坑/DoD/命令速查）；库内一律相对路径；收尾顺序 = DoD 验证 → plan/00·05 状态回写 → HANDOFF 落盘 → commit。
