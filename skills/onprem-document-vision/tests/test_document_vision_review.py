import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "document_vision_review.py"
SPEC = importlib.util.spec_from_file_location("document_vision_review", MODULE_PATH)
document_vision_review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(document_vision_review)


class ConfigResolutionTests(unittest.TestCase):
    def test_default_api_root_uses_onprem_value(self):
        with patch.dict("os.environ", {}, clear=True):
            value = document_vision_review.resolve_api_root(None)
        self.assertEqual(value, "http://10.116.240.101:8030/openai")

    def test_api_key_prefers_openai_api_key(self):
        with patch.dict("os.environ", {document_vision_review.API_KEY_ENV: "secret"}, clear=True):
            value = document_vision_review.resolve_api_key(None)
        self.assertEqual(value, "secret")

    def test_model_defaults_to_llama4_scout(self):
        with patch.dict("os.environ", {}, clear=True):
            value = document_vision_review.resolve_model(None)
        self.assertEqual(value, "Llama-4-Scout")


class PageSelectionTests(unittest.TestCase):
    def test_parse_page_selection_handles_ranges(self):
        pages = document_vision_review.parse_page_selection("1-3,5")
        self.assertEqual(pages, [1, 2, 3, 5])

    def test_select_pages_uses_one_based_indices(self):
        paths = [Path(f"page-{idx}.png") for idx in range(1, 6)]
        selected = document_vision_review.select_pages(paths, [2, 4])
        self.assertEqual(selected, [paths[1], paths[3]])


class HelperFormattingTests(unittest.TestCase):
    def test_chat_completion_url_appends_path(self):
        url = document_vision_review.chat_completions_url("http://host/openai")
        self.assertEqual(url, "http://host/openai/chat/completions")

    def test_detect_input_type_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_type = document_vision_review.detect_input_type(temp_dir)
        self.assertEqual(input_type, "image-dir")

    def test_markdown_contains_summary_and_pages(self):
        result = {
            "source_path": "C:/tmp/sample.pdf",
            "input_type": "pdf",
            "api_root": "http://host/openai",
            "model": "Llama-4-Scout",
            "analyzed_pages": [1, 2],
            "summary": "Summary body",
            "pages": [
                {"page": 1, "image_path": "page-1.png", "analysis": "Page 1 analysis"},
                {"page": 2, "image_path": "page-2.png", "analysis": "Page 2 analysis"},
            ],
        }
        markdown = document_vision_review.result_to_markdown(result)
        self.assertIn("# Document Vision Review", markdown)
        self.assertIn("## Summary", markdown)
        self.assertIn("### Page 2", markdown)


if __name__ == "__main__":
    unittest.main()
