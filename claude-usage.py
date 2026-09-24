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
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone

KEYCHAIN_SERVICE = "Claude Code-credentials"
USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
USAGE_PAGE = "https://claude.ai/settings/usage"
TIMEOUT = 10
ICON = " ⚡️ "
ICON_CALENDAR = " 🗓️ "
# Chu kỳ làm mới cho người dùng chọn. SwiftBar đọc chu kỳ từ tên file: claude-usage.<chu kỳ>.py
INTERVALS = ["2m", "5m", "10m", "15m", "30m"]
LANG_FILE = os.path.expanduser("~/Library/Application Support/claude-usage/language")
DEFAULT_LANG = "vi"
# Thứ tự hiện trong menu Ngôn ngữ. Tên ngôn ngữ viết bằng chính ngôn ngữ đó.
LANGS = [("vi", "Tiếng Việt"), ("en", "English"), ("ja", "日本語"), ("ko", "한국어"), ("zh", "简体中文")]
STRINGS = {
    "vi": {
        "weekdays": ["T2", "T3", "T4", "T5", "T6", "T7", "CN"],
        "date": "%d/%m %H:%M",
        "left": "{when} (còn {left})",
        "reset": "reset",
        "session": "Session 5h",
        "week": "Tuần",
        "week_scoped": "Tuần ({name})",
        "breakdown": "Tuần này dùng qua",
        "updated": "Cập nhật lúc {time}",
        "refresh": "Làm mới",
        "refresh_now": "Làm mới ngay",
        "auto_refresh": "Tự làm mới mỗi {interval}",
        "minutes": "{n} phút",
        "language": "Ngôn ngữ",
        "open_page": "Mở claude.ai/settings/usage",
        "err_keychain": "Không đọc được Keychain",
        "err_login": "Chưa đăng nhập Claude Code",
        "hint_login": "Chạy `claude` rồi /login để tạo token.",
        "err_cred": "Credential trong Keychain sai format",
        "err_http": "API trả HTTP {code}",
        "hint_401": "Token hết hạn, chạy `claude` một lần để refresh.",
        "err_api": "Không gọi được API",
        "err_limits": "API không có field limits",
    },
    "en": {
        "weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "date": "%d/%m %H:%M",
        "left": "{when} ({left} left)",
        "reset": "reset",
        "session": "Session 5h",
        "week": "Week",
        "week_scoped": "Week ({name})",
        "breakdown": "This week's usage by",
        "updated": "Updated at {time}",
        "refresh": "Refresh",
        "refresh_now": "Refresh now",
        "auto_refresh": "Auto-refresh every {interval}",
        "minutes": "{n} min",
        "language": "Language",
        "open_page": "Open claude.ai/settings/usage",
        "err_keychain": "Cannot read Keychain",
        "err_login": "Not logged in to Claude Code",
        "hint_login": "Run `claude`, then /login to create a token.",
        "err_cred": "Keychain credential has an unexpected format",
        "err_http": "API returned HTTP {code}",
        "hint_401": "Token expired. Run `claude` once to refresh it.",
        "err_api": "Cannot reach the API",
        "err_limits": "API response has no limits field",
    },
    "ja": {
        "weekdays": ["月", "火", "水", "木", "金", "土", "日"],
        "date": "%m/%d %H:%M",
        "left": "{when}（残り {left}）",
        "reset": "リセット",
        "session": "セッション 5時間",
        "week": "週間",
        "week_scoped": "週間 ({name})",
        "breakdown": "今週の使用内訳",
        "updated": "{time} に更新",
        "refresh": "更新",
        "refresh_now": "今すぐ更新",
        "auto_refresh": "自動更新の間隔: {interval}",
        "minutes": "{n}分",
        "language": "言語",
        "open_page": "claude.ai/settings/usage を開く",
        "err_keychain": "キーチェーンを読み取れません",
        "err_login": "Claude Code にログインしていません",
        "hint_login": "`claude` を実行し、/login でトークンを作成してください。",
        "err_cred": "キーチェーンの認証情報の形式が不正です",
        "err_http": "API が HTTP {code} を返しました",
        "hint_401": "トークンの有効期限切れです。`claude` を一度実行して更新してください。",
        "err_api": "API に接続できません",
        "err_limits": "API の応答に limits がありません",
    },
    "ko": {
        "weekdays": ["월", "화", "수", "목", "금", "토", "일"],
        "date": "%m/%d %H:%M",
        "left": "{when} ({left} 남음)",
        "reset": "초기화",
        "session": "세션 5시간",
        "week": "주간",
        "week_scoped": "주간 ({name})",
        "breakdown": "이번 주 사용 내역",
        "updated": "{time} 업데이트",
        "refresh": "새로고침",
        "refresh_now": "지금 새로고침",
        "auto_refresh": "자동 새로고침 간격: {interval}",
        "minutes": "{n}분",
        "language": "언어",
        "open_page": "claude.ai/settings/usage 열기",
        "err_keychain": "키체인을 읽을 수 없음",
        "err_login": "Claude Code에 로그인되어 있지 않음",
        "hint_login": "`claude` 실행 후 /login 으로 토큰을 만드세요.",
        "err_cred": "키체인 자격 증명 형식이 잘못됨",
        "err_http": "API가 HTTP {code} 반환",
        "hint_401": "토큰이 만료되었습니다. `claude`를 한 번 실행해 갱신하세요.",
        "err_api": "API에 연결할 수 없음",
        "err_limits": "API 응답에 limits 필드가 없음",
    },
    "zh": {
        "weekdays": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
        "date": "%m/%d %H:%M",
        "left": "{when}（剩余 {left}）",
        "reset": "重置",
        "session": "会话 5 小时",
        "week": "本周",
        "week_scoped": "本周 ({name})",
        "breakdown": "本周用量构成",
        "updated": "更新于 {time}",
        "refresh": "刷新",
        "refresh_now": "立即刷新",
        "auto_refresh": "自动刷新间隔：{interval}",
        "minutes": "{n} 分钟",
        "language": "语言",
        "open_page": "打开 claude.ai/settings/usage",
        "err_keychain": "无法读取钥匙串",
        "err_login": "未登录 Claude Code",
        "hint_login": "运行 `claude`，然后用 /login 生成令牌。",
        "err_cred": "钥匙串中的凭据格式错误",
        "err_http": "API 返回 HTTP {code}",
        "hint_401": "令牌已过期，运行一次 `claude` 即可刷新。",
        "err_api": "无法连接 API",
        "err_limits": "API 响应中没有 limits 字段",
    },
}
NAME_RE = re.compile(r"^claude-usage\.(\d+[smhd])\.py$")


