#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ln -sf "$PROJECT_DIR/src/obs.zsh" "$HOME/.config/zsh/functions/obs.zsh"
echo "Symlinked obs.zsh to ~/.config/zsh/functions/obs.zsh"
