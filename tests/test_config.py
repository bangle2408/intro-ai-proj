import pytest
from hydra import initialize_config_dir

from utils.config import ROOT, load_config, project_path


@pytest.mark.parametrize("preset,depth", [("easy", 2), ("default", 4), ("hard", 8)])
def test_hydra_groups(preset, depth):
    cfg = load_config([f"engine={preset}", "ui.player_color=black"])
    assert cfg.engine.depth == depth
    assert cfg.ui.player_color == "black"


def test_composition_inside_running_hydra():
    with initialize_config_dir(version_base="1.3", config_dir=str(ROOT / "config")):
        assert load_config(["engine=easy"]).engine.depth == 2


@pytest.mark.parametrize(
    "override",
    [
        "engine.depth=0",
        "engine.time_ms=-1",
        "ui.mode=unknown",
        "engine.book_threshold=2",
        "ui.move_method=unknown",
        "ui.max_premoves=6",
        "ui.animation_ms=-1",
        "ui.premove_cost_ms=-1",
        "ui.drag_threshold_px=0",
        "ui.max_premoves=1.5",
        "ui.annotation_opacity=-0.1",
        "ui.annotation_opacity=1.1",
        "ui.annotation_knight_bend=unknown",
    ],
)
def test_invalid_config_fails_early(override):
    with pytest.raises(ValueError):
        load_config([override])


def test_paths_do_not_depend_on_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert project_path("assets/openings.bin").is_file()
