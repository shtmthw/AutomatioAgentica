#!/usr/bin/env bash
# One-command setup for AutomatioAgentica (Linux and macOS; on Windows use WSL2 Ubuntu).
#
#   scripts/setup.sh              install what is missing, asking before system packages
#   scripts/setup.sh --yes        no questions (CI, fresh machines)
#   scripts/setup.sh --skip-system  only the Python side (venv, packages, .env, checks)
#   scripts/setup.sh --no-tests   skip the ~30 s offline test at the end
#
# Steps: system packages (ffmpeg, cairo/pango, the three fonts, uv) -> Python 3.12 venv in
# .venv -> Python packages (incl. the MCP SDK) -> .env from .env.example -> doctor -> tests.
# Safe to run again: each step skips what is already there.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

YES=0; SKIP_SYSTEM=0; TESTS=1
for arg in "$@"; do
  case "$arg" in
    -y|--yes) YES=1 ;;
    --skip-system) SKIP_SYSTEM=1 ;;
    --no-tests) TESTS=0 ;;
    -h|--help) sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg (see --help)" >&2; exit 2 ;;
  esac
done

bold() { printf '\033[1m%s\033[0m\n' "$*"; }
note() { printf '  %s\n' "$*"; }
warn() { printf '  \033[33m! %s\033[0m\n' "$*"; }
ask() {  # ask "question" -> 0 for yes
  [ "$YES" = 1 ] && return 0
  [ -t 0 ] || { warn "not a terminal: pass --yes to allow: $1"; return 1; }
  read -r -p "  $1 [Y/n] " r; [ -z "$r" ] || [[ "$r" =~ ^[Yy] ]]
}
have() { command -v "$1" >/dev/null 2>&1; }
SUDO=""; if [ "$(id -u)" != 0 ] && have sudo; then SUDO="sudo"; fi
FONT_LIST=""; if have fc-list; then FONT_LIST="$(fc-list : family 2>/dev/null || true)"; fi
font_ok() { grep -qiE "$1" <<<"$FONT_LIST"; }      # here-string, not a pipe: pipefail + grep -q

# ------------------------------------------------------------------ 1. system packages
PM=""
if have brew; then PM=brew; elif have pacman; then PM=pacman; elif have apt-get; then PM=apt; elif have dnf; then PM=dnf; fi

pkg_installed() {
  case "$PM" in
    pacman) pacman -Q "$1" >/dev/null 2>&1 ;;
    apt)    dpkg -s "$1" >/dev/null 2>&1 ;;
    dnf)    rpm -q "$1" >/dev/null 2>&1 ;;
    brew)   brew list "$1" >/dev/null 2>&1 ;;
  esac
}
core=(); fonts=()
need() { for p in "$@"; do pkg_installed "$p" || core+=("$p"); done; }      # libraries and tools
need_font() { font_ok "$1" || fonts+=("$2"); }                             # need_font <fc regex> <package>

install_pkgs() {  # install_pkgs required|fonts pkg...
  local kind="$1"; shift
  [ "$#" = 0 ] && return 0
  case "$PM" in
    pacman) cmd=($SUDO pacman -S --needed --noconfirm "$@") ;;
    apt)    cmd=($SUDO apt-get install -y "$@") ;;
    dnf)    cmd=($SUDO dnf install -y "$@") ;;
    brew)   if [ "$kind" = fonts ]; then cmd=(brew install --cask "$@"); else cmd=(brew install "$@"); fi ;;
  esac
  note "${cmd[*]}"
  if ! "${cmd[@]}"; then
    if [ "$kind" = required ]; then warn "install failed: ${*}"; return 1; fi
    warn "font package(s) not installed: ${*} (doctor will name what is missing)"
  fi
}

bold "1/6 System packages"
if [ "$SKIP_SYSTEM" = 1 ]; then
  note "skipped (--skip-system)"
elif [ -z "$PM" ]; then
  warn "no supported package manager (brew, pacman, apt, dnf). Install by hand: ffmpeg (libx264, rubberband),"
  warn "cairo + pango, the fonts Inter, JetBrains Mono and Noto Sans Devanagari, and uv."
