#!/usr/bin/env python3
import argparse
import base64
import importlib.util
import json
import mimetypes
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_ROOT_ENV = "OPENAI_BASE_URL"
API_KEY_ENV = "OPENAI_API_KEY"
MODEL_ENV = "OPENAI_MODEL_VISION"
DEFAULT_MODEL = "Llama-4-Scout"
DEFAULT_API_ROOT = "http://10.116.240.101:8030/openai"

DOCX_SUFFIXES = {".docx", ".docm", ".dotx", ".dotm"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def configure_stdio():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def missing_env_message(name, description, example):
    return (
        f"Missing {name}. Set it before running the on-prem document vision helper. "
        f"{description} "
        f'PowerShell: $env:{name}="{example}" '
        f'Bash: export {name}="{example}"'
    )


def resolve_api_root(cli_value):
    if cli_value:
        return cli_value.strip().rstrip("/")

    env_value = os.environ.get(API_ROOT_ENV, "").strip()
    if env_value:
        return env_value.rstrip("/")

    return DEFAULT_API_ROOT


def resolve_api_key(cli_value):
    if cli_value:
        return cli_value.strip()

    env_value = os.environ.get(API_KEY_ENV, "").strip()
    if env_value:
        return env_value

    raise RuntimeError(
        missing_env_message(
            API_KEY_ENV,
            "Use the on-prem API key for the OpenAI-compatible vision endpoint.",
            "your-api-key",
        )
    )


def resolve_model(cli_value):
    if cli_value:
        return cli_value.strip()
    env_value = os.environ.get(MODEL_ENV, "").strip()
    if env_value:
        return env_value
    return DEFAULT_MODEL


def chat_completions_url(api_root):
    base = resolve_api_root(api_root)
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def detect_input_type(input_path):
    path = Path(input_path)
    if path.is_dir():
        return "image-dir"
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in DOCX_SUFFIXES:
        return "docx"
    if suffix in IMAGE_SUFFIXES:
        return "image"
    raise RuntimeError(f"Unsupported input type for '{input_path}'.")


def sort_key_for_page_path(path):
    matches = re.findall(r"(\d+)", path.stem)
    page_num = int(matches[-1]) if matches else 0
    return (page_num, path.name.lower())


def parse_page_selection(spec):
    if not spec:
        return None

    pages = set()
    for chunk in spec.split(","):
        token = chunk.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            if start <= 0 or end <= 0 or end < start:
                raise RuntimeError(f"Invalid page range '{token}'.")
            pages.update(range(start, end + 1))
        else:
            page_num = int(token)
            if page_num <= 0:
                raise RuntimeError(f"Invalid page number '{token}'.")
            pages.add(page_num)
    return sorted(pages)


def write_text(path, text):
    Path(path).write_text(text, encoding="utf-8")


def write_json(path, data):
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


def image_to_data_url(image_path):
    mime_type = mimetypes.guess_type(str(image_path))[0] or "image/png"
    encoded = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def call_chat_completions(api_root, api_key, payload):
    body = json.dumps(payload).encode("utf-8")
    request = Request(chat_completions_url(api_root), data=body, method="POST")
    request.add_header("Authorization", f"Bearer {api_key}")
    request.add_header("Content-Type", "application/json")
    request.add_header("Accept", "application/json")

    try:
        with urlopen(request) as response:
            raw_body = response.read().decode("utf-8")
            return json.loads(raw_body)
    except HTTPError as err:
        body_text = err.read().decode("utf-8", "ignore")
        raise RuntimeError(f"HTTP {err.code} for {request.full_url}: {body_text or err.reason}") from err
    except URLError as err:
        raise RuntimeError(f"Network error for {request.full_url}: {err.reason}") from err


def extract_message_text(response_json):
    choices = response_json.get("choices") or []
    if not choices:
        raise RuntimeError("Vision endpoint returned no choices.")
    message = choices[0].get("message") or {}
    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "\n".join(part for part in parts if part).strip()
    raise RuntimeError("Unsupported response content format from vision endpoint.")


def load_pdfium():
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise RuntimeError(
            "Missing Python package 'pypdfium2'. Install it with 'python -m pip install pypdfium2 pillow'."
        ) from exc
    return pdfium


def render_pdf_pages(input_path, output_dir, max_pages=None):
    pdfium = load_pdfium()
    pdf = pdfium.PdfDocument(str(input_path))
    try:
        page_count = len(pdf)
        if page_count == 0:
            raise RuntimeError(f"No PDF pages were found in '{input_path}'.")
        last_page_index = min(page_count, max_pages) if max_pages else page_count
        page_paths = []
        for page_index in range(last_page_index):
            page = pdf[page_index]
            bitmap = page.render(scale=200 / 72.0)
            pil_image = bitmap.to_pil()
            page_path = Path(output_dir) / f"page-{page_index + 1}.png"
            pil_image.save(page_path, format="PNG")
            page_paths.append(page_path)
    finally:
        close = getattr(pdf, "close", None)
        if callable(close):
            close()

    if not page_paths:
        raise RuntimeError(f"No PDF pages were rendered from '{input_path}'.")
    return page_paths


def load_render_docx_module():
    module_path = Path(__file__).resolve().parents[2] / "doc" / "scripts" / "render_docx.py"
    if not module_path.exists():
        raise RuntimeError("DOCX renderer from the shared doc skill was not found.")
    spec = importlib.util.spec_from_file_location("render_docx", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render_docx_pages(input_path, output_dir, width=1600, height=2000, dpi_override=None):
    module = load_render_docx_module()
    module.configure_stdio()
    module.ensure_system_tools()
    if dpi_override is not None:
        dpi = int(dpi_override)
    else:
        try:
            dpi = module.calc_dpi_via_ooxml_docx(str(input_path), width, height)
        except Exception:
            dpi = module.calc_dpi_via_pdf(str(input_path), width, height)
    page_paths = module.rasterize(str(input_path), str(output_dir), dpi)
    if not page_paths:
        raise RuntimeError(f"No DOCX pages were rendered from '{input_path}'.")
    return [Path(path) for path in page_paths]


def collect_image_inputs(input_path, max_pages=None):
    path = Path(input_path)
    input_type = detect_input_type(path)

    if input_type == "image":
        return input_type, [path]
    if input_type == "image-dir":
        page_paths = sorted(
            [candidate for candidate in path.iterdir() if candidate.suffix.lower() in IMAGE_SUFFIXES],
            key=sort_key_for_page_path,
        )
        if not page_paths:
            raise RuntimeError(f"No supported image files were found in '{input_path}'.")
        if max_pages:
            page_paths = page_paths[:max_pages]
        return input_type, page_paths

    with tempfile.TemporaryDirectory(prefix="document_vision_") as temp_dir:
        output_dir = Path(temp_dir)
        if input_type == "pdf":
            page_paths = render_pdf_pages(path, output_dir, max_pages=max_pages)
        elif input_type == "docx":
            page_paths = render_docx_pages(path, output_dir)
            if max_pages:
                page_paths = page_paths[:max_pages]
        else:
            raise RuntimeError(f"Unsupported rendered input type '{input_type}'.")

        retained_dir = Path(tempfile.mkdtemp(prefix="document_vision_pages_"))
        retained_paths = []
        for rendered_page in page_paths:
            retained_path = retained_dir / rendered_page.name
            retained_path.write_bytes(rendered_page.read_bytes())
            retained_paths.append(retained_path)
        return input_type, retained_paths


def select_pages(page_paths, page_numbers):
    if not page_numbers:
        return page_paths
    selected = []
    for page_num in page_numbers:
        index = page_num - 1
        if index < 0 or index >= len(page_paths):
            raise RuntimeError(f"Requested page {page_num}, but only {len(page_paths)} page(s) are available.")
        selected.append(page_paths[index])
    return selected


def page_analysis_prompt(page_num, total_pages, instructions):
    base = (
        "Review this rendered document page for a non-vision coding assistant. "
        "Return concise markdown with these headings: "
        "'Visible text', 'Layout and figures', 'Important findings', and 'Uncertainties'. "
        "Describe tables, charts, screenshots, diagrams, stamps, annotations, signatures, or image-only content. "
        "Do not guess text you cannot read clearly."
    )
    if instructions:
        base += f" Additional task instructions: {instructions}"
    return f"Page {page_num} of {total_pages}. {base}"


def summary_prompt(per_page_markdown, instructions):
    prompt = (
        "You are summarizing document-page analyses for a non-vision coding assistant. "
        "Return markdown with these headings: 'Document summary', 'Visual-only findings', "
        "'Tables and figures', 'Risks or uncertainties', and 'Recommended next step'. "
        "Be explicit about where visual inspection still matters."
    )
    if instructions:
        prompt += f" Additional task instructions: {instructions}"
    prompt += "\n\nPer-page analyses:\n\n" + per_page_markdown
    return prompt


def analyze_page(api_root, api_key, model, image_path, page_num, total_pages, detail, instructions, max_tokens):
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "system",
                "content": "You analyze rendered document pages accurately and conservatively for internal on-prem document workflows.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": page_analysis_prompt(page_num, total_pages, instructions),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_to_data_url(image_path),
                            "detail": detail,
                        },
                    },
                ],
            },
        ],
    }
    response_json = call_chat_completions(api_root, api_key, payload)
    return extract_message_text(response_json)


