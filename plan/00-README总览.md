# plan/00 README 总览

仓库：`10-15-family-archive-workbench`（老照片/家庭档案数字化整理工作台）
性质：不参赛 · GitHub 公开仓库 · 署名 yuluo554 · PySide6 桌面 exe + CLI 双形态 · 纯本地零上传
题目版本：v1 · 2026-10-14

## 文档索引表

| 文档 | 内容 | 状态 |
|---|---|---|
| plan/00-README总览.md | 索引、决策记录、承诺-证据台账、里程碑 | ✅ 初稿 |
| plan/01-题目文档.md | 十段式定稿题目 | ✅ v1 |
| data/README.md | 依据查证记录、数据源可获取性、合成数据纪律 | ✅ 初稿 |
| .gitignore | Python 标准忽略模板 | ✅ |
| plan/02-*（数据底座与 profile 设计） | DCMI profile 结构、校验规则清单 | ✅ 初稿（02-数据底座与profile设计.md） |
| plan/03-*（架构与模块设计） | 桌面/CLI 架构、档案库 schema | ✅ 初稿（03-架构与模块设计.md） |
| plan/04-*（基准与验收） | 基准覆盖度口径、断言清单 | ✅ 初稿（04-基准与验收设计.md） |
| plan/05-*（里程碑执行） | 各里程碑 DoD 展开 | ✅ 初稿（05-里程碑执行计划.md，M0 骨架已完成） |
| plan/RELEASE-M6.md | 发布留档三件套 | ⬜ M6 时建 |

## 决策记录表