else
  case "$PM" in
    pacman) have ffmpeg || core+=(ffmpeg); need cairo pango pkgconf base-devel; have uv || core+=(uv)
            need_font "^Inter" inter-font; need_font "JetBrains ?Mono" ttf-jetbrains-mono
            need_font "Noto Sans Devanagari" noto-fonts ;;
    apt)    have ffmpeg || core+=(ffmpeg)
            need libcairo2-dev libpango1.0-dev pkg-config build-essential python3-dev curl
            need_font "^Inter" fonts-inter; need_font "JetBrains ?Mono" fonts-jetbrains-mono
            need_font "Noto Sans Devanagari" fonts-noto-core ;;
    dnf)    if ! have ffmpeg; then
              warn "Fedora's ffmpeg-free lacks libx264: enable RPM Fusion first"
              warn "(https://rpmfusion.org/Configuration), then this installs ffmpeg"; core+=(ffmpeg)
            fi
            need cairo-devel pango-devel pkgconf-pkg-config gcc python3-devel; have uv || core+=(uv)
            need_font "^Inter" rsms-inter-fonts; need_font "JetBrains ?Mono" jetbrains-mono-fonts
            need_font "Noto Sans Devanagari" google-noto-sans-devanagari-fonts ;;
    brew)   have ffmpeg || core+=(ffmpeg); need cairo pango pkg-config; have uv || core+=(uv)
            need_font "^Inter" font-inter; need_font "JetBrains ?Mono" font-jetbrains-mono
            need_font "Noto Sans Devanagari" font-noto-sans-devanagari ;;
  esac
  note "package manager: $PM"
  if [ "${#core[@]}" = 0 ] && [ "${#fonts[@]}" = 0 ]; then
    note "all present"
  elif ask "install system packages: ${core[*]:-} ${fonts[*]:-}?"; then
    [ "$PM" = apt ] && { note "$SUDO apt-get update"; $SUDO apt-get update -qq; }
    [ "${#core[@]}" -gt 0 ] && install_pkgs required "${core[@]}"
    [ "${#fonts[@]}" -gt 0 ] && install_pkgs fonts "${fonts[@]}"
    have fc-cache && fc-cache -f >/dev/null 2>&1 || true
  else
    note "skipped; doctor lists what is missing"
  fi
fi

# ------------------------------------------------------------------ 2. uv
bold "2/6 uv (Python package manager)"
if ! have uv; then
  [ -x "$HOME/.local/bin/uv" ] && export PATH="$HOME/.local/bin:$PATH"
fi
if ! have uv; then
  if ask "uv is missing: install it with the official installer (https://astral.sh/uv)?"; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
  fi
fi
have uv || { warn "uv is required: https://docs.astral.sh/uv/getting-started/installation/"; exit 1; }
note "$(uv --version)"

# ------------------------------------------------------------------ 3. venv
bold "3/6 Python 3.12 virtual environment (.venv)"
if [ -x .venv/bin/python ] && .venv/bin/python -c 'import sys; sys.exit(sys.version_info[:2] != (3, 12))'; then
  note "exists: $(.venv/bin/python --version)"
else
  [ -e .venv ] && { warn ".venv is not Python 3.12: recreating it"; rm -rf .venv; }
  uv venv --python 3.12 .venv           # uv downloads Python 3.12 if the system has none
fi

# ------------------------------------------------------------------ 4. packages
bold "4/6 Python packages (manim, edge-tts, numpy, soundfile, mcp)"
uv pip install --quiet --python .venv/bin/python -r pyproject.toml --extra mcp
note "installed"

# ------------------------------------------------------------------ 5. credentials file
bold "5/6 Credentials file (.env)"
if [ -f .env ]; then
  note ".env exists (not read here, never printed)"
else
  cp .env.example .env
  chmod 600 .env
  note "created .env from .env.example. Add ELEVENLABS_API_KEY only if you want the Hindi voice;"
  note "English needs no key."
fi

# ------------------------------------------------------------------ 6. checks
bold "6/6 Checks"
.venv/bin/python -m automatio doctor || warn "doctor found missing items (✗ above)"
if [ "$TESTS" = 1 ]; then
  note "offline end-to-end test (~30 s: renders a tiny production with test tones, no network)"
  .venv/bin/python -m unittest discover -s tests
fi

bold "Ready. Connect your agent harness:"
note "Claude Code, Codex, Cursor, Gemini CLI: open this folder; the agent reads AGENTS.md (Claude Code: /produce-video)."
note "Any MCP client: .venv/bin/python -m automatio mcp-config    # prints the config for your client"
