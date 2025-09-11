# RankMyMP3 🎵

Sistema inteligente de ranking de músicas usando comparações diretas e busca binária.

## � Instalação Rápida

**👤 Usuário Final**: Baixe o ZIP, execute `install.bat` (Windows) ou `install.sh` (Linux/Mac) → `run.bat`/`run.sh`  
**📖 Guia Detalhado**: Veja [INSTALL_GUIDE.md](INSTALL_GUIDE.md) para instruções passo-a-passo  
**🧑‍💻 Desenvolvedores**: Continue lendo para instalação completa com ambiente virtual

## �📋 Características

- **Ranking por comparações**: Sistema baseado em comparações diretas entre músicas
- **Busca binária inteligente**: Classificação eficiente com limite de 5 comparações por música
- **Redistribuição automática**: Sistema de estrelas (1-5) redistribuído automaticamente
- **Interface amigável**: Interface gráfica wxPython simples e intuitiva
## 🎵 Funcionalidades Principais

### 🎯 Sistema de Ranking Inteligente
- **Comparações Pareadas**: Compare músicas duas a duas para classificação precisa
- **Algoritmo de Busca Binária**: Inserção eficiente de novas músicas no ranking
- **Skip/Ignore**: Pule músicas temporariamente ou ignore permanentemente
- **Estado Persistente**: Continue de onde parou após fechar o aplicativo

### 🏷️ Sistema de Tags e Filtros
- **Tags Personalizadas**: Adicione tags como "rock", "favoritas", "treino", etc.
- **Filtros Avançados**: Combine filtros por estrelas e tags
- **Sugestões Inteligentes**: Tags mais usadas aparecem primeiro
- **Interface Intuitiva**: Dropdowns e diálogos fáceis de usar

### 📁 Navegação de Arquivos
- **Mostrar Caminho**: Veja o caminho completo de qualquer música
- **Abrir Pasta**: Acesse a pasta da música no explorador de arquivos
- **Mover Música**: Mova arquivos para outras pastas e atualize o banco automaticamente
- **Multiplataforma**: Funciona no Windows, macOS e Linux
- **Integração Nativa**: Usa o gerenciador de arquivos padrão do sistema

### 🎛️ Interface Completa
- **Árvore de Análise**: Visualize músicas por pasta e status
- **Lista de Ranking**: Veja o ranking final ordenado por estrelas
- **Menus Contextuais**: Clique direito para acessar todas as funcionalidades
- **Filtros em Tempo Real**: Veja resultados instantaneamente
- **Persistência de Janela**: Tamanho e posição da janela são salvos automaticamente

### 🔄 Gerenciamento de Estado
- **Auto-save**: Progresso salvo automaticamente
- **Recuperação de Estado**: Continue comparações interrompidas
- **Validação de Consistência**: Sistema detecta e corrige inconsistências
- **Backup Automático**: Dados seguros no SQLite

## 🏗️ Arquitetura

```
RankMyMP3/
├── controllers/          # Lógica de negócio
│   ├── folder_controller.py    # Gerenciamento de pastas
│   └── music_controller.py     # Lógica principal de ranking
├── models/               # Camada de dados
│   ├── comparison_model.py         # Comparações diretas
│   ├── comparison_state_model.py   # Estado da busca binária
│   ├── folder_model.py             # Dados de pastas
│   └── music_model.py              # Dados das músicas
├── views/                # Interface gráfica
│   ├── folder_config_panel.py # Configuração de pastas
│   └── music_app.py           # Interface principal
├── utils/                # Utilitários
│   ├── database_initializer.py # Inicialização do banco
│   └── file_operations.py      # Operações de arquivo
├── tests/                # Testes unitários (92% cobertura)
│   ├── test_controllers/     # Testes dos controllers
│   ├── test_models/          # Testes dos models
│   └── test_utils/           # Testes dos utilitários
├── data/                 # Banco de dados
└── main.py              # Ponto de entrada
```

## 🛠️ Instalação

### 📦 Para Usuários Finais (Recomendado)

