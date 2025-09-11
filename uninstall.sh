#!/bin/bash

# Script de desinstalação do RankMyMP3
echo "========================================"
echo "   RankMyMP3 - Desinstalador Unix"
echo "========================================"
echo

# Detectar sistema operacional
OS="$(uname -s)"
case "${OS}" in
    Linux*)     SYSTEM=Linux;;
    Darwin*)    SYSTEM=Mac;;
    *)          SYSTEM="Unknown";;
esac

echo "🖥️  Sistema detectado: $SYSTEM"
echo

# Remover integração com o sistema Linux
if [ "$SYSTEM" = "Linux" ]; then
    echo "🗑️  Removendo integração com o sistema..."
    
    # Remover arquivo .desktop
    DESKTOP_FILE="$HOME/.local/share/applications/rankmymp3.desktop"
    if [ -f "$DESKTOP_FILE" ]; then
        rm "$DESKTOP_FILE"
        echo "✅ Entrada do menu removida"
    fi
    
    # Atualizar cache do desktop
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$HOME/.local/share/applications" 2>/dev/null
    fi
fi

echo
echo "⚠️  Dados do RankMyMP3:"
echo "   📁 Pasta do projeto: $(pwd)"
echo "   🗄️  Banco de dados: $(pwd)/data/music_ranking.db"
echo

read -p "❓ Deseja remover os dados (rankings e configurações)? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "data" ]; then
        rm -rf data/
        echo "✅ Dados removidos"
    fi
    
    if [ -f "app_settings.json" ]; then
        rm app_settings.json
        echo "✅ Configurações removidas"
    fi
else
    echo "📦 Dados mantidos - você pode usar novamente mais tarde"
fi

echo
read -p "❓ Deseja remover as dependências Python (wxpython, send2trash)? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Removendo dependências..."
    
    if command -v pip3 &> /dev/null; then
        pip3 uninstall -y wxpython send2trash 2>/dev/null
    elif command -v pip &> /dev/null; then
        pip uninstall -y wxpython send2trash 2>/dev/null
    fi
    
    echo "✅ Dependências removidas"
else
    echo "📦 Dependências mantidas - podem ser úteis para outros apps"
fi

echo
echo "✅ Desinstalação concluída!"
echo
echo "📁 Para remover completamente, delete esta pasta:"
echo "   rm -rf $(pwd)"
echo
