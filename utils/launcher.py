import logging

import hydra
from omegaconf import DictConfig

from utils.config import ROOT, validate_config


@hydra.main(version_base="1.3", config_path=str(ROOT / "config"), config_name="app")
def main(cfg: DictConfig):
    logging.basicConfig(level=logging.WARNING, force=True)
    validate_config(cfg)
    if cfg.mode == "gui":
        from ui.app import run
    elif cfg.mode == "uci":
        from services.uci import run
    elif cfg.mode == "match":
        from services.match import run
    elif cfg.mode == "analyze":
        from services.analysis import run
    elif cfg.mode == "lichess":
        from services.lichess import run
    elif cfg.mode == "worker":
        from core.worker import run
    else:
        from core.engine import run
    run(cfg)
