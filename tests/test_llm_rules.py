import os

import pytest

from price_bot.llm.rules import RulesLoader


class TestRulesLoader:
    def test_nonexistent_directory_returns_empty_string(self, tmp_path):
        result = RulesLoader.load(str(tmp_path / "no_such_dir"))
        assert result == ""

    def test_empty_directory_returns_empty_string(self, tmp_path):
        result = RulesLoader.load(str(tmp_path))
        assert result == ""

    def test_single_md_file_returned(self, tmp_path):
        (tmp_path / "rules.md").write_text("правило 1", encoding="utf-8")
        result = RulesLoader.load(str(tmp_path))
        assert "правило 1" in result

    def test_multiple_md_files_concatenated(self, tmp_path):
        (tmp_path / "aaa.md").write_text("первое", encoding="utf-8")
        (tmp_path / "bbb.md").write_text("второе", encoding="utf-8")
        result = RulesLoader.load(str(tmp_path))
        assert "первое" in result
        assert "второе" in result

    def test_files_in_alphabetical_order(self, tmp_path):
        (tmp_path / "zzz.md").write_text("Z-правило", encoding="utf-8")
        (tmp_path / "aaa.md").write_text("A-правило", encoding="utf-8")
        result = RulesLoader.load(str(tmp_path))
        assert result.index("A-правило") < result.index("Z-правило")

    def test_non_md_files_ignored(self, tmp_path):
        (tmp_path / "rules.md").write_text("нужное", encoding="utf-8")
        (tmp_path / "notes.txt").write_text("ненужное", encoding="utf-8")
        result = RulesLoader.load(str(tmp_path))
        assert "нужное" in result
        assert "ненужное" not in result
