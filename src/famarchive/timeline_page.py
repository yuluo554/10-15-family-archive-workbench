"""年表页：家庭年表只收编目完成的档案项（必填齐 + 零 error）。"""

from __future__ import annotations

from PySide6 import QtWidgets

from famarchive.persons import build_timeline
from famarchive.store import Store


class TimelinePage(QtWidgets.QWidget):
    def __init__(self, store: Store, profile: dict | None) -> None:
        super().__init__()
        self.store = store
        self.profile = profile

        layout = QtWidgets.QVBoxLayout(self)
        refresh_btn = QtWidgets.QPushButton("刷新年表")
        refresh_btn.clicked.connect(self.reload)
        layout.addWidget(refresh_btn)
        layout.addWidget(QtWidgets.QLabel("编目完成（必填齐、零 error）的档案项按著录时间排列："))
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["时间", "标题", "人物", "媒体类型", "条目 ID"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        self.reload()

    def reload(self) -> None:
        if not self.profile:
            return
        events = build_timeline(self.store, self.profile)
        self.table.setRowCount(len(events))
        for row, ev in enumerate(events):
            for col, value in enumerate(
                (ev["date"], ev["title"], "、".join(ev["persons"]), ev["media_type"], ev["item_id"])
            ):
                self.table.setItem(row, col, QtWidgets.QTableWidgetItem(str(value)))
