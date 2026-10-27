from omegaconf import OmegaConf
from PyQt5.QtWidgets import QApplication

from ui.theme import apply_theme
from ui.widgets import ActionButton
from utils.config import ROOT


class GameAppearance:
    def toggle_appearance(self):
        self.set_appearance("light" if self.cfg.appearance.name == "dark" else "dark")

    def set_appearance(self, name):
        if name not in ("light", "dark"):
            raise ValueError("Appearance must be light or dark")
        self.cfg.appearance = OmegaConf.load(ROOT / "config" / "appearance" / f"{name}.yaml")
        apply_theme(QApplication.instance(), self.cfg.ui)
        self.board_view.reset_pointer()
        self.header.appearance.symbol = "moon" if name == "dark" else "sun"
        self.header.appearance.setChecked(name == "dark")
        self.header.appearance.setAccessibleDescription(
            f"{name.title()} appearance. Click to switch."
        )
        for button in self.findChildren(ActionButton):
            button.update_icon(self.cfg.ui)
        self.top_player.color = self.bottom_player.color = None
        self.panel.history.viewport().update()
        self.refresh()
