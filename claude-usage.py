#!/usr/bin/env python3
# <xbar.title>Claude Usage</xbar.title>
# <xbar.version>v1.0</xbar.version>
# <xbar.desc>Hiện % usage Claude (session 5h, tuần) và giờ reset.</xbar.desc>
# <xbar.dependencies>python3</xbar.dependencies>
# <swiftbar.hideAbout>true</swiftbar.hideAbout>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideSwiftBar>true</swiftbar.hideSwiftBar>
"""
Plugin SwiftBar: đọc token OAuth của Claude Code trong Keychain,
gọi https://api.anthropic.com/api/oauth/usage, in ra định dạng SwiftBar.
Không có dependency ngoài stdlib.
"""
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

KEYCHAIN_SERVICE = "Claude Code-credentials"
USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
USAGE_PAGE = "https://claude.ai/settings/usage"
TIMEOUT = 10
ICON = "⚡"
WEEKDAYS = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
# Chu kỳ làm mới cho người dùng chọn. SwiftBar đọc chu kỳ từ tên file: claude-usage.<chu kỳ>.py
INTERVALS = [("2m", "2 phút"), ("5m", "5 phút"), ("10m", "10 phút"), ("15m", "15 phút"), ("30m", "30 phút")]
NAME_RE = re.compile(r"^claude-usage\.(\d+[smhd])\.py$")


def self_path():
    return os.environ.get("SWIFTBAR_PLUGIN_PATH") or os.path.abspath(__file__)


def current_interval():
    m = NAME_RE.match(os.path.basename(self_path()))
    return m.group(1) if m else None


def set_interval(value):
    """Đổi chu kỳ bằng cách đổi tên file plugin. SwiftBar thấy thư mục thay đổi và tự nạp lại."""
    if value not in dict(INTERVALS):
        print(f"Chu kỳ không hợp lệ: {value}. Chọn một trong: {', '.join(k for k, _ in INTERVALS)}", file=sys.stderr)
        sys.exit(2)
    src = self_path()
    if not NAME_RE.match(os.path.basename(src)):
        print(f"Tên file không đúng dạng claude-usage.<chu kỳ>.py: {src}", file=sys.stderr)
        sys.exit(2)
    dst = os.path.join(os.path.dirname(src), f"claude-usage.{value}.py")
    if dst != src:
        os.rename(src, dst)
    sys.exit(0)


LOG_FILE = os.path.expanduser("~/Library/Logs/claude-usage.log")


def log_error(short, detail):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')} {short}: {detail}\n")
    except OSError:
        pass


def die(short, detail):
    """In trạng thái lỗi rồi thoát. Menu bar hiện ⚡?, dropdown hiện lý do và ghi log."""
    log_error(short, detail)
    print(f"{ICON}? | color=gray")
    print("---")
    print(f"{short} | color=red")
    for line in str(detail).splitlines():
        print(f"{line} | size=11 font=Menlo")
    print("---")
    print("Làm mới | refresh=true")
    sys.exit(0)


