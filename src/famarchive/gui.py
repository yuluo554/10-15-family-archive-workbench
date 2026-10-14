"""GUI 子命令与 PySide6 页面（可选依赖 `.[gui]`）。

核心库无 GUI 依赖（plan/03 §1）：本模块只做表单装配与展示，
全部业务逻辑走 famarchive core（validator / persons / store）。
缺 PySide6 时给出可读提示，不崩溃。

M3 实装三页：编目页 / 人物页 / 年表页；M5 补齐检索页 / 导出页（全链路 GUI 可达）。
"""

from __future__ import annotations


def _require_pyside():
    try:
        from PySide6 import QtCore, QtWidgets  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "GUI 需要 PySide6（可选依赖）：.venv/Scripts/python -m pip install -e .[gui]"
        ) from exc


def run_gui(db_path: str) -> int:
    """启动主窗口：编目/人物/年表/检索/导出五个标签页（M5 全链路）。"""
    _require_pyside()

    from PySide6 import QtWidgets

    from famarchive.export_page import ExportPage
    from famarchive.search_page import SearchPage
    from famarchive.store import Store
    from famarchive.catalog_page import CatalogPage
    from famarchive.persons_page import PersonsPage
    from famarchive.timeline_page import TimelinePage

    app = QtWidgets.QApplication([])
    store = Store(db_path)
    window = QtWidgets.QMainWindow()
    window.setWindowTitle("家庭档案整理工作台（纯本地零上传）")

    tabs = QtWidgets.QTabWidget()
    profile = None
    from famarchive.profile import load_profile

    try:
        profile = load_profile()
    except Exception as exc:  # profile 损坏时 GUI 仍可开人物/年表页
        QtWidgets.QMessageBox.warning(None, "profile 加载失败", str(exc))

    tabs.addTab(CatalogPage(store, profile), "编目")
    tabs.addTab(PersonsPage(store), "人物")
    tabs.addTab(TimelinePage(store, profile), "年表")
    tabs.addTab(SearchPage(store, profile), "检索")
    tabs.addTab(ExportPage(store, profile), "导出")
    window.setCentralWidget(tabs)
    window.show()
    return app.exec()
