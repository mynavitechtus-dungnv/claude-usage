#!/usr/bin/env bash
# Cài plugin claude-usage cho SwiftBar trên macOS.
#
# Dùng:
#   ./install.sh                cài / cập nhật
#   ./install.sh --uninstall    gỡ plugin (giữ SwiftBar)
#   curl -fsSL https://raw.githubusercontent.com/mynavitechtus-dungnv/claude-usage/main/install.sh | bash
#
# Biến môi trường:
#   SWIFTBAR_PLUGIN_DIR   thư mục plugin (mặc định ~/.swiftbar-plugins)
set -euo pipefail

REPO_RAW="https://raw.githubusercontent.com/mynavitechtus-dungnv/claude-usage/main"
SWIFTBAR_ZIP="https://github.com/swiftbar/SwiftBar/releases/download/v2.1.1/SwiftBar.v2.1.1.b597.zip"
PLUGIN="claude-usage.2m.py"
PLUGIN_DIR="${SWIFTBAR_PLUGIN_DIR:-$HOME/.swiftbar-plugins}"
DEFAULTS_DOMAIN="com.ameba.SwiftBar"   # bundle id của SwiftBar
KEYCHAIN_SERVICE="Claude Code-credentials"

# Khi chạy qua "curl | bash" thì không có file script, HERE trỏ vào thư mục hiện tại.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || pwd)"

