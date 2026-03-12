#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import os
import re
import sys
from contextlib import contextmanager
from datetime import datetime
from email.utils import parseaddr
from pathlib import Path

COMPANY_EMAIL_DOMAIN = "lgdisplay.com"
SELF_ADDRESS_OVERRIDE_ENV = "OUTLOOK_MAIL_SELF_ADDRESS"
DEFAULT_FOLDER_MAP = {
    "deleted": 3,
    "deleteditems": 3,
    "drafts": 16,
    "inbox": 6,
    "outbox": 4,
    "sent": 5,
    "sentitems": 5,
    "trash": 3,
    "받은편지함": 6,
    "보낸편지함": 5,
    "삭제된항목": 3,
    "삭제된 항목": 3,
    "임시보관함": 16,
}
MAIL_ITEM_CLASS = 43
MAIL_MESSAGE_PREFIX = "IPM.Note"
OL_MAIL_ITEM = 0
OL_MSG_UNICODE = 9


def configure_stdio():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def resolve_local_username():
    for key in ("USERNAME", "USER"):
        value = safe_text(os.environ.get(key, "")).strip().lower()
        if value:
            return value

    home_name = safe_text(Path.home().name).strip().lower()
    if home_name:
        return home_name
    return ""


def resolve_auto_allowed_self_address():
    override = normalize_email_address(os.environ.get(SELF_ADDRESS_OVERRIDE_ENV, ""))
    if override:
        return override

    username = resolve_local_username()
    if not username:
        return ""
    if not re.fullmatch(r"[a-z0-9._-]+", username):
        return ""
    return f"{username}@{COMPANY_EMAIL_DOMAIN}"


def resolve_auto_allowed_write_recipients():
    address = resolve_auto_allowed_self_address()
    if not address:
        return set()
    return {address}


def parse_datetime_arg(value):
    raw = value.strip()
    if raw.endswith("Z"):
        raw = f"{raw[:-1]}+00:00"
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Use ISO-like dates such as 2026-03-12 or 2026-03-12T09:00:00."
        ) from exc


def ensure_windows():
    if os.name != "nt":
        raise RuntimeError("This Outlook skill works only on Windows with desktop Outlook.")


def import_outlook_modules():
    ensure_windows()
    try:
        import pythoncom
        import win32com.client
    except ImportError as exc:
        raise RuntimeError(
            "Missing pywin32. Install it with: python -m pip install pywin32"
        ) from exc
    return pythoncom, win32com.client


@contextmanager
def open_outlook_namespace():
    pythoncom, win32_client = import_outlook_modules()
    pythoncom.CoInitialize()
    try:
        app = win32_client.Dispatch("Outlook.Application")
        namespace = app.GetNamespace("MAPI")
        yield app, namespace
    finally:
        pythoncom.CoUninitialize()


def iter_outlook_collection(collection):
    for index in range(1, int(collection.Count) + 1):
        yield collection.Item(index)


def safe_text(value):
    if value is None:
        return ""
    return str(value)


