# plan/HANDOFF-M6.md — 下一阶段交接快照

> 状态：M5 交付已收尾 · 2026-10-14 · 下一棒：M6 发布（git tag + GitHub Release + 发布留档）
> 续接提示词：`/goal 读取 <项目绝对路径>\plan\HANDOFF-M6.md 继续完成任务`（绝对路径只出现在用户侧启动命令，本文件库内一律相对路径）

## 1. 当前进度与证据

- **M5 全部收尾**：
  - `search.py` 实装（原骨架桩删除）：`Query` dataclass 条件全可选（text/field_name+field_value/person/date_from+date_to/media_type/ids），`search(store, query)` 组合查询 AND 语义；关键词全字段模糊、指定字段按名匹配、人物按姓名或 person_id（同名全部并入）、W3CDTF 前缀截齐字典序比较时间范围；结果附著录字段与关联人物名。
  - `exporter.py` 实装（原占位桩删除）：`load_whitelist()` 读 data/export-whitelist.yaml（v0.1.0-draft，缺必备键报错）；`export_package()` 白名单驱动序列化循环（白名单外键根本不进循环）+ sensitive_fields **防御性再排除**（K13：抹除=键不出现，非置空）；manifest 记 profile v0.2.0 / 白名单版本 / 导出时间 / erased_fields / item_count，留痕写 `export_manifests` 表；支持 `item_ids` 子集导出。
  - CLI `search` / `export` 子命令实装（search：--text/--field/--value/--person/--date-from/--date-to/--media-type；export：位置参数 out + --whitelist + 可重复 --item）；main() 不再有"尚未实装"分支（全部子命令可达）。
  - GUI 五页补齐：新增 search_page.py（profile 驱动字段下拉+条件表单+结果表）、export_page.py（白名单/抹除字段展示+导出+manifest 预览）；gui.py 挂检索/导出两页为五页全链路；**修复 `run_gui` 里 `QApplication.setWindowTitle` 误用**（脚本模式死代码未暴露，exe 内首跑即崩，已删）。
  - PyInstaller 打包：`famarchive.spec` 单文件 exe（Analysis datas 把 data/profiles、data/vocabularies、export-whitelist.yaml 内嵌 `famarchive_data/`，hiddenimports collect_submodules('famarchive')）；`resources.data_dir()` 已有 sys._MEIPASS 分支无需改动；exe 56.6 MB。sha256 留档 `plan/DIST-sha256-M5.txt`（`b67228c529f4…fab986`）。
- 证据：`pytest` **57 passed**（M4 后 47 + M5 新增 10：组合查询 AND 语义/人物/时间范围/字段值/空查询、白名单加载、K13 敏感键不出现、manifest 版本留痕+export_manifests 表、子集导出）。GUI offscreen 全链路冒烟通过（编目→人物→年表→检索关键词/人物→导出抹除）。**exe 内全链路实测**：`profile show`（读内嵌 profile v0.2.0）、`benchmark` 七类全过、`import`→`search`→`export`（manifest erased_fields 正确）→ `gui` 启动成功。

## 2. 下一里程碑待办（M6 发布，plan/05）

- [ ] GitHub 首推（此前从未推过远端，CI 一次都没跑过——M0 诚实口径，首推后据实回填真实 CI 结论与 run id，修正 plan/00 M0 行）
- [ ] git tag（建议 v0.1.0 或按用户口径）+ GitHub Release 附 release zip（dist/famarchive.exe + 源码包，本地留副本）
- [ ] release zip sha256 留档（沿用 plan/DIST-sha256-M5.txt 格式，建议另立 plan/DIST-sha256-M6.txt）
- [ ] plan/RELEASE-M6.md 发布留档（三件套之一）
- [ ] DoD：三件套（tag + Release 附产物 + RELEASE-M6.md）缺一即未达成；CI 首跑绿灯证据回填

## 3. 既定口径清单（动了会打挂测试）

- **K1–K14 全部沿用**（见 HANDOFF-M2/M3/M4/M5 前版与测试），M5 未新增版本级口径，但两条 M4 口径在 M5 落地实装：
  - **K13（敏感抹除="键不出现"）**：exporter 以 export-whitelist.yaml 的 sensitive_fields（gps/id-number/phone/biometric）为准，序列化循环只走 export_fields 且 sensitive_fields 防御性再排除——**白名单若把敏感键加进 export_fields 也导不出去**（test_export_sensitive_keys_absent 锁定）；manifest 里 erased_fields 登记本身含敏感键名，属登记非数据，断言勿把 manifest 当记录体查键。
  - **K12（基准真值单一来源）**：test_m5_search_export.py 的 fixture 直接消费 `generate_samples()` 植入库，不手抄第二份样例数据。
- **库层 JSON 字符串口径（K9 延伸）**：`metadata_fields.value`、`exif_snapshot`、`exif_suggestions` 在库层是 JSON 字符串，search/exporter 均经 `get_metadata_fields()`（内部 json.loads）消费，勿绕开直接 SELECT 后当 dict 用。
- **export_manifests 留痕**：export_package 每次导出 INSERT OR REPLACE 一行（export_id 随机 8 hex），测试锁定导出后表计数=1。

## 4. 本机环境坑（只写实测过的）