def current_lang():
    try:
        with open(LANG_FILE) as f:
            lang = f.read().strip()
    except OSError:
        return DEFAULT_LANG
    return lang if lang in STRINGS else DEFAULT_LANG


LANG = current_lang()


def t(key, **kw):
    s = STRINGS[LANG][key]
    return s.format(**kw) if kw else s


def interval_label(value):
    return t("minutes", n=value[:-1]) if value and value.endswith("m") else (value or "?")


def set_lang(value):
    """Lưu ngôn ngữ vào LANG_FILE. Mục menu gọi kèm refresh=true nên SwiftBar vẽ lại ngay."""
    if value not in STRINGS:
        print(f"Ngôn ngữ không hợp lệ: {value}. Chọn một trong: {', '.join(STRINGS)}", file=sys.stderr)
        sys.exit(2)
    os.makedirs(os.path.dirname(LANG_FILE), exist_ok=True)
    with open(LANG_FILE, "w") as f:
        f.write(value)
    sys.exit(0)


def self_path():
    return os.environ.get("SWIFTBAR_PLUGIN_PATH") or os.path.abspath(__file__)


def current_interval():
    m = NAME_RE.match(os.path.basename(self_path()))
    return m.group(1) if m else None


def set_interval(value):
    """Đổi chu kỳ bằng cách đổi tên file plugin. SwiftBar thấy thư mục thay đổi và tự nạp lại."""
    if value not in INTERVALS:
        print(f"Chu kỳ không hợp lệ: {value}. Chọn một trong: {', '.join(INTERVALS)}", file=sys.stderr)
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
    print(f"{t('refresh')} | refresh=true")
    sys.exit(0)


