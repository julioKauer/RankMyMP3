# RankMyMP3 🎵

Sistema inteligente de ranking de músicas usando comparações diretas e busca binária.

## 📋 Características

- **Ranking por comparações**: Sistema baseado em comparações diretas entre músicas
- **Busca binária inteligente**: Classificação eficiente com máximo de log₂(n) comparações por música
- **Redistribuição automática**: Sistema de estrelas (1-5) redistribuído automaticamente
- **Interface amigável**: Interface gráfica wxPython simples e intuitiva
- **Gerenciamento de pastas**: Adição e gerenciamento de pastas de música
- **Persistência**: Banco SQLite para armazenar comparações e rankings

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

### Pré-requisitos
- Python 3.8+
- pip

### Passos

1. **Clone o repositório**:
```bash
git clone https://github.com/seu-usuario/RankMyMP3.git
cd RankMyMP3
```

2. **Crie um ambiente virtual** (recomendado):
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

3. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

4. **Execute o programa**:
```bash
python main.py
```

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
- **141 testes** cobrindo todo o sistema
- **92%+ de cobertura** de código
- Testes unitários, de integração e edge cases
- Testes de regressão para bugs conhecidos
- Testes de workflows completos de usuário

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

## 🧠 Como funciona

### Sistema de Comparações
- Cada classificação é baseada em **comparações diretas** entre músicas
- Comparações são armazenadas permanentemente no banco
- O ranking é construído a partir do histórico de comparações

### Busca Binária Inteligente
- Nova música é inserida no ranking usando busca binária
- **Máximo log₂(n) comparações** por música (eficiente para milhares de músicas)
- Posicionamento preciso baseado em comparações diretas

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

- ✅ **100 músicas**: ~7 comparações por música
- ✅ **1.000 músicas**: ~10 comparações por música  
- ✅ **10.000 músicas**: ~14 comparações por música
- ✅ **100.000 músicas**: ~17 comparações por música

**Complexidade**: O(log n) por música → Sistema escala para qualquer quantidade de músicas!

---

*Sistema desenvolvido com foco em eficiência e simplicidade.*
