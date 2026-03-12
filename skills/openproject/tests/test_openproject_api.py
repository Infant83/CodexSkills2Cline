import importlib.util
import base64
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "openproject_api.py"
SPEC = importlib.util.spec_from_file_location("openproject_api", MODULE_PATH)
openproject_api = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(openproject_api)


class BuildUrlTests(unittest.TestCase):
    def test_relative_path_uses_api_root(self):
        api_root = "https://example.test/openproject/api/v3"
        url = openproject_api.build_url(api_root, "work_packages/42")
        self.assertEqual(url, "https://example.test/openproject/api/v3/work_packages/42")

    def test_absolute_api_path_keeps_deployment_prefix(self):
        api_root = "https://example.test/openproject/api/v3"
        url = openproject_api.build_url(api_root, "/api/v3/users/7")
        self.assertEqual(url, "https://example.test/openproject/api/v3/users/7")

    def test_instance_relative_path_is_not_duplicated_for_subpath_deployment(self):
        api_root = "https://example.test/openproject/api/v3"
        url = openproject_api.build_url(api_root, "/openproject/api/v3/users/7")
        self.assertEqual(url, "https://example.test/openproject/api/v3/users/7")

    def test_leading_slash_path_inherits_instance_base_path(self):
        api_root = "https://example.test/openproject/api/v3"
        url = openproject_api.build_url(api_root, "/attachments/99")
        self.assertEqual(url, "https://example.test/openproject/attachments/99")

    def test_root_deployment_keeps_root_relative_paths(self):
        api_root = "https://example.test/api/v3"
        url = openproject_api.build_url(api_root, "/attachments/99")
        self.assertEqual(url, "https://example.test/attachments/99")


class BasicAuthHeaderTests(unittest.TestCase):
    def test_basic_auth_header_uses_expected_ascii_value(self):
        header = openproject_api.basic_auth_header("token-123")
        self.assertEqual(header, "Basic YXBpa2V5OnRva2VuLTEyMw==")

    def test_basic_auth_header_supports_non_ascii_api_key(self):
        header = openproject_api.basic_auth_header("키-123")
        encoded = header.split(" ", 1)[1]
        decoded = base64.b64decode(encoded).decode("utf-8")
        self.assertEqual(decoded, "apikey:키-123")


class MissingEnvMessageTests(unittest.TestCase):
    def test_missing_base_url_message_mentions_setup_examples(self):
        with self.assertRaises(RuntimeError) as context:
            openproject_api.normalize_api_root("")
        message = str(context.exception)
        self.assertIn("OPENPROJECT_BASE_URL", message)
        self.assertIn("PowerShell:", message)
        self.assertIn("Bash:", message)

    def test_missing_api_key_message_mentions_basic_auth_usage(self):
        with self.assertRaises(RuntimeError) as context:
            openproject_api.OpenProjectClient("https://example.test/openproject", "")
        message = str(context.exception)
        self.assertIn("OPENPROJECT_API_KEY", message)
        self.assertIn("Basic auth", message)


if __name__ == "__main__":
    unittest.main()
