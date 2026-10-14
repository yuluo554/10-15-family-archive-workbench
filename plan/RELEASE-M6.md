# plan/RELEASE-M6.md — v0.1.0 发布留档（收官）

> 状态：已发布 · 2026-10-14 · 收官里程碑（M0–M6 全链路交付完毕）
> 仓库：<https://github.com/yuluo554/10-15-family-archive-workbench>

## 1. 发布三件套（DoD 逐项）

| DoD 项 | 结果 | 证据 |
|---|---|---|
| git tag | ✅ v0.1.0（annotated，已推送远端） | tag 指向 693448d（M5 收尾提交） |
| GitHub Release 附产物 | ✅ <https://github.com/yuluo554/10-15-family-archive-workbench/releases/tag/v0.1.0> | 附件 `famarchive-v0.1.0-win64-src.zip`（= famarchive.exe 56.6 MB 单文件 + src-v0.1.0.zip 源码包）；本地留副本 `dist-release/`（gitignore，不入库） |
| plan/RELEASE-M6.md 发布留档 | ✅ 本文件 | — |
| 首推后 CI 真实结论回填 | ✅ 全绿 | run id **38588707991**（main 首推触发，42s），4 矩阵 job（ubuntu/windows × py3.10/3.12）全部 success、0 失败步；`famarchive --version` + `profile show` CLI 冒烟通过；pytest 57 passed（CI 环境实测，非本地等价校验） |

## 2. 产物指纹（详 plan/DIST-sha256-M6.txt）

- `famarchive.exe` = `b67228c529f4…fab986`（与 M5 留档一致，打包产物未变更）
- `src-v0.1.0.zip` = `871caef9…52a8ac`（`git archive HEAD`，即 693448d）
- release zip = `ecf3de93…16f2a4`（exe + 源码包）

## 3. 发布过程记录（含实际排障）

1. **首推**：`gh repo create --push` 建公开仓库时被拒——OAuth token 缺 `workflow` scope，无法推 `.github/workflows/ci.yml`。改走 SSH 通道（`git remote set-url origin git@github.com:…`，ssh -T 已认证）后 `git push -u origin main` 成功。
2. **tag**：`git tag -a v0.1.0` + 推送远端（tag push 未触发第二条 CI，Actions 只挂 main push / PR，属预期）。
3. **产物**：源码包 `git archive`；release zip 因 Git Bash 无 zip 命令改用 Python zipfile 打包；exe 直接复用 M5 打包产物（指纹核对一致，未重打）。
4. **CI**：首推后自动触发，run 38588707991 全绿。M0 行"未接远端，CI 待首推验证"的诚实口径就此闭环。

## 4. 收官状态

- 全部子命令可达（import/validate/persons/timeline/search/export/benchmark/profile/gui），GUI 五页全链路，exe 内实测通过。
- pytest 57 passed（发布前复跑确认）；CI 远端 4 矩阵同绿。
- 提交元数据核验口径：`git log --format="%ae %ce" --all` 应仅 noreply（M0 整改沿用）。
- M6 为收官里程碑，无下一阶段 HANDOFF；后续如有用户新需求再立新档。
