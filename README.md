**English** | [Tiếng Việt](README.vi.md)

# Claude Usage in the macOS menu bar

Shows your Claude usage right in the menu bar and refreshes it on the interval you choose (5 minutes by default).

```
⚡16% · 42%
```

- **The first number** is your usage in the current 5-hour session.
- **The second number** is your usage for the week.
- **Click it** to see when each limit resets and how long is left.

```
Session 5h     16%   reset 13:40 (3h34m left)
Week           42%   reset Sun 27/09 16:59 (4d 6h left)  ●
Week (Fable)   42%   reset Sun 27/09 16:59 (4d 6h left)
```

The ● marks the limit currently in effect. Text turns orange when you are close to a limit and red once you hit it.

## Change the language

The menu is in Vietnamese by default. Click the number in the menu bar, choose **Ngôn ngữ (Language)**, then pick
**Tiếng Việt, English, 日本語, 한국어 or 简体中文**. The menu redraws right away in the new language. Your choice is stored
in `~/Library/Application Support/claude-usage/language`, so it survives reinstalls and updates.

## Change the refresh interval

Click the number in the menu bar, choose **Auto-refresh every...**, then pick **2, 5, 10, 15 or 30 min**.
The current interval has a check mark. Your choice is kept when you reinstall or update.

To see fresh numbers without waiting, click **Refresh now**.

## Before you install

You need **Claude Code** installed and logged in on this Mac. The plugin reads the login credentials that Claude Code stores in the Keychain.

Quick check: open Terminal and type `claude`. If it asks you to log in, type `/login` and follow the steps.
If you don't have Claude Code yet, install it from <https://code.claude.com/docs/en/setup>.

The plugin does not work if you only use Claude on the web or in the desktop app without Claude Code.

## Install

### Option 1: paste one command into Terminal (recommended)

1. Open **Terminal**: press `⌘ Space`, type `Terminal`, press Enter.
2. Paste the command below and press Enter:

```bash
curl -fsSL https://raw.githubusercontent.com/mynavitechtus-dungnv/claude-usage/main/install.sh | bash
```

3. Wait until it prints **Hoàn tất** (Done). Look at the top right of the menu bar.

### Option 2: download and double-click

1. On the GitHub page, click the green **Code** button, then **Download ZIP**.
2. Open the downloaded zip file to extract it.
3. In the extracted folder, **double-click `install.command`**. A Terminal window opens and installs everything.

If macOS says it cannot open `install.command` because the developer cannot be verified:

- Close the message.
- Open **System Settings → Privacy & Security**, scroll down, and click **Open Anyway** next to `install.command`.
- Double-click `install.command` again and choose **Open**.

This message appears because files downloaded from the Internet are not signed by Apple. Option 1 skips this step.

### What the installer does

