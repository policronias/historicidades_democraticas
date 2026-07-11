"""
Backup manual do arquivo de sessão (anotações + séries temáticas).

Copia sessions/current_session.json para backups/, com timestamp no nome,
protegendo contra perda acidental já que esse arquivo não é versionado no git.

Uso:
    python scripts/backup_sessao.py
"""

import shutil
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
SESSION_FILE = PROJECT_DIR / 'sessions' / 'current_session.json'
BACKUPS_DIR = PROJECT_DIR / 'backups'


def main():
    if not SESSION_FILE.exists():
        print(f"Arquivo de sessão não encontrado: {SESSION_FILE}")
        sys.exit(1)

    BACKUPS_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    destino = BACKUPS_DIR / f'current_session_{timestamp}.json'

    shutil.copy2(SESSION_FILE, destino)
    print(f"Backup criado: {destino}")


if __name__ == '__main__':
    main()
