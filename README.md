# Smart Parking Pygame

Dự án mô phỏng hệ thống bãi đỗ xe thông minh bằng Python + Pygame trên bản đồ lưới 2D.

## Mục tiêu

- Mô phỏng bãi đỗ xe dạng grid 12x18.
- Tạo xe ô tô và xe máy từ cổng vào.
- Tìm ô đỗ phù hợp theo loại xe.
- Tìm đường bằng các thuật toán tìm kiếm cơ bản.
- Hiển thị map, xe, đường đi, trạng thái và log bằng Pygame.
- Không sử dụng Machine Learning, Deep Learning hoặc Computer Vision.

## Trạng thái hiện tại

Đã có bản chạy demo cơ bản:

- Load map 12x18 từ `data/maps/default_map.txt`.
- Parse các cell type: gate, road, intersection, obstacle, car slot, motorbike slot.
- Spawn xe bằng phím `C` và `M`.
- Assign slot theo scoring đơn giản.
- Tìm đường bằng A* và cho xe di chuyển từng cell, không đi xuyên qua ô đang có xe khác.
- Có BFS, DFS, Greedy, A* trong `ai/pathfinding/`.
- Có traffic controller rule-based ở mức cơ bản.
- Có renderer Pygame vẽ grid, xe, path, sidebar, stats và logs.

UI hiện tại ở mức demo/basic test, chưa phải giao diện game hoàn thiện.

## Cấu trúc thư mục

```text
smart_parking_pygame/
├── main.py
├── config.py
├── requirements.txt
├── README.md
├── history.md
├── core/
├── models/
├── ai/
│   ├── pathfinding/
│   └── decision/
├── ui/
├── utils/
├── data/
│   ├── maps/
│   └── scenarios/
└── tests/
```

## Cài đặt

```bash
pip install -r requirements.txt
```

Trên máy hiện tại, lệnh `python` đang trỏ tới MSYS Python chưa có `pygame`. Python 3.13 đã có `pygame`, nên lệnh chạy ổn là:

```bash
py -3.13 main.py
```

Nếu muốn dùng đúng:

```bash
python main.py
```

hãy đảm bảo `python` trỏ tới interpreter đã cài `pygame`.

## Điều khiển

- `C`: spawn xe ô tô.
- `M`: spawn xe máy.
- `A`: bật/tắt auto spawn.
- Click chuột trái vào xe: chọn xe và chuyển sang manual mode.
- `W/A/S/D` hoặc phím mũi tên: di chuyển xe manual.
- `ENTER`: xác nhận đỗ xe đã chọn.
- `ESC`: bỏ chọn xe.

## Kiểm tra nhanh

```bash
py -3.13 -m compileall -q .
py -3.13 main.py
```

## Giới hạn hiện tại

- Chưa có đồ họa sprite/tilemap nâng cao.
- Chưa có animation mượt, xe đang nhảy theo cell.
- Traffic/congestion logic mới ở mức rule-based cơ bản.
- Collision/occupancy đã được chặn ở mức cơ bản; vẫn cần test thêm cho nhiều xe và ùn tắc phức tạp.
- Test trong `tests/` vẫn cần được phát triển thêm.


