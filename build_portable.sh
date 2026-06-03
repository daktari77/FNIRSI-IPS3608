#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

# Driven by IPS3608RemoteControl.spec (single source of truth: output name
# FNIRSI-IPS3608, bundled font asset, windowed mode).
python -m PyInstaller --noconfirm --clean IPS3608RemoteControl.spec
