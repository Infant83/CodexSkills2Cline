#!/usr/bin/env python3
import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

DEFAULT_PER_PAGE = 20
API_SUFFIX = "/api/v4"
USER_TOKEN_ENV = "GITLAB_TOKEN"
ADMIN_TOKEN_ENV = "GITLAB_ADMIN_TOKEN"
PRIMARY_BASE_URL_ENV = "GITLAB_BASE_URL"
COMPAT_BASE_URL_ENV = "GITHUB_BASE_URL"


def configure_stdio():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def missing_env_message(name, description, example):
    return (
        f"Missing {name}. Set it before running the AIMS GitLab helper. "
        f"{description} "
        f'PowerShell: $env:{name}="{example}" '
        f'Bash: export {name}="{example}"'
    )


def resolve_base_url(cli_value):
    if cli_value:
        return cli_value

    direct = os.environ.get(PRIMARY_BASE_URL_ENV, "").strip()
    if direct:
        return direct

    compat = os.environ.get(COMPAT_BASE_URL_ENV, "").strip()
    if compat:
        return compat

    raise RuntimeError(
        "Missing GitLab base URL. Set "
        f"{PRIMARY_BASE_URL_ENV} to the AIMS GitLab instance root. "
        f"{COMPAT_BASE_URL_ENV} is accepted only as a compatibility fallback. "
        f'PowerShell: $env:{PRIMARY_BASE_URL_ENV}="https://aims.example.com" '
        f'Bash: export {PRIMARY_BASE_URL_ENV}="https://aims.example.com"'
    )


def normalize_api_root(base_url):
    base = resolve_base_url(base_url).strip().rstrip("/")
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


def encode_project_ref(project):
    project_text = str(project).strip()
    if not project_text:
        raise RuntimeError("Project reference cannot be empty.")
    if project_text.isdigit():
        return project_text
    return quote(project_text, safe="")


def build_project_path(project, suffix=""):
    project_root = f"projects/{encode_project_ref(project)}"
    if suffix:
        return f"{project_root}/{suffix.lstrip('/')}"
    return project_root


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


def resolve_token(cli_token, use_admin):
    if cli_token:
        return cli_token

    env_name = ADMIN_TOKEN_ENV if use_admin else USER_TOKEN_ENV
    token = os.environ.get(env_name, "").strip()
    if token:
        return token

    if use_admin:
        raise RuntimeError(
            missing_env_message(
                ADMIN_TOKEN_ENV,
                "Use the admin token only for explicit admin or sudo actions.",
                "your-admin-token",
            )
        )

    raise RuntimeError(
        missing_env_message(
            USER_TOKEN_ENV,
            "Use the normal user token for read, branch, merge-request, and approval inspection tasks.",
            "your-user-token",
        )
    )


def validate_prerequisites(base_url, cli_token, use_admin):
    errors = []

    try:
        resolved_base_url = resolve_base_url(base_url)
    except RuntimeError as exc:
        resolved_base_url = None
        errors.append(str(exc))

    try:
        resolved_token = resolve_token(cli_token, use_admin)
    except RuntimeError as exc:
        resolved_token = None
        errors.append(str(exc))

    if errors:
        raise RuntimeError("\n".join(errors))

    return resolved_base_url, resolved_token


class GitLabClient:
    def __init__(self, base_url, token, sudo=None):
        self.api_root = normalize_api_root(base_url)
        self.token = token
        self.sudo = sudo

    def request(self, method, path="", params=None, payload=None, headers=None):
        url = build_url(self.api_root, path, params=params)
        body = None
        request_headers = {
            "PRIVATE-TOKEN": self.token,
            "Accept": "application/json",
        }
        if self.sudo:
            request_headers["Sudo"] = str(self.sudo)
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

    def whoami(self):
        return self.request("GET", "user")


