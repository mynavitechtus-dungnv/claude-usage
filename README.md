# Claude Usage trên thanh menu macOS

Hiện mức dùng Claude của bạn ngay trên thanh menu, cập nhật mỗi 2 phút.

```
⚡16% · 42%
```

- **Số đầu** là mức dùng trong phiên 5 giờ hiện tại.
- **Số sau** là mức dùng trong tuần.
- **Bấm vào** để xem giờ reset của từng giới hạn và còn bao lâu nữa.

```
Session 5h     16%   reset 13:40 (còn 3h34m)
Tuần           42%   reset CN 27/09 16:59 (còn 4d 6h)  ●
Tuần (Fable)   42%   reset CN 27/09 16:59 (còn 4d 6h)
```

Dấu ● đánh dấu giới hạn đang có hiệu lực. Chữ chuyển cam khi sắp chạm giới hạn và đỏ khi đã chạm.

## Trước khi cài

Bạn cần **Claude Code** đã đăng nhập trên máy. Plugin đọc thông tin đăng nhập mà Claude Code lưu trong Keychain.

Kiểm tra nhanh: mở Terminal, gõ `claude`. Nếu nó hỏi đăng nhập thì gõ `/login` và làm theo.
Nếu máy chưa có Claude Code, cài theo hướng dẫn tại <https://code.claude.com/docs/en/setup>.

Plugin không dùng được nếu bạn chỉ dùng Claude trên web hoặc app desktop mà không có Claude Code.

## Cài đặt

### Cách 1: dán một lệnh vào Terminal (khuyên dùng)

1. Mở **Terminal**: bấm `⌘ Space`, gõ `Terminal`, Enter.
2. Dán lệnh dưới đây rồi Enter:

```bash
curl -fsSL https://raw.githubusercontent.com/mynavitechtus-dungnv/claude-usage/main/install.sh | bash
```

3. Đợi chữ **Hoàn tất**. Nhìn lên thanh menu phía trên bên phải.

### Cách 2: tải về và bấm đúp

1. Trên trang GitHub, bấm nút xanh **Code** rồi **Download ZIP**.
2. Mở file zip vừa tải để giải nén.
3. Trong thư mục vừa giải nén, **bấm đúp `install.command`**. Một cửa sổ Terminal mở ra và tự cài.

Nếu macOS báo không mở được `install.command` vì chưa xác minh được nhà phát triển:

- Đóng thông báo.
- Mở **System Settings → Privacy & Security**, cuộn xuống, bấm **Open Anyway** cạnh dòng `install.command`.
- Bấm đúp `install.command` lần nữa rồi chọn **Open**.

Thông báo này xuất hiện vì file tải từ Internet chưa được Apple ký. Cách 1 không gặp bước này.

### Trình cài làm gì

