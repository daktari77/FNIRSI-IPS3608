#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

python -m PyInstaller --noconfirm --clean \
  --onedir \
  --windowed \
  --name IPS3608RemoteControl \
  --add-data "ips3608_app/assets:ips3608_app/assets" \
  ips3608_remote_ui.py
