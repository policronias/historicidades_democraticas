#!/usr/bin/env python3
"""
Script de Limpeza Automática - Historicidades Democráticas
Realiza a limpeza da pasta e reorganiza arquivos.

Executar com: python limpeza_executar.py
"""

import os
import shutil
from pathlib import Path
import sys

# Detectar plataforma
IS_WINDOWS = sys.platform == 'win32'


class ProjetoLimpador:
    """Gerencia limpeza do projeto."""
    
    def __init__(self, projeto_dir: str = '.'):
        """
        Inicializa o limpador.
        
        Args:
            projeto_dir: Caminho do projeto (default: diretório atual)
        """
        self.projeto_path = Path(projeto_dir).resolve()
        self.stats = {
            'deleted': [],
            'moved': [],
            'errors': [],
            'saved_space': 0,
        }
    
    def get_dir_size(self, path: Path) -> int:
        """Calcula tamanho total de um diretório em bytes."""
        total = 0
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    total += entry.stat().st_size
        except Exception as e:
            print(f"  ⚠️ Erro ao calcular tamanho: {e}")
        return total
    
    def limpar_pycache(self) -> None:
        """Remove todos os diretórios __pycache__ e arquivos .pyc."""
        print("\n🗑️  FASE 1: Limpando __pycache__ e .pyc")
        print("=" * 60)
        
        pycache_dirs = list(self.projeto_path.rglob('__pycache__'))
        pyc_files = list(self.projeto_path.rglob('*.pyc'))
        
        if not pycache_dirs and not pyc_files:
            print("✅ Nenhum cache encontrado. Projeto já está limpo!")
            return
        
        # Deletar diretórios __pycache__
        for pycache in pycache_dirs:
            if '.venv' not in str(pycache):  # Não mexer no .venv
                try:
                    size = self.get_dir_size(pycache)
                    shutil.rmtree(pycache)
                    self.stats['deleted'].append(str(pycache))
                    self.stats['saved_space'] += size
                    print(f"  ✓ Deletado: {pycache.relative_to(self.projeto_path)} ({size/1024/1024:.2f} MB)")
                except Exception as e:
                    self.stats['errors'].append(f"Erro ao deletar {pycache}: {e}")
                    print(f"  ✗ Erro ao deletar {pycache}: {e}")
        
        # Deletar arquivos .pyc
        for pyc in pyc_files:
            if '.venv' not in str(pyc):  # Não mexer no .venv
                try:
                    size = pyc.stat().st_size
                    pyc.unlink()
                    self.stats['deleted'].append(str(pyc))
                    self.stats['saved_space'] += size
                    print(f"  ✓ Deletado: {pyc.relative_to(self.projeto_path)}")
                except Exception as e:
                    self.stats['errors'].append(f"Erro ao deletar {pyc}: {e}")
                    print(f"  ✗ Erro ao deletar {pyc}: {e}")
    
    def mover_scripts_antigos(self) -> None:
        """Move scripts de teste e visualization para /deprecated."""
        print("\n🚀 FASE 2: Movendo scripts antigos para /deprecated")
        print("=" * 60)
        
        # Scripts a serem movidos
        scripts_to_move = [
            'test_phase1_optimization.py',
            'test_phase2_optimization.py',
            'visualizar_campo_semantico.py',
            'visualizar_campo_semantico_umap.py',
            'analise_semantica_historia.py',
            'busca_palavra_alvo.py',
            'extrair_contextos.py',
        ]
        
        # Criar diretório deprecated
        deprecated_dir = self.projeto_path / 'deprecated'
        deprecated_dir.mkdir(exist_ok=True)
        print(f"  ✓ Diretório /deprecated criado: {deprecated_dir}")
        
        # Mover arquivos
        for script_name in scripts_to_move:
            script_path = self.projeto_path / script_name
            
            if script_path.exists():
                try:
                    dest_path = deprecated_dir / script_name
                    shutil.move(str(script_path), str(dest_path))
                    self.stats['moved'].append(script_name)
                    print(f"  ✓ Movido: {script_name} → /deprecated/")
                except Exception as e:
                    self.stats['errors'].append(f"Erro ao mover {script_name}: {e}")
                    print(f"  ✗ Erro ao mover {script_name}: {e}")
            else:
                print(f"  ℹ️  {script_name} não encontrado (pode ter sido removido)")
    
    def remover_importacoes_nao_usadas(self) -> None:
        """Remove importações não usadas do app.py."""
        print("\n🧹 FASE 3: Limpando importações não usadas")
        print("=" * 60)
        
        app_path = self.projeto_path / 'app.py'
        
        if not app_path.exists():
            print(f"  ⚠️  app.py não encontrado em {self.projeto_path}")
            return
        
        try:
            with open(app_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remover BytesIO não usado (manter StringIO)
            original_size = len(content)
            content = content.replace(
                'from io import BytesIO, StringIO',
                'from io import StringIO'
            )
            
            if len(content) != original_size:
                with open(app_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("  ✓ Removido: import BytesIO (não utilizado)")
                print("  ✓ Mantido: import StringIO (utilizado em _build_semantic_csv_cached)")
            else:
                print("  ℹ️  Nenhuma importação não utilizada encontrada")
        
        except Exception as e:
            self.stats['errors'].append(f"Erro ao processar app.py: {e}")
            print(f"  ✗ Erro ao processar app.py: {e}")
    
    def criar_readme_deprecated(self) -> None:
        """Cria README.md na pasta deprecated."""
        print("\n📝 FASE 4: Criando documentação")
        print("=" * 60)
        
        readme_path = self.projeto_path / 'deprecated' / 'README.md'
        
        readme_content = """# Deprecated Scripts

Esta pasta contém scripts de teste, visualização e ferramentas auxiliares que não são mais necessários para o funcionamento principal da aplicação.

## Por que foram movidos?

Durante a refatoração e limpeza do projeto (Junho 2026), estes scripts foram identificados como:
- **Scripts de teste de otimização** (test_phase*.py) - Testes já validados
- **Ferramentas de visualização** (visualizar_*.py) - Funcionalidades exploratórias
- **Análises auxiliares** (analise_*, busca_*, extrair_*) - Utilitários específicos para pesquisa

## Como usar se necessário

Se você precisar destes scripts novamente:

1. Localize o arquivo em `/deprecated/`
2. Copie de volta para a raiz do projeto: `mv deprecated/arquivo.py ./`
3. Execute normalmente: `python arquivo.py`

## Descrição dos scripts

- **test_phase1_optimization.py** - Testes de otimização de cache (Phase 1)
- **test_phase2_optimization.py** - Testes de otimização de lazy-load (Phase 2)
- **visualizar_campo_semantico.py** - Visualização 2D de embeddings
- **visualizar_campo_semantico_umap.py** - Visualização UMAP de embeddings
- **analise_semantica_historia.py** - Análise semântica de textos históricos
- **busca_palavra_alvo.py** - Busca por palavras-chave específicas
- **extrair_contextos.py** - Extração de contextos de cartas

## Nota para desenvolvedores

Se estes scripts contêm funcionalidades que deveriam estar na aplicação principal, considere:
1. Extrair as funções úteis como módulos separados em `/modules/`
2. Integrá-las como ferramentas na barra lateral (sidebar)
3. Criar uma seção "Ferramentas Avançadas" na aplicação

---

Gerado automaticamente durante refatoração - June 2026
"""
        
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            print(f"  ✓ Criado: /deprecated/README.md")
        except Exception as e:
            self.stats['errors'].append(f"Erro ao criar README: {e}")
            print(f"  ✗ Erro ao criar README: {e}")
    
    def exibir_relatorio(self) -> None:
        """Exibe relatório final da limpeza."""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL DA LIMPEZA")
        print("=" * 60)
        
        print(f"\n✅ Arquivos deletados: {len(self.stats['deleted'])}")
        for deleted in self.stats['deleted']:
            print(f"   • {Path(deleted).name}")
        
        print(f"\n↪️  Arquivos movidos para /deprecated: {len(self.stats['moved'])}")
        for moved in self.stats['moved']:
            print(f"   • {moved}")
        
        if self.stats['errors']:
            print(f"\n⚠️  Erros encontrados: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                print(f"   • {error}")
        else:
            print("\n✅ Nenhum erro encontrado!")
        
        space_saved = self.stats['saved_space'] / 1024 / 1024
        print(f"\n💾 Espaço economizado: {space_saved:.2f} MB")
        
        print("\n" + "=" * 60)
        print("✨ LIMPEZA CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        print("\nPróximas etapas:")
        print("1. ✓ Remover importações não usadas")
        print("2. ✓ Mover scripts antigos para /deprecated")
        print("3. ✓ Criar novos módulos (cache_manager, ui_manager, config_manager)")
        print("4. ✓ Refatorar app.py usando novos módulos")
        print("\nPara atualizar seu projeto:")
        print("  1. Copie os novos módulos de /modules/ para seu projeto")
        print("  2. Atualize app.py com a versão refatorada")
        print("  3. Teste com: streamlit run app.py")
        print("\n" + "=" * 60)
    
    def executar(self) -> None:
        """Executa limpeza completa."""
        print("\n" + "=" * 60)
        print("🧹 LIMPEZA DO PROJETO - Historicidades Democráticas")
        print("=" * 60)
        print(f"Projeto: {self.projeto_path}")
        print(f"Plataforma: {'Windows' if IS_WINDOWS else 'Linux/Mac'}")
        
        # Executar fases
        self.limpar_pycache()
        self.mover_scripts_antigos()
        self.remover_importacoes_nao_usadas()
        self.criar_readme_deprecated()
        
        # Exibir relatório
        self.exibir_relatorio()


def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Limpeza automática do projeto Historicidades Democráticas'
    )
    parser.add_argument(
        '--dir',
        type=str,
        default='.',
        help='Caminho do projeto (default: diretório atual)'
    )
    
    args = parser.parse_args()
    
    limpador = ProjetoLimpador(args.dir)
    limpador.executar()


if __name__ == '__main__':
    main()
