"""人物页：人物索引 + 关系边编辑（词表下拉）+ 同名人工确认合并。

同名合并必须人工点"确认合并"——库层 confirm_same_name_merge 只暴露给此路径。
"""

from __future__ import annotations

from PySide6 import QtWidgets

from famarchive.persons import add_relation_checked, find_same_name_persons, load_relation_type_ids
from famarchive.store import Store


class PersonsPage(QtWidgets.QWidget):
    def __init__(self, store: Store) -> None:
        super().__init__()
        self.store = store

        layout = QtWidgets.QHBoxLayout(self)

        # 左：人物索引 + 新增
        left = QtWidgets.QVBoxLayout()
        left.addWidget(QtWidgets.QLabel("人物索引"))
        self.person_list = QtWidgets.QListWidget()
        left.addWidget(self.person_list)
        add_row = QtWidgets.QHBoxLayout()
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("姓名")
        self.relation_combo = QtWidgets.QComboBox()
        add_row.addWidget(self.name_edit)
        add_row.addWidget(self.relation_combo)
        add_btn = QtWidgets.QPushButton("新增人物")
        add_btn.clicked.connect(self._add_person)
        add_row.addWidget(add_btn)
        left.addLayout(add_row)
        layout.addLayout(left, 1)

        # 右：关系边 + 同名确认
        right = QtWidgets.QVBoxLayout()
        right.addWidget(QtWidgets.QLabel("关系边（relation-type 词表约束）"))
        self.relation_list = QtWidgets.QListWidget()
        right.addWidget(self.relation_list)
        rel_row = QtWidgets.QHBoxLayout()
        self.rel_from = QtWidgets.QComboBox()
        self.rel_to = QtWidgets.QComboBox()
        self.rel_type = QtWidgets.QComboBox()
        for cb, tip in ((self.rel_from, "从"), (self.rel_to, "到")):
            cb.setToolTip(tip)
            rel_row.addWidget(cb)
        rel_row.addWidget(self.rel_type)
        rel_btn = QtWidgets.QPushButton("添加关系")
        rel_btn.clicked.connect(self._add_relation)
        rel_row.addWidget(rel_btn)
        right.addLayout(rel_row)

        right.addWidget(QtWidgets.QLabel("同名人物（须人工确认后合并）"))
        self.same_name_list = QtWidgets.QListWidget()
        right.addWidget(self.same_name_list)
        merge_btn = QtWidgets.QPushButton("确认合并选中组（保留第一位）")
        merge_btn.clicked.connect(self._merge_same_name)
        right.addWidget(merge_btn)
        layout.addLayout(right, 2)

        self._relation_type_ids = sorted(load_relation_type_ids())
        self.rel_type.addItems(self._relation_type_ids)
        self.reload()

    def reload(self) -> None:
        self.person_list.clear()
        self.rel_from.clear()
        self.rel_to.clear()
        persons = self.store.list_persons()
        for p in persons:
            label = f"{p['person_id']}  {p['name']}" + (f"（{p['relation']}）" if p["relation"] else "")
            self.person_list.addItem(label)
            self.rel_from.addItem(p["person_id"])
            self.rel_to.addItem(p["person_id"])
        self.relation_list.clear()
        for r in self.store.list_relations():
            self.relation_list.addItem(f"{r['from_person']} → {r['to_person']} : {r['relation_type']}")
        self.same_name_list.clear()
        for group in find_same_name_persons(self.store):
            names = " / ".join(p["person_id"] for p in group)
            self.same_name_list.addItem(f"同名[{group[0]['name']}]：{names}")

    def _add_person(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            return
        import uuid

        self.store.add_person(
            person_id=f"person-{uuid.uuid4().hex[:8]}",
            name=name,
            relation=self.relation_combo.currentText() or None,
        )
        self.name_edit.clear()
        self.reload()

    def _add_relation(self) -> None:
        frm = self.rel_from.currentText()
        to = self.rel_to.currentText()
        if not frm or not to or frm == to:
            return
        try:
            add_relation_checked(self.store, frm, to, self.rel_type.currentText())
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "关系类型非法", str(exc))
            return
        self.reload()

    def _merge_same_name(self) -> None:
        row = self.same_name_list.currentRow()
        if row < 0:
            return
        text = self.same_name_list.item(row).text()
        ids = [tok for tok in text.split("：", 1)[1].split(" / ") if tok.strip()]
        if len(ids) < 2:
            return
        confirm = QtWidgets.QMessageBox.question(
            self,
            "同名合并确认",
            f"确认把 {ids[1:]} 并入 {ids[0]}？此操作不可撤销。",
        )
        if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        for drop in ids[1:]:
            self.store.confirm_same_name_merge(ids[0], drop)
        self.reload()