def coerce_datetime(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
        return datetime(
            value.year,
            value.month,
            value.day,
            getattr(value, "hour", 0),
            getattr(value, "minute", 0),
            getattr(value, "second", 0),
        )
    return datetime.fromisoformat(str(value))


def normalize_outlook_folder_path(folder):
    return safe_text(getattr(folder, "FolderPath", "")).lstrip("\\")


def resolve_folder(namespace, folder_path):
    if not folder_path:
        return namespace.GetDefaultFolder(6)

    normalized = folder_path.strip().strip("\\/")
    if not normalized:
        return namespace.GetDefaultFolder(6)

    alias_key = normalized.lower()
    if alias_key in DEFAULT_FOLDER_MAP:
        return namespace.GetDefaultFolder(DEFAULT_FOLDER_MAP[alias_key])

    segments = [segment for segment in re.split(r"[\\/]+", normalized) if segment]
    if not segments:
        return namespace.GetDefaultFolder(6)

    stores = list(iter_outlook_collection(namespace.Stores))
    matching_store = next((store for store in stores if safe_text(store.DisplayName) == segments[0]), None)

    if matching_store is not None:
        folder = matching_store.GetRootFolder()
        start_index = 1
    else:
        folder = namespace.DefaultStore.GetRootFolder()
        start_index = 0

    for segment in segments[start_index:]:
        child = next(
            (candidate for candidate in iter_outlook_collection(folder.Folders) if safe_text(candidate.Name) == segment),
            None,
        )
        if child is None:
            raise RuntimeError(
                f"Could not resolve Outlook folder path '{folder_path}' at segment '{segment}'."
            )
        folder = child

    return folder


def iter_folder_rows(folder, store_name, depth=0, max_depth=99, include_item_count=False):
    item_count = None
    if include_item_count:
        try:
            item_count = int(folder.Items.Count)
        except Exception:
            item_count = None

    yield {
        "store": store_name,
        "name": safe_text(folder.Name),
        "folder_path": normalize_outlook_folder_path(folder),
        "depth": depth,
        "item_count": item_count,
    }

    if depth >= max_depth:
        return

    for child in iter_outlook_collection(folder.Folders):
        yield from iter_folder_rows(
            child,
            store_name=store_name,
            depth=depth + 1,
            max_depth=max_depth,
            include_item_count=include_item_count,
        )


def iter_folders(folder, include_subfolders):
    yield folder
    if not include_subfolders:
        return
    for child in iter_outlook_collection(folder.Folders):
        yield from iter_folders(child, include_subfolders=True)


def is_mail_item(item):
    try:
        if int(item.Class) != MAIL_ITEM_CLASS:
            return False
        return safe_text(item.MessageClass).startswith(MAIL_MESSAGE_PREFIX)
    except Exception:
        return False


def get_sender_address(mail_item):
    try:
        if safe_text(mail_item.SenderEmailType) == "EX" and getattr(mail_item, "Sender", None) is not None:
            exchange_user = mail_item.Sender.GetExchangeUser()
            if exchange_user is not None and safe_text(exchange_user.PrimarySmtpAddress):
                return safe_text(exchange_user.PrimarySmtpAddress)
    except Exception:
        pass

    if safe_text(getattr(mail_item, "SenderEmailAddress", "")):
        return safe_text(mail_item.SenderEmailAddress)
    return safe_text(getattr(mail_item, "SenderName", ""))


def attachment_rows(mail_item):
    rows = []
    for attachment in iter_outlook_collection(mail_item.Attachments):
        rows.append(
            {
                "file_name": safe_text(getattr(attachment, "FileName", "")),
                "display_name": safe_text(getattr(attachment, "DisplayName", "")),
                "size": int(getattr(attachment, "Size", 0) or 0),
            }
        )
    return rows


def markdown_body(mail_item, folder_path, sender_address):
    subject = safe_text(mail_item.Subject).strip() or "(no subject)"
    received = coerce_datetime(getattr(mail_item, "ReceivedTime", None))
    received_value = received.isoformat(sep=" ", timespec="seconds") if received else ""
    body_text = safe_text(getattr(mail_item, "Body", ""))
    lines = [
        f"# {subject}",
        "",
        f"- Received: {received_value}",
        f"- From: {sender_address}",
        f"- To: {safe_text(getattr(mail_item, 'To', ''))}",
        f"- CC: {safe_text(getattr(mail_item, 'CC', ''))}",
        f"- Folder: {folder_path}",
        f"- Outlook Entry ID: {safe_text(getattr(mail_item, 'EntryID', ''))}",
        "",
        "## Body",
        "",
        body_text,
    ]
    return "\n".join(lines)


def message_record(mail_item, folder_path):
    received = coerce_datetime(getattr(mail_item, "ReceivedTime", None))
    body_text = safe_text(getattr(mail_item, "Body", ""))
    attachments = attachment_rows(mail_item)
    parent = getattr(mail_item, "Parent", None)
    return {
        "subject": safe_text(mail_item.Subject).strip() or "(no subject)",
        "sender": get_sender_address(mail_item),
        "to": safe_text(getattr(mail_item, "To", "")),
        "cc": safe_text(getattr(mail_item, "CC", "")),
        "received_time": received.isoformat() if received else None,
        "folder_path": folder_path,
        "entry_id": safe_text(getattr(mail_item, "EntryID", "")),
        "store_id": safe_text(getattr(parent, "StoreID", "")) if parent is not None else "",
        "unread": bool(getattr(mail_item, "UnRead", False)),
        "importance": int(getattr(mail_item, "Importance", 0) or 0),
        "has_attachments": bool(attachments),
        "attachment_count": len(attachments),
        "attachments": attachments,
        "body_preview": body_text[:200].replace("\r\n", "\n").replace("\r", "\n"),
    }


def normalize_email_address(value):
    _display_name, address = parseaddr(value)
    normalized = address or value
    return normalized.strip().lower()


def normalize_recipients(values):
    recipients = []
    for value in values or []:
        for raw_part in re.split(r"[;,]", value):
            part = raw_part.strip()
            if part:
                recipients.append(part)
    return recipients


def read_text_file(path_value):
    return Path(path_value).read_text(encoding="utf-8-sig")


def safe_file_name(name, max_length=120):
    if not name or not name.strip():
        return "untitled"
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name.strip())
    value = re.sub(r"\s+", " ", value).strip(" ._")
    if not value:
        value = "untitled"
    if len(value) > max_length:
        value = value[:max_length].rstrip(" ._")
    return value or "untitled"


