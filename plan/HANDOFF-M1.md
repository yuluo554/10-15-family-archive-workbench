# plan/HANDOFF-M1.md — 下一阶段交接快照

> 状态：M0 已收尾（含自查整改）· 2026-10-14 · 下一棒：M1 数据先行
> 续接提示词：`/goal 读取 <项目绝对路径>\plan\HANDOFF-M1.md 继续完成任务`（绝对路径只出现在用户侧启动命令，本文件库内一律相对路径）

## 1. 当前进度与证据

- **M0 全部完成**：plan/02–05 设计文档、famarchive 核心库骨架、profile v0.1.0-draft（5 条规则全挂出处）、受控词表 3 份、导出白名单、烟囱测试 7 项、CI workflow。
- 证据：`pytest -v` 7 passed（本地等价校验，未接远端，CI 待首推验证）；`famarchive profile show` 输出版本与规则出处。
- 提交元数据已改写为 GitHub noreply（ae/ce 双字段验证仅剩 noreply 一值）；改写前仓外 bundle 备份（仓库树外）。

## 2. 下一里程碑待办（M1 数据先行，plan/05）

- [ ] DCMI terms 页面快照 + RDF（dublin_core_terms.nt）下载落库 `data/raw/dcmi/`（官方直连可得，状态 ✅）
- [ ] 从 RDF 提取 DCMI Type 词汇 → `src/famarchive/data/vocabularies/dcmi-type.yaml`（挂出处；脚本转写禁手抄）
- [ ] GB/T 11821-2002 预览人工落地 `data/raw/gbt11821/`（阻断时如实记录 pending，不硬卡后续里程碑）
- [ ] PIPL 第 6/28/29 条国家法律法规数据库核对 → data/README.md 台账回填
- [ ] DoD：每条引用规则挂原文出处；未核对（⬜）不落库不进计算路径

## 3. 既定口径清单（动了会打挂测试）

- **K1 profile 规则出处强制**：`profile.py` 加载器对缺 `source` 的规则抛 ValueError（`test_profile_rejects_rule_without_source` 锁死）；新规则必须带出处。
- **K2 必备键集**：profile 必备键 = `profile_id / version / based_on / rules`，规则必备键 = `id / field / type / severity / source`，规则类型枚举 = `required / vocabulary / format`——改口径须同步 loader + 测试 + plan/02 三处。
- **K3 词表文件名**：`src/famarchive/data/vocabularies/{media-type,relation-type,假名白名单}.yaml`，测试 `test_data_files_present` 按名断言——改名须同步测试。
- **K4 抹除语义**：白名单外字段导出时**不出现**（非置空）——M5 exporter 实装时不得偏离。
- **K5 EXIF 纪律**：EXIF 只进预填建议，永不自动写入著录字段。
- **K6 版本化承诺**：profile v0.2.0 必须与 v0.1.0 必填/可选集实质可区分（M3 DoD）。
- **K7 CI 矩阵**：ubuntu+windows × py3.10/3.12，env 带 `PYTHONUTF8=1`，checkout `fetch-depth: 0`——历史扫描类守门依赖全量历史。

## 4. 本机环境坑（只写实测过的）

- `python` 命令不可用（商店占位符）；`py -0` 只有 3.8.8 与 3.12——**项目开发统一走 `py -3.12` 建的 `.venv`**（本会话已建好，`.venv/Scripts/` 下可执行文件直接调）。
- venv 内命令一律用 `.venv/Scripts/python.exe` / `.venv/Scripts/famarchive.exe`（Git Bash 相对路径可跑）。
- `py` 启动器会无视 venv——venv 内安装/运行一律 `python -m pip`，别写 `py -m`。
- pip 曾报 exit 49（无输出）：改为 `py -3.12 -m venv .venv` 后在 venv 内安装解决。
- Windows Git Bash 下 `filter-branch` 输出接管道有杀进程风险——本次重写直跑 + 重定向文件，未踩。

## 5. DoD 逐项 checklist（M1）

- [ ] DCMI RDF 落库且来源/许可登记进 data/README.md
- [ ] dcmi-type.yaml 每个词条挂 DCMI 出处
- [ ] GB/T 11821 落地或 pending 状态如实登记（阻断不空转）
- [ ] PIPL 条文核对回填或显式"待核对"
- [ ] 收尾：pytest 复跑全绿 → plan/00/05 状态回写 → **写 plan/HANDOFF-M2.md（本对话内，先落盘再结束）** → commit

## 6. 关键命令速查

```bash
cd <项目根>                                            # 仓库根（用户侧拼绝对路径）
.venv/Scripts/python -m pytest -v                      # 全量测试
.venv/Scripts/famarchive.exe profile show              # profile 版本与规则出处
.venv/Scripts/famarchive.exe --version                 # 版本
.venv/Scripts/python -m pip install -e .[dev]          # 依赖变更后重装
git log --format="%ae %ce" --all | sort -u             # 提交元数据核验（应仅 noreply）
```

## 7. 里程碑收尾出口纪律（对下一棒同样生效）

每个里程碑 DoD 达成后，**必须在本对话内写完下一阶段 HANDOFF-M<next> 才允许结束对话**（六节齐：进度证据/待办/既定口径/环境坑/DoD/命令速查）；库内一律相对路径；收尾顺序 = DoD 验证 → plan/00·05 状态回写 → HANDOFF 落盘 → commit。
