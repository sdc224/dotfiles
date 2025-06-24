# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# mise
# https://github.com/mise-app/mise
eval "$(/Users/schatterjee10/.local/bin/mise activate zsh)"

### MANAGED BY RANCHER DESKTOP START (DO NOT EDIT)
export PATH="/Users/schatterjee10/.rd/bin:$PATH"
### MANAGED BY RANCHER DESKTOP END (DO NOT EDIT)

# zinit plugin manager
# https://github.com/zdharma-continuum/zinit
ZINIT_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}/zinit/zinit.git"

# Download zinit if it doesn't exist
if [ ! -d "$ZINIT_HOME" ]; then
    mkdir -p "$(dirname $ZINIT_HOME)"
    git clone https://github.com/zdharma-continuum/zinit.git "$ZINIT_HOME"
fi

# Source/Load zinit
source "${ZINIT_HOME}/zinit.zsh"
autoload -Uz _zinit
(( ${+_comps} )) && _comps[zinit]=_zinit

#########################################################################
# TMUX
#########################################################################
# Auto-start tmux only in interactive terminal sessions
if command -v tmux &>/dev/null && [[ -z "$TMUX" ]] && [[ $- == *i* ]] && [[ -t 0 ]]; then
  # Check if there are any tmux sessions running
  if ! tmux list-sessions &>/dev/null; then
    # No sessions exist, create a new one
    tmux new-session -d -s λ && tmux attach-session -t λ
  else
    # Sessions exist, attach to the first available or create new if all attached
    tmux attach-session || tmux new-session -d -s λ && tmux attach-session -t λ
  fi
fi

# TMUX Configuration
if command -v tmux &>/dev/null; then
  # Set tmux to use 256 colors
  alias tmux='tmux -2'
fi

