@echo off
REM Script de instalação do RankMyMP3 para Windows
echo ========================================
echo     RankMyMP3 - Instalador Windows
echo ========================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python não encontrado!
    echo.
    echo Por favor, instale o Python primeiro:
    echo 1. Vá para https://www.python.org/downloads/
    echo 2. Baixe a versão mais recente
    echo 3. Durante a instalação, MARQUE "Add Python to PATH"
    echo 4. Execute este script novamente
    pause
    exit /b 1
)

echo ✅ Python encontrado!
python --version

echo.
echo 📦 Instalando dependências...
pip install wxpython send2trash

if %errorlevel% neq 0 (
    echo ❌ Erro ao instalar dependências!
    echo Tente executar como administrador ou verifique sua conexão com a internet.
    pause
    exit /b 1
)

echo.
echo ✅ Instalação concluída com sucesso!
echo.

REM Criar atalho na área de trabalho
echo � Criando atalho na área de trabalho...
set "DESKTOP=%USERPROFILE%\Desktop"
set "PROJECT_DIR=%~dp0"

REM Criar arquivo batch para execução
echo @echo off > "%PROJECT_DIR%RankMyMP3.bat"
echo cd /d "%PROJECT_DIR%" >> "%PROJECT_DIR%RankMyMP3.bat"
echo python main.py >> "%PROJECT_DIR%RankMyMP3.bat"

REM Criar atalho usando PowerShell
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\RankMyMP3.lnk'); $Shortcut.TargetPath = '%PROJECT_DIR%RankMyMP3.bat'; $Shortcut.WorkingDirectory = '%PROJECT_DIR%'; $Shortcut.IconLocation = '%PROJECT_DIR%icon.ico'; $Shortcut.Description = 'Sistema inteligente de ranking de músicas'; $Shortcut.Save()" 2>nul

if exist "%DESKTOP%\RankMyMP3.lnk" (
    echo ✅ Atalho criado na área de trabalho!
) else (
    echo ⚠️  Não foi possível criar atalho automaticamente
)

echo.
echo 🚀 Formas de executar o RankMyMP3:
echo    1. Atalho na área de trabalho: RankMyMP3
echo    2. Duplo clique em: RankMyMP3.bat  
echo    3. Script direto: run.bat
echo    4. Terminal: python main.py
echo.

pause
