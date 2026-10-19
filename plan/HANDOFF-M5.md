# plan/HANDOFF-M5.md — 下一阶段交接快照

> 状态：M4 基准已收尾 · 2026-10-14 · 下一棒：M5 交付（模块 4 导出 + 检索 + 打包）
> 续接提示词：`/goal 读取 <项目绝对路径>\plan\HANDOFF-M5.md 继续完成任务`（绝对路径只出现在用户侧启动命令，本文件库内一律相对路径）

## 1. 当前进度与证据

- **M4 全部收尾**：
  - `benchmark.py` 实装（原占位桩删除）：
    - **合成样例生成器** `generate_samples()`：6 件样例（baseline-full / missing-required / vocabulary-out / bad-date-format / sensitive-carry / uncatalogued），每类 plan/04 §2 异常至少一件（不偏科）；人名只取 `src/famarchive/data/vocabularies/假名白名单.yaml` 的 names，证件号 999999 段、电话 199 段**占位段从词表文件读取**（`load_fake_name_whitelist`/`load_fake_placeholders`，不硬编码第二份）；
    - **真值单一来源**：manifest 里 `expected_errors` 与 `planted_fields` 由同一次生成推导产出（缺失样例必触发 REQ-*、基线零 error、bad-date 只触发 FMT-DATE 均测试锁定"非手抄"）；断言函数只消费生成结果，不自带期望值；
    - **断言** `ASSERTIONS` 七类（必填缺失/词表外取值/W3CDTF非法日期/敏感字段抹除/人物关系/指纹去重/EXIF纪律），CLI 与 pytest 共用同一实现（`run_benchmark()`，断言失败抛 AssertionError 转逐类 fail 行 + exit 1）；
    - **敏感抹除口径**：manifest `sensitive_export_plan` 登记 exported=False 的键（gps/id-number/phone/biometric），断言"键不出现于著录字段"+ 携带值落占位段；导出器 M5 落地后可直接消费此口径断言导出文件。
  - CLI `benchmark` 子命令实装：输出样例清单 + 七类断言逐类结果 + 覆盖度口径（断言失败 exit 1）。
  - **覆盖度口径进 manifest**：`coverage` 键按七类异常类型列断言内容，**不写随实现漂移的硬数字**（plan/04 §2 要求），测试锁定七类不缺项。
- 证据：`pytest` **47 passed**（M3 后 34 + M4 新增 13：生成器纪律人名/占位段、真值同源、七类逐项断言、覆盖度不缺项、断言注册表对齐七类、整体复跑）。`famarchive benchmark` 复跑七类全 pass。

## 2. 下一里程碑待办（M5 交付，plan/05）

- [ ] `search.py`（现为骨架）：组合查询（字段/人物/时间/媒体类型）
- [ ] `exporter.py`（现为占位桩）：白名单导出包（`src/famarchive/data/export-whitelist.yaml` v0.1.0-draft）+ manifest；**抹除=字段不出现，非置空**；断言消费 benchmark 的 sensitive_export_plan 口径
- [ ] GUI 检索页/导出页补齐，全链路 GUI 可达
- [ ] CLI `search`/`export` 子命令实装（现为占位桩，main() 走"尚未实装"分支）
- [ ] PyInstaller 打包 Windows exe（数据文件内嵌，`resources.py` 已有 sys._MEIPASS 分支），sha256 留档
- [ ] DoD：exe 内全链路可达（录入→编目→年表→检索→导出）；导出抹除断言通过

## 3. 既定口径清单（动了会打挂测试）

- **K1–K9、K10、K11 全部沿用**（见 plan/HANDOFF-M2.md/M3.md/M4 前版与测试）：
  - K1 规则出处强制；K2 profile/规则必备键集（vocabulary 规则可带 `vocab_source`）；K3 词表文件名按名断言；K5 EXIF 只进建议队列（benchmark EXIF 纪律断言再次锁定：导入后 metadata_fields 必为空）；K6 profile 现行 **v0.2.0**（再改须升版本号+留档 archived/）；K9 指纹唯一在库层、metadata_fields.value 为 JSON 字符串；
  - K10 年表门槛：只收"必填齐 + 零 error"项（benchmark 人物关系断言依赖此口径）；K11 同名合并只走人工确认路径。
