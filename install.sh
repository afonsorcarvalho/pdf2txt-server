#!/usr/bin/env bash
#
# Script de instalação do serviço pdf2txt-watcher em sistemas baseados em systemd
# (Raspberry Pi OS/Debian). Cria venv, instala dependências, configura e inicia o service.
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
PYTHON_BIN="python3"

echo "[1/5] Criando e ativando venv em: $VENV_DIR"
if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "[2/5] Instalando dependências no venv"
pip install --upgrade pip
pip install pdfplumber watchdog pyyaml

echo "[3/5] Garantindo diretório monitorado do config.yml"
WATCH_DIR="$($VENV_DIR/bin/python -c "import yaml,sys; print(yaml.safe_load(open('$PROJECT_DIR/config.yml','r',encoding='utf-8'))['watch_directory'])")"
mkdir -p "$WATCH_DIR"

SERVICE_PATH="/etc/systemd/system/pdf2txt-watcher.service"
RUN_USER="$(whoami)"

echo "[4/5] Registrando service em: $SERVICE_PATH"
sudo bash -c "cat > '$SERVICE_PATH'" <<EOF
[Unit]
Description=Watcher para conversão PDF -> TXT (pdf2txt-server)
After=network.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_DIR/bin/python $PROJECT_DIR/watcher.py --config $PROJECT_DIR/config.yml
Restart=on-failure
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "[5/5] Habilitando e iniciando service"
sudo systemctl daemon-reload
sudo systemctl enable pdf2txt-watcher.service
sudo systemctl restart pdf2txt-watcher.service
sudo systemctl status --no-pager pdf2txt-watcher.service || true

echo "Instalação concluída. Para logs: journalctl -u pdf2txt-watcher -f"


