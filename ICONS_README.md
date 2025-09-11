# 🎨 Ícones do RankMyMP3

## 📁 Arquivos de Ícone

### Principais
- `icon.png` - Ícone principal 128x128 (padrão)
- `icon.ico` - Ícone multi-resolução para Windows
- `icon_original.png` - Imagem original 1024x1024 (fonte)

### Tamanhos Específicos (PNG)
- `icon-16.png` - 16x16 (menus, listas)
- `icon-32.png` - 32x32 (barras de tarefas pequenas)
- `icon-48.png` - 48x48 (padrão Linux)
- `icon-64.png` - 64x64 (barras de tarefas)
- `icon-128.png` - 128x128 (principal, same as icon.png)
- `icon-256.png` - 256x256 (alta resolução)

### Originais/Backup
- `icon_original.png` - Imagem original 1024x1024
- `icon_old.png` - Ícone anterior (backup)

## 🎯 Uso pelos Instaladores

### Windows (`install.bat`)
- Usa `icon.ico` para atalhos na área de trabalho
- Arquivo ICO contém múltiplas resoluções (16-256px)

### Linux (`install.sh`)
- Usa `icon.png` (128x128) no arquivo .desktop
- Funciona com todos os gerenciadores de janela

### macOS
- Usa `icon.png` como fallback
- Para apps nativos, seria necessário converter para .icns

## 🛠️ Como Regenerar

Se precisar recriar os ícones a partir de uma nova imagem:

```bash
# Partir de uma imagem de alta resolução (ex: nova_imagem.png)
cp nova_imagem.png icon_original.png

# Criar todos os tamanhos
convert icon_original.png -resize 128x128 icon.png
convert icon_original.png -resize 256x256 icon-256.png
convert icon_original.png -resize 64x64 icon-64.png
convert icon_original.png -resize 48x48 icon-48.png
convert icon_original.png -resize 32x32 icon-32.png
convert icon_original.png -resize 16x16 icon-16.png

# Criar ICO multi-resolução para Windows
convert icon_original.png \
  \( +clone -resize 16x16 \) \
  \( +clone -resize 32x32 \) \
  \( +clone -resize 48x48 \) \
  \( +clone -resize 64x64 \) \
  \( +clone -resize 128x128 \) \
  \( +clone -resize 256x256 \) \
  -delete 0 icon.ico
```

## 📋 Checklist para Novos Ícones

- [ ] Imagem original em alta resolução (1024x1024 mínimo)
- [ ] Boa visibilidade em fundos claros e escuros
- [ ] Elementos reconhecíveis em 16x16
- [ ] Cores consistentes com a marca
- [ ] Geração de todos os tamanhos
- [ ] Teste em diferentes sistemas operacionais
