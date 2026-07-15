#!/bin/sh
set -eu

usage() {
  echo "usage: configure-git-hooks.sh --check | --install | --self-test" >&2
  exit 2
}

if [ "${1:-}" = "--self-test" ]; then
  script=$(cd "$(dirname "$0")" && pwd)/$(basename "$0")
  source_root=$(cd "$(dirname "$0")/../.." && pwd)
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT HUP INT TERM
  git -C "$tmp" init -q
  mkdir -p "$tmp/.githooks"
  cp "$source_root/.githooks/pre-commit" "$tmp/.githooks/pre-commit"
  chmod +x "$tmp/.githooks/pre-commit"
  if (cd "$tmp" && "$script" --check >/dev/null 2>&1); then
    echo "self-test: inactive hooks path was accepted" >&2
    exit 1
  fi
  (cd "$tmp" && "$script" --install >/dev/null)
  (cd "$tmp" && "$script" --check >/dev/null)
  git -C "$tmp" config --local core.hooksPath foreign-hooks
  if (cd "$tmp" && "$script" --install >/dev/null 2>&1); then
    echo "self-test: foreign hooks path was overwritten" >&2
    exit 1
  fi
  test "$(git -C "$tmp" config --local --get core.hooksPath)" = "foreign-hooks"
  echo "configure-git-hooks self-test: PASS (check, explicit install, collision refusal)"
  exit 0
fi

[ "$#" -eq 1 ] || usage
case "$1" in
  --check|--install) ;;
  *) usage ;;
esac

root=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "not inside a Git repository" >&2
  exit 2
}
hook="$root/.githooks/pre-commit"
if [ ! -x "$hook" ]; then
  echo "tracked .githooks/pre-commit is missing or not executable" >&2
  exit 2
fi
current=$(git -C "$root" config --local --get core.hooksPath 2>/dev/null || true)

if [ "$1" = "--check" ]; then
  if [ "$current" = ".githooks" ]; then
    echo "core.hooksPath: PASS (.githooks)"
    exit 0
  fi
  if [ -z "$current" ]; then
    echo "core.hooksPath: INACTIVE (explicit --install required)" >&2
  else
    echo "core.hooksPath: REFUSED (foreign value: $current)" >&2
  fi
  exit 2
fi

if [ -n "$current" ] && [ "$current" != ".githooks" ]; then
  echo "refusing to overwrite foreign core.hooksPath: $current" >&2
  exit 2
fi
if [ -z "$current" ]; then
  git -C "$root" config --local core.hooksPath .githooks
fi
echo "core.hooksPath: PASS (.githooks)"