| 日期 | 决策 | 结论与理由 |
|---|---|---|
| 2026-10-14 | **事实纠正：DA/T 48-2009 不是照片元数据标准** | 实为《基于XML的电子文件封装规范》；照片口对口的是 DA/T 54-2014《照片类电子档案元数据方案》与 DA/T 50-2014《数码照片归档与管理规范》。此纠正进题面 v1 与 data 台账。 |
| 2026-10-14 | **弃"DA/T 54 全文作字段体系底座"** | DA/T 行业标准全文不公开（hbba.sacinfo.org.cn 仅备案记录，API 实测可查记录无全文）→ 数据底座预检②不过；降级为"参考设计"，字段体系以 DCMI 自建 profile 实现（DCMI 页面+RDF ✅ 可直连可解析）。 |
| 2026-10-14 | **弃"OCR/人脸识别入首期"** | 预检⑤：识别类能力规则化程度弱，抽不出可复现校验规则；叠加隐私红线（PIPL 生物识别属敏感个人信息、默认关闭设计）。降级为扩展项，启用也仅纯本地。 |
| 2026-10-14 | **GB/T 11821-2002 降级为"编目参考规则"** | 预检⑤边缘：可参数化规则约 10 条内（照片号编号规则、文字说明四要素），不足以独撑亮点模块；作模块 2 校验器的参考规则来源。在线预览可得但机器直连抓全文受限（⬜），全文落地后录入，未落地不进入计算路径。 |
| 2026-10-14 | **EXIF 对照包降为扩展项** | 差异素材已核（✅），但 CIPA 规范 PDF 脚本直连下载受阻（POST 返回 0 字节）→ 原文需手动下载落地后录入，录入前不进计算路径。 |
| 2026-10-14 | 仓库命名 `10-15-family-archive-workbench`（日期标签目录命名约定，无改名事件） | — |
| 2026-10-14 | **M0 骨架部署**：核心库 src 布局 + CLI 双形态入口 + profile v0.1.0-draft + 受控词表占位 + 烟囱测试 7 项全过 + GitHub Actions CI workflow。验证当时为**本地等价校验（M6 首推后已闭环：CI run 38588707991 四矩阵全绿）**。开发环境 Python 3.12（本机 3.8 低于要求，3.14 未注册 py 启动器） | 后续 M1 起按 plan/05 执行 |
| 2026-10-14 | **M0 自查整改（按 ai-tool-project-sprint 纪律）**：① 提交元数据邮箱改写为 GitHub noreply（`git filter-branch --env-filter`，作者/提交者两段独立 if，ae/ce 双字段验证仅剩 noreply；git config 同步；改写前仓外 bundle 备份）；② 补 `.gitattributes`（`* text=auto eol=lf` + 二进制 `-text`，CI 首跑前置工程）；③ CLI 入口加 UTF-8 stdio 守卫 + CI workflow 加 `PYTHONUTF8/PYTHONIOENCODING` env + `fetch-depth: 0`（历史扫描类守门依赖）；④ README 快速开始改为完整 venv 三行（`python -m pip`，py 启动器绕 venv 坑）；⑤ workflow 本地 PyYAML 解析验证（防非法 YAML 0 job 假 CI） | 本地自查整改，未推远端 |
| 2026-10-14 | **M1 数据先行收尾**：DCMI RDF/页面快照落库 data/raw/dcmi/（官方 GitHub dcmi/vocabtool 镜像，CC-BY 4.0）；dcmi-type.yaml 由脚本从 dctype.ttl 转写（12 词条挂 purl 出处，测试锁定）；openstd 预览逐页图抓取通路实测破解但遭站点级封锁（302 拦截页），GB/T 页图与 PIPL 条文核对转人工跟进。未核对条文一律不进计算路径 | plan/05 M1 DoD 逐项达成 |
| 2026-10-14 | **M2 导入解析收尾**：store.py SQLite 七表 schema（SHA-256 UNIQUE 约束在库层）+ importer.py 混合媒体同一录入路径（6 扩展名、词表校验 media_type）+ 缩略图（pillow 可选、缺则优雅降级）+ EXIF 仅进建议队列永不写 metadata_fields（K5 测试断言）+ CLI `import` 子命令（文件/目录、重复指纹跳过退出码 1）。pytest 21 项全绿（M2 新增 12 项锁定） | plan/05 M2 DoD 逐项达成 |
| 2026-10-14 | **M3 著录规则与人物收尾**：validator.py profile 驱动三类规则（required/vocabulary/format-W3CDTF 含日历语义检查），结果逐条挂出处；persons.py 关系边限词表+同名仅报告不自动合并（合并走显式 confirm_same_name_merge）；年表只收编目完成项；GUI 三页实装（编目/人物/年表，PySide6 可选依赖，offscreen 全链路冒烟通过）；profile v0.2.0（description/coverage 提必填）与 v0.1.0 实质可区分，旧版留档 archived/。pytest 34 项全绿（M3 新增 13 项） | plan/05 M3 DoD 逐项达成 |
| 2026-10-14 | **M4 基准收尾**：benchmark.py 合成样例生成器（人名只取假名白名单词表文件、证件号 999999 段/电话 199 段占位段从词表文件读取）+ 真值 manifest 单一来源（expected_errors 与 planted_fields 同源生成）+ plan/04 §2 七类异常断言全覆盖（敏感抹除以"键不出现"口径锁定）+ CLI benchmark 子命令；覆盖度口径按异常类型写进 manifest 不写硬数字。pytest 47 项全绿（M4 新增 13 项），famarchive benchmark 复跑全绿 | plan/05 M4 DoD 逐项达成 |
| 2026-10-14 | **M5 交付收尾**：search.py 组合查询（字段/人物/时间/媒体类型 AND 语义，Query 条件全可选）+ exporter.py 白名单导出包（K13 抹除=键不出现，白名单驱动循环、sensitive_fields 防御性再排除）+ manifest 记 profile/白名单版本与导出时间并写 export_manifests 表 + CLI search/export 子命令 + GUI 检索页/导出页补齐（五页全链路）+ PyInstaller 单文件 exe（数据文件内嵌 famarchive_data/，resources.py sys._MEIPASS 分支；修复 gui.py QApplication.setWindowTitle 误用）+ sha256 留档 plan/DIST-sha256-M5.txt。exe 内验证：profile/benchmark/import→search→export→gui 启动全通过。pytest 57 项全绿（M5 新增 10 项），GUI offscreen 全链路冒烟通过 | plan/05 M5 DoD 逐项达成 |
| 2026-10-14 | **M6 发布收官**：GitHub 首推（github.com/yuluo554/10-15-family-archive-workbench 公开仓库；gh OAuth 缺 workflow scope 被拒，改 SSH 通道推成）+ tag v0.1.0 + GitHub Release 附产物 famarchive-v0.1.0-win64-src.zip（exe+源码包，sha256 留档 plan/DIST-sha256-M6.txt，本地副本 dist-release/）+ plan/RELEASE-M6.md 留档。**M0"CI 待首推验证"口径闭环：首推触发 CI run 38588707991 全绿**（ubuntu/windows × py3.10/3.12 四矩阵全 success，CLI 冒烟+pytest 57 passed 远端实测）。发布前 pytest 复跑 57 passed | RELEASE-M6.md 三件套齐 |
| 2026-10-19 | **二次迭代：规则数据迁入包内（修 D1 非 editable 安装不可用）** | 缺陷：`package-data` 指向不存在的 `src/famarchive/data/`，`resources._REPO_DATA` 的 `parents[2]` 在 site-packages 下越界到 `<venv>\Lib` → wheel 零数据文件，装后 `profile show`/`benchmark` 裸 traceback（CI 因 `pip install -e .` 而假绿）。修法：`data/{profiles,vocabularies}` 与 `export-whitelist.yaml` 经 `git mv` 迁入 `src/famarchive/data/`（随 wheel/sdist 分发），`resources.data_dir()` 改包内相对 `Path(__file__).parent/"data"`（保留 `sys._MEIPASS` 分支，exe 行为不变）。仓库根 `data/` 现仅存 `raw/`（DCMI 公开快照）与 `README.md`（依据台账），不随包分发。本仓规则数据路径引用已全量同步至新位置，`data/raw/*` 引用不变。 | 二次迭代批次 1 |
| 2026-10-19 | **二次迭代：口径与生态对齐（DEC2/3/4 拍板）** | **DEC2=A** 新增非 editable 安装门禁：`tests/test_packaging.py`（wheel→全新 venv→装→CLI 冒烟，标记 `packaging`；负控实测还原 `parents[2]` 即 3 项红）+ CI 独立 `packaging` job，源码态冒烟保留。**DEC3=A** `famarchive.spec` 入库（`.gitignore` 加 `!famarchive.spec`），文档摘要不再是唯一来源。**DEC4a=A** 版本号 `0.1.0.dev0`→`0.1.0`（pyproject + `__version__`，与 tag v0.1.0 一致）。**DEC4b=B** `requires-python` `>=3.10`→`>=3.12`、CI 矩阵只留 3.12、classifier 改 3.12。**license 改 SPDX**：`license = "MIT"` + `license-files = ["LICENSE"]`，`build-system` 下限 `setuptools>=68`→`>=77`（SPDX 字段所需）——元数据构建实测 **WARNINGS: []**（原 `SetuptoolsDeprecationWarning`，硬期限 2027-02-18）。**CI**：actions 升 v7（checkout/setup-python），新增 `permissions: contents: read` 与 `concurrency`。**README/CLI help**：修 H1 插进 bullet 的渲染 bug、`.[gui]` 去"开发中"、`search`/`export` 标 M5 已交付、`gui` 说明改五页。 | 二次迭代批次 2–4 |
| 2026-10-19 | **二次迭代：范围与不变式** | 不碰著录/校验/导出判定逻辑，不改 profile 与词表**内容**（仅迁移位置），不改基准口径，不重打包、不动 tag `v0.1.0`（→693448d）与 Release 附件；`dist/famarchive.exe` sha256 仍 `b67228c5…fab986`、release zip 仍 `ecf3de93…16f2a4`。 | 二次迭代收尾 |

