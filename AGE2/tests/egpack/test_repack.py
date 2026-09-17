from __future__ import annotations

import csv
from pathlib import Path
import tempfile
import unittest

from AGE2.tools.egpack.egpack_codec import (
    EgpackChange,
    EgpackChangeError,
    apply_changes,
    parse_egpack_bytes,
)
from AGE2.tools.egpack.repack_egpack import CHANGE_COLUMNS, REVIEWED_BREAK_COLUMNS, load_changes, main
from AGE2.tools.egpack.verify_egpack import verify_paths

from .fixtures import build_egpack


class EgpackRepackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original = build_egpack(
            [
                {"id": "game_t00000", "jp": "日本語", "en": "English"},
                {"id": "game_t00001", "jp": "短い", "en": "Second"},
            ]
        )

    def change(
        self,
        text_id: str = "game_t00000",
        slot: str = "jp",
        expected: str = "日本語",
        replacement: str = "这是一段更长的中文",
    ) -> EgpackChange:
        return EgpackChange("scene.egpack", text_id, slot, expected, replacement)

    def test_applies_longer_text_to_only_the_target_slot(self) -> None:
        patched = apply_changes(self.original, [self.change()], source="scene.egpack")
        document = parse_egpack_bytes(patched)

        self.assertEqual(document.records[0].slots["jp"].text, "这是一段更长的中文")
        self.assertEqual(document.records[0].slots["en"].text, "English")
        self.assertEqual(document.records[1].slots["jp"].text, "短い")
        self.assertEqual(len(patched), int.from_bytes(patched[8:12], "little"))

    def test_applies_multiple_changes_in_reverse_offset_order(self) -> None:
        changes = [
            self.change(replacement="中"),
            self.change("game_t00001", "jp", "短い", "第二条更长的中文"),
        ]

        patched = apply_changes(self.original, changes, source="scene.egpack")
        document = parse_egpack_bytes(patched)

        self.assertEqual(document.records[0].slots["jp"].text, "中")
        self.assertEqual(document.records[1].slots["jp"].text, "第二条更长的中文")

    def test_empty_replacement_is_an_intentional_change(self) -> None:
        patched = apply_changes(
            self.original,
            [self.change(replacement="")],
            source="scene.egpack",
        )

        self.assertEqual(parse_egpack_bytes(patched).records[0].slots["jp"].text, "")

    def test_rejects_manual_newlines_in_replacement_text(self) -> None:
        for replacement in (r"Chinese\ntext", r"Chinese\rtext", "Chinese\ntext", "Chinese\rtext"):
            with self.subTest(replacement=repr(replacement)):
                with self.assertRaisesRegex(EgpackChangeError, "manual newline"):
                    apply_changes(
                        self.original,
                        [self.change(replacement=replacement)],
                        source="scene.egpack",
                    )

    def test_no_changes_is_byte_identical(self) -> None:
        self.assertEqual(apply_changes(self.original, [], source="scene.egpack"), self.original)

    def test_chinese_can_preserve_native_multi_speaker_line_breaks(self) -> None:
        original = build_egpack([
            {"id": "game_t00000", "jp": r"一人目\n二人目\n三人目", "en": "Three voices"},
        ])
        change = self.change(slot="zh_hans", expected="", replacement=r"第一人\n第二人\n第三人")
        with self.assertRaisesRegex(EgpackChangeError, "manual newline"):
            apply_changes(original, [change])
        patched = parse_egpack_bytes(apply_changes(
            original, [change], preserve_native_line_breaks=True,
        ))
        self.assertEqual(patched.records[0].slots["zh_hans"].text, change.replacement_text)
        self.assertEqual(patched.records[0].slots["jp"].text, r"一人目\n二人目\n三人目")
        self.assertEqual(patched.records[0].slots["en"].text, "Three voices")

    def test_native_line_break_option_rejects_extra_breaks_and_other_slots(self) -> None:
        original = build_egpack([
            {"id": "game_t00000", "jp": r"一人目\n二人目", "en": "Two voices"},
        ])
        cases = [
            ("zh_hans", "", r"第一人\n第二人\n第三人"),
            ("zh_hans", "", "第一人\\n第二人\n第三人"),
            ("zh_hans", "", r"第一人\n第二人\r"),
            ("jp", r"一人目\n二人目", r"第一人\n第二人"),
        ]
        for slot, expected, replacement in cases:
            with self.subTest(slot=slot, replacement=repr(replacement)):
                with self.assertRaisesRegex(EgpackChangeError, "manual newline"):
                    apply_changes(original, [self.change(
                        slot=slot, expected=expected, replacement=replacement,
                    )], preserve_native_line_breaks=True)

    def test_rejects_duplicate_target(self) -> None:
        change = self.change()
        with self.assertRaisesRegex(EgpackChangeError, "duplicate"):
            apply_changes(self.original, [change, change], source="scene.egpack")

    def test_reviewed_scene_break_roundtrip_without_japanese_break(self) -> None:
        change = EgpackChange("scene.egpack", "game_t00000", "zh_hans", "",
                              r"第一句。\w\n第二句。\p", "Separate two voices; body and Log review required")
        patched = apply_changes(self.original, [change])
        before, after = parse_egpack_bytes(self.original), parse_egpack_bytes(patched)
        for old, new in zip(before.records, after.records):
            for slot in old.slots:
                expected = change.replacement_text if old.text_id == change.text_id and slot == "zh_hans" else old.slots[slot].text
                self.assertEqual(new.slots[slot].text, expected)
        self.assertIn(b"\\n", patched)
        self.assertNotIn(b"\x0a", patched[after.records[0].slots['zh_hans'].value_offset:][:after.records[0].slots['zh_hans'].value_length])

    def test_review_note_cannot_allow_raw_newlines_or_other_resource_types(self) -> None:
        for slot, text_id, expected, replacement, reason in [
            ("zh_hans", "game_t00000", "", "一\\n二\n三", "reviewed"),
            ("zh_hans", "game_t00000", "", "一\\n二\r三", "reviewed"),
            ("zh_hans", "game_t00000", "", r"一\n二\r三", "reviewed"),
            ("jp", "game_t00000", "日本語", r"一\n二", "reviewed"),
            ("zh_hans", "game_t00000", "", r"一\n二", "   "),
            ("zh_hans", "game_t00000", "", "一二", "reviewed"),
        ]:
            with self.subTest(slot=slot, replacement=repr(replacement), reason=reason):
                with self.assertRaises(EgpackChangeError):
                    apply_changes(self.original, [EgpackChange("scene.egpack", text_id, slot, expected, replacement, reason)])
        ruby = build_egpack([{"id": "game_t00000_ruby", "jp": "字:じ"}])
        with self.assertRaises(EgpackChangeError):
            apply_changes(ruby, [EgpackChange("scene.egpack", "game_t00000_ruby", "zh_hans", "", r"字\n音", "reviewed")])

    def test_reviewed_break_csv_is_per_row_and_cli_repack_preserves_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, changes = root / 'scene.egpack', root / 'changes.csv'
            source.write_bytes(self.original)
            with changes.open('w', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=REVIEWED_BREAK_COLUMNS)
                writer.writeheader()
                writer.writerow(dict(relative_path='scene.egpack', id='game_t00000', slot='zh_hans', expected_text='', replacement_text=r'一\n二', line_break_reason='Two separate utterances'))
                writer.writerow(dict(relative_path='scene.egpack', id='game_t00001', slot='zh_hans', expected_text='', replacement_text='普通正文', line_break_reason=''))
            self.assertEqual(main([str(source), '--changes', str(changes), '--output-dir', str(root / 'output')]), 0)
            self.assertEqual(source.read_bytes(), self.original)
            loaded = load_changes(changes)
            self.assertEqual(loaded[0].line_break_reason, 'Two separate utterances')
            self.assertEqual(loaded[1].line_break_reason, '')
            output = parse_egpack_bytes((root / 'output/scene.egpack').read_bytes())
            self.assertEqual(output.records[0].slots['zh_hans'].text, r'一\n二')
            self.assertEqual(verify_paths(source, root / 'output', changes), (1, 2))
            # One row's note must not relax the other row's default policy.
            with self.assertRaisesRegex(EgpackChangeError, 'manual newline'):
                apply_changes(self.original, [loaded[0], EgpackChange('scene.egpack', 'game_t00001', 'zh_hans', '', r'三\n四')])

    def test_rejects_expected_text_mismatch(self) -> None:
        with self.assertRaisesRegex(EgpackChangeError, "expected_text"):
            apply_changes(
                self.original,
                [self.change(expected="错误原文")],
                source="scene.egpack",
            )

    def test_rejects_unknown_slot_and_missing_id(self) -> None:
        with self.assertRaisesRegex(EgpackChangeError, "unknown slot"):
            apply_changes(self.original, [self.change(slot="xx")], source="scene.egpack")
        with self.assertRaisesRegex(EgpackChangeError, "missing id"):
            apply_changes(
                self.original,
                [self.change(text_id="game_t99999")],
                source="scene.egpack",
            )

    def test_changes_csv_preserves_empty_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "changes.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=CHANGE_COLUMNS)
                writer.writeheader()
                writer.writerow({
                    "relative_path": "scene.egpack",
                    "id": "game_t00000",
                    "slot": "jp",
                    "expected_text": "日本語",
                    "replacement_text": "",
                })

            changes = load_changes(path)

        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].replacement_text, "")

    def test_cli_writes_new_file_without_touching_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source_root = root / "source"
            output_root = root / "output"
            source = source_root / "nested" / "scene.egpack"
            changes_path = root / "changes.csv"
            source.parent.mkdir(parents=True)
            source.write_bytes(self.original)
            self._write_changes(changes_path, "nested/scene.egpack")

            result = main([
                str(source_root),
                "--changes",
                str(changes_path),
                "--output-dir",
                str(output_root),
            ])

            self.assertEqual(result, 0)
            self.assertEqual(source.read_bytes(), self.original)
            patched_path = output_root / "nested" / "scene.egpack"
            self.assertTrue(patched_path.is_file())
            self.assertEqual(
                parse_egpack_bytes(patched_path.read_bytes()).records[0].slots["jp"].text,
                "这是一段更长的中文",
            )

    def test_cli_rejects_existing_output_and_source_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "scene.egpack"
            changes_path = root / "changes.csv"
            output_root = root / "output"
            source.write_bytes(self.original)
            self._write_changes(changes_path, "scene.egpack")
            output_root.mkdir()
            (output_root / "scene.egpack").write_bytes(b"existing")

            with self.assertRaisesRegex(EgpackChangeError, "already exists"):
                main([str(source), "--changes", str(changes_path), "--output-dir", str(output_root)])
            with self.assertRaisesRegex(EgpackChangeError, "overlap"):
                main([str(source), "--changes", str(changes_path), "--output-dir", str(root)])

    def test_cli_validates_all_files_before_writing_any_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source_root = root / "source"
            output_root = root / "output"
            changes_path = root / "changes.csv"
            source_root.mkdir()
            (source_root / "a.egpack").write_bytes(self.original)
            (source_root / "b.egpack").write_bytes(self.original)
            with changes_path.open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=CHANGE_COLUMNS)
                writer.writeheader()
                writer.writerow({
                    "relative_path": "a.egpack",
                    "id": "game_t00000",
                    "slot": "jp",
                    "expected_text": "日本語",
                    "replacement_text": "中文",
                })
                writer.writerow({
                    "relative_path": "b.egpack",
                    "id": "game_t00000",
                    "slot": "jp",
                    "expected_text": "错误原文",
                    "replacement_text": "中文",
                })

            with self.assertRaisesRegex(EgpackChangeError, "expected_text"):
                main([
                    str(source_root),
                    "--changes",
                    str(changes_path),
                    "--output-dir",
                    str(output_root),
                ])

            self.assertFalse((output_root / "a.egpack").exists())

    def _write_changes(self, path: Path, relative_path: str) -> None:
        with path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=CHANGE_COLUMNS)
            writer.writeheader()
            writer.writerow({
                "relative_path": relative_path,
                "id": "game_t00000",
                "slot": "jp",
                "expected_text": "日本語",
                "replacement_text": "这是一段更长的中文",
            })


if __name__ == "__main__":
    unittest.main()
