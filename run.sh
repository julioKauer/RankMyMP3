#!/bin/bash
# Executar RankMyMP3

echo "🎵 Iniciando RankMyMP3..."

# Tentar python3 primeiro, depois python
if command -v python3 &> /dev/null; then
    python3 main.py
elif command -v python &> /dev/null; then
    python main.py
else
    echo "❌ Python não encontrado!"
    echo "Execute install.sh primeiro para instalar as dependências."
    exit 1
fi

if [ $? -ne 0 ]; then
    echo
    echo "❌ Erro ao executar RankMyMP3!"
    echo "Certifique-se de que as dependências estão instaladas."
    echo "Execute install.sh primeiro se necessário."
fi
