# Chess

Ứng dụng cờ vua Python/PyQt5: chơi với AI, hai người chơi hoặc xem AI tự đấu.

## Cài đặt

Sử dụng Python 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python game.py
```

## Cách chơi

- **New game:** chọn chế độ, màu quân và đồng hồ.
- Kéo thả hoặc click quân rồi click ô đích để đi.
- Đặt trước nước đi (premove) khi AI đang nghĩ; chuột phải hoặc **Esc** để hủy.
- Giữ chuột phải và kéo để vẽ mũi tên; click phải để khoanh ô. Vẽ lại để xóa riêng,
  click trái hoặc **Esc** để xóa hết. Giữ **Ctrl / Alt / Shift** để đổi màu.
- **Preferences:** chỉnh độ khó, cách di chuyển và hiển thị.
- **Appearance:** chuyển sáng/tối. Thanh cạnh bàn cờ biểu thị ưu thế Trắng/Đen;
  bật/tắt trong **Preferences → Evaluation bar**.
- **Undo / Flip:** đi lại nước trước hoặc lật bàn cờ.
- **⋯:** lưu, tải ván cờ và đầu hàng.

## Cấu hình

Cấu hình Hydra nằm trong [`config/`](config/). Có thể chỉnh bằng tham số khi chạy:

```bash
python game.py engine=easy ui.player_color=black
python game.py engine=hard engine.time_ms=5000
python game.py --cfg job
```

`engine.time_ms` là thời gian suy nghĩ tối đa mỗi nước, tính bằng mili giây.
`--cfg job` hiển thị cấu hình hiện tại.

## Chế độ dòng lệnh

| Chế độ | Lệnh |
| --- | --- |
| Engine UCI | `python game.py mode=uci` |
| AI tự đấu, lưu PGN | `python game.py mode=match match.games=2` |
| Thống kê kết quả PGN | `python game.py mode=analyze pgn=results/match.pgn` |
| Bot Lichess | `python game.py mode=lichess` |

Lichess cần tài khoản BOT và token trong biến môi trường `LICHESS_TOKEN`.

## Kiểm thử

```bash
pip install -e ".[dev]"
QT_QPA_PLATFORM=offscreen python -m pytest -q
ruff check .
```
