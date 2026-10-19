# 10-15 老照片/家庭档案数字化整理工作台

人工元数据编目优先的家庭档案整理工具：面向**无 EXIF 的扫描件、家书、证件**等混合媒体，
以 [DCMI Metadata Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/) 为骨架
自建著录字段 profile，提供可复现的著录规则校验、版本化字段方案与敏感字段白名单导出。

**纯本地单机，零上传**——不联网、不识别人脸、不跑 OCR（见[边界与非目标](plan/01-题目文档.md#六边界与非目标)）。

## 为什么是它

主流照片工具（Immich / digiKam / elodie…）围绕"有 EXIF 的现代照片 + 自动识别"转，
家庭档案的主食恰是无 EXIF 的扫描件。本工具以人工编目为核心：

- **混合媒体导入**：照片扫描件/翻拍/家书/文献/证件同一录入路径；EXIF 仅作预填建议，永不自动写入；SHA-256 指纹防重复入库；
- **DCMI-based 著录 profile（核心）**：字段定义、必填集、受控词表、W3CDTF 日期校验全部以数据文件定义，逐条规则标注出处，profile 带版本号可版本化；
- **人物与家庭年表**：代际关系边（受控词表）、同名人工确认合并、按编目时间轴生成年表；
- **白名单导出**：默认抹除 GPS/证件号类敏感字段（抹除 = 不出现，非置空），导出包附 manifest；
- **内置基准**：合成样例带真值（假名白名单），断言可复跑。

## 快速开始

需要 Python ≥ 3.12（`requires-python` 口径）。

```bash
py -m venv .venv                    # Windows；其他系统 python3 -m venv .venv
.venv/Scripts/activate              # Windows Git Bash；cmd 用 activate.bat
python -m pip install -e .[dev]     # 核心 + 测试（venv 内用 python，别用 py——py 启动器会绕过 venv）
pytest                              # 烟囱 + 基准断言
famarchive --help                   # CLI
famarchive profile show             # 查看著录 profile 与规则出处
```

可选 extras：`.[gui]` PySide6 桌面界面（五页：编目/人物/年表/检索/导出）、`.[pack]` PyInstaller 打包、`.[exif]` EXIF 辅助预填。

> 规则数据（profile/词表/白名单）随包分发：`pip install .`（非 editable）同样可用，`famarchive profile show` / `benchmark` 无需仓库 `data/`；CI 有 `packaging` 守门复核该形态。

| 子命令 | 说明 | 状态 |
|---|---|---|
| `import` | 混合媒体导入 | ✅（M2） |
| `validate` | 著录字段校验 | ✅（M3） |
| `persons` / `timeline` | 人物与年表 | ✅（M3） |
| `benchmark` | 合成样例基准断言复跑 | ✅（M4） |
| `search` / `export` | 检索与白名单导出 | ✅（M5） |
| `profile show` | profile 版本与规则出处 | ✅ |

## 仓库结构

- `src/famarchive/` 核心库（CLI 与 GUI 共用，无网络依赖）
- `src/famarchive/data/profiles/` DCMI 著录 profile（版本化）
- `src/famarchive/data/vocabularies/` 受控词表（媒体类型/关系边/假名白名单）
- `src/famarchive/data/export-whitelist.yaml` 导出字段白名单
- `data/raw/dcmi/` DCMI 公开参考快照（RDF/HTML，仓库侧资料，不随包分发）
- `data/README.md` 依据查证台账（标准条文三态核对记录）
- `plan/` 题目、设计与里程碑文档

## 路线图

见 [plan/05-里程碑执行计划.md](plan/05-里程碑执行计划.md)：M1 数据先行 → M2 导入 → M3 著录规则与人物 → M4 基准 → M5 打包交付 → M6 发布。

## 定位声明

本工具是家庭档案整理的辅助编目工具，不是档案鉴定/法律凭证工具；著录质量由使用者人工负责。
测试样例人物一律使用假名白名单，禁止真实个人信息入库。

## License

MIT
