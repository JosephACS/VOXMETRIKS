#!/bin/sh
# Instala hooks locales para bloquear co-autores de Cursor en commits.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/.git/hooks"
cp "$ROOT/.githooks/commit-msg" "$ROOT/.git/hooks/commit-msg"
chmod +x "$ROOT/.git/hooks/commit-msg"
echo "Git hook instalado: .git/hooks/commit-msg"