#########################################################################
# THEME
#########################################################################
# P10K
zinit ice depth=1; zinit light romkatv/powerlevel10k
# STARSHIP
# zinit ice from"gh-r" as"command" atload'eval "$(starship init zsh)"'
# zinit load starship/starship
#########################################################################
# PLUGINS
#########################################################################
# SSH-AGENT
# zinit light bobsoppe/zsh-ssh-agent
# FZF
zinit ice from="gh-r" as="command"
zinit light junegunn/fzf
# FZF BYNARY AND TMUX HELPER SCRIPT
zinit ice lucid wait'0c' as="command" id-as="junegunn/fzf-tmux" pick="bin/fzf-tmux"
zinit light junegunn/fzf
# BIND MULTIPLE WIDGETS USING FZF
zinit ice lucid wait'0c' multisrc"shell/{completion,key-bindings}.zsh" id-as="junegunn/fzf_completions" pick="/dev/null"
zinit light junegunn/fzf
# FZF-TAB
zinit ice wait="1" lucid
zinit light Aloxaf/fzf-tab
# AUTOSUGGESTIONS, TRIGGER PRECMD HOOK UPON LOAD
ZSH_AUTOSUGGEST_BUFFER_MAX_SIZE=20
ZSH_AUTOSUGGEST_STRATEGY=(history completion)
zinit ice wait="0a" lucid
zinit light zsh-users/zsh-autosuggestions
# ENHANCD
zinit ice wait="0b" lucid
zinit light b4b4r07/enhancd
export ENHANCD_FILTER=fzf:fzy:peco
# ZOXIDE
zinit ice wait="0" lucid from="gh-r" as="program" pick="zoxide-*/zoxide -> zoxide" cp="zoxide-*/completions/_zoxide -> _zoxide" atclone="./zoxide init zsh > init.zsh" atpull="%atclone" src="init.zsh"
zinit light ajeetdsouza/zoxide
# HISTORY SUBSTRING SEARCHING (use atuin)
# zinit ice wait="0b" lucid atload'bindkey "$terminfo[kcuu1]" history-substring-search-up; bindkey "$terminfo[kcud1]" history-substring-search-down'
# zinit light zsh-users/zsh-history-substring-search
# bindkey '^[[A' history-substring-search-up
# bindkey '^[[B' history-substring-search-down
# bindkey -M vicmd 'k' history-substring-search-up
# bindkey -M vicmd 'j' history-substring-search-down
# TAB COMPLETIONS
zinit ice wait="0b" lucid blockf
zinit light zsh-users/zsh-completions
zstyle ':completion:*' completer _expand _complete _ignored _approximate
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'
zstyle ':completion:*' menu no
zstyle ':completion:*' select-prompt '%SScrolling active: current selection at %p%s'
zstyle ':completion:*:descriptions' format '[%d]'
zstyle ':completion:*:processes' command 'ps -au$USER'
zstyle ':completion:complete:*:options' sort false
zstyle ':fzf-tab:complete:_zlua:*' query-string input
zstyle ':completion:*:*:*:*:processes' command "ps -u $USER -o pid,user,comm,cmd -w -w"
zstyle ':fzf-tab:complete:kill:argument-rest' extra-opts --preview=$extract'ps --pid=$in[(w)1] -o cmd --no-headers -w -w' --preview-window=down:3:wrap
zstyle ':fzf-tab:complete:cd:*' fzf-preview 'ls $realpath'
zstyle ':fzf-tab:*' use-fzf-default-opts yes
zstyle ":completion:*:git-checkout:*" sort false
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}
# SAD
zinit ice from="gh-r" as="program" bpick="*apple-darwin*" pick="sad"
zinit light ms-jpq/sad
# SYNTAX HIGHLIGHTING
zinit ice wait="0c" lucid atinit="zpcompinit;zpcdreplay"
zinit light zdharma-continuum/fast-syntax-highlighting
# LSD
zinit ice wait="2" lucid from="gh-r" as="program" bpick="*apple-darwin.tar.gz" mv="*/lsd -> lsd"
zinit light lsd-rs/lsd
zinit ice wait blockf atpull'zinit creinstall -q .'
# MISE ZSH PLUGIN - Enhanced completions and suggestions
# https://github.com/wintermi/zsh-mise
zinit ice wait="0a" lucid
zinit light wintermi/zsh-mise
# DELTA
# zinit ice lucid wait="0" as="program" from="gh-r" pick="delta*/delta"
# zinit light dandavison/delta
# DUST for RUST
# zinit ice wait="2" lucid from="gh-r" as="program" atload="alias du=dust"
# zinit light bootandy/dust
# BOTTOM
zinit ice wait="2" lucid from="gh-r" as="program" bpick="*apple-darwin*" pick="*/btm"
zinit light ClementTsang/bottom
# DUF
zinit ice lucid wait="0" as="program" from="gh-r" atload="alias df=duf"
zinit light muesli/duf
# BAT for CAT
# zinit ice from="gh-r" as="program" mv="bat* -> bat" pick="bat/bat" atload="alias cat=bat"
# zinit light sharkdp/bat
# BAT-EXTRAS
# zinit ice lucid wait="1" as="program" pick="src/batgrep.sh"
# zinit ice lucid wait="1" as="program" pick="src/batdiff.sh"
# zinit light eth-p/bat-extras
# alias rg=batgrep.sh
# alias bd=batdiff.sh
# alias man=batman.sh
# RIPGREP
zinit ice from="gh-r" as="program" mv="ripgrep* -> ripgrep" pick="ripgrep/rg"
zinit light BurntSushi/ripgrep
# NEOVIM
# zinit ice lucid wait from="gh-r" as="program" ver="nightly" pick"./*/*/nvim"
# zinit light neovim/neovim
# # NEOVIDE
# zinit ice from="gh-r" as="program" bpick="*appimage"  mv="neo* -> neovide" pick="neovide"
# zinit light neovide/neovide
# WEZTERM for Multiplexer Terminal
# zinit ice from="gh-r" as="program" bpick="*ebian11.deb" ver="nightly" pick="usr/bin/wezterm"
# zinit ice from="gh-r" as="program" bpick="*appimage*" mv="Wez* -> wezterm" pick="wezterm"
# zinit light wez/wezterm
# FORGIT
zinit ice wait lucid
zinit load wfxr/forgit
# LAZYGIT
zinit ice lucid wait="0" as="program" from="gh-r" mv="lazygit* -> lazygit" atload="alias lg='lazygit'"
zinit light jesseduffield/lazygit
# LAZYDOCKER
zinit ice lucid wait="0" as="program" from="gh-r" mv="lazydocker* -> lazydocker" atload="alias ld='lazydocker'"
zinit light jesseduffield/lazydocker
# FD
zinit ice as="command" from="gh-r" mv="fd* -> fd" pick="fd/fd"
zinit light sharkdp/fd
# GH-CLI
zinit ice lucid wait="0" as="program" from="gh-r" pick="gh*/bin/gh"
zinit light cli/cli
# 1PASSWORD COMPLETION
zinit ice as="completion" atclone="command -v op &>/dev/null && op completion zsh > _op || true" atpull="zinit creinstall -q ."  nocompile
zinit light zdharma-continuum/null
# GOOGLE-CLOUD-SDK COMPLETION
# zinit ice as="completion"; zinit snippet /opt/google-cloud-sdk/completion.zsh.inc
# TMUXINATOR
# zinit ice as="completion"; zinit snippet ~/.tmuxinator.zsh
# ZSH MANYDOTS MAGIC (Creating conflict - https://github.com/knu/zsh-manydots-magic/issues/2)
# zinit ice depth"1" wait lucid pick"manydots-magic" compile"manydots-magic"
# zinit light knu/zsh-manydots-magic
# TREE-SITTER for NeoVIM
# zinit ice as="program" from="gh-r" mv="tree* -> tree-sitter" pick="tree-sitter"
# zinit light tree-sitter/tree-sitter
# XURLS (extract urls from text - requires go)
# zinit ice as="program" from="gh-r" mv="xurls* -> xurls" pick="xurls"
# zinit light mvdan/xurls
# PRETTYPING
zinit ice lucid wait="" as="program" pick="prettyping" atload="alias ping=prettyping"
zinit load denilsonsa/prettyping