def read_token():
    try:
        raw = subprocess.run(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            capture_output=True, text=True, timeout=TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        die(t("err_keychain"), e)
    if raw.returncode != 0:
        die(t("err_login"), t("hint_login") + "\n" + raw.stderr.strip())
    try:
        return json.loads(raw.stdout)["claudeAiOauth"]["accessToken"]
    except (ValueError, KeyError, TypeError) as e:
        die(t("err_cred"), e)


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
        hint = t("hint_401") if e.code == 401 else ""
        die(t("err_http", code=e.code), hint or e.read()[:300].decode(errors="replace"))
    except (urllib.error.URLError, OSError, ValueError) as e:
        die(t("err_api"), e)


def parse_iso(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def fmt_reset(dt, now):
    """'13:40 (còn 3h34m)' nếu hôm nay, 'T7 27/09 17:00 (còn 4d 14h)' nếu khác ngày (theo ngôn ngữ đang chọn)."""
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
        when = f"{t('weekdays')[local.weekday()]} {local.strftime(t('date'))}"
    return t("left", when=when, left=left)


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
            label = t("session")
        elif kind == "weekly_all":
            label = t("week")
        elif kind == "weekly_scoped":
            name = ((lim.get("scope") or {}).get("model") or {}).get("display_name") or "model"
            label = t("week_scoped", name=name)
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
    for kind, key, label in (("session", "five_hour", t("session")), ("weekly_all", "seven_day", t("week"))):
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


def text_width(s):
    """Độ rộng hiển thị: chữ Nhật/Hàn/Trung chiếm 2 ô."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)


def pad(s, width):
    return s + " " * (width - text_width(s))


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
        die(t("err_limits"), json.dumps(data)[:400])

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
    title = f"{ICON}{ICON_CALENDAR.join(parts)}"
    c = color_for(worst)
    print(f"{title} | font=Menlo{' color=' + c if c else ''}")
    print("---")

    # Chi tiết
    width = max(text_width(r["label"]) for r in rows)
    for r in rows:
        line = f"{pad(r['label'], width)}  {pct(r['percent']):>4}"
        if r["resets_at"]:
            line += f"   {t('reset')} {fmt_reset(r['resets_at'], now)}"
        if r["active"]:
            line += "  ●"
        c = color_for(r["severity"])
        print(f"{line} | font=Menlo{' color=' + c if c else ''}")

    breakdown = (data.get("seven_day_breakdown") or {}).get("rows") or []
    used = [b for b in breakdown if b.get("percent")]
    if used:
        print("---")
        print(f"{t('breakdown')} | size=11 color=gray")
        for b in used:
            print(f"  {b.get('display_name', b.get('key'))}: {b.get('percent')}% | size=11 font=Menlo")

    print("---")
    print(f"{t('updated', time=datetime.now().strftime('%H:%M'))} | size=11 color=gray")
    print(f"{t('refresh_now')} | refresh=true")
    cur = current_interval()
    print(t("auto_refresh", interval=interval_label(cur)))
    path = self_path().replace('"', '\\"')
    for key in INTERVALS:
        mark = " checked=true" if key == cur else ""
        print(f'--{interval_label(key)} | bash="{path}" param1=--set-interval param2={key} terminal=false{mark}')
    # Giữ chữ "Language" để ai lỡ chọn ngôn ngữ không đọc được vẫn tìm ra đường quay lại.
    print(t("language") if LANG == "en" else f"{t('language')} (Language)")
    for key, name in LANGS:
        mark = " checked=true" if key == LANG else ""
        print(f'--{name} | bash="{path}" param1=--set-lang param2={key} terminal=false refresh=true{mark}')
    print(f"{t('open_page')} | href={USAGE_PAGE}")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--set-interval":
        set_interval(sys.argv[2])
    if len(sys.argv) == 3 and sys.argv[1] == "--set-lang":
        set_lang(sys.argv[2])
    main()
