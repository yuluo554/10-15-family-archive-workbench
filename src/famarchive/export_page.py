"""导出页：白名单导出包 + manifest 预览（M5，走 exporter.py 核心库）。

抹除口径（K13）：白名单外与 sensitive_fields 内的字段在导出文件中
**键不出现**（非置空）；页面展示白名单与抹除字段清单供确认。
"""

from __future__ import annotations

from PySide6 import QtWidgets

from famarchive.exporter import load_whitelist
from famarchive.store import Store


class ExportPage(QtWidgets.QWidget):
    def __init__(self, store: Store, profile: dict | None) -> None:
        super().__init__()
        self.store = store
        self.profile = profile

        layout = QtWidgets.QVBoxLayout(self)

        self.whitelist_info = QtWidgets.QLabel()
        layout.addWidget(self.whitelist_info)
        self.erased_info = QtWidgets.QLabel("（未加载白名单）")
        layout.addWidget(self.erased_info)

        out_row = QtWidgets.QHBoxLayout()
        out_row.addWidget(QtWidgets.QLabel("导出文件："))
        self.out_edit = QtWidgets.QLineEdit("export-package.json")
        out_row.addWidget(self.out_edit)
        layout.addLayout(out_row)

        export_btn = QtWidgets.QPushButton("导出档案包（JSON，含 manifest）")
        export_btn.clicked.connect(self.run_export)
        layout.addWidget(export_btn)

        self.result_view = QtWidgets.QPlainTextEdit()
        self.result_view.setReadOnly(True)
        layout.addWidget(self.result_view)
        self._load_whitelist()

    def _load_whitelist(self) -> None:
        try:
            wl = load_whitelist()
        except Exception as exc:
            self.whitelist_info.setText(f"白名单加载失败：{exc}")
            return
        self.whitelist = wl
        self.whitelist_info.setText(
            f"导出白名单 v{wl['version']}：导出字段 "
            f"{'、'.join(wl['export_fields'])}"
        )
        self.erased_info.setText(
            f"抹除字段（导出文件中键不出现，非置空）：{'、'.join(wl['sensitive_fields'])}"
        )

    def run_export(self) -> None:
        if not self.profile:
            QtWidgets.QMessageBox.warning(self, "导出失败", "profile 未加载，无法导出")
            return
        out_path = self.out_edit.text().strip() or "export-package.json"
        from famarchive.exporter import export_package

        try:
            manifest = export_package(self.store, out_path, self.profile)
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "导出失败", str(exc))
            return
        lines = [
            f"导出完成：{out_path}",
            f"export_id={manifest['export_id']}  条目 {manifest['item_count']} 件",
            f"profile v{manifest['profile_version']}  白名单 v{manifest['whitelist_version']}",
            f"导出时间 {manifest['exported_at']}",
            f"抹除字段：{'、'.join(manifest['erased_fields'])}",
        ]
        self.result_view.setPlainText("\n".join(lines))
