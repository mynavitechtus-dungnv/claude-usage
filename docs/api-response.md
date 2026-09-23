# Response của `GET /api/oauth/usage`

Gọi thực tế ngày 2026-09-23 từ máy dev, HTTP 200. Chỉ giữ các field plugin dùng.

```
curl -H "Authorization: Bearer <accessToken>" \
     -H "anthropic-beta: oauth-2025-04-20" \
     https://api.anthropic.com/api/oauth/usage
```

```json
{
  "five_hour": { "utilization": 16.0, "resets_at": "2026-09-23T06:40:00.056602+00:00" },
  "seven_day": { "utilization": 42.0, "resets_at": "2026-09-27T10:00:00.056629+00:00" },
  "limits": [
    { "kind": "session",       "group": "session", "percent": 16, "severity": "normal",
      "resets_at": "2026-09-23T06:40:00.056602+00:00", "scope": null, "is_active": false },
    { "kind": "weekly_all",    "group": "weekly",  "percent": 42, "severity": "normal",
      "resets_at": "2026-09-27T10:00:00.056629+00:00", "scope": null, "is_active": true },
    { "kind": "weekly_scoped", "group": "weekly",  "percent": 42, "severity": "normal",
      "resets_at": "2026-09-27T10:00:00.056881+00:00",
      "scope": { "model": { "id": null, "display_name": "Fable" }, "surface": null },
      "is_active": false }
  ],
  "seven_day_breakdown": {
    "rows": [
      { "key": "claude_code", "display_name": "Claude Code", "percent": 100 },
      { "key": "chat",        "display_name": "Chats",       "percent": 0 }
    ]
  }
}
```

## Field plugin dùng

| Field | Ý nghĩa |
|---|---|
| `limits[].kind` | `session` = cửa sổ 5 giờ, `weekly_all` = tuần mọi model, `weekly_scoped` = tuần theo model |
| `limits[].percent` | số nguyên 0–100 |
| `limits[].severity` | `normal` hoặc mức cảnh báo, dùng đổi màu |
| `limits[].resets_at` | ISO 8601 UTC |
| `limits[].scope.model.display_name` | tên model của limit `weekly_scoped` |
| `limits[].is_active` | limit nào đang là mức chặn hiệu lực |

`five_hour` và `seven_day` là bản cũ của cùng dữ liệu, plugin dùng làm fallback khi thiếu `limits`.

## Token

Keychain macOS, item `Claude Code-credentials`, giá trị là JSON:

```json
{ "claudeAiOauth": { "accessToken": "...", "refreshToken": "...", "expiresAt": 0,
                     "scopes": ["user:profile", "..."], "subscriptionType": "...", "rateLimitTier": "..." } }
```

Đọc bằng: `security find-generic-password -s "Claude Code-credentials" -w`