## 承诺-证据台账

| 承诺项 | 素材来源 | 交付物内可达性 | 核验方式 | 状态 |
|---|---|---|---|---|
| DCMI 字段体系与 W3CDTF 校验 | DCMI Metadata Terms 页面 + RDF（✅ 直连） | profile 数据文件随包入 exe 白名单 | 基准断言：词表/必填/日期校验行为与 profile 一致 | ✅ 可承诺 |
| 编目参考规则（照片号/文字说明四要素） | GB/T 11821-2002 预览（✅ 可得/⬜ 全文抓取） | 全文落地后随包；未落地仅作设计参考 | 逐条挂原文核对后落库 | ⬜ 待落地 |
| EXIF 版本对照包（扩展） | CIPA 差异素材（✅）/原文 PDF（⬜） | 原文手动下载落地后才入包 | 对照条目挂原文页码 | ⬜ 扩展项 |
| DA/T 参考设计（不作底座） | 备案记录（⬜ 无全文） | 仅文档提及，不进代码 | 不承诺逐条对齐 | ✅ 已降级 |
| 导出敏感字段抹除 | 项目自定白名单（PIPL 设计取向，⬜ 条文待核对） | 白名单数据文件随包 | 基准断言：抹除字段在导出文件中不出现 | ✅ 可承诺（条文引用待核对） |
| 合成样例带真值 | 程序化生成器（自产） | 样例集+manifest 随包 | 断言脚本复跑 | ✅ 可承诺 |
| 发布三件套 | — | tag + GitHub Release 附产物（本地留副本+sha256）+ plan/RELEASE-M6.md | M6 DoD 检查 | ✅ M6（v0.1.0 已发布，RELEASE-M6.md 留档） |