- `python` 命令不可用（商店占位符）；**统一走 `py -3.12` 建的 `.venv`**，命令用 `.venv/Scripts/python.exe` / `.venv/Scripts/famarchive.exe`，安装用 `python -m pip`。
- **Git Bash `/tmp` 与 Windows Python 路径不一致**——临时文件放项目内目录（如 `.smoke/`，用完即删，别提交；`.smoke/` 已在本次收尾删除）。benchmark/测试内部一律 `tempfile.TemporaryDirectory()` 或 pytest `tmp_path`。
- **Bash 工具每次调用后工作目录不保证回到项目根**（本对话实测多次 `cd .smoke` 后下一条命令仍在 .smoke 报 127）——每条命令开头显式 `cd /d/ProgramData/zcode/10-15-family-archive-workbench`。
- **exe 管道输出中文显示乱码**（Git Bash 管道下 cp936 解码 UTF-8 字节）：`_ensure_utf8_stdio` 已把 stdio 重配为 UTF-8，字节正确，仅 Git Bash 终端按 cp936 显示乱；结构化验证（读导出 JSON、grep 关键英文段）不受影响，勿据此改编码逻辑。
- PyInstaller 6.22.3 已装入 venv；**famarchive.spec 在 .gitignore（`*.spec`）内不入库**——M6 若需可复现打包，spec 内容已摘录进本节（Analysis datas 三项 + hiddenimports collect_submodules('famarchive') + EXE 单文件 console=True）；重新打包命令 `.venv/Scripts/python -m PyInstaller famarchive.spec --noconfirm`，产物 dist/famarchive.exe。
- **dist/、build/ 均 gitignore**：exe 本体不入 git，发布走 GitHub Release 附产物 + 本地留副本。
- GUI 无头冒烟用 `QT_QPA_PLATFORM=offscreen`（QFontDatabase 字体目录警告、propagateSizeHints 警告均可忽略）；**给 `run_gui` 做非阻塞冒烟**用 `QtWidgets.QApplication.exec = lambda *a, **k: 0` 打补丁后调用（exe 内 GUI 冒烟则后台起进程 + `tasklist //FI "IMAGENAME eq famarchive.exe"` 确认 + `taskkill //IM famarchive.exe //F`）。
- pillow 12.3.0、PySide6 6.12.0、PyInstaller 6.22.3 已装入 venv。
- 网络坑（M1 实测，M2–M5 无新增）：purl.archive.org 阻断走 dublincore.org + api.github.com；openstd 站点级封锁勿重试；flk 验证码死路。**M6 首推 GitHub 时注意 api.github.com 可用、git push 走正常远端。**

## 5. DoD 逐项 checklist（M6）

- [ ] git tag（本地打 tag 并推送）
- [ ] GitHub Release 附产物（release zip：exe + 源码包；本地留副本 + sha256 留档）
- [ ] plan/RELEASE-M6.md 发布留档
- [ ] 首推后 CI 真实结论回填（run id + 绿灯证据，修正 plan/00 M0 行"未接远端"口径）
- [ ] 收尾：pytest 复跑全绿 → plan/00/05 状态回写 → commit（M6 无下一里程碑 HANDOFF，M6 是最后一棒；若用户有后续需求再补）

## 6. 关键命令速查

```bash
cd <项目根>                                            # 仓库根（用户侧拼绝对路径）
.venv/Scripts/python -m pytest -v                      # 全量测试（M5 后 57 项）
.venv/Scripts/famarchive.exe benchmark                 # 独立复跑基准（七类断言 + 覆盖度输出；exit 1=有断言失败）
.venv/Scripts/famarchive.exe import <文件或目录> --media-type photo-scan --db archive.sqlite3
.venv/Scripts/famarchive.exe validate [--item ID] [--save-history] --db archive.sqlite3   # exit 0 = 全部无 error
.venv/Scripts/famarchive.exe persons --db archive.sqlite3 [--add 名 称谓] [--link 人物 条目 角色] [--relation 从 到 类型] [--merge 保留 删除]
.venv/Scripts/famarchive.exe timeline --db archive.sqlite3
.venv/Scripts/famarchive.exe search --db archive.sqlite3 [--text 关键词] [--field 字段 --value 值] [--person 人物] [--date-from 起] [--date-to 止] [--media-type 类型]
.venv/Scripts/famarchive.exe export <out.json> --db archive.sqlite3 [--whitelist x.yaml] [--item ID]…   # 白名单导出包+manifest，留痕 export_manifests
.venv/Scripts/famarchive.exe gui --db archive.sqlite3  # 桌面 GUI 五页（编目/人物/年表/检索/导出，需 .[gui]）
.venv/Scripts/famarchive.exe profile show              # profile 版本与规则出处（现 v0.2.0）
.venv/Scripts/python -m PyInstaller famarchive.spec --noconfirm   # 重新打包 exe（spec 不入库，内容见 HANDOFF §4）
sha256sum dist/famarchive.exe                          # 打包产物指纹核对
QT_QPA_PLATFORM=offscreen .venv/Scripts/python -c "…"  # GUI 无头冒烟模式
.venv/Scripts/python -m pip install -e .[exif,gui,pack,dev]       # 全可选依赖
git log --format="%ae %ce" --all | sort -u             # 提交元数据核验（应仅 noreply）
```

## 7. 里程碑收尾出口纪律（对下一棒同样生效）

每个里程碑 DoD 达成后，必须在本对话内写完下一阶段 HANDOFF-M<next> 才允许结束对话（六节齐：进度证据/待办/既定口径/环境坑/DoD/命令速查）；库内一律相对路径；收尾顺序 = DoD 验证 → plan/00·05 状态回写 → HANDOFF 落盘 → commit。**M6 为收官里程碑：无下一阶段 HANDOFF，改以 plan/RELEASE-M6.md 作为收官留档。**
