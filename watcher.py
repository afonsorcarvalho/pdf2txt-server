#!/usr/bin/env python3
"""
Watcher de diretório para converter arquivos PDF em TXT usando o script existente
`pdf2txt.py`. Este serviço observa criações e modificações de arquivos `.pdf` no
diretório configurado e mantém o `.txt` correspondente atualizado.

Requisitos (instalados pelo install.sh):
- pdfplumber (utilizado pelo pdf2txt.py)
- watchdog (monitoramento de sistema de arquivos)
- pyyaml (leitura do arquivo de configuração)
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import yaml
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


def resolve_project_paths() -> tuple[Path, Path]:
    """Retorna caminhos absolutos do diretório do projeto e do script pdf2txt.py."""
    project_dir = Path(__file__).resolve().parent
    pdf2txt_script = project_dir / "pdf2txt.py"
    return project_dir, pdf2txt_script


def compute_txt_path(pdf_path: Path) -> Path:
    """Dado um caminho de PDF, retorna o caminho de saída .txt correspondente."""
    return pdf_path.with_suffix(".txt")


def needs_conversion(pdf_path: Path, txt_path: Path) -> bool:
    """Determina se o TXT precisa ser (re)gerado com base nos tempos de modificação.

    - Se o TXT não existe: converter
    - Se o PDF é mais novo que o TXT: converter
    - Caso contrário: não converter
    """
    if not txt_path.exists():
        return True
    try:
        return pdf_path.stat().st_mtime > txt_path.stat().st_mtime
    except FileNotFoundError:
        return True


def convert_pdf_to_txt(pdf2txt_script: Path, pdf_path: Path) -> None:
    """Executa o `pdf2txt.py` para um PDF específico, respeitando o mesmo interpretador.

    Usa `sys.executable` para garantir execução dentro do mesmo ambiente/venv do watcher.
    """
    logging.info("Convertendo PDF para TXT: %s", pdf_path)
    try:
        subprocess.run(
            [sys.executable, str(pdf2txt_script), str(pdf_path)],
            check=True,
        )
        logging.info("Conversão concluída: %s", compute_txt_path(pdf_path))
    except subprocess.CalledProcessError as exc:
        logging.exception("Falha ao converter '%s': %s", pdf_path, exc)


def sync_existing_pdfs(pdf2txt_script: Path, watch_dirs: list[Path]) -> None:
    """Faz uma sincronização inicial: converte todos os PDFs que precisam atualização em todos os diretórios."""
    for watch_dir in watch_dirs:
        logging.info("Sincronizando diretório: %s", watch_dir)
        for pdf_path in sorted(watch_dir.glob("*.pdf")):
            txt_path = compute_txt_path(pdf_path)
            if needs_conversion(pdf_path, txt_path):
                convert_pdf_to_txt(pdf2txt_script, pdf_path)


class PdfEventHandler(FileSystemEventHandler):
    """Manipula eventos de criação/modificação para PDFs e aciona conversão."""

    def __init__(self, pdf2txt_script: Path):
        self.pdf2txt_script = pdf2txt_script

    def on_any_event(self, event: FileSystemEvent) -> None:
        # Ignora eventos de diretório
        if event.is_directory:
            return

        # Determina o caminho relevante do evento
        path_str: Optional[str] = None
        if hasattr(event, "dest_path") and event.dest_path:
            path_str = event.dest_path
        elif event.src_path:
            path_str = event.src_path

        if not path_str:
            return

        path = Path(path_str)
        if path.suffix.lower() != ".pdf":
            return

        # Converte somente se necessário
        txt_path = compute_txt_path(path)
        if needs_conversion(path, txt_path):
            convert_pdf_to_txt(self.pdf2txt_script, path)


def load_config(config_path: Path) -> list[Path]:
    """Carrega o arquivo YAML de configuração e retorna a lista de diretórios monitorados."""
    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    
    # Suporte para configuração antiga (watch_directory) e nova (watch_directories)
    watch_dirs = data.get("watch_directories")
    if not watch_dirs:
        # Fallback para configuração antiga
        watch_dir = data.get("watch_directory")
        if watch_dir:
            watch_dirs = [watch_dir]
        else:
            raise ValueError("Chave 'watch_directories' ou 'watch_directory' não definida em config.yml")
    
    if not isinstance(watch_dirs, list):
        raise ValueError("'watch_directories' deve ser uma lista de diretórios")
    
    if not watch_dirs:
        raise ValueError("Lista 'watch_directories' não pode estar vazia")
    
    return [Path(directory).resolve() for directory in watch_dirs]


def configure_logging() -> None:
    """Configura logging simples, adequado para journalctl/systemd."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def main() -> int:
    """Ponto de entrada do watcher."""
    configure_logging()

    parser = argparse.ArgumentParser(
        description="Monitora diretório e converte PDFs em TXTs"
    )
    parser.add_argument(
        "--config",
        default=str(Path(__file__).resolve().parent / "config.yml"),
        help="Caminho para o arquivo de configuração YAML",
    )
    args = parser.parse_args()

    project_dir, pdf2txt_script = resolve_project_paths()
    config_path = Path(args.config).resolve()
    watch_dirs = load_config(config_path)

    # Cria diretórios que não existem
    for watch_dir in watch_dirs:
        if not watch_dir.exists():
            logging.info("Criando diretório monitorado: %s", watch_dir)
            watch_dir.mkdir(parents=True, exist_ok=True)

    logging.info("Diretório do projeto: %s", project_dir)
    logging.info("Script conversor: %s", pdf2txt_script)
    logging.info("Monitorando %d diretório(s):", len(watch_dirs))
    for i, watch_dir in enumerate(watch_dirs, 1):
        logging.info("  %d. %s", i, watch_dir)

    # Sincronização inicial
    sync_existing_pdfs(pdf2txt_script, watch_dirs)

    # Inicia os observers do watchdog para cada diretório
    event_handler = PdfEventHandler(pdf2txt_script)
    observer = Observer()
    
    for watch_dir in watch_dirs:
        observer.schedule(event_handler, str(watch_dir), recursive=False)
        logging.info("Observer configurado para: %s", watch_dir)
    
    observer.start()

    try:
        observer.join()
    except KeyboardInterrupt:
        logging.info("Encerrando watcher...")
    finally:
        observer.stop()
        observer.join()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


