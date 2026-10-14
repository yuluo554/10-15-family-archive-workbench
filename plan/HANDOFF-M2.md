# plan/HANDOFF-M2.md — 下一阶段交接快照

> 状态：M1 数据先行已收尾 · 2026-10-14 · 下一棒：M2 导入解析（模块 1）
> 续接提示词：`/goal 读取 <项目绝对路径>\plan\HANDOFF-M2.md 继续完成任务`（绝对路径只出现在用户侧启动命令，本文件库内一律相对路径）

## 1. 当前进度与证据

- **M1 全部收尾**：
  - DCMI 快照落库 `data/raw/dcmi/`（dublin_core_terms.nt/.ttl、dctype.ttl/.rdf、2 份 HTML 页面快照）；RDF 经 dublincore.org 主站直连 + DCMI 官方 GitHub `dcmi/vocabtool` build/ 镜像取得；许可 **CC-BY 4.0** 已登记 data/README.md。
  - `data/vocabularies/dcmi-type.yaml`：DCMI Type 12 词条（Collection/Dataset/Event/Image/InteractiveResource/MovingImage/PhysicalObject/Service/Software/Sound/StillImage/Text），由 `scripts/extract_dcmi_type.py` 从 dctype.ttl **脚本转写**（禁手抄纪律），每词条挂 purl URI + issued/modified/history 出处；namespace modified 2012-06-14。
  - GB/T 11821-2002：openstd 在线预览逐页图抓取通路**已实测破解**（`scripts/fetch_gbt11821.py`；关键点：showGb 须带 newGbInfo 的 Referer，否则 302 回详情页；每页有独立防爬令牌；页面图仅作人工核对底稿，不 OCR）。执行期触发服务端**站点级封锁**——showGb 请求现被 302 重定向至网信办《个人信息保护合规审计管理办法》新闻页（拦截页，冷却 5–15 分钟均不恢复，非限流是封锁）。**不阻断后续里程碑**：封锁解除或换网络环境后重跑脚本即可全本落库。
  - PIPL 第 6/28/29 条：flk.npc.gov.cn 检索 API 实测须过**人机验证码**（无头脚本不可行），转人工浏览器核对；台账获取路径已回填；核对前不引用条文原文口径不变。
- 证据：`pytest -v` **9 passed**（原 7 项烟囱 + 新增 `test_dcmi_type_vocabulary_extracted_with_sources`、`test_dcmi_raw_snapshot_registered` 两项 M1 锁定）。
- `data/raw/dcmi/` 在 .gitignore 例外出库（公开参考资料、无隐私）；`data/raw/gbt11821/` 仍在忽略内，全本落地时再登记例外。

## 2. 下一里程碑待办（M2 导入解析，plan/05）

- [ ] `importer.py` + `store.py`：混合媒体导入（照片扫描件/翻拍/家书/文书/证件扫描页）、SHA-256 指纹唯一、缩略图、EXIF 预填建议（pillow 可选依赖）
- [ ] 无 EXIF 文件与有 EXIF 文件走同一路径；**EXIF 永不自动写入著录字段（K5）**
- [ ] 重复指纹不入库断言；导入 DoD 断言通过
- [ ] （顺手项）封锁解除或换网络环境后重跑 `scripts/fetch_gbt11821.py` 把 GB/T 页图全本落库（先小步验证是否仍被 302 拦截页），例外登记 .gitignore，data/README.md 状态改 ✅

## 3. 既定口径清单（动了会打挂测试）

- **K1 profile 规则出处强制**：`profile.py` 加载器对缺 `source` 的规则抛 ValueError（`test_profile_rejects_rule_without_source` 锁死）；新规则必须带出处。
- **K2 必备键集**：profile 必备键 = `profile_id / version / based_on / rules`，规则必备键 = `id / field / type / severity / source`，规则类型枚举 = `required / vocabulary / format`——改口径须同步 loader + 测试 + plan/02 三处。
- **K3 词表文件名**：`data/vocabularies/{media-type,relation-type,假名白名单}.yaml`，测试 `test_data_files_present` 按名断言——改名须同步测试。**M1 新增第 4 份：`dcmi-type.yaml`**（12 词条、锁定测试 `test_dcmi_type_vocabulary_extracted_with_sources`；改词表内容须改 `scripts/extract_dcmi_type.py` 重跑，禁手抄）。
- **K4 抹除语义**：白名单外字段导出时**不出现**（非置空）——M5 exporter 实装时不得偏离。
- **K5 EXIF 纪律**：EXIF 只进预填建议，永不自动写入著录字段（M2 就是实装点）。
- **K6 版本化承诺**：profile v0.2.0 必须与 v0.1.0 必填/可选集实质可区分（M3 DoD）。
- **K7 CI 矩阵**：ubuntu+windows × py3.10/3.12，env 带 `PYTHONUTF8=1`，checkout `fetch-depth: 0`——历史扫描类守门依赖全量历史。
- **K8 M1 新增**：DCMI 词表转写只认 `scripts/extract_dcmi_type.py` 单一来源；data/raw/dcmi 快照与 data/README.md 登记绑定（`test_dcmi_raw_snapshot_registered` 同时断言 README 含 `dcmi/vocabtool` 与 `CC-BY`）。