def short_hash(value):
    effective = value if value is not None else ""
    return hashlib.sha256(effective.encode("utf-8")).hexdigest()[:12]


def unique_path(path):
    if not path.exists():
        return path
    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem}-{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def unique_directory(path):
    if not path.exists():
        return path
    counter = 1
    while True:
        candidate = path.with_name(f"{path.name}-{counter}")
        if not candidate.exists():
            return candidate
        counter += 1


def write_text(path, value, bom=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    encoding = "utf-8-sig" if bom else "utf-8"
    path.write_text("" if value is None else str(value), encoding=encoding, newline="\n")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def write_manifest_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "received_time",
                "subject",
                "sender",
                "folder_path",
                "message_directory",
                "body_path",
                "msg_path",
                "attachment_count",
                "entry_id",
                "store_id",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def filtered_messages(namespace, args):
    root_folder = resolve_folder(namespace, args.folder_path)
    matched = []
    scanned = 0

    for folder in iter_folders(root_folder, include_subfolders=args.include_subfolders):
        folder_path = normalize_outlook_folder_path(folder)
        items = folder.Items
        try:
            items.Sort("[ReceivedTime]", True)
        except Exception:
            pass

        for item in iter_outlook_collection(items):
            scanned += 1
            if not is_mail_item(item):
                continue

            received = coerce_datetime(getattr(item, "ReceivedTime", None))
            if received is None:
                continue

            if args.received_since and received < args.received_since:
                continue
            if args.received_until and received > args.received_until:
                continue
            if args.unread_only and not bool(getattr(item, "UnRead", False)):
                continue

            subject = safe_text(item.Subject).strip() or "(no subject)"
            if args.subject_contains and args.subject_contains.lower() not in subject.lower():
                continue

            sender = get_sender_address(item)
            if args.sender_contains and args.sender_contains.lower() not in sender.lower():
                continue

            body_text = safe_text(getattr(item, "Body", ""))
            if args.body_contains and args.body_contains.lower() not in body_text.lower():
                continue

            attachments = attachment_rows(item)
            if args.has_attachments and not attachments:
                continue
            if args.attachment_name_contains:
                attachment_query = args.attachment_name_contains.lower()
                if not any(attachment_query in row["file_name"].lower() for row in attachments):
                    continue

            matched.append(
                {
                    "item": item,
                    "folder_path": folder_path,
                    "record": {
                        "subject": subject,
                        "sender": sender,
                        "to": safe_text(getattr(item, "To", "")),
                        "cc": safe_text(getattr(item, "CC", "")),
                        "received_time": received.isoformat(),
                        "folder_path": folder_path,
                        "entry_id": safe_text(getattr(item, "EntryID", "")),
                        "store_id": safe_text(getattr(getattr(item, "Parent", None), "StoreID", "")),
                        "unread": bool(getattr(item, "UnRead", False)),
                        "importance": int(getattr(item, "Importance", 0) or 0),
                        "has_attachments": bool(attachments),
                        "attachment_count": len(attachments),
                        "attachments": attachments,
                        "body_preview": body_text[:200].replace("\r\n", "\n").replace("\r", "\n"),
                    },
                }
            )

            if len(matched) >= args.max_items:
                return root_folder, matched, scanned

    return root_folder, matched, scanned


def render_rows(rows):
    if not rows:
        print("No results.")
        return
    for row in rows:
        print(f"[{row.get('received_time') or ''}] {row.get('sender') or ''} | {row.get('subject') or ''}")
        print(f"  Folder: {row.get('folder_path') or ''}")
        print(f"  EntryID: {row.get('entry_id') or ''}")
        print(
            f"  Unread: {row.get('unread')} | Attachments: {row.get('attachment_count', 0)}"
        )
        print()


def load_mail_item(namespace, entry_id, store_id=None):
    if store_id:
        item = namespace.GetItemFromID(entry_id, store_id)
    else:
        item = namespace.GetItemFromID(entry_id)
    if not is_mail_item(item):
        raise RuntimeError("The requested Outlook item is not a mail message.")
    return item


def export_one_message(
    mail_item,
    folder_path,
    output_root,
    body_format="markdown",
    save_msg=True,
    save_attachments=True,
    skip_existing=False,
):
    received = coerce_datetime(getattr(mail_item, "ReceivedTime", None)) or datetime.now()
    subject = safe_text(mail_item.Subject).strip() or "(no subject)"
    entry_id = safe_text(getattr(mail_item, "EntryID", ""))
    identifier = entry_id or f"{received.isoformat()}::{subject}"
    directory_name = (
        f"{received.strftime('%Y%m%d-%H%M%S')}_"
        f"{safe_file_name(subject, max_length=80)}_"
        f"{short_hash(identifier)}"
    )
    target_dir = (
        output_root
        / received.strftime("%Y")
        / received.strftime("%m")
        / received.strftime("%d")
        / directory_name
    )

    if target_dir.exists():
        if skip_existing:
            return None
        target_dir = unique_directory(target_dir)

    target_dir.mkdir(parents=True, exist_ok=True)
    sender = get_sender_address(mail_item)

    if body_format == "markdown":
        body_path = target_dir / "message.md"
        body_value = markdown_body(mail_item, folder_path, sender)
    else:
        body_path = target_dir / "message.txt"
        body_value = safe_text(getattr(mail_item, "Body", ""))
    write_text(body_path, body_value, bom=True)

    saved_attachments = []
    if save_attachments and int(getattr(mail_item.Attachments, "Count", 0) or 0) > 0:
        attachments_dir = target_dir / "attachments"
        attachments_dir.mkdir(parents=True, exist_ok=True)
        for index, attachment in enumerate(iter_outlook_collection(mail_item.Attachments), start=1):
            raw_name = (
                safe_text(getattr(attachment, "FileName", ""))
                or safe_text(getattr(attachment, "DisplayName", ""))
                or f"attachment-{index}"
            )
            file_path = unique_path(attachments_dir / safe_file_name(raw_name))
            attachment.SaveAsFile(str(file_path))
            saved_attachments.append(
                {
                    "file_name": safe_text(getattr(attachment, "FileName", "")),
                    "display_name": safe_text(getattr(attachment, "DisplayName", "")),
                    "size": int(getattr(attachment, "Size", 0) or 0),
                    "saved_path": str(file_path),
                }
            )

    msg_path = ""
    if save_msg:
        msg_file = target_dir / "original.msg"
        mail_item.SaveAs(str(msg_file), OL_MSG_UNICODE)
        msg_path = str(msg_file)

    metadata = message_record(mail_item, folder_path)
    metadata.update(
        {
            "message_directory": str(target_dir),
            "body_path": str(body_path),
            "msg_path": msg_path,
            "saved_attachments": saved_attachments,
        }
    )
    write_json(target_dir / "metadata.json", metadata)

    return {
        "received_time": metadata["received_time"] or "",
        "subject": metadata["subject"],
        "sender": metadata["sender"],
        "folder_path": metadata["folder_path"],
        "message_directory": str(target_dir),
        "body_path": str(body_path),
        "msg_path": msg_path,
        "attachment_count": len(saved_attachments),
        "entry_id": metadata["entry_id"],
        "store_id": metadata["store_id"],
    }


def ensure_write_policy(args):
    if not getattr(args, "explicit_write_request", False):
        raise RuntimeError(
            "Drafting or sending mail is blocked unless --explicit-write-request is provided."
        )

    recipients = {
        "to": normalize_recipients(getattr(args, "to", [])),
        "cc": normalize_recipients(getattr(args, "cc", [])),
        "bcc": normalize_recipients(getattr(args, "bcc", [])),
    }
    if not recipients["to"]:
        raise RuntimeError("At least one --to recipient is required.")

    approved = {
        normalize_email_address(value)
        for value in normalize_recipients(getattr(args, "allow_recipient", []))
    }
    auto_allowed_recipients = resolve_auto_allowed_write_recipients()
    blocked = []

    for field_name, values in recipients.items():
        for value in values:
            normalized = normalize_email_address(value)
            if not normalized or "@" not in normalized:
                raise RuntimeError(f"Invalid {field_name.upper()} recipient: {value}")
            if (
                normalized not in auto_allowed_recipients
                and normalized not in approved
            ):
                blocked.append(normalized)

    if blocked:
        blocked_text = ", ".join(sorted(set(blocked)))
        auto_allowed_text = ", ".join(sorted(auto_allowed_recipients)) or "<not detected>"
        raise RuntimeError(
            "Recipient approval required before drafting or sending mail to: "
            f"{blocked_text}. Auto-allowed self address: {auto_allowed_text}. "
            f"If detection is wrong, set {SELF_ADDRESS_OVERRIDE_ENV} and re-run with "
            "--allow-recipient only after the user explicitly approves non-self recipients."
        )

    return {
        "to": recipients["to"],
        "cc": recipients["cc"],
        "bcc": recipients["bcc"],
        "approved": sorted(approved),
        "auto_allowed": sorted(auto_allowed_recipients),
    }


def build_body_payload(args):
    sources = [
        args.body is not None,
        bool(args.body_file),
        bool(args.html_body_file),
    ]
    if sum(bool(source) for source in sources) > 1:
        raise RuntimeError(
            "Provide only one of --body, --body-file, or --html-body-file."
        )
    if args.html_body_file:
        return "html", read_text_file(args.html_body_file)
    if args.body_file:
        return "text", read_text_file(args.body_file)
    return "text", safe_text(args.body)


def attach_files(mail_item, attachment_paths):
    attached_files = []
    for raw_path in attachment_paths or []:
        file_path = Path(raw_path).expanduser()
        if not file_path.exists() or not file_path.is_file():
            raise RuntimeError(f"Attachment file does not exist: {file_path}")
        resolved = str(file_path.resolve())
        mail_item.Attachments.Add(resolved)
        attached_files.append(resolved)
    return attached_files


def outgoing_result(mail_item, action, policy, attached_files):
    parent = getattr(mail_item, "Parent", None)
    return {
        "action": action,
        "subject": safe_text(getattr(mail_item, "Subject", "")),
        "to": safe_text(getattr(mail_item, "To", "")),
        "cc": safe_text(getattr(mail_item, "CC", "")),
        "bcc": safe_text(getattr(mail_item, "BCC", "")),
        "entry_id": safe_text(getattr(mail_item, "EntryID", "")),
        "store_id": safe_text(getattr(parent, "StoreID", "")) if parent is not None else "",
        "attachment_count": int(getattr(mail_item.Attachments, "Count", 0) or 0),
        "attachment_paths": attached_files,
        "approved_recipients": policy["approved"],
        "auto_allowed_recipients": policy["auto_allowed"],
    }


def handle_list_folders(args):
    with open_outlook_namespace() as (_app, namespace):
        payload = []
        stores = list(iter_outlook_collection(namespace.Stores))

        if args.json:
            for store in stores:
                store_name = safe_text(store.DisplayName)
                root = store.GetRootFolder()
                payload.extend(
                    iter_folder_rows(
                        root,
                        store_name=store_name,
                        max_depth=args.max_depth,
                        include_item_count=args.include_item_count,
                    )
                )
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        for store in stores:
            store_name = safe_text(store.DisplayName)
            print(f"[Store] {store_name}")
            root = store.GetRootFolder()
            for row in iter_folder_rows(
                root,
                store_name=store_name,
                max_depth=args.max_depth,
                include_item_count=args.include_item_count,
            ):
                indent = "  " * row["depth"]
                line = f"{indent}- {row['name']}"
                if row["folder_path"]:
                    line += f" [{row['folder_path']}]"
                if row["item_count"] is not None:
                    line += f" ({row['item_count']})"
                print(line)
            print()
    return 0


def handle_search_messages(args):
    with open_outlook_namespace() as (_app, namespace):
        root_folder, matched, scanned = filtered_messages(namespace, args)
        rows = [entry["record"] for entry in matched]
        payload = {
            "searched_folder": normalize_outlook_folder_path(root_folder),
            "scanned": scanned,
            "matched": len(rows),
            "messages": rows,
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        print(
            f"Searched '{payload['searched_folder']}' and scanned {scanned} Outlook item(s). "
            f"Matched {len(rows)} mail message(s)."
        )
        print()
        render_rows(rows)
    return 0


def handle_get_message(args):
    with open_outlook_namespace() as (_app, namespace):
        mail_item = load_mail_item(namespace, args.entry_id, args.store_id)
        folder_path = normalize_outlook_folder_path(getattr(mail_item, "Parent", None))
        record = message_record(mail_item, folder_path)
        if args.body_format == "markdown":
            body_value = markdown_body(mail_item, folder_path, record["sender"])
        else:
            body_value = safe_text(getattr(mail_item, "Body", ""))
        if args.json:
            payload = dict(record)
            payload["body_format"] = args.body_format
            payload["body"] = body_value
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(body_value)
    return 0


def handle_export_messages(args):
    output_root = Path(args.output_root).expanduser()
    if not output_root.is_absolute():
        output_root = output_root.resolve()

    with open_outlook_namespace() as (_app, namespace):
        root_folder, matched, scanned = filtered_messages(namespace, args)
        manifest_rows = []
        skipped = 0

        for entry in matched:
            manifest_row = export_one_message(
                entry["item"],
                entry["folder_path"],
                output_root=output_root,
                body_format=args.body_format,
                save_msg=args.save_msg,
                save_attachments=args.save_attachments,
                skip_existing=args.skip_existing,
            )
            if manifest_row is None:
                skipped += 1
                continue
            manifest_rows.append(manifest_row)

        manifest_path = ""
        if manifest_rows:
            manifest_file = output_root / f"manifest-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
            write_manifest_csv(manifest_file, manifest_rows)
            manifest_path = str(manifest_file)

        payload = {
            "searched_folder": normalize_outlook_folder_path(root_folder),
            "scanned": scanned,
            "matched": len(matched),
            "exported": len(manifest_rows),
            "skipped": skipped,
            "output_root": str(output_root),
            "manifest_path": manifest_path,
            "messages": manifest_rows,
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        print(
            f"Searched '{payload['searched_folder']}' and scanned {scanned} Outlook item(s). "
            f"Matched {len(matched)} message(s), exported {len(manifest_rows)}, skipped {skipped}."
        )
        print(f"Output root: {output_root}")
        if manifest_path:
            print(f"Manifest: {manifest_path}")
        if manifest_rows:
            print()
            for row in manifest_rows:
                print(
                    f"[{row['received_time']}] {row['sender']} | {row['subject']} -> {row['message_directory']}"
                )
    return 0


def prepare_outgoing_mail(args, app, policy, body_kind, body_value):
    mail_item = app.CreateItem(OL_MAIL_ITEM)
    mail_item.To = "; ".join(policy["to"])
    if policy["cc"]:
        mail_item.CC = "; ".join(policy["cc"])
    if policy["bcc"]:
        mail_item.BCC = "; ".join(policy["bcc"])
    mail_item.Subject = safe_text(args.subject)
    if body_kind == "html":
        mail_item.HTMLBody = body_value
    else:
        mail_item.Body = body_value
    attached_files = attach_files(mail_item, args.attachment)
    return mail_item, attached_files


def handle_draft_message(args):
    policy = ensure_write_policy(args)
    body_kind, body_value = build_body_payload(args)
    with open_outlook_namespace() as (app, _namespace):
        mail_item, attached_files = prepare_outgoing_mail(
            args,
            app,
            policy=policy,
            body_kind=body_kind,
            body_value=body_value,
        )
        mail_item.Save()
        print(
            json.dumps(
                outgoing_result(mail_item, "draft", policy, attached_files),
                ensure_ascii=False,
                indent=2,
            )
        )
    return 0


def handle_send_message(args):
    if not args.confirm_send:
        raise RuntimeError("Sending mail requires --confirm-send.")

    policy = ensure_write_policy(args)
    body_kind, body_value = build_body_payload(args)
    with open_outlook_namespace() as (app, _namespace):
        mail_item, attached_files = prepare_outgoing_mail(
            args,
            app,
            policy=policy,
            body_kind=body_kind,
            body_value=body_value,
        )
        mail_item.Save()
        result = outgoing_result(mail_item, "send", policy, attached_files)
        mail_item.Send()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def add_filter_arguments(parser):
    parser.add_argument(
        "--folder-path",
        default="Inbox",
        help="Outlook folder path or alias such as Inbox or Mailbox - Team\\Inbox",
    )
    parser.add_argument(
        "--include-subfolders",
        action="store_true",
        help="Search the selected folder recursively.",
    )
    parser.add_argument(
        "--received-since",
        type=parse_datetime_arg,
        help="Only include messages received on or after this ISO-like date/time.",
    )
    parser.add_argument(
        "--received-until",
        type=parse_datetime_arg,
        help="Only include messages received on or before this ISO-like date/time.",
    )
    parser.add_argument("--unread-only", action="store_true")
    parser.add_argument("--sender-contains")
    parser.add_argument("--subject-contains")
    parser.add_argument("--body-contains")
    parser.add_argument("--has-attachments", action="store_true")
    parser.add_argument("--attachment-name-contains")
    parser.add_argument("--max-items", type=int, default=50)


def add_outgoing_arguments(parser):
    parser.add_argument(
        "--to",
        action="append",
        required=True,
        help="Recipient address. Repeat the flag or use comma/semicolon-separated values.",
    )
    parser.add_argument("--cc", action="append", default=[])
    parser.add_argument("--bcc", action="append", default=[])
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body")
    parser.add_argument("--body-file")
    parser.add_argument("--html-body-file")
    parser.add_argument("--attachment", action="append", default=[])
    parser.add_argument(
        "--allow-recipient",
        action="append",
        default=[],
        help="Explicit recipient approval. Use only after the user approves non-default recipients.",
    )
    parser.add_argument(
        "--explicit-write-request",
        action="store_true",
        help="Required guard to confirm the current user turn explicitly requested mail writing.",
    )


def build_parser():
    parser = argparse.ArgumentParser(
        description="Read, export, draft, and send Outlook mail through desktop Outlook COM."
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    list_parser = subparsers.add_parser(
        "list-folders", help="List Outlook stores and folders visible to the current profile."
    )
    list_parser.add_argument("--max-depth", type=int, default=2)
    list_parser.add_argument("--include-item-count", action="store_true")
    list_parser.add_argument("--json", action="store_true")
    list_parser.set_defaults(handler=handle_list_folders)

    search_parser = subparsers.add_parser(
        "search-messages", help="Search messages in an Outlook folder with filters."
    )
    add_filter_arguments(search_parser)
    search_parser.add_argument("--json", action="store_true")
    search_parser.set_defaults(handler=handle_search_messages)

    get_parser = subparsers.add_parser(
        "get-message", help="Fetch a single mail message by Outlook entry ID."
    )
    get_parser.add_argument("--entry-id", required=True)
    get_parser.add_argument("--store-id")
    get_parser.add_argument("--body-format", choices=("markdown", "text"), default="markdown")
    get_parser.add_argument("--json", action="store_true")
    get_parser.set_defaults(handler=handle_get_message)

    export_parser = subparsers.add_parser(
        "export-messages",
        help="Export matching messages, metadata, original MSG files, and attachments.",
    )
    add_filter_arguments(export_parser)
    export_parser.add_argument("--output-root", required=True)
    export_parser.add_argument("--body-format", choices=("markdown", "text"), default="markdown")
    export_parser.add_argument("--skip-existing", action="store_true")
    export_parser.add_argument("--save-msg", dest="save_msg", action="store_true")
    export_parser.add_argument("--no-save-msg", dest="save_msg", action="store_false")
    export_parser.set_defaults(save_msg=True)
    export_parser.add_argument(
        "--save-attachments", dest="save_attachments", action="store_true"
    )
    export_parser.add_argument(
        "--no-save-attachments", dest="save_attachments", action="store_false"
    )
    export_parser.set_defaults(save_attachments=True)
    export_parser.add_argument("--json", action="store_true")
    export_parser.set_defaults(handler=handle_export_messages)

    draft_parser = subparsers.add_parser(
        "draft-message", help="Create an Outlook draft with the guarded recipient policy."
    )
    add_outgoing_arguments(draft_parser)
    draft_parser.set_defaults(handler=handle_draft_message)

    send_parser = subparsers.add_parser(
        "send-message", help="Send an Outlook message after explicit confirmation."
    )
    add_outgoing_arguments(send_parser)
    send_parser.add_argument(
        "--confirm-send",
        action="store_true",
        help="Required guard to confirm that sending is intended right now.",
    )
    send_parser.set_defaults(handler=handle_send_message)

    return parser


def main():
    configure_stdio()
    parser = build_parser()
    args = parser.parse_args()

    if getattr(args, "max_items", 1) <= 0:
        parser.error("--max-items must be a positive integer.")
    if getattr(args, "max_depth", 0) < 0:
        parser.error("--max-depth cannot be negative.")
    if (
        getattr(args, "received_since", None)
        and getattr(args, "received_until", None)
        and args.received_since > args.received_until
    ):
        parser.error("--received-since must be earlier than or equal to --received-until.")

    try:
        return args.handler(args)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
