#!/usr/bin/env python3
import argparse
import base64
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

DEFAULT_LIMIT = 20
API_SUFFIX = "/api/v3"


def normalize_api_root(base_url):
    if not base_url:
        raise RuntimeError(
            "Missing OPENPROJECT_BASE_URL. Set it to the OpenProject instance root "
            "or the /api/v3 endpoint."
        )
    base = base_url.strip().rstrip("/")
    if base.lower().endswith(API_SUFFIX):
        return base
    return f"{base}{API_SUFFIX}"


def instance_root(api_root):
    if api_root.lower().endswith(API_SUFFIX):
        return api_root[: -len(API_SUFFIX)]
    return api_root


def resolve_instance_path(api_root, path):
    root = instance_root(api_root)
    parts = urlsplit(root)
    base_path = parts.path.rstrip("/")

    if base_path and (path == base_path or path.startswith(f"{base_path}/")):
        resolved_path = path
    elif base_path:
        resolved_path = f"{base_path}{path}"
    else:
        resolved_path = path

    return urlunsplit((parts.scheme, parts.netloc, resolved_path, "", ""))


def build_url(api_root, path="", params=None):
    if path.startswith("http://") or path.startswith("https://"):
        url = path
    elif not path or path == ".":
        url = api_root
    elif path.startswith(API_SUFFIX):
        url = resolve_instance_path(api_root, path)
    elif path.startswith("/"):
        url = resolve_instance_path(api_root, path)
    else:
        url = f"{api_root.rstrip('/')}/{path.lstrip('/')}"

    if params:
        query = urlencode(params, doseq=True)
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{query}"

    return url


def basic_auth_header(api_key):
    token = base64.b64encode(f"apikey:{api_key}".encode("ascii")).decode("ascii")
    return f"Basic {token}"


