#!/bin/sh

set -eu

INSTALL_DIR="${SHUOHA_INSTALL_DIR:-$HOME/.local/bin}"
MARK_BEGIN="# >>> shuoha >>>"
MARK_END="# <<< shuoha <<<"

usage() {
  cat <<'EOF'
用法:
  uninstall.sh [--install-dir <dir>]

示例:
  curl -fsSL https://raw.githubusercontent.com/synctoai/shuoha/main/scripts/uninstall.sh | sh
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --install-dir)
      INSTALL_DIR="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "未知参数: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

remove_block() {
  file="$1"
  [ -f "$file" ] || return 0

  tmp_file="$(mktemp)"
  awk -v begin="$MARK_BEGIN" -v end="$MARK_END" '
    $0 == begin { skip = 1; next }
    $0 == end { skip = 0; next }
    skip != 1 { print }
  ' "$file" >"$tmp_file"
  mv "$tmp_file" "$file"
}

rm -f "$INSTALL_DIR/shuoha"

remove_block "$HOME/.zshrc"
remove_block "$HOME/.bashrc"
remove_block "$HOME/.bash_profile"
remove_block "$HOME/.profile"

if [ -d "$INSTALL_DIR" ] && [ -z "$(ls -A "$INSTALL_DIR")" ]; then
  rmdir "$INSTALL_DIR"
fi

echo "已卸载 shuoha。"
echo "如果当前终端仍然保留旧 PATH，请重新打开一个终端窗口。"
