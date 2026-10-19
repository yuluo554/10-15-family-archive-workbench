# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec：famarchive 单文件 exe（M5，plan/05 打包 DoD）。
# 数据文件（profile/词表/白名单）内嵌 famarchive_data/，resources.data_dir()
# 走 sys._MEIPASS 分支定位。GUI 页面与 PySide6 由依赖分析自动收录。
import sys
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('famarchive')

a = Analysis(
    ['src/famarchive/cli.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('src/famarchive/data/profiles', 'famarchive_data/profiles'),
        ('src/famarchive/data/vocabularies', 'famarchive_data/vocabularies'),
        ('src/famarchive/data/export-whitelist.yaml', 'famarchive_data'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='famarchive',
    console=True,
    upx=False,
)