## 4. 本机环境坑（只写实测过的）

- `python` 命令不可用（商店占位符）；`py -0` 只有 3.8.8 与 3.12——**项目开发统一走 `py -3.12` 建的 `.venv`**。
- venv 内命令一律用 `.venv/Scripts/python.exe` / `.venv/Scripts/famarchive.exe`（Git Bash 相对路径可跑）；venv 内安装/运行一律 `python -m pip`。
- **网络坑（M1 实测新增）**：
  - `purl.archive.org` 本机 TCP 直连被阻断（连接超时）→ purl.org 的 dcmitype RDF 拿不到，改走 dublincore.org 主站 + DCMI 官方 GitHub（raw.githubusercontent.com 也超时，用 `api.github.com` + `Accept: application/vnd.github.raw` 头下载）。
  - `openstd.samr.gov.cn` 有 Referer 校验 + 会话 cookie + 每页独立令牌 + **站点级封锁**：高频访问先表现为 RemoteDisconnected（冷却 5–8 分钟曾恢复），持续访问后 showGb 被 302 至网信办新闻页拦截页（15 分钟冷却也不恢复）。抓取脚本已带重试 + sleep；被拦截时勿再重试，等封锁解除或换网络环境。
  - `flk.npc.gov.cn` 检索 API 须人机验证码，无头脚本死路，勿再浪费时间试 API。
  - gov.cn 老转载页 404、npc.gov.cn 原文页 302 回首页，PIPL 全文脚本化获取不可行。
- Windows Git Bash 下 `filter-branch` 输出接管道有杀进程风险——重写直跑 + 重定向文件。

## 5. DoD 逐项 checklist（M2）

- [ ] 混合媒体导入：`importer.py` 支持词表 5 类媒体文件入库，路径/指纹落 `store.py`（SQLite）
- [ ] SHA-256 指纹唯一：同指纹二次导入被拒，断言通过
- [ ] 缩略图生成（pillow 可选依赖，缺 pillow 时优雅降级不崩）
- [ ] EXIF 预填建议：读出的 EXIF 只进建议队列，著录字段表内无 EXIF 自动写入痕迹（K5 断言）
- [ ] 无 EXIF 文件走同一路径不报错
- [ ] 收尾：pytest 复跑全绿 → plan/00/05 状态回写 → **写 plan/HANDOFF-M3.md（本对话内，先落盘再结束）** → commit

## 6. 关键命令速查

```bash
cd <项目根>                                            # 仓库根（用户侧拼绝对路径）
.venv/Scripts/python -m pytest -v                      # 全量测试（M1 后 9 项）
.venv/Scripts/famarchive.exe profile show              # profile 版本与规则出处
.venv/Scripts/python scripts/extract_dcmi_type.py      # 重转写 dcmi-type.yaml（改脚本后跑）
.venv/Scripts/python scripts/fetch_gbt11821.py         # GB/T 页图抓取（站点封锁解除后重跑；被 302 拦截时勿重试）
.venv/Scripts/python -m pip install -e .[dev]          # 依赖变更后重装
git log --format="%ae %ce" --all | sort -u             # 提交元数据核验（应仅 noreply）
```

## 7. 里程碑收尾出口纪律（对下一棒同样生效）

每个里程碑 DoD 达成后，**必须在本对话内写完下一阶段 HANDOFF-M<next> 才允许结束对话**（六节齐：进度证据/待办/既定口径/环境坑/DoD/命令速查）；库内一律相对路径；收尾顺序 = DoD 验证 → plan/00·05 状态回写 → HANDOFF 落盘 → commit。
