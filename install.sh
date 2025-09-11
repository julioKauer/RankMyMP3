#!/bin/bash

# Script de instalação do RankMyMP3 para Linux/Mac
echo "========================================"
echo "     RankMyMP3 - Instalador Unix"
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

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado!"
    echo
    if [ "$SYSTEM" = "Linux" ]; then
        echo "Por favor, instale o Python:"
        echo "  Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip"
        echo "  CentOS/RHEL:   sudo yum install python3 python3-pip"
        echo "  Arch:          sudo pacman -S python python-pip"
    elif [ "$SYSTEM" = "Mac" ]; then
        echo "Por favor, instale o Python:"
        echo "  Com Homebrew:  brew install python"
        echo "  Ou baixe de:   https://www.python.org/downloads/"
    fi
    exit 1
fi

echo "✅ Python encontrado!"
python3 --version
echo

# Verificar se pip está disponível
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 não encontrado!"
    echo "Instalando pip..."
    if [ "$SYSTEM" = "Linux" ]; then
        sudo apt install python3-pip 2>/dev/null || sudo yum install python3-pip 2>/dev/null || sudo pacman -S python-pip 2>/dev/null
    fi
fi

echo "📦 Instalando dependências..."

# Tentar usar pip3 primeiro, depois pip
if command -v pip3 &> /dev/null; then
    pip3 install wxpython send2trash
elif command -v pip &> /dev/null; then
    pip install wxpython send2trash
else
    echo "❌ pip não encontrado!"
    exit 1
fi

if [ $? -ne 0 ]; then
    echo "❌ Erro ao instalar dependências!"
    echo "Tente executar com sudo ou verifique sua conexão com a internet."
    echo "Comando manual: pip3 install wxpython send2trash"
    exit 1
fi

echo
echo "✅ Dependências instaladas com sucesso!"
echo

# Configurar integração com o sistema Linux
if [ "$SYSTEM" = "Linux" ]; then
    echo "�️  Configurando integração com o sistema..."
    
    # Obter caminho absoluto do projeto
    PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
    
    # Criar arquivo .desktop para o menu
    DESKTOP_FILE="$HOME/.local/share/applications/rankmymp3.desktop"
    mkdir -p "$HOME/.local/share/applications"
    
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=RankMyMP3
Comment=Sistema inteligente de ranking de músicas
Exec=python3 $PROJECT_DIR/main.py
Icon=$PROJECT_DIR/icon.png
Terminal=false
Type=Application
Categories=AudioVideo;Audio;Player;
Keywords=music;ranking;mp3;audio;
StartupNotify=true
EOF
    
    # Tornar o arquivo .desktop executável
    chmod +x "$DESKTOP_FILE"
    
    # Atualizar cache do desktop
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$HOME/.local/share/applications" 2>/dev/null
    fi
    
    echo "✅ RankMyMP3 adicionado ao menu de aplicações!"
    echo "   Procure por 'RankMyMP3' no menu de aplicações do seu sistema"
    echo
fi

echo "🚀 Formas de executar o RankMyMP3:"
echo "   1. Pelo menu de aplicações (Linux): Procure 'RankMyMP3'"
echo "   2. Pelo terminal: python3 main.py"
echo "   3. Script direto: ./run.sh"
echo

# Fazer o script executável
chmod +x "$0"