def parse_json_text(raw_value, file_path):
    if raw_value and file_path:
        raise RuntimeError("Use either --json or --json-file, not both.")
    if file_path:
        with open(file_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    if raw_value:
        return json.loads(raw_value)
    return None


def parse_key_value_pairs(items, option_name):
    result = {}
    for item in items or []:
        if "=" not in item:
            raise RuntimeError(f"Invalid {option_name} '{item}'. Expected key=value.")
        key, value = item.split("=", 1)
        result[key] = value
    return result


class OpenProjectClient:
    def __init__(self, base_url, api_key):
        if not api_key:
            raise RuntimeError("Missing OPENPROJECT_API_KEY.")
        self.api_root = normalize_api_root(base_url)
        self.api_key = api_key

    def request(self, method, path="", params=None, payload=None, headers=None):
        url = build_url(self.api_root, path, params=params)
        body = None
        request_headers = {
            "Authorization": basic_auth_header(self.api_key),
            "Accept": "application/json",
        }
        if headers:
            request_headers.update(headers)
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")

        request = Request(url, data=body, method=method.upper())
        for key, value in request_headers.items():
            request.add_header(key, value)

        try:
            with urlopen(request) as response:
                raw_body = response.read().decode("utf-8")
                if not raw_body:
                    return None
                content_type = response.headers.get("Content-Type", "")
                if "json" in content_type:
                    return json.loads(raw_body)
                return {"raw": raw_body}
        except HTTPError as err:
            body_text = err.read().decode("utf-8", "ignore")
            message = body_text or err.reason
            raise RuntimeError(f"HTTP {err.code} for {url}: {message}") from err
        except URLError as err:
            raise RuntimeError(f"Network error for {url}: {err.reason}") from err

    def get_root(self):
        return self.request("GET")

    def whoami(self):
        root = self.get_root()
        user_href = root.get("_links", {}).get("user", {}).get("href")
        if not user_href:
            raise RuntimeError("OpenProject root response did not include the current user link.")
        return self.request("GET", user_href)


def dump_output(data, compact=False):
    if compact:
        print(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


def build_filters(args, client):
    filters = []

    if getattr(args, "filters_json", None):
        parsed = json.loads(args.filters_json)
        if not isinstance(parsed, list):
            raise RuntimeError("--filters-json must decode to a JSON array.")
        filters.extend(parsed)

    project_id = getattr(args, "project_id", None)
    if project_id is not None:
        filters.append({"project": {"operator": "=", "values": [str(project_id)]}})

    assignee_id = getattr(args, "assignee_id", None)
    if assignee_id:
        if assignee_id == "me":
            assignee_id = client.whoami()["id"]
        filters.append({"assignee": {"operator": "=", "values": [str(assignee_id)]}})

    status_id = getattr(args, "status_id", None)
    if status_id is not None and getattr(args, "state", "all") != "all":
        raise RuntimeError("Use either --status-id or --state, not both.")
    if status_id is not None:
        filters.append({"status": {"operator": "=", "values": [str(status_id)]}})
    else:
        state = getattr(args, "state", "all")
        if state == "open":
            filters.append({"status": {"operator": "o", "values": [""]}})
        elif state == "closed":
            filters.append({"status": {"operator": "c", "values": [""]}})

    return filters


def handle_get_user(client, args):
    if args.user_id == "me":
        return client.whoami()
    return client.request("GET", f"users/{args.user_id}")


def handle_search_users(client, args):
    filters = [
        {
            "name_and_email_or_login": {
                "operator": "**",
                "values": [args.query],
            }
        }
    ]
    params = {
        "filters": json.dumps(filters, ensure_ascii=False, separators=(",", ":")),
        "pageSize": args.limit,
        "offset": args.offset,
    }
    return client.request("GET", "users", params=params)


def handle_list_projects(client, args):
    params = {
        "pageSize": args.limit,
        "offset": args.offset,
    }
    if args.filters_json:
        params["filters"] = json.dumps(
            json.loads(args.filters_json),
            ensure_ascii=False,
            separators=(",", ":"),
        )
    return client.request("GET", "projects", params=params)


def handle_list_statuses(client, args):
    params = {
        "pageSize": args.limit,
        "offset": args.offset,
    }
    return client.request("GET", "statuses", params=params)


def handle_list_types(client, args):
    return client.request("GET", f"projects/{args.project_id}/types")


def handle_list_work_packages(client, args):
    params = {
        "filters": json.dumps(
            build_filters(args, client),
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "pageSize": args.limit,
        "offset": args.offset,
        "sortBy": json.dumps([[args.sort_field, args.sort_direction]]),
    }
    if args.include_subprojects:
        params["includeSubprojects"] = "true"
    return client.request("GET", "work_packages", params=params)


def handle_request(client, args):
    payload = parse_json_text(args.json, args.json_file)
    params = parse_key_value_pairs(args.query, "--query")
    headers = parse_key_value_pairs(args.header, "--header")
    return client.request(args.method, args.path, params=params, payload=payload, headers=headers)


def build_parser():
    parser = argparse.ArgumentParser(
        description="OpenProject API helper for common inspection and raw requests."
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OPENPROJECT_BASE_URL"),
        help="OpenProject base URL. Accepts the instance root or /api/v3.",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENPROJECT_API_KEY"),
        help="OpenProject API key. Defaults to OPENPROJECT_API_KEY.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print compact JSON output.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("whoami", help="Get the current authenticated user.")

    get_user = subparsers.add_parser("get-user", help="Get a user by ID or 'me'.")
    get_user.add_argument("user_id")

    search_users = subparsers.add_parser(
        "search-users",
        help="Search users by login, name, or email.",
    )
    search_users.add_argument("query")
    search_users.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    search_users.add_argument("--offset", type=int, default=1)

    list_projects = subparsers.add_parser("list-projects", help="List projects.")
    list_projects.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    list_projects.add_argument("--offset", type=int, default=1)
    list_projects.add_argument(
        "--filters-json",
        help="Raw OpenProject filters JSON array.",
    )

    get_project = subparsers.add_parser("get-project", help="Get a project by ID.")
    get_project.add_argument("project_id")

    list_types = subparsers.add_parser("list-types", help="List project types.")
    list_types.add_argument("--project-id", required=True)

    list_statuses = subparsers.add_parser("list-statuses", help="List statuses.")
    list_statuses.add_argument("--limit", type=int, default=50)
    list_statuses.add_argument("--offset", type=int, default=1)

    list_work_packages = subparsers.add_parser(
        "list-work-packages",
        help="List work packages with common filters.",
    )
    list_work_packages.add_argument("--project-id")
    list_work_packages.add_argument("--assignee-id")
    list_work_packages.add_argument("--status-id")
    list_work_packages.add_argument(
        "--state",
        choices=("all", "open", "closed"),
        default="all",
    )
    list_work_packages.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    list_work_packages.add_argument("--offset", type=int, default=1)
    list_work_packages.add_argument("--sort-field", default="id")
    list_work_packages.add_argument(
        "--sort-direction",
        choices=("asc", "desc"),
        default="asc",
    )
    list_work_packages.add_argument(
        "--include-subprojects",
        action="store_true",
        help="Include subprojects in work package queries.",
    )
    list_work_packages.add_argument(
        "--filters-json",
        help="Raw OpenProject filters JSON array.",
    )

    get_work_package = subparsers.add_parser(
        "get-work-package",
        help="Get a work package by ID.",
    )
    get_work_package.add_argument("work_package_id")

    request = subparsers.add_parser(
        "request",
        help="Send a raw request to an OpenProject API path.",
    )
    request.add_argument(
        "method",
        choices=("get", "post", "patch", "put", "delete", "options", "head"),
    )
    request.add_argument(
        "path",
        help="Relative API path like 'projects/1' or absolute '/api/v3/projects/1'.",
    )
    request.add_argument(
        "--json",
        help="Inline JSON request body.",
    )
    request.add_argument(
        "--json-file",
        help="Path to a JSON file to send as the request body.",
    )
    request.add_argument(
        "--query",
        action="append",
        default=[],
        help="Query parameter as key=value. Repeat as needed.",
    )
    request.add_argument(
        "--header",
        action="append",
        default=[],
        help="Additional header as key=value. Repeat as needed.",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    client = OpenProjectClient(args.base_url, args.api_key)

    if args.command == "whoami":
        data = client.whoami()
    elif args.command == "get-user":
        data = handle_get_user(client, args)
    elif args.command == "search-users":
        data = handle_search_users(client, args)
    elif args.command == "list-projects":
        data = handle_list_projects(client, args)
    elif args.command == "get-project":
        data = client.request("GET", f"projects/{args.project_id}")
    elif args.command == "list-types":
        data = handle_list_types(client, args)
    elif args.command == "list-statuses":
        data = handle_list_statuses(client, args)
    elif args.command == "list-work-packages":
        data = handle_list_work_packages(client, args)
    elif args.command == "get-work-package":
        data = client.request("GET", f"work_packages/{args.work_package_id}")
    elif args.command == "request":
        data = handle_request(client, args)
    else:
        raise RuntimeError(f"Unknown command: {args.command}")

    dump_output(data, compact=args.compact)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