| Step | Action |
|---|---|
| 1 | Checks for Python 3. If Command Line Tools are missing, it opens Apple's install dialog and stops. Run it again after that finishes. |
| 2 | Checks that Claude Code is logged in. If not, it only warns and keeps going. |
| 3 | Installs [SwiftBar](https://swiftbar.app), a free open-source app that shows content in the menu bar. Uses Homebrew if available, otherwise downloads the official v2.1.1 release from GitHub. |
| 4 | Copies the plugin to `~/.swiftbar-plugins`, keeps the refresh interval you chose before, and hides the "SwiftBar" label in the menu bar so only the Claude numbers remain. |
| 5 | Opens SwiftBar and adds it to Login Items so it starts when you log in. |

You can run the installer as many times as you like. Running it again updates to the latest version.

### macOS dialogs you may see

| Dialog | Choose |
|---|---|
| SwiftBar wants to access the Keychain item "Claude Code-credentials" | **Always Allow** |
| Terminal wants to control "System Events" | **OK** (to add SwiftBar to Login Items) |
| Install Command Line Tools | **Install** |

## Uninstall

- Double-click **`uninstall.command`**, or
- Paste into Terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/mynavitechtus-dungnv/claude-usage/main/install.sh | bash -s -- --uninstall
```

This only removes the plugin. To remove SwiftBar completely, drag `SwiftBar.app` from Applications to the Trash and
remove it from System Settings → General → Login Items.

## When you see `⚡?`

Click `⚡?` to see the reason. Errors are also written to `~/Library/Logs/claude-usage.log`.

| Reason shown | Fix |
|---|---|
| Not logged in to Claude Code | Open Terminal, type `claude`, then `/login` |
| API returned HTTP 401 | The token expired. Open Terminal and type `claude` once so it refreshes |
| Cannot reach the API | Check your network |
| Anything else | Open an issue on GitHub and paste the log file |

## Quit SwiftBar

The menu bar shows only the Claude numbers. Right after startup, the "SwiftBar" label may show for a few seconds before it hides.

To quit SwiftBar, paste into Terminal:

```bash
osascript -e 'quit app "SwiftBar"'
```

To show the "SwiftBar" label again:

```bash
defaults delete com.ameba.SwiftBar StealthMode
```

---

## For developers

### How it works

1. Reads the OAuth token that Claude Code stores in the Keychain,
   item `Claude Code-credentials`, field `claudeAiOauth.accessToken`.
2. Calls `GET https://api.anthropic.com/api/oauth/usage` with the header `anthropic-beta: oauth-2025-04-20`.
3. Reads the `limits[]` array. Each element has `kind` (`session`, `weekly_all`, `weekly_scoped`), `percent`, `severity`, `resets_at`.
4. Prints it in SwiftBar format.

SwiftBar takes the run interval from the file name. In the repo the file is `claude-usage.py`. The installer copies it as
`claude-usage.<interval>.py`, for example `claude-usage.5m.py`. When the user picks an interval in the menu, SwiftBar calls
`claude-usage.<interval>.py --set-interval 10m`. The plugin renames its own file, and SwiftBar sees the folder change and
reloads it with the new interval. To choose the interval at install time, use an environment variable:

```bash
REFRESH=15m ./install.sh
```

The language chosen in the menu is applied by SwiftBar calling `claude-usage.<interval>.py --set-lang <code>`
(`vi`, `en`, `ja`, `ko`, `zh`). The plugin writes the code to `~/Library/Application Support/claude-usage/language`,
then SwiftBar reruns the plugin thanks to `refresh=true`. All displayed strings live in the `STRINGS` table at the top of the file.

This is an internal claude.ai endpoint with no public documentation. If the format changes, the plugin shows `⚡?` instead of crashing.
See `docs/api-response.md` for a sample response.

The plugin uses only the Python standard library, with no external dependencies. The token is only sent to `api.anthropic.com`.

### Editing the plugin

The plugin is **copied** into the plugin folder, not symlinked. After editing `claude-usage.py`, run `./install.sh` again.

Why no symlink: if the repo lives in `~/Documents`, `~/Desktop` or `~/Downloads`, macOS blocks SwiftBar from reading
the file through a symlink (`Operation not permitted`), and SwiftBar shows `?`.

Hiding the "SwiftBar" label takes two layers. The installer turns on `StealthMode`. But SwiftBar 2.1.1 on macOS 26 ignores
the hide setting at startup, so the label still shows. It only hides when SwiftBar rescans the plugin folder. So on the first
run after each SwiftBar launch, the plugin creates and deletes a hidden file in the plugin folder to force a rescan. The plugin
detects a launch through the `SWIFTBAR_LAUNCH_TIME` variable. See the `hide_swiftbar_fallback_item` function.

The installer does not call the `swiftbar://refreshallplugins` URL, because SwiftBar 2.1.1 crashes on it.
It restarts SwiftBar instead.

### Layout

```
claude-usage/
├── README.md              # English
├── README.vi.md           # Tiếng Việt
├── docs/api-response.md   # real sample response, token redacted
├── claude-usage.py        # SwiftBar plugin; the installer adds the interval to its name when copying
├── install.sh             # main installer, also works via curl | bash
├── install.command        # double-click in Finder to install
└── uninstall.command      # double-click in Finder to uninstall
```
