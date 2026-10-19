# plan/HANDOFF-M4.md — 下一阶段交接快照

> 状态：M3 著录规则与人物已收尾 · 2026-10-14 · 下一棒：M4 基准（模块 5）
> 续接提示词：`/goal 读取 <项目绝对路径>\plan\HANDOFF-M4.md 继续完成任务`（绝对路径只出现在用户侧启动命令，本文件库内一律相对路径）

## 1. 当前进度与证据

- **M3 全部收尾**：
  - `validator.py`：profile 驱动三类规则校验——required（必填缺失，空白串也算缺）/ vocabulary（词表越界，按 `vocab_source` 读 src/famarchive/data/vocabularies/ 数据文件）/ format（W3CDTF：YYYY / YYYY-MM / YYYY-MM-DD / 带时区 datetime，**含日历语义检查**，`1963-13`、`1963/05/02` 均拒绝）。结果逐条 `{rule_id, field, severity, message, source}`（K1 出处透出）。规则不硬编码：自造 profile 文件也能驱动校验（测试锁定）。
  - `persons.py` + `store.py`：`add_relation_checked` 关系边限 relation-type 词表（越界 ValueError）；`find_same_name_persons` 同名**只报告不合并**，合并必须走显式 `store.confirm_same_name_merge`（链接与关系边随迁、自环清理）；`build_timeline` 年表只收编目完成项（必填齐 + 零 error，按 date 升序）。
  - GUI 三页实装（`famarchive gui --db` 启动）：编目页（profile 驱动表单、逐字段校验提示挂出处、EXIF 建议仅点"采纳"进表单且仍须过校验保存——K5 唯一写入路径）/ 人物页（索引、词表下拉关系边、同名合并确认对话框）/ 年表页（只显编目完成项）。PySide6 6.12.0 已装入 venv，offscreen 冒烟三页全链路通过（校验拦截→修正→保存落库→同名合并→年表刷新）。
  - CLI 四子命令：`validate`（无 error 才 exit 0，`--save-history` 登记 profile_history）、`persons`（--add/--link/--relation/--merge）、`timeline`、`gui`。
  - profile **v0.2.0**：description、coverage 由可选提升必填（新增 REQ-DESCRIPTION/REQ-COVERAGE 挂项目自建出处；VOC-TYPE 补 `vocab_source: media-type` 键——vocabulary 规则校验器按此读词表）；v0.1.0-draft 全文留档 `src/famarchive/data/profiles/archived/dcmi-family-profile-v0.1.0-draft.yaml`，两版本必填集实质可区分（K6，测试锁定）。
- 证据：`pytest` **34 passed**（M2 后 21 + M3 新增 13：三类规则逐条出处断言 / W3CDTF 合法非法形态表 / 自造 profile 驱动 / 关系词表越界拒绝 / 同名不自动合并 / 年表拦截未编目项 / v0.2.0↔v0.1.0 必填集可区分 / profile_history 登记）。CLI 端到端冒烟（导入 2 件 → 一件编目全 → validate 拦截另一件含出处错误行 → 人物/链接/关系词表拒绝 → 年表只出 1 件）通过。

## 2. 下一里程碑待办（M4 基准，plan/04 §2）

- [ ] `benchmark.py`：合成样例生成器（人名只从 `src/famarchive/data/vocabularies/假名白名单.yaml` 取，证件号 999999 段、电话 199 段）+ 真值 manifest 单一来源
- [ ] 断言清单按 plan/04 §2 七类异常类型全覆盖（缺失/越界/格式/重复/敏感字段/同名/未编目——以 plan/04 实际清单为准）
- [ ] CLI `benchmark` 子命令实装（现为占位桩）
- [ ] DoD：`pytest` + `famarchive benchmark` 复跑通过；覆盖度口径进 manifest

## 3. 既定口径清单（动了会打挂测试）

