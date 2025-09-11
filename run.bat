@echo off
REM Executar RankMyMP3
echo Iniciando RankMyMP3...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ Erro ao executar RankMyMP3!
    echo Certifique-se de que o Python e as dependências estão instalados.
    echo Execute install.bat primeiro se necessário.
    pause
)