#### Opção 1: Download Direto (Mais Simples)
1. **Baixe o arquivo ZIP** do projeto do GitHub
2. **Extraia** para uma pasta de sua escolha (ex: `C:\RankMyMP3` ou `~/RankMyMP3`)
3. **Instale o Python** se não tiver:
   - Windows: Baixe de [python.org](https://www.python.org/downloads/) ✅ Marque "Add to PATH"
   - Mac: `brew install python` ou baixe de python.org
   - Linux: `sudo apt install python3 python3-pip` (Ubuntu/Debian)
4. **Abra o terminal/prompt** na pasta do RankMyMP3
5. **Instale dependências**: `pip install wxpython send2trash`
6. **Execute**: `python main.py`

#### Opção 2: Instalação com Script (Em Breve)
```bash
# Windows
curl -o install.bat https://raw.githubusercontent.com/seu-usuario/RankMyMP3/main/install.bat
install.bat

# Linux/Mac
curl -sSL https://raw.githubusercontent.com/seu-usuario/RankMyMP3/main/install.sh | bash
```

### 🧑‍💻 Para Desenvolvedores

#### Pré-requisitos
- Python 3.8+
- Git
- pip

#### Instalação Completa

1. **Clone o repositório**:
```bash
git clone https://github.com/seu-usuario/RankMyMP3.git
cd RankMyMP3
```

2. **Crie um ambiente virtual** (recomendado):
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows
```

3. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

4. **Execute o programa**:
```bash
python main.py
```

## 📚 Como Usar

### 🎯 Classificação Básica
1. **Adicione suas pastas de música** via `Arquivo > Configurar Pastas`
2. **Inicie as comparações** - o sistema apresentará pares de músicas
3. **Escolha a melhor** clicando no botão correspondente
4. **Continue até classificar** todas as músicas

### 🏷️ Sistema de Tags
- **Adicionar Tags**: Clique direito em uma música → "🏷️ Gerenciar Tags"
- **Filtrar por Tags**: Use o dropdown "Tags" na interface
- **Combinar Filtros**: Combine filtros de estrelas e tags
- **Tags Sugeridas**: Sistema sugere tags mais utilizadas

### 📁 Navegação de Arquivos
- **Ver Caminho**: Clique direito → "📁 Mostrar Caminho"
- **Abrir Pasta**: Clique direito → "🗂️ Abrir Pasta"
- **Funciona em**: Windows (Explorer), macOS (Finder), Linux (gerenciador padrão)

### 🔍 Filtros Avançados
- **Por Estrelas**: Filtre músicas com 5⭐, 4⭐, etc.
- **Por Tags**: Mostre apenas músicas com tags específicas
- **Combinados**: Use ambos os filtros simultaneamente
- **Tempo Real**: Resultados aparecem instantaneamente

### ⚡ Dicas de Produtividade
- **Atalhos**: Use clique direito para acesso rápido
- **Multi-seleção**: Selecione várias músicas na árvore para operações em lote
- **Estado Persistente**: Feche e reabra - o progresso é mantido
- **Skip Inteligente**: Use "Skip" para pular temporariamente durante comparações

## 🧪 Desenvolvimento

### Instalar dependências de desenvolvimento:
```bash
pip install -r requirements-dev.txt
```

### Executar testes:
```bash
# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=. --cov-report=html

# Ver relatório de cobertura
open htmlcov/index.html  # Linux/Mac
start htmlcov/index.html # Windows
```

### Estrutura de testes:
- **244 testes** cobrindo todo o sistema
- **92%+ de cobertura** de código
- Testes unitários, de integração e edge cases
- Testes de regressão para bugs conhecidos
- Testes de workflows completos de usuário
- Testes de persistência de configurações

### Tipos de teste:
- **Unitários**: `tests/test_models/`, `tests/test_controllers/`, `tests/test_utils/`
- **Integração**: `tests/test_user_workflows.py`
- **Regressão**: `tests/test_regression_problems.py`
- **Bug fixes**: `tests/test_bug_fix_validation.py`

### Comandos úteis:
```bash
# Executar apenas um arquivo de teste
pytest tests/test_models/test_music_model.py

# Executar com verbosidade
pytest -v

# Executar testes específicos por nome
pytest -k "test_binary_search"

# Gerar relatório de cobertura em texto
pytest --cov=. --cov-report=term-missing

# Limpar cache de testes
pytest --cache-clear
```
│   └── file_operations.py     # Operações de arquivo
├── data/                 # Banco de dados
│   └── music_ranking.db       # SQLite database
└── main.py              # Ponto de entrada
```

## 🚀 Como usar

1. **Executar aplicação**:
   ```bash
   python main.py
   ```

2. **Adicionar música**:
   - Clique no botão "📁" na toolbar
   - Selecione uma pasta com arquivos MP3
   - As músicas serão automaticamente importadas

3. **Classificar músicas**:
   - Clique em "🎯 Iniciar Classificação"
   - Compare as duas músicas apresentadas
   - Clique em "Prefiro Esta" na música de sua preferência
   - Continue até classificar todas as músicas

4. **Ver ranking**:
   - O ranking é exibido automaticamente na coluna direita
   - Músicas são ordenadas por estrelas (5⭐ = melhor)

5. **Gerenciar arquivos**:
   - **Clique direito** em qualquer música para acessar opções:
     - **📁 Mostrar Caminho**: Ver localização completa do arquivo
     - **🗂️ Abrir Pasta**: Abrir pasta no explorador de arquivos
     - **📦 Mover para Pasta**: Mover arquivo para outro local
   - Todas as operações atualizam automaticamente o banco de dados

## 🧠 Como funciona

### Sistema de Comparações
- Cada classificação é baseada em **comparações diretas** entre músicas
- Comparações são armazenadas permanentemente no banco
- O ranking é construído a partir do histórico de comparações

### Busca Binária Inteligente
- Nova música é inserida no ranking usando busca binária
- **Limite de 5 comparações** por música (proteção contra loops infinitos)
- Posicionamento preciso baseado em comparações diretas
- **Configuração futura**: Limite será configurável em versões futuras

### Sistema de Estrelas
- Estrelas são apenas **visualização** do ranking real
- **Redistribuição automática**: 1-5 estrelas distribuídas proporcionalmente
- Ranking verdadeiro é sempre baseado em comparações

## 🗃️ Banco de Dados

O sistema usa SQLite com 4 tabelas principais:

- **`music`**: Músicas e metadados (path, stars, tags)
- **`comparisons`**: Comparações diretas (música_a vs música_b, vencedor)  
- **`comparison_state`**: Estado da busca binária (contexto, posições)
- **`folders`**: Pastas adicionadas pelo usuário

## 🔧 Requisitos

- Python 3.7+
- wxPython (`pip install wxpython`)
- SQLite (incluído no Python)

## 📊 Escalabilidade

- ✅ **Coleções pequenas**: Busca binária ideal com até 5 comparações
- ✅ **Coleções médias**: Sistema adaptativo para rankings de centenas de músicas  
- ✅ **Coleções grandes**: Algoritmo otimizado para qualquer quantidade
- ⚙️ **Configuração futura**: Limite de comparações será configurável

**Complexidade**: O(log n) por música, limitado a 5 comparações para proteção contra loops infinitos.

## ⚙️ Limitações Atuais e Roadmap

### 🚧 Limitações
- **Busca Binária**: Limitada a 5 comparações por música (hardcoded)
- **Motivo**: Proteção contra loops infinitos em casos extremos
- **Impacto**: Pode não encontrar posição ideal em coleções muito grandes

### 🛣️ Roadmap
- [ ] **Configuração de Limites**: Tornar o limite de comparações configurável pelo usuário
- [ ] **Algoritmo Adaptativo**: Ajustar limite automaticamente baseado no tamanho da coleção
- [ ] **Busca Híbrida**: Combinar busca binária com outros algoritmos de ordenação
- [ ] **Análise de Performance**: Métricas detalhadas sobre eficiência das comparações

---

*Sistema desenvolvido com foco em eficiência e simplicidade.*
