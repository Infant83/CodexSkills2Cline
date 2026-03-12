#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="all"
HOME_ROOT="${HOME:-}"
DEEPAGENTS_AGENT_NAME="agent"
DRY_RUN=0

resolve_primary_username() {
  if [[ -n "${USERNAME:-}" ]]; then
    printf '%s\n' "${USERNAME,,}"
    return
  fi

  basename "$HOME_ROOT" | tr '[:upper:]' '[:lower:]'
}

resolve_outlook_self_address() {
  if [[ -n "${OUTLOOK_MAIL_SELF_ADDRESS:-}" ]]; then
    printf '%s\n' "${OUTLOOK_MAIL_SELF_ADDRESS,,}"
    return
  fi

  local username
  username="$(resolve_primary_username)"
  if [[ -z "$username" ]]; then
    return
  fi

  printf '%s\n' "${username}@lgdisplay.com"
}

usage() {
  cat <<'EOF'
Usage: ./install.sh [--target all|cline|deepagents] [--home-root PATH] [--deepagents-agent-name NAME] [--dry-run]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="$2"
      shift 2
      ;;
    --home-root)
      HOME_ROOT="$2"
      shift 2
      ;;
    --deepagents-agent-name)
      DEEPAGENTS_AGENT_NAME="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

case "$TARGET" in
  all|cline|deepagents) ;;
  *)
    echo "Unsupported target: $TARGET" >&2
    exit 1
    ;;
esac

if [[ -z "$HOME_ROOT" ]]; then
  HOME_ROOT="$HOME"
fi

if [[ -z "$HOME_ROOT" ]]; then
  echo "Could not resolve the user home directory." >&2
  exit 1
fi

copy_dir_contents() {
  local source="$1"
  local target="$2"

  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[dry-run] mkdir -p $target"
    echo "[dry-run] cp -R $source/. $target/"
    return
  fi

  mkdir -p "$target"
  cp -R "$source"/. "$target"/
}

copy_file_to_target() {
  local source="$1"
  local target="$2"

  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[dry-run] mkdir -p $(dirname "$target")"
    echo "[dry-run] cp $source $target"
    return
  fi

  mkdir -p "$(dirname "$target")"
  cp "$source" "$target"
}

resolve_documents_root() {
  if command -v xdg-user-dir >/dev/null 2>&1; then
    local documents_root
    documents_root="$(xdg-user-dir DOCUMENTS 2>/dev/null || true)"
    if [[ -n "$documents_root" ]]; then
      printf '%s\n' "$documents_root"
      return
    fi
  fi

  printf '%s\n' "$HOME_ROOT/Documents"
}

install_cline_pack() {
  local source_root="$SCRIPT_DIR/cline"
  local skills_source="$SCRIPT_DIR/skills"
  local managed_home="$HOME_ROOT/.cline"
  local managed_rules="$managed_home/rules"
  local managed_workflows="$managed_home/workflows"
  local managed_skills="$managed_home/skills"
  local documents_root
  documents_root="$(resolve_documents_root)"
  local runtime_root="$documents_root/Cline"
  local runtime_rules="$runtime_root/Rules"
  local runtime_workflows="$runtime_root/Workflows"

  echo "Installing Cline pack"
  echo "  Managed home: $managed_home"
  echo "  Runtime rules: $runtime_rules"
  echo "  Runtime workflows: $runtime_workflows"

  copy_dir_contents "$source_root/rules" "$managed_rules"
  copy_dir_contents "$source_root/workflows" "$managed_workflows"
  copy_dir_contents "$skills_source" "$managed_skills"
  copy_dir_contents "$source_root/rules" "$runtime_rules"
  copy_dir_contents "$source_root/workflows" "$runtime_workflows"
}

install_deepagents_pack() {
  local source_root="$SCRIPT_DIR/deepagents"
  local skills_source="$SCRIPT_DIR/skills"
  local managed_home="$HOME_ROOT/.deepagents"
  local agent_home="$managed_home/$DEEPAGENTS_AGENT_NAME"
  local agent_skills="$agent_home/skills"

  echo "Installing DeepAgents pack"
  echo "  Managed home: $managed_home"
  echo "  Agent home: $agent_home"

  copy_file_to_target "$source_root/config.toml" "$managed_home/config.toml"
  copy_file_to_target "$source_root/agent/AGENTS.md" "$agent_home/AGENTS.md"
  copy_dir_contents "$skills_source" "$agent_skills"
}

if [[ "$TARGET" == "all" || "$TARGET" == "cline" ]]; then
  install_cline_pack
fi

if [[ "$TARGET" == "all" || "$TARGET" == "deepagents" ]]; then
  install_deepagents_pack
fi

echo
echo "Install complete."
echo
OUTLOOK_SELF_ADDRESS="$(resolve_outlook_self_address)"
if [[ -n "$OUTLOOK_SELF_ADDRESS" ]]; then
  echo "Outlook mail default self address: $OUTLOOK_SELF_ADDRESS"
  if [[ -n "${OUTLOOK_MAIL_SELF_ADDRESS:-}" ]]; then
    echo "  Source: OUTLOOK_MAIL_SELF_ADDRESS"
  else
    echo "  Source: current OS username + @lgdisplay.com"
  fi
else
  echo "Outlook mail default self address: <not detected>"
fi
echo "If this does not match your actual company mailbox address, set OUTLOOK_MAIL_SELF_ADDRESS before using outlook-mail."
echo '  Bash example: export OUTLOOK_MAIL_SELF_ADDRESS="actual.user@lgdisplay.com"'
echo "Restart or reload Cline and DeepAgents to pick up the updated files."