# VSCODE-NODE-DEBUG for NVIM-DAP
# npm install
# npm run buil
zinit ice lucid wait="0" nocompile nocompletions
zinit light microsoft/vscode-node-debug2.git
# CROC (for file sharing)
# zinit ice lucid wait="0" as="program" from="gh-r" bpick="*64bit*"
# zinit light schollz/croc
# GLOW
# zinit ice lucid wait"0" as"program" from"gh-r" bpick='*_amd64.deb' pick"usr/bin/glow"
# zinit light charmbracelet/glow
# ERDTREE
zinit ice lucid wait"0" as"program" from"gh-r"
zinit light solidiquis/erdtree
# GTRASH (for trash)
# zinit ice lucid wait"0" as"program" from"gh-r"
# zinit light umlx5h/gtrash
# ATUIN
zinit ice as"program" from"gh-r" pick="**/atuin" ver="v18.2.0"
zinit light atuinsh/atuin
# YAZI
zinit ice lucid wait"0" as"program" from"gh-r" pick="*/yazi"
zinit light sxyazi/yazi
# ZSH-VI-MODE
# zinit light jeffreytse/zsh-vi-mode
# OVERMIND (for process management using procfile go)
# zinit ice lucid wait"0" as"program" from"gh-r" mv="over* -> overmind" pick="overmind"
# zinit light DarthSim/overmind

#########################################################################
# HISTORY
#########################################################################
[ -z "$HISTFILE" ] && HISTFILE="$HOME/.zhistory"
HISTSIZE=290000
SAVEHIST=$HISTSIZE

#########################################################################
# SETOPT
#########################################################################
setopt extended_history       # record timestamp of command in HISTFILE
setopt hist_expire_dups_first # delete duplicates first when HISTFILE size exceeds HISTSIZE
setopt hist_ignore_all_dups   # ignore duplicated commands history list
setopt hist_ignore_space      # ignore commands that start with space
setopt hist_verify            # show command with history expansion to user before running it
setopt inc_append_history     # add commands to HISTFILE in order of execution
setopt share_history          # share command history data
setopt always_to_end          # cursor moved to the end in full completion
setopt hash_list_all          # hash everything before completion
# setopt completealiases        # complete alisases
setopt always_to_end          # when completing from the middle of a word, move the cursor to the end of the word
setopt complete_in_word       # allow completion from within a word/phrase
setopt nocorrect                # spelling correction for commands
setopt list_ambiguous         # complete as much of a completion until it gets ambiguous.
setopt nolisttypes
setopt listpacked
setopt automenu
unsetopt BEEP