- **K1–K9 全部沿用**（见 plan/HANDOFF-M2.md/M3.md 与测试；核心不变项）：
  - K1 规则出处强制：profile 规则缺 `source` 加载即 ValueError；
  - K2 必备键集：profile = `profile_id/version/based_on/rules`，规则 = `id/field/type/severity/source`，类型枚举 `required/vocabulary/format`；**M3 增补**：vocabulary 规则可带 `vocab_source`（词表文件名去 .yaml）；
  - K3 词表文件名按名断言（media-type/relation-type/假名白名单/dcmi-type.yaml）；
  - K5 EXIF 纪律：EXIF 只进建议队列，唯一写入路径 = GUI"采纳"（仍须过校验保存）/人工确认；
  - K6 版本化：profile 现行 **v0.2.0**，与 archived/v0.1.0-draft 必填集实质可区分（description/coverage 差集，测试 `test_archived_v010_exists_and_is_distinguishable` 锁定）——**再改 profile 须同步升级版本号并留档 archived/**；
  - K9 指纹唯一在库层、metadata_fields.value 为 JSON 字符串。
- **M3 新增 K10（年表门槛）**：年表只收"必填齐 + 零 error"的档案项，date 缺失也不进——改动须同步 `build_timeline` + 测试。
- **M3 新增 K11（同名合并纪律）**：`confirm_same_name_merge` 只能由人工确认路径（GUI 对话框 / CLI `--merge`）调用，任何自动流程不得调用。

## 4. 本机环境坑（只写实测过的）

- `python` 命令不可用（商店占位符）；**统一走 `py -3.12` 建的 `.venv`**，命令用 `.venv/Scripts/python.exe` / `.venv/Scripts/famarchive.exe`，安装用 `python -m pip`。
- **Git Bash `/tmp` 与 Windows Python 路径不一致**（/tmp 映射到 %LOCALAPPDATA%/Temp，但 import 等相对解析会踩空）——冒烟临时文件放项目内目录（如 `.smoke/`，用完即删，已在 .gitignore 外注意别提交）。
- GUI 无头冒烟用 `QT_QPA_PLATFORM=offscreen`；PySide6 offscreen 会报 QFontDatabase 字体目录警告，可忽略不影响断言。
- pillow 12.3.0、PySide6 6.12.0 已装入 venv（均为可选依赖，运行时缺失优雅降级/可读提示）。
- 网络坑（M1 实测，M2/M3 期间无新增）：purl.archive.org 阻断走 dublincore.org + api.github.com；openstd 站点级封锁勿重试；flk 验证码死路。

## 5. DoD 逐项 checklist（M4）

- [ ] 合成样例生成器只从假名白名单取人名；证件号/电话占位段合规（999999/199）
- [ ] 真值 manifest 单一来源（生成器同源产出，非手抄）
- [ ] plan/04 §2 七类异常断言全覆盖（逐类有对应测试/断言函数）
- [ ] `famarchive benchmark` CLI 子命令实装且复跑通过
- [ ] 覆盖度口径写进 manifest
- [ ] 收尾：pytest 复跑全绿 → plan/00/05 状态回写 → **写 plan/HANDOFF-M5.md（本对话内，先落盘再结束）** → commit

## 6. 关键命令速查

```bash
cd <项目根>                                            # 仓库根（用户侧拼绝对路径）
.venv/Scripts/python -m pytest -v                      # 全量测试（M3 后 34 项）
.venv/Scripts/famarchive.exe import <文件或目录> --media-type photo-scan --db archive.sqlite3
.venv/Scripts/famarchive.exe validate [--item ID] [--save-history] --db archive.sqlite3   # exit 0 = 全部无 error
.venv/Scripts/famarchive.exe persons --db archive.sqlite3 [--add 名 称谓] [--link 人物 条目 角色] [--relation 从 到 类型] [--merge 保留 删除]
.venv/Scripts/famarchive.exe timeline --db archive.sqlite3
.venv/Scripts/famarchive.exe gui --db archive.sqlite3  # 桌面 GUI 三页（需 .[gui]）
.venv/Scripts/famarchive.exe profile show              # profile 版本与规则出处（现 v0.2.0）
QT_QPA_PLATFORM=offscreen .venv/Scripts/python -c "…"  # GUI 无头冒烟模式
.venv/Scripts/python -m pip install -e .[exif,gui]     # pillow / PySide6 可选依赖（均已装）
git log --format="%ae %ce" --all | sort -u             # 提交元数据核验（应仅 noreply）
```

## 7. 里程碑收尾出口纪律（对下一棒同样生效）

每个里程碑 DoD 达成后，**必须在本对话内写完下一阶段 HANDOFF-M<next> 才允许结束对话**（六节齐：进度证据/待办/既定口径/环境坑/DoD/命令速查）；库内一律相对路径；收尾顺序 = DoD 验证 → plan/00·05 状态回写 → HANDOFF 落盘 → commit。