- **M4 新增 K12（基准真值单一来源）**：manifest 的 expected_errors/planted_fields/coverage 必须由 `generate_samples()` 同源产出；人名取值域==假名白名单文件、占位段==词表文件键值。**在 benchmark.py 里手抄第二份期望值/绕过词表文件取人名会打挂 `test_manifest_truth_single_source`/`test_names_only_from_fake_whitelist`**。
- **M4 新增 K13（敏感抹除口径="键不出现"）**：sensitive_export_plan 中 exported=False 的键在导出文件中不得出现（非置空）；M5 exporter 断言必须沿用此口径，与 export-whitelist.yaml 的 sensitive_fields（gps/id-number/phone/biometric）一致。
- **M4 新增 K14（覆盖度口径不写硬数字）**：manifest.coverage 按异常类型描述覆盖项；七类键名（必填缺失/词表外取值/W3CDTF非法日期/敏感字段抹除/人物关系/指纹去重/EXIF纪律）被 `test_coverage_covers_all_seven_categories` 与 `test_assertion_registry_matches_seven_categories` 双锁。

## 4. 本机环境坑（只写实测过的）

- `python` 命令不可用（商店占位符）；**统一走 `py -3.12` 建的 `.venv`**，命令用 `.venv/Scripts/python.exe` / `.venv/Scripts/famarchive.exe`，安装用 `python -m pip`。
- **Git Bash `/tmp` 与 Windows Python 路径不一致**——临时文件放项目内目录（如 `.smoke/`，用完即删，别提交）。M4 benchmark 断言内部一律用 `tempfile.TemporaryDirectory()`（Windows 路径安全），外部脚本不要往 /tmp 塞冒烟文件。
- **库层 JSON 字符串坑**：`exif_suggestions`/`metadata_fields.value` 在库层是 JSON 字符串，消费前须 `json.loads`（M4 实测踩过：断言 EXIF 建议队列时直接迭代字符串报 TypeError）。
- GUI 无头冒烟用 `QT_QPA_PLATFORM=offscreen`（QFontDatabase 警告可忽略）。
- pillow 12.3.0、PySide6 6.12.0 已装入 venv；benchmark 两个依赖 pillow 的断言（指纹去重/EXIF纪律）缺 pillow 时优雅跳过（pytest 侧 skip），CI 无 pillow 环境不假红。
- 网络坑（M1 实测，M2–M4 无新增）：purl.archive.org 阻断走 dublincore.org + api.github.com；openstd 站点级封锁勿重试；flk 验证码死路。

## 5. DoD 逐项 checklist（M5）

- [ ] search.py 组合查询（字段/人物/时间/媒体类型）实装 + CLI/GUI 可达
- [ ] exporter.py 白名单导出包 + manifest（记 profile/白名单版本、导出时间）；敏感字段**键不出现**断言通过（衔接 K13）
- [ ] GUI 检索页/导出页补齐，全链路（录入→编目→年表→检索→导出）GUI 可达 + offscreen 冒烟
- [ ] PyInstaller 打包 Windows exe（数据文件内嵌），sha256 留档
- [ ] DoD：exe 内全链路可达；导出抹除断言通过
- [ ] 收尾：pytest 复跑全绿 → plan/00/05 状态回写 → **写 plan/HANDOFF-M6.md（本对话内，先落盘再结束）** → commit

## 6. 关键命令速查

```bash
cd <项目根>                                            # 仓库根（用户侧拼绝对路径）
.venv/Scripts/python -m pytest -v                      # 全量测试（M4 后 47 项）
.venv/Scripts/famarchive.exe benchmark                 # 独立复跑基准（七类断言 + 覆盖度输出；exit 1=有断言失败）
.venv/Scripts/famarchive.exe import <文件或目录> --media-type photo-scan --db archive.sqlite3
.venv/Scripts/famarchive.exe validate [--item ID] [--save-history] --db archive.sqlite3   # exit 0 = 全部无 error
.venv/Scripts/famarchive.exe persons --db archive.sqlite3 [--add 名 称谓] [--link 人物 条目 角色] [--relation 从 到 类型] [--merge 保留 删除]
.venv/Scripts/famarchive.exe timeline --db archive.sqlite3
.venv/Scripts/famarchive.exe gui --db archive.sqlite3  # 桌面 GUI 三页（需 .[gui]）
.venv/Scripts/famarchive.exe profile show              # profile 版本与规则出处（现 v0.2.0）
QT_QPA_PLATFORM=offscreen .venv/Scripts/python -c "…"  # GUI 无头冒烟模式
.venv/Scripts/python -m pip install -e .[exif,gui,pack]  # pillow / PySide6 / PyInstaller（M5 打包用）
git log --format="%ae %ce" --all | sort -u             # 提交元数据核验（应仅 noreply）
```

## 7. 里程碑收尾出口纪律（对下一棒同样生效）

每个里程碑 DoD 达成后，**必须在本对话内写完下一阶段 HANDOFF-M<next> 才允许结束对话**（六节齐：进度证据/待办/既定口径/环境坑/DoD/命令速查）；库内一律相对路径；收尾顺序 = DoD 验证 → plan/00·05 状态回写 → HANDOFF 落盘 → commit。
