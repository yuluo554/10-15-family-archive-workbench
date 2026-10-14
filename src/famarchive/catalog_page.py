"""编目页：档案项选择 → profile 驱动逐字段表单 → 校验提示（挂出处）。

业务纪律落点：
- EXIF 建议只作为"待人工确认"提示展示，点"采纳"才写入字段（K5）；
- 校验结果逐条显示 rule_id 与 source（K1）。
"""

from __future__ import annotations

from PySide6 import QtWidgets

from famarchive.store import Store
from famarchive.validator import validate


class CatalogPage(QtWidgets.QWidget):
    def __init__(self, store: Store, profile: dict | None) -> None:
        super().__init__()
        self.store = store
        self.profile = profile
        self._item_id: str | None = None

        layout = QtWidgets.QHBoxLayout(self)

        # 左：档案项列表
        left = QtWidgets.QVBoxLayout()
        left.addWidget(QtWidgets.QLabel("档案项（导入后待编目）"))
        self.item_list = QtWidgets.QListWidget()
        self.item_list.currentItemChanged.connect(self._on_item_selected)
        left.addWidget(self.item_list)
        self.reload_items()
        layout.addLayout(left, 1)

        # 右：编目表单
        right = QtWidgets.QVBoxLayout()
        self.form_label = QtWidgets.QLabel("选择左侧档案项开始编目")
        right.addWidget(self.form_label)
        self.form = QtWidgets.QFormLayout()
        right.addLayout(self.form)
        self.accept_suggestion_btn = QtWidgets.QPushButton("采纳选中 EXIF 建议（人工确认）")
        self.accept_suggestion_btn.clicked.connect(self._accept_suggestion)
        right.addWidget(self.accept_suggestion_btn)
        self.validate_btn = QtWidgets.QPushButton("校验并保存")
        self.validate_btn.clicked.connect(self._validate_and_save)
        right.addWidget(self.validate_btn)
        self.result_view = QtWidgets.QPlainTextEdit()
        self.result_view.setReadOnly(True)
        right.addWidget(self.result_view)
        layout.addLayout(right, 2)

        self._editors: dict[str, QtWidgets.QLineEdit] = {}
        self._suggestions: list[dict] = []

    def reload_items(self) -> None:
        self.item_list.clear()
        for item in self.store.list_items():
            self.item_list.addItem(f"{item['item_id']}  {item['file_name']}")

    def _on_item_selected(self, current, _previous) -> None:
        if current is None:
            return
        self._item_id = current.text().split()[0]
        item = self.store.get_item(self._item_id)
        self.form_label.setText(f"编目：{item['file_name']}")
        self._rebuild_form()

    def _rebuild_form(self) -> None:
        import json

        while self.form.count():
            w = self.form.takeAt(0).widget()
            if w:
                w.deleteLater()
        self._editors.clear()

        if not self.profile:
            return
        current = self.store.get_metadata_fields(self._item_id) if self._item_id else {}
        for fdef in self.profile["fields"]:
            name = fdef["name"]
            editor = QtWidgets.QLineEdit(str(current.get(name, "")))
            label = f"{fdef['label']}（{fdef['dcmi_term']}）" + ("*" if fdef.get("required") else "")
            self.form.addRow(label, editor)
            self._editors[name] = editor

        self._suggestions = []
        item = self.store.get_item(self._item_id)
        if item and item.get("exif_suggestions"):
            self._suggestions = json.loads(item["exif_suggestions"])
        sug_text = "\n".join(
            f"{s['field']}: {s['suggested_value']}  [{s['origin']} 待确认]"
            for s in self._suggestions
        )
        self.accept_suggestion_btn.setToolTip(sug_text or "本项无 EXIF 建议")
        self.accept_suggestion_btn.setEnabled(bool(self._suggestions))

    def _accept_suggestion(self) -> None:
        """EXIF 建议唯一写入路径：人工点击确认后填入表单（仍需校验保存）。"""
        if not self._suggestions:
            return
        for s in self._suggestions:
            editor = self._editors.get(s["field"])
            if editor and not editor.text().strip():
                editor.setText(str(s["suggested_value"]))

    def _validate_and_save(self) -> None:
        from famarchive.profile import load_profile

        if not self._item_id or not self.profile:
            return
        fields = {name: e.text().strip() for name, e in self._editors.items()}
        fields = {k: v for k, v in fields.items() if v}
        results = validate(fields, self.profile)
        lines = [
            f"[{r['severity']}] {r['rule_id']} {r['field']}: {r['message']}"
            f"（出处：{r['source']}）"
            for r in results
        ]
        errors = [r for r in results if r["severity"] == "error"]
        if errors:
            self.result_view.setPlainText(
                "存在 error，未保存：\n" + "\n".join(lines) if lines else "存在 error，未保存"
            )
            return
        self.store.set_metadata_fields(
            self._item_id, fields, profile_version=self.profile["version"]
        )
        self.result_view.setPlainText(
            ("已保存（profile v" + self.profile["version"] + "）\n" + "\n".join(lines))
            if lines
            else "校验通过，已保存"
        )
