#!/bin/bash
# Bấm đúp file này trong Finder để cài Claude Usage lên thanh menu.
cd "$(dirname "$0")" || exit 1
bash ./install.sh
code=$?
echo
if [ $code -ne 0 ]; then echo "Cài đặt chưa xong (mã lỗi $code). Xem thông báo phía trên."; fi
read -n 1 -s -r -p "Nhấn phím bất kỳ để đóng cửa sổ này..."
echo
exit $code
