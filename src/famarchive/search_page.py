"""检索页：字段/人物/时间/媒体类型组合查询（M5，走 search.py 核心库）。"""

from __future__ import annotations

from PySide6 import QtWidgets

from famarchive.search import Query, search
from famarchive.store import Store


class SearchPage(QtWidgets.QWidget):
    def __init__(self, store: Store, profile: dict | None) -> None:
        super().__init__()
        self.store = store
        self.profile = profile

        layout = QtWidgets.QVBoxLayout(self)

        form = QtWidgets.QGridLayout()
        self.text_edit = QtWidgets.QLineEdit()
        self.text_edit.setPlaceholderText("全字段关键词（可选）")
        self.field_combo = QtWidgets.QComboBox()
        self.field_combo.addItem("（任意字段）", None)
        if profile:
            for f in profile["fields"]:
                self.field_combo.addItem(f["label"], f["name"])
        self.value_edit = QtWidgets.QLineEdit()
        self.value_edit.setPlaceholderText("字段取值（可选）")
        self.person_edit = QtWidgets.QLineEdit()
        self.person_edit.setPlaceholderText("人物姓名（可选）")
        self.date_from_edit = QtWidgets.QLineEdit()
        self.date_from_edit.setPlaceholderText("起始日期 YYYY[-MM[-DD]]（可选）")
        self.date_to_edit = QtWidgets.QLineEdit()
        self.date_to_edit.setPlaceholderText("结束日期（可选）")
        self.media_combo = QtWidgets.QComboBox()
        self.media_combo.addItem("（任意媒体类型）", None)
        for mt in ("photo-scan", "photo-reprint", "letter", "document", "id-card"):
            self.media_combo.addItem(mt, mt)
        form.addWidget(QtWidgets.QLabel("关键词"), 0, 0)
        form.addWidget(self.text_edit, 0, 1)
        form.addWidget(QtWidgets.QLabel("字段"), 0, 2)
        form.addWidget(self.field_combo, 0, 3)
        form.addWidget(QtWidgets.QLabel("取值"), 1, 0)
        form.addWidget(self.value_edit, 1, 1)
        form.addWidget(QtWidgets.QLabel("人物"), 1, 2)
        form.addWidget(self.person_edit, 1, 3)
        form.addWidget(QtWidgets.QLabel("日期从"), 2, 0)
        form.addWidget(self.date_from_edit, 2, 1)
        form.addWidget(QtWidgets.QLabel("日期到"), 2, 2)
        form.addWidget(self.date_to_edit, 2, 3)
        form.addWidget(QtWidgets.QLabel("媒体类型"), 3, 0)
        form.addWidget(self.media_combo, 3, 1)
        layout.addLayout(form)

        search_btn = QtWidgets.QPushButton("检索")
        search_btn.clicked.connect(self.run_search)
        layout.addWidget(search_btn)

        self.summary = QtWidgets.QLabel("（尚未检索）")
        layout.addWidget(self.summary)
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["条目 ID", "标题", "时间", "人物", "媒体类型"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def run_search(self) -> None:
        query = Query(
            text=self.text_edit.text().strip() or None,
            field_name=self.field_combo.currentData(),
            field_value=self.value_edit.text().strip() or None,
            person=self.person_edit.text().strip() or None,
            date_from=self.date_from_edit.text().strip() or None,
            date_to=self.date_to_edit.text().strip() or None,
            media_type=self.media_combo.currentData(),
        )
        results = search(self.store, query)
        self.summary.setText(f"命中 {len(results)} 件")
        self.table.setRowCount(len(results))
        for row, r in enumerate(results):
            values = (
                r["item_id"],
                r["fields"].get("title") or "（无标题）",
                r["fields"].get("date") or "—",
                "、".join(r["persons"]) or "—",
                r["media_type"],
            )
            for col, value in enumerate(values):
                self.table.setItem(row, col, QtWidgets.QTableWidgetItem(str(value)))