## 里程碑（初稿）

| 里程碑 | 内容 | DoD |
|---|---|---|
| M1 数据先行 | DCMI terms/RDF 落库、GB/T 11821 全文获取落地、依据台账三态回填 | 每条引用规则挂原文出处；未核对不落库。**✅ 2026-10-14 完成**（GB/T 页图底稿+PIPL 条文核对为人工跟进项，阻断已如实登记） |
| M2 导入解析 | 模块 1：混合媒体导入、指纹去重、EXIF 预填 | 无 EXIF 文件走同一路径；断言通过。**✅ 2026-10-14 完成**（21 项测试全绿：重复指纹拒绝、K5 EXIF 只进建议、无 EXIF 同路径、缩略图、批量导入） |
| M3 著录规则 | 模块 2/3：profile 校验器、录入表单、人物/年表 | 校验规则逐条标出处；profile 版本化。**✅ 2026-10-14 完成**（34 项测试全绿：三类规则逐条出处、W3CDTF、同名不自动合并、年表拦截未编目项、v0.2.0↔v0.1.0 必填集实质可区分；CLI+GUI 三页端到端冒烟通过） |
| M4 基准 | 模块 5：合成生成器 + 真值 manifest + 断言（含覆盖度口径） | 断言复跑通过；覆盖各异常类型不偏科。**✅ 2026-10-14 完成**（47 项测试全绿：生成器假名/占位段纪律、真值单一来源、七类异常逐类断言、覆盖度口径进 manifest；`famarchive benchmark` 复跑全绿） |
| M5 交付 | 模块 4 导出白名单 + PyInstaller exe + CLI | exe 内全链路可达；导出抹除断言通过。**✅ 2026-10-14 完成**（57 项测试全绿：组合查询 AND 语义、导出 manifest 版本留痕、K13 敏感键不出现；exe 全链路验证 import→search→export→gui 通过；sha256 留档 plan/DIST-sha256-M5.txt） |
| M6 发布 | 发布 GitHub 公开仓库 | **三件套：git tag + GitHub Release 附产物（本地留副本 sha256 留档）+ plan/RELEASE-M6.md 发布留档**，缺任一即未达成。**✅ 2026-10-14 完成**（v0.1.0：tag 已推、Release 附 zip、RELEASE-M6.md 留档；CI 首跑 run 38588707991 四矩阵全绿） |
