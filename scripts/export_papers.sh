#!/usr/bin/env bash
# Copia i markdown/_full.md dei paper indicati in assets/tmp_papers/<nome-cartella>.md
# Uso: ./scripts/export_papers.sh "assets/papers/Autore et al - Anno - Titolo" [...]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="$REPO_ROOT/assets/tmp_papers"

if [ "$#" -eq 0 ]; then
  echo "Uso: $0 <path-cartella-paper> [<path-cartella-paper> ...]" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"

for paper_dir in "$@"; do
  # Permette sia path assoluti che relativi alla root del repo
  if [[ "$paper_dir" != /* ]]; then
    paper_dir="$REPO_ROOT/$paper_dir"
  fi

  src="$paper_dir/markdown/_full.md"
  name="$(basename "$paper_dir")"
  dest="$DEST_DIR/$name.md"

  if [ ! -f "$src" ]; then
    echo "ATTENZIONE: non trovato $src, salto." >&2
    continue
  fi

  cp "$src" "$dest"
  echo "Copiato: $dest"
done