def dump_output(data, compact=False):
    if compact:
        print(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


def handle_list_projects(client, args):
    params = {
        "page": args.page,
        "per_page": args.per_page,
    }
    if args.search:
        params["search"] = args.search
    if args.membership:
        params["membership"] = "true"
    if args.owned:
        params["owned"] = "true"
    if args.simple:
        params["simple"] = "true"
    if args.min_access_level is not None:
        params["min_access_level"] = args.min_access_level
    return client.request("GET", "projects", params=params)


def handle_get_project(client, args):
    return client.request("GET", build_project_path(args.project))


def handle_list_project_members(client, args):
    suffix = "members" if args.direct_only else "members/all"
    params = {
        "page": args.page,
        "per_page": args.per_page,
    }
    if args.query:
        params["query"] = args.query
    return client.request("GET", build_project_path(args.project, suffix), params=params)


def handle_list_merge_requests(client, args):
    params = {
        "state": args.state,
        "scope": args.scope,
        "page": args.page,
        "per_page": args.per_page,
        "order_by": args.order_by,
        "sort": args.sort,
    }
    if args.search:
        params["search"] = args.search
    if args.author_username:
        params["author_username"] = args.author_username
    if args.reviewer_username:
        params["reviewer_username"] = args.reviewer_username
    if args.source_branch:
        params["source_branch"] = args.source_branch
    if args.target_branch:
        params["target_branch"] = args.target_branch
    if args.labels:
        params["labels"] = args.labels

    if args.project:
        path = build_project_path(args.project, "merge_requests")
    else:
        path = "merge_requests"
    return client.request("GET", path, params=params)


def handle_get_merge_request(client, args):
    path = build_project_path(args.project, f"merge_requests/{args.mr_iid}")
    return client.request("GET", path)


def handle_get_mr_approvals(client, args):
    path = build_project_path(args.project, f"merge_requests/{args.mr_iid}/approvals")
    return client.request("GET", path)


def handle_get_mr_approval_state(client, args):
    path = build_project_path(args.project, f"merge_requests/{args.mr_iid}/approval_state")
    return client.request("GET", path)


def handle_approve_merge_request(client, args):
    params = {}
    if args.sha:
        params["sha"] = args.sha
    path = build_project_path(args.project, f"merge_requests/{args.mr_iid}/approve")
    return client.request("POST", path, params=params or None)


def handle_unapprove_merge_request(client, args):
    path = build_project_path(args.project, f"merge_requests/{args.mr_iid}/unapprove")
    return client.request("POST", path)


def handle_request(client, args):
    payload = parse_json_text(args.json, args.json_file)
    params = parse_key_value_pairs(args.query, "--query")
    headers = parse_key_value_pairs(args.header, "--header")
    return client.request(args.method, args.path, params=params, payload=payload, headers=headers)


def build_parser():
    parser = argparse.ArgumentParser(
        description="AIMS GitLab helper for project, merge request, and admin API tasks."
    )
    parser.add_argument(
        "--base-url",
        help="GitLab instance root or /api/v4 endpoint. Defaults to GITLAB_BASE_URL, then GITHUB_BASE_URL.",
    )
    parser.add_argument(
        "--token",
        help="Explicit GitLab token. Defaults to GITLAB_TOKEN or GITLAB_ADMIN_TOKEN when --admin is set.",
    )
    parser.add_argument(
        "--admin",
        action="store_true",
        help="Use GITLAB_ADMIN_TOKEN by default instead of GITLAB_TOKEN.",
    )
    parser.add_argument(
        "--sudo",
        help="Act as another user with an admin token that has sudo scope.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print compact JSON output.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("whoami", help="Get the current authenticated GitLab user.")

    list_projects = subparsers.add_parser("list-projects", help="List accessible projects.")
    list_projects.add_argument("--search")
    list_projects.add_argument("--membership", action="store_true")
    list_projects.add_argument("--owned", action="store_true")
    list_projects.add_argument("--simple", action="store_true")
    list_projects.add_argument("--min-access-level", type=int)
    list_projects.add_argument("--page", type=int, default=1)
    list_projects.add_argument("--per-page", type=int, default=DEFAULT_PER_PAGE)

    get_project = subparsers.add_parser("get-project", help="Get one project by numeric ID or path.")
    get_project.add_argument("project")

    list_members = subparsers.add_parser(
        "list-project-members",
        help="List project members. Uses /members/all by default.",
    )
    list_members.add_argument("--project", required=True)
    list_members.add_argument("--direct-only", action="store_true")
    list_members.add_argument("--query")
    list_members.add_argument("--page", type=int, default=1)
    list_members.add_argument("--per-page", type=int, default=DEFAULT_PER_PAGE)

    list_mrs = subparsers.add_parser(
        "list-merge-requests",
        help="List merge requests globally or within one project.",
    )
    list_mrs.add_argument("--project")
    list_mrs.add_argument(
        "--state",
        choices=("opened", "closed", "locked", "merged", "all"),
        default="opened",
    )
    list_mrs.add_argument(
        "--scope",
        choices=("created_by_me", "assigned_to_me", "reviews_for_me", "all"),
        default="all",
    )
    list_mrs.add_argument("--search")
    list_mrs.add_argument("--author-username")
    list_mrs.add_argument("--reviewer-username")
    list_mrs.add_argument("--source-branch")
    list_mrs.add_argument("--target-branch")
    list_mrs.add_argument("--labels")
    list_mrs.add_argument("--page", type=int, default=1)
    list_mrs.add_argument("--per-page", type=int, default=DEFAULT_PER_PAGE)
    list_mrs.add_argument(
        "--order-by",
        choices=("created_at", "title", "updated_at"),
        default="updated_at",
    )
    list_mrs.add_argument(
        "--sort",
        choices=("asc", "desc"),
        default="desc",
    )

    get_mr = subparsers.add_parser("get-merge-request", help="Get one merge request by project and IID.")
    get_mr.add_argument("--project", required=True)
    get_mr.add_argument("--mr-iid", required=True)

    get_mr_approvals = subparsers.add_parser(
        "get-mr-approvals",
        help="Get the approval summary for one merge request.",
    )
    get_mr_approvals.add_argument("--project", required=True)
    get_mr_approvals.add_argument("--mr-iid", required=True)

    get_mr_approval_state = subparsers.add_parser(
        "get-mr-approval-state",
        help="Get the detailed approval-state breakdown for one merge request.",
    )
    get_mr_approval_state.add_argument("--project", required=True)
    get_mr_approval_state.add_argument("--mr-iid", required=True)

    approve_mr = subparsers.add_parser(
        "approve-merge-request",
        help="Approve a merge request as the authenticated user.",
    )
    approve_mr.add_argument("--project", required=True)
    approve_mr.add_argument("--mr-iid", required=True)
    approve_mr.add_argument("--sha")

    unapprove_mr = subparsers.add_parser(
        "unapprove-merge-request",
        help="Remove the current authenticated user's approval from a merge request.",
    )
    unapprove_mr.add_argument("--project", required=True)
    unapprove_mr.add_argument("--mr-iid", required=True)

    request = subparsers.add_parser(
        "request",
        help="Send a raw request to a GitLab API path.",
    )
    request.add_argument(
        "method",
        choices=("get", "post", "put", "patch", "delete", "head", "options"),
    )
    request.add_argument(
        "path",
        help="Relative path like 'projects/1' or absolute '/api/v4/projects/1'.",
    )
    request.add_argument("--json", help="Inline JSON request body.")
    request.add_argument("--json-file", help="Path to a JSON file request body.")
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
    configure_stdio()
    parser = build_parser()
    args = parser.parse_args()

    base_url, token = validate_prerequisites(args.base_url, args.token, args.admin)
    client = GitLabClient(base_url, token, sudo=args.sudo)

    if args.command == "whoami":
        data = client.whoami()
    elif args.command == "list-projects":
        data = handle_list_projects(client, args)
    elif args.command == "get-project":
        data = handle_get_project(client, args)
    elif args.command == "list-project-members":
        data = handle_list_project_members(client, args)
    elif args.command == "list-merge-requests":
        data = handle_list_merge_requests(client, args)
    elif args.command == "get-merge-request":
        data = handle_get_merge_request(client, args)
    elif args.command == "get-mr-approvals":
        data = handle_get_mr_approvals(client, args)
    elif args.command == "get-mr-approval-state":
        data = handle_get_mr_approval_state(client, args)
    elif args.command == "approve-merge-request":
        data = handle_approve_merge_request(client, args)
    elif args.command == "unapprove-merge-request":
        data = handle_unapprove_merge_request(client, args)
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