#########################################################################
# ENV VARIABLE
#########################################################################
export EDITOR='/usr/local/bin/cursor'
export VISUAL=$EDITOR
# export PAGER='less'
export SHELL='/bin/zsh'
# export LANG='it_IT.UTF-8'
# export LC_ALL='it_IT.UTF-8'
# export BAT_THEME="gruvbox-dark"

#########################################################################
# COLORING
#########################################################################
autoload colors && colors

#########################################################################
# ALIASES
#########################################################################
source $HOME/.zsh_aliases

# env
#########################################################################
# source $HOME/.nubem_env

#########################################################################
# YAZI
#########################################################################
function ya() {
  local tmp="$(mktemp -t "yazi-cwd.XXXXX")"
  yazi "$@" --cwd-file="$tmp"
  if cwd="$(cat -- "$tmp")" && [ -n "$cwd" ] && [ "$cwd" != "$PWD" ]; then
    cd -- "$cwd"
  fi
  rm -f -- "$tmp"
}

#########################################################################
# FANCY-CTRL-Z
#########################################################################
function fg-fzf() {
  job="$(jobs | fzf -0 -1 | sed -E 's/\[(.+)\].*/\1/')" && echo '' && fg %$job
}

function fancy-ctrl-z () {
  if [[ $#BUFFER -eq 0 ]]; then
    BUFFER=" fg-fzf"
    zle accept-line -w
  else
    zle push-input -w
    zle clear-screen -w
  fi
}
zle -N fancy-ctrl-z
bindkey '^Z' fancy-ctrl-z

#########################################################################
# FZF SETTINGS
#########################################################################
export FZF_DEFAULT_OPTS="
--ansi
--layout=default
--info=inline
--color bg+:-1,gutter:-1
--height=50%
--multi
--preview-window=right:50%
--preview-window=sharp
--preview-window=cycle
--preview '([[ -f {} ]] && (bat --style=numbers --color=always --line-range :500 {} || cat {})) || ([[ -d {} ]] && (tree -C {} | less)) || echo {} 2> /dev/null | head -200'
--prompt='λ -> '
--pointer='❯'
--marker='✓'
--bind 'ctrl-e:execute(nvim {} < /dev/tty > /dev/tty 2>&1)' > selected
--bind 'ctrl-v:execute(code {+})'"
export FZF_DEFAULT_COMMAND='rg --files --no-ignore --hidden --follow -g "!{.git,node_modules}/*" 2> /dev/null'
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"

#########################################################################
# ATUIN
#########################################################################
atuin-setup() {
  ! hash atuin && return
  # bindkey '^R' _atuin_search_widget
  eval "$(atuin init zsh)"
}
atuin-setup

#########################################################################
# FZF-GC-PROJECT
#########################################################################
# Thanks to sei40kr/zsh-fzf-gcloud

# function fzf-gcloud-config-set-project() {
#   local project="$(gcloud projects list |
#     fzf --header-lines=1 --reverse |
#     awk '{ print $1 }')"
#   if [[ -n "$project" ]]; then
#     gcloud config set project "$project"
#   fi
# }
# zle -N fzf-gcloud-config-set-project
# bindkey '^G' fzf-gcloud-config-set-project
#########################################################################
# PATH
#########################################################################
export PATH=$PATH:/usr/local/go/bin:~/.local/bin:~/bin
#########################################################################
# GOOGLE-SDK
#########################################################################
# if [ -f '/opt/google-cloud-sdk/path.zsh.inc' ]; then . '/opt/google-cloud-sdk/path.zsh.inc'; fi
#########################################################################
# GO SETTINGS
#########################################################################
# export GOPATH=$HOME/Dev/go
#########################################################################
# FLUTTER SETTINGS
#########################################################################
# export PATH="$PATH:$HOME/Dev/flutter/bin"
#########################################################################
# ANDROID STUDIO SETTINGS
#########################################################################
# export PATH="$PATH:/opt/android-studio/bin"
#########################################################################
# MSSQL-TOOLS
#########################################################################
# export PATH="$PATH:/opt/mssql-tools18/bin"
#########################################################################
# CARGO
#########################################################################
# . "$HOME/.cargo/env"
#########################################################################
# YARN
#########################################################################
# export PATH="$HOME/.yarn/bin:$HOME/.config/yarn/global/node_modules/.bin:$PATH"
#########################################################################
# P10K SETTINGS (`p10k configure` to customize)
#########################################################################
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh
