#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Install research skills for Codex and/or Claude.

Usage:
  ./install.sh [--target codex|claude|both] [--method symlink|copy] [--skill NAME] [--agent-home PATH] [--force] [--dry-run]

Defaults:
  --target both
  --method symlink
  --skill all folders in this repo that contain SKILL.md

Examples:
  ./install.sh
  ./install.sh --target codex
  ./install.sh --method copy --force
  ./install.sh --skill create-dl-project --target both

Environment:
  CODEX_HOME   Defaults to ~/.codex
  CLAUDE_HOME  Defaults to ~/.claude
EOF
}

repo_root="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
target="both"
method="symlink"
force="false"
dry_run="false"
agent_home_override=""
skills=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      [ "$#" -ge 2 ] || { echo "Missing value for --target" >&2; exit 2; }
      target="$2"
      shift 2
      ;;
    --method)
      [ "$#" -ge 2 ] || { echo "Missing value for --method" >&2; exit 2; }
      method="$2"
      shift 2
      ;;
    --skill)
      [ "$#" -ge 2 ] || { echo "Missing value for --skill" >&2; exit 2; }
      skills+=("$2")
      shift 2
      ;;
    --agent-home)
      [ "$#" -ge 2 ] || { echo "Missing value for --agent-home" >&2; exit 2; }
      agent_home_override="$2"
      shift 2
      ;;
    --force)
      force="true"
      shift
      ;;
    --dry-run)
      dry_run="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$target" in
  codex|claude|both) ;;
  *) echo "--target must be codex, claude, or both" >&2; exit 2 ;;
esac

if [ -n "$agent_home_override" ] && [ "$target" = "both" ]; then
  echo "--agent-home requires --target codex or --target claude" >&2
  exit 2
fi

case "$method" in
  symlink|copy) ;;
  *) echo "--method must be symlink or copy" >&2; exit 2 ;;
esac

if [ "${#skills[@]}" -eq 0 ]; then
  for skill_dir in "$repo_root"/*; do
    if [ -d "$skill_dir" ] && [ -f "$skill_dir/SKILL.md" ]; then
      skills+=("$(basename "$skill_dir")")
    fi
  done
fi

if [ "${#skills[@]}" -eq 0 ]; then
  echo "No skill folders with SKILL.md found in $repo_root" >&2
  exit 1
fi

install_skill() {
  agent_label="$1"
  agent_home="$2"
  skill="$3"
  src="$repo_root/$skill"
  dest="$agent_home/skills/$skill"

  if [[ ! "$skill" =~ ^[a-z0-9][a-z0-9-]*$ ]] || [ ! -f "$src/SKILL.md" ]; then
    echo "Skill not found: $src" >&2
    exit 1
  fi

  echo "Installing $skill for $agent_label"
  echo "  source: $src"
  echo "  target: $dest"
  echo "  method: $method"

  if [ "$method" = "symlink" ] && [ -L "$dest" ]; then
    existing="$(readlink "$dest")"
    if [ "$existing" = "$src" ]; then
      echo "  already linked"
      return
    fi
  fi

  backup=""
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    if [ "$force" != "true" ]; then
      echo "Destination exists. Re-run with --force to replace: $dest" >&2
      exit 1
    fi
  fi

  if [ "$dry_run" = "true" ]; then
    return
  fi

  mkdir -p "$agent_home/skills"
  staging_dir="$(mktemp -d "$agent_home/.skill-install-XXXXXXXX")"
  if [ "$method" = "symlink" ]; then
    ln -s "$src" "$staging_dir/$skill" && prepared=true || prepared=false
  else
    cp -R "$src" "$staging_dir/$skill" && prepared=true || prepared=false
  fi
  if [ "$prepared" != "true" ]; then
    rm -rf "$staging_dir"
    echo "Could not prepare installation: $src" >&2
    exit 1
  fi
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    mkdir -p "$agent_home/skill-backups"
    backup_dir="$(mktemp -d "$agent_home/skill-backups/$skill-XXXXXXXX")"
    backup="$backup_dir/$skill"
    mv "$dest" "$backup"
    echo "  backup: $backup"
  fi

  mv "$staging_dir/$skill" "$dest" && installed=true || installed=false
  rm -rf "$staging_dir"
  if [ "$installed" != "true" ]; then
    if [ -n "$backup" ]; then
      mv "$backup" "$dest"
    fi
    echo "Installation failed; previous skill restored: $dest" >&2
    exit 1
  fi
}

for skill in "${skills[@]}"; do
  if [ "$target" = "codex" ] || [ "$target" = "both" ]; then
    install_skill "Codex" "${agent_home_override:-${CODEX_HOME:-$HOME/.codex}}" "$skill"
  fi

  if [ "$target" = "claude" ] || [ "$target" = "both" ]; then
    install_skill "Claude" "${agent_home_override:-${CLAUDE_HOME:-$HOME/.claude}}" "$skill"
  fi
done

echo "Done."
