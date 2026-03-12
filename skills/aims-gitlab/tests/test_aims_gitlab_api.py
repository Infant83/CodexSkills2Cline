import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "aims_gitlab_api.py"
SPEC = importlib.util.spec_from_file_location("aims_gitlab_api", MODULE_PATH)
aims_gitlab_api = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(aims_gitlab_api)


class NormalizeApiRootTests(unittest.TestCase):
    def test_normalize_api_root_adds_api_suffix(self):
        with patch.dict("os.environ", {aims_gitlab_api.PRIMARY_BASE_URL_ENV: "https://aims.example.com"}, clear=True):
            root = aims_gitlab_api.normalize_api_root(None)
        self.assertEqual(root, "https://aims.example.com/api/v4")

    def test_normalize_api_root_accepts_existing_api_root(self):
        root = aims_gitlab_api.normalize_api_root("https://aims.example.com/api/v4")
        self.assertEqual(root, "https://aims.example.com/api/v4")

    def test_compat_base_url_fallback_is_supported(self):
        with patch.dict("os.environ", {aims_gitlab_api.COMPAT_BASE_URL_ENV: "https://compat.example.com"}, clear=True):
            root = aims_gitlab_api.normalize_api_root(None)
        self.assertEqual(root, "https://compat.example.com/api/v4")


class UrlHelpersTests(unittest.TestCase):
    def test_project_path_encodes_group_and_project(self):
        path = aims_gitlab_api.build_project_path("group/sub/project", "merge_requests")
        self.assertEqual(path, "projects/group%2Fsub%2Fproject/merge_requests")

    def test_build_url_uses_relative_api_path(self):
        url = aims_gitlab_api.build_url("https://aims.example.com/api/v4", "projects/1")
        self.assertEqual(url, "https://aims.example.com/api/v4/projects/1")

    def test_build_url_keeps_absolute_api_path(self):
        url = aims_gitlab_api.build_url("https://aims.example.com/gitlab/api/v4", "/api/v4/projects/1")
        self.assertEqual(url, "https://aims.example.com/gitlab/api/v4/projects/1")


class TokenResolutionTests(unittest.TestCase):
    def test_user_token_is_default(self):
        with patch.dict("os.environ", {aims_gitlab_api.USER_TOKEN_ENV: "user-token"}, clear=True):
            token = aims_gitlab_api.resolve_token(None, use_admin=False)
        self.assertEqual(token, "user-token")

    def test_admin_token_is_selected_with_admin_flag(self):
        with patch.dict("os.environ", {aims_gitlab_api.ADMIN_TOKEN_ENV: "admin-token"}, clear=True):
            token = aims_gitlab_api.resolve_token(None, use_admin=True)
        self.assertEqual(token, "admin-token")

    def test_missing_admin_token_mentions_env_name(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RuntimeError) as context:
                aims_gitlab_api.resolve_token(None, use_admin=True)
        self.assertIn(aims_gitlab_api.ADMIN_TOKEN_ENV, str(context.exception))


class PrerequisiteValidationTests(unittest.TestCase):
    def test_validation_reports_both_missing_base_url_and_user_token(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RuntimeError) as context:
                aims_gitlab_api.validate_prerequisites(None, None, use_admin=False)
        message = str(context.exception)
        self.assertIn(aims_gitlab_api.PRIMARY_BASE_URL_ENV, message)
        self.assertIn(aims_gitlab_api.USER_TOKEN_ENV, message)


if __name__ == "__main__":
    unittest.main()