| Bước | Việc làm |
|---|---|
| 1 | Kiểm tra Python 3. Nếu máy chưa có Command Line Tools, mở hộp thoại cài của Apple rồi dừng, cài xong chạy lại. |
| 2 | Kiểm tra Claude Code đã đăng nhập chưa. Chưa thì chỉ cảnh báo, vẫn cài tiếp. |
| 3 | Cài [SwiftBar](https://swiftbar.app), app miễn phí mã nguồn mở để hiện nội dung lên thanh menu. Dùng Homebrew nếu có, không thì tải bản chính thức v2.1.1 từ GitHub. |
| 4 | Copy plugin vào `~/.swiftbar-plugins` và ẩn chữ "SwiftBar" trên thanh menu, chỉ để lại số liệu Claude. |
| 5 | Mở SwiftBar và thêm nó vào Login Items để tự chạy khi bật máy. |

Chạy lại trình cài bao nhiêu lần cũng được. Lần sau chính là cập nhật lên bản mới.

### Các hộp thoại macOS có thể hỏi

| Hộp thoại | Chọn |
|---|---|
| SwiftBar muốn truy cập Keychain "Claude Code-credentials" | **Always Allow** |
| Terminal muốn điều khiển "System Events" | **OK** (để thêm SwiftBar vào Login Items) |
| Cài Command Line Tools | **Install** |

## Gỡ cài đặt

- Bấm đúp **`uninstall.command`**, hoặc
- Dán vào Terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/mynavitechtus-dungnv/claude-usage/main/install.sh | bash -s -- --uninstall
```

Lệnh gỡ chỉ xoá plugin. Muốn bỏ hẳn SwiftBar thì kéo `SwiftBar.app` trong Applications vào Thùng rác, và xoá nó khỏi System Settings → General → Login Items.

## Khi thấy `⚡?`

Bấm vào `⚡?` để xem lý do. Lỗi cũng được ghi vào `~/Library/Logs/claude-usage.log`.

| Lý do hiện ra | Cách sửa |
|---|---|
| Chưa đăng nhập Claude Code | Mở Terminal, gõ `claude`, rồi `/login` |
| API trả HTTP 401 | Token hết hạn. Mở Terminal, gõ `claude` một lần để nó tự làm mới |
| Không gọi được API | Kiểm tra mạng |
| Khác | Mở issue trên GitHub, dán nội dung file log |

## Thoát SwiftBar

Thanh menu chỉ hiện số liệu Claude. Lúc mới bật máy, chữ "SwiftBar" có thể hiện vài giây rồi tự ẩn.

Muốn thoát SwiftBar, dán vào Terminal:

```bash
osascript -e 'quit app "SwiftBar"'
```

Muốn hiện lại chữ "SwiftBar":

```bash
defaults delete com.ameba.SwiftBar StealthMode
```

---

## Dành cho người phát triển

### Cách hoạt động

1. Đọc token OAuth mà Claude Code lưu trong Keychain,
   item `Claude Code-credentials`, field `claudeAiOauth.accessToken`.
2. Gọi `GET https://api.anthropic.com/api/oauth/usage` với header `anthropic-beta: oauth-2025-04-20`.
3. Đọc mảng `limits[]`. Mỗi phần tử có `kind` (`session`, `weekly_all`, `weekly_scoped`), `percent`, `severity`, `resets_at`.
4. In ra định dạng SwiftBar. SwiftBar tự chạy lại mỗi 2 phút theo tên file `*.2m.py`.

Đây là endpoint nội bộ của claude.ai, chưa có tài liệu công khai. Nếu format đổi, plugin hiện `⚡?` thay vì crash.
Mẫu response xem `docs/api-response.md`.

Plugin chỉ dùng thư viện chuẩn của Python, không có dependency ngoài. Token chỉ gửi tới `api.anthropic.com`.

### Sửa plugin

Plugin được **copy** vào thư mục plugin, không symlink. Sửa `claude-usage.2m.py` xong thì chạy lại `./install.sh`.

Lý do không symlink: nếu repo nằm trong `~/Documents`, `~/Desktop` hoặc `~/Downloads`, macOS chặn SwiftBar
đọc file qua symlink (`Operation not permitted`), và SwiftBar hiện dấu `?`.

Ẩn chữ "SwiftBar" cần hai lớp. Trình cài bật `StealthMode`. Nhưng SwiftBar 2.1.1 trên macOS 26 bỏ qua lệnh ẩn
lúc khởi động, nên chữ đó vẫn hiện. Nó chỉ ẩn khi SwiftBar quét lại thư mục plugin. Vì vậy, lần chạy đầu tiên sau mỗi
lần SwiftBar khởi động, plugin tạo rồi xoá một file ẩn trong thư mục plugin để ép SwiftBar quét lại. Plugin nhận biết lần
khởi động qua biến `SWIFTBAR_LAUNCH_TIME`. Xem hàm `hide_swiftbar_fallback_item`.

Trình cài không gọi URL `swiftbar://refreshallplugins`, vì SwiftBar 2.1.1 crash khi nhận URL này.
Nó khởi động lại SwiftBar thay thế.

### Cấu trúc

```
claude-usage/
├── README.md
├── docs/api-response.md   # mẫu response thực tế, đã che token
├── claude-usage.2m.py     # plugin SwiftBar
├── install.sh             # trình cài chính, chạy được cả qua curl | bash
├── install.command        # bấm đúp trong Finder để cài
└── uninstall.command      # bấm đúp trong Finder để gỡ
```
