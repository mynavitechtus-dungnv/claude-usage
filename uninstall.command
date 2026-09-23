#!/bin/bash
# Bấm đúp file này trong Finder để gỡ Claude Usage khỏi thanh menu.
cd "$(dirname "$0")" || exit 1
bash ./install.sh --uninstall
code=$?
echo
read -n 1 -s -r -p "Nhấn phím bất kỳ để đóng cửa sổ này..."
echo
exit $code
