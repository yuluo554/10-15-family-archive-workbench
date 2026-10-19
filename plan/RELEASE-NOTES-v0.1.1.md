# v0.1.1 — 二次迭代：修复"非 editable 安装不可用" + 补齐装完能用门禁

## 修掉的核心缺陷（D1，P1）

`pyproject.toml` 的 `package-data` 指向了**不存在的** `src/famarchive/data/`（规则数据实际在仓库根 `data/`，包外），而 `resources.data_dir()` 用 `Path(__file__).resolve().parents[2] / "data"` 定位——在 `site-packages` 下 `parents[2]` 会**越界到 `<venv>\Lib`**。后果：

- wheel 里**零数据文件**（40,774 B / 23 条目全是 `.py`）；
- `pip install <whl>` 后 **`famarchive profile show`（README 快速开始第 5 条命令）与 `benchmark` 直接裸 traceback，退出码 1**；
- 本地与 CI 之所以全绿，是因为 `.venv` 与 CI 都用 `pip install -e .`，editable 的 `.pth` 把仓库根塞进 `sys.path`，恰好让 `parents[2]` 命中仓库根 `data/`——**是假绿**。

## 本次改动

- **规则数据随包分发**：`data/{profiles,vocabularies}` 与 `export-whitelist.yaml` 迁入 `src/famarchive/data/`；`resources.data_dir()` 改包内相对定位 `Path(__file__).parent / "data"`，`sys._MEIPASS` 分支原样保留（**exe 行为不变**）。仓库根 `data/` 现仅存 `raw/`（DCMI 公开快照）与依据台账 `README.md`。
- **新增装完能用门禁**：`tests/test_packaging.py`（构建 wheel → 全新 venv → 安装 → 跑 CLI 冒烟，pytest 标记 `packaging`）+ CI 独立 `packaging` job；源码态冒烟保留。负控已验：把定位改回 `parents[2]` 时该门禁立即 3 项红。
- **exe 可复现**：`famarchive.spec` 入库（此前被 `*.spec` 忽略），并加 `MANIFEST.in` 让 **sdist 也带 spec**。
- **发布口径统一**：版本号 `0.1.0.dev0` → `0.1.1`（与 tag/Release 一致）。
- **license 元数据**：`license = "MIT"` + `license-files`（SPDX），`build-system` 抬到 `setuptools>=77`——元数据构建**零 warning**（原为含硬期限 2027-02-18 的 `SetuptoolsDeprecationWarning`）。
- **解释器口径**：`requires-python >=3.10` → `>=3.12`，CI 矩阵只留 3.12，classifier 改 3.12。
- **CI**：actions 升 `v7`，新增 `permissions: contents: read` 与 `concurrency`——本轮 CI **注解归零**（Node20 弃用提示消失）。
- **README/CLI help**：修掉插在 bullet 列表中间的 H1 渲染 bug；`.[gui]` 去掉"开发中"；`search`/`export` 标为 M5 已交付；`gui` 说明改五页。

## 验证

- `pytest`：**62 passed**（57 + 5 守门）。
- 中立目录 + 全新 venv 装 wheel：`profile show` / `benchmark` / `search --help` / `export --help` **全 exit 0**；`data_dir()` 落在 `site-packages\famarchive\data`。
- wheel 30 条目含 **7 个 yaml**；sdist 含 spec 与规则数据。
- CI run **39280132304** 三 job 全绿（ubuntu/windows test + packaging），所有步骤 success、零注解。
- exe 实跑：`--version` 0.1.1、`profile show`、`benchmark` 均 exit 0。
- 发布后复验：从 Release **真下载**附件解压，逐层 sha256 与 `plan/DIST-sha256-v0.1.1.txt` 逐字符一致，下载到的 exe 实跑同样通过。

## 不改动的部分

不碰著录/校验/导出判定逻辑，不改 profile 与词表**内容**（仅迁移位置），不改基准口径，**不重写 tag `v0.1.0` 及其 Release 附件**。

## 产物

- `famarchive.exe`（单文件 Windows exe，0.1.1）
- `src-v0.1.1.zip`（源码包，含 `famarchive.spec` 与 `MANIFEST.in`）
- `famarchive-v0.1.1-win64-src.zip`（Release 附件 = exe + 源码包）

sha256 见仓库 `plan/DIST-sha256-v0.1.1.txt`。