step() { printf '\n\033[1;34m[%s]\033[0m %s\n' "$1" "$2"; }
ok()   { printf '    \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '    \033[33m!\033[0m %s\n' "$*"; }
fail() { printf '\n\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

[[ "$(uname)" == "Darwin" ]] || fail "Chỉ chạy trên macOS."

find_swiftbar() {
  for p in /Applications/SwiftBar.app "$HOME/Applications/SwiftBar.app"; do
    [[ -d "$p" ]] && { echo "$p"; return 0; }
  done
  return 1
}

restart_swiftbar() {
  if pgrep -xq SwiftBar; then
    osascript -e 'quit app "SwiftBar"' >/dev/null 2>&1 || pkill -x SwiftBar || true
    for _ in $(seq 1 20); do pgrep -xq SwiftBar || break; sleep 0.5; done
  fi
  # Không dùng URL swiftbar://refreshallplugins: SwiftBar 2.1.1 crash khi nhận URL này.
  open -a SwiftBar
}

# ---------------------------------------------------------------- gỡ cài đặt
if [[ "${1:-}" == "--uninstall" ]]; then
  current="$(defaults read "$DEFAULTS_DOMAIN" PluginDirectory 2>/dev/null || echo "$PLUGIN_DIR")"
  if [[ -e "$current/$PLUGIN" || -L "$current/$PLUGIN" ]]; then
    rm -f "$current/$PLUGIN"
    ok "Đã xoá plugin khỏi $current"
  else
    warn "Không thấy plugin trong $current"
  fi
  pgrep -xq SwiftBar && restart_swiftbar
  printf '\nXong. SwiftBar vẫn còn trên máy. Muốn gỡ hẳn: kéo /Applications/SwiftBar.app vào Thùng rác.\n'
  exit 0
fi

echo "Cài Claude Usage lên thanh menu macOS"

# ---------------------------------------------------------------- 1. Python
step 1/5 "Kiểm tra Python 3"
if ! xcode-select -p >/dev/null 2>&1; then
  warn "Máy chưa có Command Line Tools của Apple (cần để chạy python3)."
  warn "Một cửa sổ cài đặt sẽ hiện ra. Bấm Install, đợi xong rồi chạy lại trình cài này."
  xcode-select --install >/dev/null 2>&1 || true
  fail "Chạy lại sau khi cài Command Line Tools xong."
fi
/usr/bin/env python3 -c 'import sys; assert sys.version_info >= (3, 7)' 2>/dev/null \
  || fail "python3 không chạy được hoặc quá cũ (cần 3.7+)."
ok "$(/usr/bin/env python3 --version 2>&1)"

# ---------------------------------------------------------------- 2. Claude Code
step 2/5 "Kiểm tra đăng nhập Claude Code"
if security find-generic-password -s "$KEYCHAIN_SERVICE" >/dev/null 2>&1; then
  ok "Đã thấy token Claude Code trong Keychain"
else
  warn "Chưa thấy token Claude Code. Plugin sẽ hiện ⚡? cho tới khi bạn đăng nhập."
  warn "Cách sửa: mở Terminal, gõ 'claude', rồi gõ /login."
fi

# ---------------------------------------------------------------- 3. SwiftBar
step 3/5 "Cài SwiftBar (ứng dụng hiển thị trên thanh menu)"
if app="$(find_swiftbar)"; then
  ok "Đã có: $app"
elif command -v brew >/dev/null 2>&1; then
  brew install --cask swiftbar
  ok "Đã cài qua Homebrew"
else
  tmp="$(mktemp -d)"
  echo "    Đang tải SwiftBar..."
  curl -fL --progress-bar "$SWIFTBAR_ZIP" -o "$tmp/SwiftBar.zip"
  ditto -x -k "$tmp/SwiftBar.zip" "$tmp/unzip"
  dest="/Applications"
  [[ -w "$dest" ]] || { dest="$HOME/Applications"; mkdir -p "$dest"; }
  rm -rf "$dest/SwiftBar.app"
  mv "$tmp/unzip/SwiftBar.app" "$dest/"
  rm -rf "$tmp"
  ok "Đã cài vào $dest/SwiftBar.app"
fi

# ---------------------------------------------------------------- 4. Plugin
step 4/5 "Cài plugin"
current="$(defaults read "$DEFAULTS_DOMAIN" PluginDirectory 2>/dev/null || true)"
if [[ -n "$current" && "$current" != "$PLUGIN_DIR" && -z "${SWIFTBAR_PLUGIN_DIR:-}" ]]; then
  PLUGIN_DIR="$current"
  ok "Dùng thư mục plugin SwiftBar đang có: $PLUGIN_DIR"
fi
mkdir -p "$PLUGIN_DIR"
defaults write "$DEFAULTS_DOMAIN" PluginDirectory -string "$PLUGIN_DIR"
# Ẩn mục "SwiftBar" dự phòng trên thanh menu, chỉ để lại số liệu Claude.
# Hoàn tác: defaults delete com.ameba.SwiftBar StealthMode
defaults write "$DEFAULTS_DOMAIN" StealthMode -bool true

# Copy, không symlink: nếu thư mục nguồn nằm trong ~/Documents, ~/Desktop, ~/Downloads
# thì macOS chặn SwiftBar đọc file qua symlink ("Operation not permitted").
rm -f "$PLUGIN_DIR/$PLUGIN"
if [[ -f "$HERE/$PLUGIN" ]]; then
  install -m 755 "$HERE/$PLUGIN" "$PLUGIN_DIR/$PLUGIN"
  ok "Đã copy plugin từ $HERE"
else
  curl -fsSL "$REPO_RAW/$PLUGIN" -o "$PLUGIN_DIR/$PLUGIN"
  chmod 755 "$PLUGIN_DIR/$PLUGIN"
  ok "Đã tải plugin từ GitHub"
fi

if out="$("$PLUGIN_DIR/$PLUGIN" 2>&1)"; then
  ok "Chạy thử: $(printf '%s\n' "$out" | head -1 | sed 's/ |.*//')"
else
  warn "Plugin chạy thử bị lỗi:"
  printf '%s\n' "$out" | sed 's/^/      /'
fi

# ---------------------------------------------------------------- 5. Khởi động
step 5/5 "Mở SwiftBar và bật tự chạy khi đăng nhập"
restart_swiftbar
ok "SwiftBar đã chạy"
app="$(find_swiftbar)"
if osascript -e 'tell application "System Events" to get name of every login item' 2>/dev/null | grep -q SwiftBar; then
  ok "SwiftBar đã có trong danh sách mở khi đăng nhập"
elif osascript -e "tell application \"System Events\" to make login item at end with properties {path:\"$app\", hidden:false}" >/dev/null 2>&1; then
  ok "Đã thêm SwiftBar vào danh sách mở khi đăng nhập"
else
  warn "Không tự thêm được. Tự thêm tại: System Settings > General > Login Items > bấm + > chọn SwiftBar."
fi

cat <<'MSG'

Hoàn tất. Nhìn lên thanh menu phía trên bên phải, sẽ thấy dạng:  ⚡16% · 42%
  - số đầu: mức dùng phiên 5 giờ
  - số sau: mức dùng trong tuần
Bấm vào để xem giờ reset.

Nếu macOS hỏi quyền truy cập Keychain, chọn "Always Allow".
MSG
