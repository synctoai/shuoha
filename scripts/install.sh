#!/bin/sh

set -eu

REPO="${SHUOHA_REPO:-synctoai/shuoha}"
VERSION="latest"
INSTALL_DIR="${SHUOHA_INSTALL_DIR:-$HOME/.local/bin}"
MARK_BEGIN="# >>> shuoha >>>"
MARK_END="# <<< shuoha <<<"

usage() {
  cat <<'EOF'
用法:
  install.sh [--version <tag>] [--install-dir <dir>] [--repo <owner/name>]

示例:
  curl -fsSL https://raw.githubusercontent.com/synctoai/shuoha/main/scripts/install.sh | sh
  curl -fsSL https://raw.githubusercontent.com/synctoai/shuoha/main/scripts/install.sh | sh -s -- --version v0.1.0
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --version)
      VERSION="$2"
      shift 2
      ;;
    --install-dir)
      INSTALL_DIR="$2"
      shift 2
      ;;
    --repo)
      REPO="$2"
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

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "缺少依赖命令: $1" >&2
    exit 1
  fi
}

detect_asset() {
  os="$(uname -s)"
  arch="$(uname -m)"

  case "$os" in
    Darwin) platform="darwin" ;;
    *)
      echo "当前安装脚本只支持 macOS。检测到系统: $os" >&2
      exit 1
      ;;
  esac

  case "$arch" in
    arm64|aarch64) machine="arm64" ;;
    x86_64|amd64) machine="amd64" ;;
    *)
      echo "不支持的 CPU 架构: $arch" >&2
      exit 1
      ;;
  esac

  echo "shuoha-${platform}-${machine}.tar.gz"
}

release_url() {
  asset="$1"
  if [ "$VERSION" = "latest" ]; then
    echo "https://github.com/${REPO}/releases/latest/download/${asset}"
  else
    echo "https://github.com/${REPO}/releases/download/${VERSION}/${asset}"
  fi
}

choose_rc_file() {
  shell_name="$(basename "${SHELL:-}")"
  case "$shell_name" in
    zsh)
      echo "$HOME/.zshrc"
      ;;
    bash)
      if [ "$(uname -s)" = "Darwin" ]; then
        echo "$HOME/.bash_profile"
      else
        echo "$HOME/.bashrc"
      fi
      ;;
    *)
      if [ -f "$HOME/.zshrc" ]; then
        echo "$HOME/.zshrc"
      elif [ -f "$HOME/.bash_profile" ]; then
        echo "$HOME/.bash_profile"
      else
        echo "$HOME/.bashrc"
      fi
      ;;
  esac
}

ensure_path_in_shell_rc() {
  rc_file="$1"
  mkdir -p "$(dirname "$rc_file")"
  touch "$rc_file"

  if grep -Fq "$MARK_BEGIN" "$rc_file"; then
    return
  fi

  {
    printf "\n%s\n" "$MARK_BEGIN"
    printf "export PATH=\"%s:\$PATH\"\n" "$INSTALL_DIR"
    printf "%s\n" "$MARK_END"
  } >>"$rc_file"
}

need_cmd curl
need_cmd tar
need_cmd mktemp

asset="$(detect_asset)"
url="$(release_url "$asset")"
tmpdir="$(mktemp -d)"
archive_path="$tmpdir/$asset"
target_path="$INSTALL_DIR/shuoha"

cleanup() {
  rm -rf "$tmpdir"
}

trap cleanup EXIT INT TERM

echo "正在下载 ${url}"
curl -fsSL "$url" -o "$archive_path"

mkdir -p "$INSTALL_DIR"
tar -xzf "$archive_path" -C "$tmpdir"
install -m 0755 "$tmpdir/shuoha" "$target_path"

rc_file="$(choose_rc_file)"
ensure_path_in_shell_rc "$rc_file"
PATH="$INSTALL_DIR:$PATH"

"$target_path" --help >/dev/null 2>&1

echo "已安装到 $target_path"
echo "已写入 PATH 配置: $rc_file"
echo "如当前终端还找不到 shuoha，请执行:"
echo "  source \"$rc_file\""
echo "然后运行:"
echo "  shuoha analyze 600519"
