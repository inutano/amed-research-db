"""Tests for the HTML parser."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scraper.parser import (
    parse_project_page,
    _classify_header,
    _is_position_value,
    _is_institution_value,
    _detect_column_mapping,
)
from bs4 import BeautifulSoup


# --- Unit tests for helper functions ---

class TestClassifyHeader:
    def test_title_keywords(self):
        assert _classify_header("研究開発課題名") == "title"
        assert _classify_header("補助事業課題名") == "title"
        assert _classify_header("課題") == "title"

    def test_researcher_keywords(self):
        assert _classify_header("研究開発代表者") == "researcher"
        assert _classify_header("氏名") == "researcher"

    def test_institution_keywords(self):
        assert _classify_header("所属機関") == "institution"
        assert _classify_header("代表機関名") == "institution"
        assert _classify_header("実施機関") == "institution"

    def test_position_keywords(self):
        assert _classify_header("役職") == "position"
        assert _classify_header("職名") == "position"

    def test_skip_keywords(self):
        assert _classify_header("公募期間") == "skip"
        assert _classify_header("分野") == "skip"
        assert _classify_header("AMED-CREST") == "skip"
        assert _classify_header("#") == "skip"
        assert _classify_header("国") == "skip"

    def test_unknown(self):
        assert _classify_header("その他") == "unknown"


class TestIsPositionValue:
    def test_japanese_positions(self):
        assert _is_position_value("教授") is True
        assert _is_position_value("准教授") is True
        assert _is_position_value("助教") is True
        assert _is_position_value("講師") is True
        assert _is_position_value("部長") is True
        assert _is_position_value("センター長") is True

    def test_compound_japanese(self):
        assert _is_position_value("特任教授") is True
        assert _is_position_value("名誉教授") is True
        assert _is_position_value("副部長") is True
        assert _is_position_value("副センター長") is True

    def test_english_positions(self):
        assert _is_position_value("Professor") is True
        assert _is_position_value("Assistant Professor") is True
        assert _is_position_value("Associate Professor") is True
        assert _is_position_value("Senior Researcher") is True

    def test_not_positions(self):
        assert _is_position_value("東京大学") is False
        assert _is_position_value("田中太郎") is False
        assert _is_position_value("がん研究会") is False


class TestIsInstitutionValue:
    def test_japanese_institutions(self):
        assert _is_institution_value("東京大学") is True
        assert _is_institution_value("国立がん研究センター") is True
        assert _is_institution_value("国立感染症研究所") is True
        assert _is_institution_value("東京大学医学部附属病院") is True
        assert _is_institution_value("株式会社サンプル") is True

    def test_english_institutions(self):
        assert _is_institution_value("University of Tokyo") is True
        assert _is_institution_value("National Institute of Health") is True

    def test_not_institutions(self):
        assert _is_institution_value("教授") is False
        assert _is_institution_value("田中太郎") is False


# --- Tests for column mapping detection ---

class TestDetectColumnMapping:
    def _make_table(self, headers, data_rows):
        """Create an HTML table string from headers and data."""
        html = "<table>"
        html += "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
        for row in data_rows:
            html += "<tr>" + "".join(f"<td>{d}</td>" for d in row) + "</tr>"
        html += "</table>"
        soup = BeautifulSoup(html, "html.parser")
        return soup.find("table")

    def test_standard_4col(self):
        table = self._make_table(
            ["研究開発課題名", "研究開発代表者", "所属機関", "役職"],
            [["プロジェクトA", "田中太郎", "東京大学", "教授"]],
        )
        mapping, _ = _detect_column_mapping(table)
        assert mapping["title"] == 0
        assert mapping["researcher"] == 1
        assert mapping["institution"] == 2
        assert mapping["position"] == 3

    def test_reversed_institution_researcher(self):
        table = self._make_table(
            ["研究開発課題名", "代表機関名", "研究開発代表者", "役職"],
            [["プロジェクトA", "東京大学", "田中太郎", "教授"]],
        )
        mapping, _ = _detect_column_mapping(table)
        assert mapping["title"] == 0
        assert mapping["institution"] == 1
        assert mapping["researcher"] == 2

    def test_5col_with_category(self):
        table = self._make_table(
            ["分類", "研究開発課題名", "研究開発代表者", "所属機関", "役職"],
            [["分野A", "プロジェクトA", "田中太郎", "東京大学", "教授"]],
        )
        mapping, _ = _detect_column_mapping(table)
        assert mapping["title"] == 1
        assert mapping["researcher"] == 2

    def test_no_title_returns_none(self):
        table = self._make_table(
            ["氏名", "所属機関", "役職"],
            [["田中太郎", "東京大学", "教授"]],
        )
        mapping, _ = _detect_column_mapping(table)
        assert mapping is None

    def test_venture_3col(self):
        table = self._make_table(
            ["補助事業課題名", "実施機関", "認定ベンチャーキャピタル"],
            [["新薬開発", "株式会社A", "VC株式会社"]],
        )
        mapping, _ = _detect_column_mapping(table)
        assert mapping["title"] == 0
        assert mapping["institution"] == 1


# --- Integration tests for parse_project_page ---

class TestParseProjectPage:
    def _make_page(self, h1, table_html, date_text="令和6年4月1日"):
        return f"""<html><body>
        <h1>{h1}</h1>
        <p>{date_text}</p>
        {table_html}
        </body></html>"""

    def _make_table_html(self, headers, rows):
        html = "<table>"
        html += "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
        for row in rows:
            html += "<tr>" + "".join(f"<td>{d}</td>" for d in row) + "</tr>"
        html += "</table>"
        return html

    def test_basic_parsing(self):
        table = self._make_table_html(
            ["研究開発課題名", "研究開発代表者", "所属機関", "役職"],
            [
                ["がん免疫療法の研究", "田中太郎", "東京大学", "教授"],
                ["感染症ワクチン開発", "山田花子", "京都大学", "准教授"],
            ],
        )
        html = self._make_page('「革新的がん医療実用化研究事業」の採択課題について', table)
        result = parse_project_page(html, "https://example.com/test")

        assert result["program_name"] == "革新的がん医療実用化研究事業"
        assert result["date"] == "2024-04-01"
        assert len(result["projects"]) == 2
        assert result["projects"][0]["title"] == "がん免疫療法の研究"
        assert result["projects"][0]["researcher"] == "田中太郎"
        assert result["projects"][0]["institution"] == "東京大学"
        assert result["projects"][0]["position"] == "教授"

    def test_swapped_columns_fixed(self):
        """Institution and researcher columns in non-standard order should be fixed."""
        table = self._make_table_html(
            ["研究開発課題名", "代表機関名", "研究開発代表者", "役職"],
            [["プロジェクトA", "東京大学", "田中太郎", "教授"]],
        )
        html = self._make_page('「テスト事業」について', table)
        result = parse_project_page(html, "https://example.com/test")

        assert len(result["projects"]) == 1
        p = result["projects"][0]
        assert p["institution"] == "東京大学"
        assert p["researcher"] == "田中太郎"

    def test_position_not_stored_as_institution(self):
        """Position values like 教授 should not end up as institution names."""
        table = self._make_table_html(
            ["研究開発課題名", "研究開発代表者", "所属機関", "役職"],
            [["プロジェクトA", "田中太郎", "東京大学", "教授"]],
        )
        html = self._make_page('「テスト事業」について', table)
        result = parse_project_page(html, "https://example.com/test")

        for p in result["projects"]:
            assert not _is_position_value(p["institution"]), \
                f"Position value '{p['institution']}' stored as institution"

    def test_numeric_rows_skipped(self):
        """Rows with numeric-only values should be skipped."""
        table = self._make_table_html(
            ["課題番号", "応募数", "書面評価通過数", "採択数"],
            [["1", "10", "5", "3"]],
        )
        html = self._make_page("統計情報", table)
        result = parse_project_page(html, "https://example.com/test")
        assert len(result["projects"]) == 0

    def test_position_as_researcher_skipped(self):
        """Position values like 教授 should not be stored as researcher names."""
        # Simulate a badly-ordered table falling through to positional extraction
        html = """<html><body><h1>「テスト」について</h1>
        <table>
        <tr><td>田中太郎</td><td>教授</td><td>東京大学</td><td>がん免疫療法の研究開発について</td></tr>
        </table></body></html>"""
        result = parse_project_page(html, "https://example.com/test")
        for p in result["projects"]:
            assert not _is_position_value(p["researcher"]), \
                f"Position value '{p['researcher']}' stored as researcher"

    def test_date_parsing_reiwa(self):
        html = self._make_page("テスト", "<table></table>", "令和5年12月25日")
        result = parse_project_page(html, "https://example.com/test")
        assert result["date"] == "2023-12-25"

    def test_date_parsing_heisei(self):
        html = self._make_page("テスト", "<table></table>", "平成30年3月1日")
        result = parse_project_page(html, "https://example.com/test")
        assert result["date"] == "2018-03-01"

    def test_program_name_extraction(self):
        html = self._make_page('「難治性疾患実用化研究事業」の採択課題', "<table></table>")
        result = parse_project_page(html, "https://example.com/test")
        assert result["program_name"] == "難治性疾患実用化研究事業"

    def test_young_researcher_flag(self):
        html = '<html><body><h1>テスト</h1><p>若手あり</p></body></html>'
        result = parse_project_page(html, "https://example.com/test")
        assert result["young_researcher_flag"] is True

    def test_venture_table(self):
        """3-column venture capital tables should be parsed."""
        table = self._make_table_html(
            ["補助事業課題名", "実施機関", "認定ベンチャーキャピタル"],
            [["新薬開発プロジェクト", "株式会社サンプル", "VC株式会社"]],
        )
        html = self._make_page('「創薬ベンチャー事業」について', table)
        result = parse_project_page(html, "https://example.com/test")
        assert len(result["projects"]) == 1
        assert result["projects"][0]["title"] == "新薬開発プロジェクト"
        assert result["projects"][0]["institution"] == "株式会社サンプル"
