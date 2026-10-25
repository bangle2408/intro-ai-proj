import pytest


def luminance(color):
    values = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
    return sum(v * weight for v, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


@pytest.mark.parametrize(
    "foreground,background,minimum",
    [
        ("text", "background", 4.5),
        ("muted", "background", 4.5),
        ("text", "surface", 4.5),
        ("text", "surface_alt", 4.5),
        ("surface", "accent", 4.5),
        ("light_square", "dark_square", 3),
        ("white_piece_border", "light_square", 3),
        ("black_piece_border", "dark_square", 3),
    ],
)
def test_palette_preserves_readability(cfg, foreground, background, minimum):
    a, b = sorted((luminance(cfg.ui[foreground]), luminance(cfg.ui[background])))
    assert (b + 0.05) / (a + 0.05) >= minimum
