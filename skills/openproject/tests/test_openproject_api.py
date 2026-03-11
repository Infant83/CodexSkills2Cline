import importlib.util
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


if __name__ == "__main__":
    unittest.main()
