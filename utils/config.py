from pathlib import Path

from hydra import compose, initialize_config_dir
from hydra.core.global_hydra import GlobalHydra
from omegaconf import DictConfig

ROOT = Path(__file__).resolve().parents[1]


def project_path(value):
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def load_config(overrides=()):
    if GlobalHydra.instance().is_initialized():
        cfg = compose(config_name="app", overrides=list(overrides))
    else:
        with initialize_config_dir(version_base="1.3", config_dir=str(ROOT / "config")):
            cfg = compose(config_name="app", overrides=list(overrides))
    validate_config(cfg)
    return cfg


def validate_config(cfg: DictConfig):
    if cfg.mode not in {"gui", "move", "uci", "match", "analyze", "lichess", "worker"}:
        raise ValueError(f"Unknown mode: {cfg.mode}")
    if not 1 <= cfg.engine.depth <= 20:
        raise ValueError("engine.depth must be between 1 and 20")
    if cfg.engine.time_ms is not None and cfg.engine.time_ms <= 0:
        raise ValueError("engine.time_ms must be positive or null")
    if cfg.engine.max_ply < 4 or cfg.engine.hash_entries < 1:
        raise ValueError("max_ply must be >= 4 and hash_entries must be positive")
    if cfg.engine.max_extensions < 0 or cfg.engine.moves_to_go < 1:
        raise ValueError("max_extensions must be nonnegative and moves_to_go positive")
    if not 0 <= cfg.engine.book_threshold <= 1:
        raise ValueError("engine.book_threshold must be between 0 and 1")
    if cfg.ui.mode not in {"human_ai", "ai_ai", "human_human"}:
        raise ValueError("Invalid ui.mode")
    if cfg.ui.player_color not in {"white", "black"}:
        raise ValueError("ui.player_color must be white or black")
    if cfg.ui.base_seconds <= 0 or cfg.ui.increment_seconds < 0:
        raise ValueError("Invalid clock settings")
    if cfg.ui.board_max_size < 320 or not 236 <= cfg.ui.sidebar_width <= 400:
        raise ValueError("Invalid board or sidebar dimensions")
    if cfg.ui.move_method not in {"both", "click", "drag"}:
        raise ValueError("ui.move_method must be both, click or drag")
    for name in ("max_premoves", "drag_threshold_px", "animation_ms", "premove_cost_ms"):
        if type(cfg.ui[name]) is not int:
            raise ValueError(f"ui.{name} must be an integer")
    if not 1 <= cfg.ui.max_premoves <= 5:
        raise ValueError("ui.max_premoves must be between 1 and 5")
    if cfg.ui.drag_threshold_px < 1 or cfg.ui.animation_ms < 0 or cfg.ui.premove_cost_ms < 0:
        raise ValueError("Invalid drag, animation or premove timing")
    if len(cfg.evaluation["values"]) != 7 or cfg.evaluation.endgame_material <= 0:
        raise ValueError("Invalid evaluation values")
    if any(len(table) != 64 for table in cfg.evaluation.tables.values()):
        raise ValueError("Each piece-square table must contain 64 values")
