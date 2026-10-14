import shutil
import subprocess
from pathlib import Path

import pytest

from deepwick_spec.ansi import style_of
from deepwick_spec.check_port import check_port
from deepwick_spec.palette import load_palette
from deepwick_spec.tui import capture, tmux_available

REPO = Path(__file__).resolve().parents[1]
PALETTE = load_palette()
C = PALETTE.colors
UPSTREAM = "https://github.com/zsh-users/zsh-syntax-highlighting"

EXPECTED = {
    "default": f"fg={C['foreground']}",
    "unknown-token": f"fg={C['red']}",
    "reserved-word": f"fg={C['blue']}",
    "builtin": f"fg={C['blue']}",
    "alias": f"fg={C['yellow']}",
    "function": f"fg={C['yellow']}",
    "command": f"fg={C['yellow']}",
    "hashed-command": f"fg={C['yellow']}",
    "precommand": f"fg={C['yellow']},underline",
    "path": f"fg={C['foreground']},underline",
    "globbing": f"fg={C['gold']}",
    "single-quoted-argument": f"fg={C['orange']}",
    "double-quoted-argument": f"fg={C['orange']}",
    "dollar-double-quoted-argument": f"fg={C['lightBlue']}",
    "single-hyphen-option": f"fg={C['lightBlue']}",
    "double-hyphen-option": f"fg={C['lightBlue']}",
    "assign": f"fg={C['lightBlue']}",
    "comment": f"fg={C['comment']}",
    "bracket-error": f"fg={C['red']}",
}


@pytest.fixture(scope="module")
def upstream(tmp_path_factory):
    if shutil.which("zsh") is None or shutil.which("git") is None:
        pytest.skip("requires zsh and git")
    dest = tmp_path_factory.mktemp("zsh") / "zsh-syntax-highlighting"
    result = subprocess.run(["git", "clone", "--quiet", "--depth", "1", UPSTREAM, str(dest)], capture_output=True, text=True)
    if result.returncode != 0:
        pytest.skip(f"cannot clone zsh-syntax-highlighting: {result.stderr}")
    return dest


def test_styles_after_sourcing(upstream):
    script = (
        f"source {upstream / 'zsh-syntax-highlighting.zsh'}; source {REPO / 'deepwick.zsh'}; "
        'for k in ${(k)ZSH_HIGHLIGHT_STYLES}; do print -r -- "$k=${ZSH_HIGHLIGHT_STYLES[$k]}"; done'
    )
    out = subprocess.run(["zsh", "-f", "-c", script], capture_output=True, text=True, check=True).stdout
    styles = dict(line.split("=", 1) for line in out.splitlines())
    for key, expected in EXPECTED.items():
        assert styles[key] == expected, key


@pytest.mark.skipif(not tmux_available(), reason="requires tmux")
def test_highlighting_renders(upstream, tmp_path):
    (tmp_path / ".zshrc").write_text(
        "PS1='deepwick> '\nsetopt interactivecomments\n"
        f"source {upstream / 'zsh-syntax-highlighting.zsh'}\nsource {REPO / 'deepwick.zsh'}\n"
    )
    text = capture("zsh -i", {"ZDOTDIR": str(tmp_path)}, wait_for="deepwick>", literal="echo 'quoted' # note")
    assert style_of(text, "echo")["fg"] == C["blue"].lower()
    assert style_of(text, "'quoted'")["fg"] == C["orange"].lower()
    assert style_of(text, "# note")["fg"] == C["comment"].lower()


def test_port_conventions():
    assert check_port(REPO, PALETTE.allowed_hex()) == []
