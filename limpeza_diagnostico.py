import os
import shutil
from pathlib import Path

projeto_path = Path(r"C:\Projetos\historicidades_democraticas")

# Extensões e pastas perigosas
temp_patterns = [
    "*.pyc",
    "*.pyo",
    "__pycache__",
    "*.egg-info",
    ".pytest_cache",
    "*.tmp",
    ".DS_Store"
]

print("=" * 60)
print("DIAGNÓSTICO DE LIMPEZA - Historicidades Democráticas")
print("=" * 60)

encontrados = []

for pattern in temp_patterns:
    for match in projeto_path.rglob(pattern):
        if ".venv" not in str(match):  # Ignora .venv
            encontrados.append(match)
            print(f"❌ {match.relative_to(projeto_path)}")

print(f"\n✅ Total de arquivos desnecessários encontrados: {len(encontrados)}")
print("\n⚠️ NADA FOI DELETADO! Execute 'limpeza_executar.py' para remover.")