def read_token():
    try:
        raw = subprocess.run(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            capture_output=True, text=True, timeout=TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        die("Không đọc được Keychain", e)
    if raw.returncode != 0:
        die("Chưa đăng nhập Claude Code", "Chạy `claude` rồi /login để tạo token.\n" + raw.stderr.strip())
    try:
        return json.loads(raw.stdout)["claudeAiOauth"]["accessToken"]
    except (ValueError, KeyError, TypeError) as e:
        die("Credential trong Keychain sai format", e)


def fetch_usage(token):
    req = urllib.request.Request(
        USAGE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "anthropic-beta": "oauth-2025-04-20",
            "Content-Type": "application/json",
            "User-Agent": "claude-usage-swiftbar/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        hint = "Token hết hạn, chạy `claude` một lần để refresh." if e.code == 401 else ""
        die(f"API trả HTTP {e.code}", hint or e.read()[:300].decode(errors="replace"))
    except (urllib.error.URLError, OSError, ValueError) as e:
        die("Không gọi được API", e)


def parse_iso(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def fmt_reset(dt, now):
    """'13:40 (còn 3h34m)' nếu hôm nay, 'T7 27/09 17:00 (còn 4d 14h)' nếu khác ngày."""
    if dt is None:
        return "?"
    local = dt.astimezone()
    delta = dt - now
    secs = max(int(delta.total_seconds()), 0)
    d, rem = divmod(secs, 86400)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    if d:
        left = f"{d}d {h}h"
    elif h:
        left = f"{h}h{m:02d}m"
    else:
        left = f"{m}m"
    if local.date() == now.astimezone().date():
        when = local.strftime("%H:%M")
    else:
        when = f"{WEEKDAYS[local.weekday()]} {local.strftime('%d/%m %H:%M')}"
    return f"{when} (còn {left})"


def color_for(severity):
    if severity in (None, "normal"):
        return None
    if severity == "warning":
        return "orange"
    return "red"


def normalize(data):
    """Trả về list dict {label, percent, severity, resets_at, active} từ response."""
    rows = []
    limits = data.get("limits") or []
    for lim in limits:
        kind = lim.get("kind")
        if kind == "session":
            label = "Session 5h"
        elif kind == "weekly_all":
            label = "Tuần"
        elif kind == "weekly_scoped":
            name = ((lim.get("scope") or {}).get("model") or {}).get("display_name") or "model"
            label = f"Tuần ({name})"
        else:
            label = kind or "?"
        rows.append({
            "kind": kind,
            "label": label,
            "percent": lim.get("percent"),
            "severity": lim.get("severity"),
            "resets_at": parse_iso(lim.get("resets_at")),
            "active": bool(lim.get("is_active")),
        })
    if rows:
        return rows
    # Fallback: response cũ chỉ có five_hour / seven_day
    for kind, key, label in (("session", "five_hour", "Session 5h"), ("weekly_all", "seven_day", "Tuần")):
        blk = data.get(key)
        if isinstance(blk, dict) and blk.get("utilization") is not None:
            rows.append({
                "kind": kind, "label": label,
                "percent": round(blk["utilization"]),
                "severity": "normal",
                "resets_at": parse_iso(blk.get("resets_at")),
                "active": False,
            })
    return rows


def pct(v):
    return "?" if v is None else f"{int(round(v))}%"


def hide_swiftbar_fallback_item():
    """Workaround SwiftBar 2.1.1 trên macOS 26.

    Dù đã bật StealthMode, mục chữ "SwiftBar" vẫn hiện trên thanh menu sau mỗi lần SwiftBar
    khởi động: lệnh ẩn gọi lúc khởi động không có tác dụng. SwiftBar ẩn được nó khi quét lại
    thư mục plugin. Vì vậy mỗi lần SwiftBar khởi động, plugin tạo rồi xoá một file ẩn trong
    thư mục plugin sau vài giây để SwiftBar quét lại. File ẩn không bị nạp thành plugin.
    """
    launch = os.environ.get("SWIFTBAR_LAUNCH_TIME")
    plugins_dir = os.environ.get("SWIFTBAR_PLUGINS_PATH")
    if not launch or not plugins_dir or not os.path.isdir(plugins_dir):
        return  # không chạy dưới SwiftBar
    state = os.path.join(os.path.expanduser("~/Library/Caches"), "claude-usage-launch")
    try:
        with open(state) as f:
            if f.read().strip() == launch:
                return  # đã làm cho lần khởi động này
    except OSError:
        pass
    try:
        with open(state, "w") as f:
            f.write(launch)
    except OSError:
        return
    nudge = os.path.join(plugins_dir, ".claude-usage-rescan")
    script = f'sleep 5; touch "{nudge}"; sleep 2; rm -f "{nudge}"'
    try:
        subprocess.Popen(
            ["/bin/sh", "-c", script],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        pass


def main():
    hide_swiftbar_fallback_item()
    token = read_token()
    data = fetch_usage(token)
    rows = normalize(data)
    if not rows:
        die("API không có field limits", json.dumps(data)[:400])

    now = datetime.now(timezone.utc)
    by_kind = {r["kind"]: r for r in rows}
    session = by_kind.get("session")
    weekly = by_kind.get("weekly_all")

    # Dòng menu bar
    parts = [pct(session["percent"]) if session else "?"]
    if weekly:
        parts.append(pct(weekly["percent"]))
    worst = "normal"
    for r in rows:
        if r["severity"] not in (None, "normal"):
            worst = r["severity"] if worst == "normal" or r["severity"] != "warning" else worst
    title = f"{ICON}{' · '.join(parts)}"
    c = color_for(worst)
    print(f"{title} | font=Menlo{' color=' + c if c else ''}")
    print("---")

    # Chi tiết
    width = max(len(r["label"]) for r in rows)
    for r in rows:
        line = f"{r['label']:<{width}}  {pct(r['percent']):>4}"
        if r["resets_at"]:
            line += f"   reset {fmt_reset(r['resets_at'], now)}"
        if r["active"]:
            line += "  ●"
        c = color_for(r["severity"])
        print(f"{line} | font=Menlo{' color=' + c if c else ''}")

    breakdown = (data.get("seven_day_breakdown") or {}).get("rows") or []
    used = [b for b in breakdown if b.get("percent")]
    if used:
        print("---")
        print("Tuần này dùng qua | size=11 color=gray")
        for b in used:
            print(f"  {b.get('display_name', b.get('key'))}: {b.get('percent')}% | size=11 font=Menlo")

    print("---")
    print(f"Cập nhật lúc {datetime.now().strftime('%H:%M')} | size=11 color=gray")
    print("Làm mới ngay | refresh=true")
    cur = current_interval()
    print(f"Tự làm mới mỗi {dict(INTERVALS).get(cur, cur or '?')}")
    path = self_path().replace('"', '\\"')
    for key, label in INTERVALS:
        mark = " checked=true" if key == cur else ""
        print(f'--{label} | bash="{path}" param1=--set-interval param2={key} terminal=false{mark}')
    print(f"Mở claude.ai/settings/usage | href={USAGE_PAGE}")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--set-interval":
        set_interval(sys.argv[2])
    main()
