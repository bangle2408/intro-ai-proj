from PyQt5.QtGui import QColor, QFont, QPalette


def apply_theme(app, cfg):
    app.setStyle("Fusion")
    app.setFont(QFont(cfg.font, cfg.font_size))
    palette = app.palette()
    for role, color in (
        (QPalette.Window, cfg.background),
        (QPalette.Base, cfg.surface),
        (QPalette.Text, cfg.text),
        (QPalette.WindowText, cfg.text),
        (QPalette.ButtonText, cfg.text),
        (QPalette.Highlight, cfg.accent),
        (QPalette.HighlightedText, cfg.surface),
    ):
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    app.setStyleSheet(f'''
        QWidget {{ color: {cfg.text}; font-family: "{cfg.font}"; font-size: 14px; }}
        QMainWindow, QDialog, QWidget#canvas {{ background: {cfg.background}; }}
        QLabel {{ background: transparent; }}
        QLabel#brand {{ font-family: "DejaVu Serif"; font-size: 29px; font-weight: 500; }}
        QLabel#title {{ font-size: 23px; font-weight: 600; }}
        QLabel#section {{ font-size: 12px; color: {cfg.muted}; letter-spacing: 1px; }}
        QLabel#muted {{ color: {cfg.muted}; font-size: 12px; }}
        QLabel#status {{ font-size: 19px; font-weight: 500; }}
        QLabel#playerName {{ font-weight: 600; }}
        QLabel#playerClock {{ font-family: "DejaVu Sans Mono"; font-size: 23px;
            padding: 9px 12px; border-radius: 8px; color: {cfg.muted}; }}
        QLabel#playerClock[active="true"] {{ background: {cfg.surface_alt}; color: {cfg.text}; }}
        QPushButton {{ background: transparent; border: 1px solid transparent;
            border-radius: 8px; padding: 8px 12px; font-weight: 500; min-height: 22px; }}
        QPushButton:hover {{ background: {cfg.surface_alt}; }}
        QPushButton:pressed {{ background: {cfg.border}; }}
        QPushButton:focus {{ border: 1px solid {cfg.focus}; }}
        QPushButton:disabled {{ color: {cfg.muted}; }}
        QPushButton#primary {{ background: {cfg.accent}; color: {cfg.surface}; padding: 9px 18px; }}
        QPushButton#primary:hover {{ background: {cfg.text}; }}
        QPushButton#segment {{ border: 1px solid {cfg.border}; padding: 8px 10px; }}
        QPushButton#segment:checked {{ background: {cfg.surface_alt}; border-color: {cfg.accent}; }}
        QPushButton::menu-indicator {{ image: none; width: 0; }}
        QComboBox, QSpinBox {{ background: {cfg.surface}; border: 1px solid {cfg.border};
            border-radius: 8px; padding: 8px 28px 8px 12px; selection-background-color: {cfg.accent}; }}
        QComboBox:focus, QSpinBox:focus {{ border-color: {cfg.focus}; }}
        QComboBox::drop-down {{ border: none; width: 28px; }}
        QComboBox::down-arrow {{ image: none; }}
        QComboBox QAbstractItemView {{ background: {cfg.surface}; border: 1px solid {cfg.border};
            padding: 6px; selection-background-color: {cfg.surface_alt}; selection-color: {cfg.text}; }}
        QAbstractItemView {{ outline: none; }}
        QTableView {{ background: transparent; border: none; padding: 0; }}
        QHeaderView {{ background: transparent; }}
        QHeaderView::section {{ color: {cfg.muted}; background: transparent; border: none;
            border-bottom: 1px solid {cfg.border}; padding: 10px 0; font-size: 12px; }}
        QScrollBar:vertical {{ background: transparent; width: 5px; margin: 0; }}
        QScrollBar::handle:vertical {{ background: {cfg.border}; border-radius: 2px; min-height: 24px; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        QMenu {{ background: {cfg.surface}; border: 1px solid {cfg.border}; padding: 6px; }}
        QMenu::item {{ padding: 10px 24px 10px 12px; border-radius: 5px; }}
        QMenu::item:selected {{ background: {cfg.surface_alt}; }}
        QMenu::separator {{ height: 1px; background: {cfg.border}; margin: 5px 8px; }}
        QFrame#divider {{ background: {cfg.border}; max-height: 1px; border: none; }}
    ''')