def summarize_document(api_root, api_key, model, page_results, instructions, max_tokens):
    per_page_markdown = "\n\n".join(
        f"## Page {item['page']}\n\n{item['analysis']}" for item in page_results
    )
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "system",
                "content": "You summarize document analyses for downstream automation and review.",
            },
            {
                "role": "user",
                "content": summary_prompt(per_page_markdown, instructions),
            },
        ],
    }
    response_json = call_chat_completions(api_root, api_key, payload)
    return extract_message_text(response_json)


def result_to_markdown(result):
    lines = [
        "# Document Vision Review",
        "",
        f"- Source: `{result['source_path']}`",
        f"- Input type: `{result['input_type']}`",
        f"- Model: `{result['model']}`",
        f"- API root: `{result['api_root']}`",
        f"- Analyzed pages: `{', '.join(str(page) for page in result['analyzed_pages'])}`",
        "",
        "## Summary",
        "",
        result["summary"].strip(),
        "",
        "## Per-page Analysis",
        "",
    ]
    for page in result["pages"]:
        lines.extend(
            [
                f"### Page {page['page']}",
                "",
                f"- Image path: `{page['image_path']}`",
                "",
                page["analysis"].strip(),
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def build_parser():
    parser = argparse.ArgumentParser(
        description="Render and analyze PDFs, DOCX files, or page images with the on-prem vision model."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    review = subparsers.add_parser("review", help="Render the document if needed and analyze selected pages.")
    review.add_argument("input_path", help="Path to a PDF, DOCX, image, or directory of rendered page images.")
    review.add_argument("--api-root", help="OpenAI-compatible API root before /chat/completions.")
    review.add_argument("--api-key", help="API key. Defaults to OPENAI_API_KEY.")
    review.add_argument("--model", help="Vision model name. Defaults to OPENAI_MODEL_VISION or Llama-4-Scout.")
    review.add_argument("--instructions", help="Additional task instructions for the vision model.")
    review.add_argument("--pages", help="Specific pages to analyze, like '1-3,5'.")
    review.add_argument("--max-pages", type=int, help="Analyze only the first N pages.")
    review.add_argument(
        "--detail",
        choices=("low", "auto", "high"),
        default="high",
        help="Image detail hint for the OpenAI-compatible request.",
    )
    review.add_argument("--page-max-tokens", type=int, default=1200)
    review.add_argument("--summary-max-tokens", type=int, default=1500)
    review.add_argument("--json-output", help="Write JSON result to a file.")
    review.add_argument("--markdown-output", help="Write Markdown report to a file.")
    review.add_argument("--markdown", action="store_true", help="Print Markdown instead of JSON.")

    return parser


def main():
    configure_stdio()
    parser = build_parser()
    args = parser.parse_args()

    if args.command != "review":
        raise RuntimeError(f"Unknown command: {args.command}")

    api_root = resolve_api_root(args.api_root)
    api_key = resolve_api_key(args.api_key)
    model = resolve_model(args.model)
    requested_pages = parse_page_selection(args.pages)

    input_type, page_paths = collect_image_inputs(args.input_path, max_pages=args.max_pages)
    selected_pages = select_pages(page_paths, requested_pages)
    total_pages = len(page_paths)

    page_results = []
    for image_path in selected_pages:
        original_page_num = page_paths.index(image_path) + 1
        analysis = analyze_page(
            api_root=api_root,
            api_key=api_key,
            model=model,
            image_path=image_path,
            page_num=original_page_num,
            total_pages=total_pages,
            detail=args.detail,
            instructions=args.instructions,
            max_tokens=args.page_max_tokens,
        )
        page_results.append(
            {
                "page": original_page_num,
                "image_path": str(image_path),
                "analysis": analysis,
            }
        )

    summary = summarize_document(
        api_root=api_root,
        api_key=api_key,
        model=model,
        page_results=page_results,
        instructions=args.instructions,
        max_tokens=args.summary_max_tokens,
    )

    result = {
        "source_path": str(Path(args.input_path).resolve()),
        "input_type": input_type,
        "api_root": api_root,
        "model": model,
        "instructions": args.instructions or "",
        "analyzed_pages": [item["page"] for item in page_results],
        "page_count": total_pages,
        "summary": summary,
        "pages": page_results,
    }

    markdown = result_to_markdown(result)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        write_text(args.markdown_output, markdown)

    if args.markdown:
        print(markdown)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
