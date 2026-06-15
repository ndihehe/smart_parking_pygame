# Smart Parking Simulation

## 1. Giới thiệu dự án

**Smart Parking Simulation** là dự án mô phỏng hệ thống bãi đỗ xe thông minh trên bản đồ lưới 2D. Xe (ô tô và xe máy) vào bãi qua cổng, được gán ô đỗ phù hợp, tìm đường di chuyển và có thể rời bãi qua cổng ra.

Dự án áp dụng các thuật toán tìm kiếm trong trí tuệ nhân tạo (BFS, DFS, Greedy Best-First Search, A*) để tìm đường và điều phối xe. Giao diện được xây dựng bằng **Python** và **Pygame**, hiển thị bản đồ pixel art, sprite xe/guard và panel điều khiển bên cạnh.

Hệ thống **không** sử dụng Machine Learning, Deep Learning hay Computer Vision.

---

## 2. Mục tiêu dự án

- Mô phỏng hoạt động xe trong bãi đỗ: vào bãi, tìm chỗ, đỗ xe, rời bãi.
- Tìm đường từ vị trí hiện tại đến ô đỗ hoặc cổng ra bằng thuật toán tìm kiếm.
- So sánh và chuyển đổi giữa **BFS**, **DFS**, **Greedy Best-First Search** và **A*** trong cùng một môi trường mô phỏng.
- Quản lý trạng thái xe: `MOVING`, `PARKED`, `WAITING`, `MANUAL`, `REROUTING`, `ARRIVED`, `VIOLATION`.
- Xử lý ùn tắc giao thông trong bãi: phát hiện kẹt tại ngã tư, nhường đường theo độ ưu tiên và reroute khi cần; guard chỉ xử lý vi phạm đỗ sai chỗ/sai loại.
- Gán ô đỗ theo loại xe (ô tô / xe máy) và chấm điểm vị trí phù hợp.
- Hỗ trợ kịch bản **Traffic Jam Mode** và đặt xe thủ công để kiểm thử các tình huống.

---

## 3. Công nghệ sử dụng

| Thành phần | Chi tiết |
|---|---|
| Ngôn ngữ | Python 3 (khuyến nghị Python 3.11 trở lên; dự án đã kiểm thử với Python 3.13) |
| Thư viện chính | [Pygame](https://www.pygame.org/) `>= 2.6.0` (dependency duy nhất trong `requirements.txt`) |
| Thư viện chuẩn | `json`, `pathlib`, `collections`, `heapq`, `dataclasses`, `enum`, `unittest` |
| Assets | Kenney Pixel Vehicle Pack (CC0), TopDown Vehicles v1.17 và retro vehicle sprites — sprite xe, moto, guard, props |
| Bản đồ | `data/map_layout.json` (ảnh nền + lưới logic), `data/maps/default_map.txt` (định dạng text) |
| Công cụ phụ | `tools/map_annotator.py` — công cụ Pygame để gán loại ô lên ảnh bản đồ; `tools/map_layout_viewer.py` — công cụ xem riêng map và các ô đã đánh dấu |

---

## 4. Kiến thức áp dụng

### Trí tuệ nhân tạo cơ bản
- Mô hình bài toán tìm đường trên lưới (grid graph).
- Heuristic Manhattan cho Greedy và A*.
- Quy tắc ưu tiên (rule-based) để giải quyết xung đột tại ngã tư.
- Chấm điểm ô đỗ (`slot_scoring`) dựa trên khoảng cách, vùng tắc và chướng ngại vật lân cận.

### Thuật toán tìm kiếm không có thông tin
- **BFS** — duyệt theo chiều rộng, dùng hàng đợi (`deque`).
- **DFS** — duyệt theo chiều sâu, dùng ngăn xếp (`stack`).

### Thuật toán tìm kiếm có thông tin
- **Greedy Best-First Search** — chọn ô kế tiếp theo heuristic Manhattan.
- **A\*** — kết hợp chi phí thực tế `g(n)` và heuristic `h(n)` (Manhattan).

### Cấu trúc dữ liệu
- **Queue** (`collections.deque`) — BFS.
- **Stack** (danh sách Python) — DFS.
- **Priority queue** (`heapq`) — Greedy, A*.
- **Graph / grid** — bản đồ ô vuông với các loại cell và hàng xóm 4 hướng.

### Xử lý va chạm và ô hợp lệ
- Kiểm tra ô đi được (`is_passable`, `is_drive_cell`, `can_vehicle_enter`).
- Chặn xe đi xuyên qua xe khác, slot đã reserved/occupied và vị trí `dynamic_blocks`.
- Truyền `blocked_positions` vào mọi thuật toán pathfinding.

### Quản lý trạng thái mô phỏng
- Enum trạng thái mô phỏng: `IDLE`, `PLACING_VEHICLE`, `READY`, `RUNNING`, `PAUSED`, `FINISHED`.
- Enum lý do chờ (`WaitReason`): thiếu slot, không có đường, ùn tắc, nhường đường, vi phạm đỗ xe, v.v.
- Vòng lặp game: nhận input → cập nhật logic → render.

### Lập trình hướng đối tượng
- Các lớp quản lý: `GameController`, `MapManager`, `VehicleManager`, `ParkingManager`, `TrafficController`.
- Model dữ liệu: `Vehicle`, `Guard`, `ParkingSlot`, `MapState` (dataclass / enum).

### Thiết kế giao diện game 2D bằng Pygame
- Main menu, sidebar điều khiển, viewport map co giãn theo cửa sổ.
- Sprite loader, tile renderer, animation guard đi bộ.
- Overlay thông tin xe được chọn và highlight đường đi.

---

## 5. Chức năng chính

Các chức năng dưới đây đều có trong code hiện tại:

### Giao diện
- **Start Menu** — màn hình mở đầu với nút Play / Exit, nền ảnh và dòng credit.
- **Hiển thị map bãi đỗ** — lưới 30×40 (map mặc định), ảnh nền `parking_map.png`, tile pseudo-3D hoặc sprite trang trí.
- **Sidebar điều khiển** — chọn thuật toán, mode, điều khiển mô phỏng và thống kê; tự chuyển sang layout compact khi chiều cao cửa sổ thấp.
- **Viewport co giãn** — cửa sổ resize được; fullscreen bằng `F11`.
- **Highlight** — xe được chọn, ô đỗ được gán, đường đi (path dots), vị trí dynamic block.

### Thuật toán và mô phỏng
- **Chọn thuật toán** BFS / DFS / Greedy / A* (sidebar hoặc phím `1`–`4`).
- **Thêm xe** — bấm Car/Motorbike hoặc phím `C`/`M` khi chưa bật `Place Vehicle` để spawn xe vào bãi; hoặc bật auto spawn (`T`) để tự sinh xe ngẫu nhiên tại cổng vào.
- **Đặt xe thủ công** — bật `Place Vehicle`, chọn loại Car/Motorbike và kế hoạch Entering/Exiting, click lên map. Nút Entering/Exiting chỉ có hiệu lực trong chế độ `Place Vehicle`.
- **Traffic Jam Mode** — tạo sẵn 8 xe quanh vùng ngã tư để mô phỏng ùn tắc; trạng thái `READY`, nhấn Enter để chạy.
- **Reset mô phỏng** — xóa xe, giải phóng slot, reset guard và trạng thái.
- **Tốc độ mô phỏng** — Normal Speed, Slow View (0.25×), Step Mode (từng bước di chuyển).
- **Start simulation** — sau khi đặt xe hoặc load kịch bản, nhấn Enter để bắt đầu.

### Xe và bãi đỗ
- Hai loại xe: **CAR** (ô `C`) và **MOTORBIKE** (ô `M`).
- Gán slot theo scoring; reserve khi assign, occupied khi thực sự đỗ.
- Xe vào qua cổng trái, ra qua cổng phải.
- **Manual mode** — click trái chọn xe; điều khiển bằng `W/A/S/D` hoặc phím mũi tên; Enter xác nhận đỗ; ESC hủy chọn.
- **Rời bãi** — click phải vào xe hoặc đặt xe với plan Exiting.
- **Tandem exit** — xử lý xe máy đỗ nối đuôi (inner/outer slot).

### Giao thông và guard
- Phát hiện ùn tắc tại ngã tư (số xe chờ, thời gian chờ, timer ngã tư).
- Giải quyết xung đột nhiều xe cùng nhắm một ô (`resolve_conflict`).
- Reroute khi kẹt quá lâu.
- **Guard** — chỉ hỗ trợ xử lý vi phạm đỗ sai loại/vị trí và escort xe về luồng hợp lệ; nếu xe đã được người dùng đưa về vị trí đỗ hợp lệ thì guard hủy nhiệm vụ cũ và quay về. Xe kẹt/nhường đường do traffic logic tự xử lý.

### Thống kê và log
- Sidebar thay phần status cũ bằng bảng **Algorithm Metrics** cho BFS/DFS/Greedy/A*: `Calls`, `Last`, `Avg`, `Best`, `Worst`, `KB`, `Len`.
- Overlay góc trái khi chọn xe: id, type, status, wait reason, vị trí, slot, độ dài path.
- Log sự kiện in ra **console** qua `Logger` (không có panel log trên màn hình game). Metrics thuật toán được lưu trong RAM đến khi tắt chương trình.

### Kiểm thử
- Unit test cho map manager, parking manager, pathfinding, traffic controller trong thư mục `tests/`.

---

## 6. Mô tả thuật toán

Tất cả thuật toán được triển khai trong `ai/pathfinding/`, gọi thống nhất qua `ai/pathfinding/router.py`. Mỗi thuật toán duyệt lưới 4 hướng, bỏ qua ô không đi được, slot đã reserve/occupied (trừ goal), và vị trí bị chặn động.

### BFS (Breadth-First Search)

| | |
|---|---|
| **Ý tưởng** | Duyệt lần lượt các lớp ô theo khoảng cách tăng dần từ điểm xuất phát. |
| **Áp dụng trong dự án** | Tìm đường ngắn nhất (theo số bước) từ vị trí xe đến slot hoặc cổng ra; dùng `deque` làm frontier. |
| **Ưu điểm** | Đảm bảo đường đi ngắn nhất trên lưới không trọng số; dễ hiểu, ổn định. |
| **Hạn chế** | Không hướng về đích — duyệt nhiều ô không cần thiết trên map lớn; chậm hơn Greedy/A* khi map rộng. |

### DFS (Depth-First Search)

| | |
|---|---|
| **Ý tưởng** | Đi sâu nhất có thể theo một nhánh trước khi quay lui. |
| **Áp dụng trong dự án** | Tìm *một* đường đi hợp lệ đến đích; dùng stack. |
| **Ưu điểm** | Bộ nhớ frontier thường nhỏ; triển khai gọn. |
| **Hạn chế** | Đường tìm được có thể dài và không tối ưu; thứ tự duyệt ảnh hưởng mạnh đến kết quả. |

### Greedy Best-First Search

| | |
|---|---|
| **Ý tưởng** | Luôn mở rộng ô có heuristic Manhattan nhỏ nhất so với đích. |
| **Áp dụng trong dự án** | Tìm đường nhanh bằng cách “nhìn về phía đích”; dùng `heapq` với priority = `h(n)`. |
| **Ưu điểm** | Nhanh, ít duyệt ô hơn BFS trên nhiều bản đồ. |
| **Hạn chế** | Không đảm bảo đường ngắn nhất; có thể đi vào ngõ cụt hoặc vòng lặp nếu có chướng ngại. |

### A* (A-star)

| | |
|---|---|
| **Ý tưởng** | Ưu tiên ô có `f(n) = g(n) + h(n)` — chi phí đã đi + ước lượng còn lại. |
| **Áp dụng trong dự án** | Thuật toán **mặc định** khi chạy mô phỏng; cân bằng tốc độ và chất lượng đường đi. |
| **Ưu điểm** | Với heuristic Manhattan trên lưới 4 hướng, thường cho đường tối ưu và hiệu quả. |
| **Hạn chế** | Phức tạp hơn BFS/DFS; vẫn phụ thuộc heuristic và tập `blocked_positions` cập nhật theo thời gian thực. |

---

## 7. Luồng hoạt động hệ thống

```text
┌─────────────┐     Play      ┌──────────────────┐
│  Main Menu  │ ────────────► │  Màn hình game   │
└─────────────┘               └────────┬─────────┘
       ▲                               │
       │ Main Menu                     │ Chọn thuật toán (sidebar / 1-4)
       │                               ▼
       │                      ┌──────────────────┐
       │                      │  Thiết lập xe    │
       │                      │  - Spawn C/M/T   │
       │                      │  - Place Vehicle │
       │                      │  - Traffic Jam   │
       │                      └────────┬─────────┘
       │                               │ Enter (nếu READY)
       │                               ▼
       │                      ┌──────────────────┐
       │                      │  RUNNING         │
       │                      │  Game loop 30 FPS│
       │                      └────────┬─────────┘
       │                               │
       └───────────────────────────────┘
                    Reset (R / sidebar)
```

### Chi tiết từng bước

1. **Mở chương trình** — `py -3.13 main.py` load map từ `data/map_layout.json`, khởi tạo Pygame và `GameController`.
2. **Start Menu** — hiển thị nền và nút Play / Exit; Enter hoặc Space cũng vào game.
3. **Vào màn hình mô phỏng** — render map, sidebar; trạng thái ban đầu `IDLE`.
4. **Chọn thuật toán** — BFS / DFS / Greedy / A*; thuật toán được dùng cho mọi lần tìm đường tiếp theo.
5. **Thêm / chọn xe**
   - Spawn nhanh: bấm Car/Motorbike trên sidebar hoặc phím `C`/`M` khi chưa bật `Place Vehicle` để sinh xe vào bãi từ cổng.
   - Đặt thủ công: bật `Place Vehicle` trên sidebar → chọn loại Car/Motorbike → chọn Entering/Exiting → click lên ô hợp lệ trên map.
   - Auto spawn: phím `T` sinh xe ngẫu nhiên (Car hoặc Motorbike) tại cổng vào mỗi 5 giây.
   - Traffic Jam: tạo 8 xe sẵn quanh ngã tư, trạng thái `READY`.
6. **Bắt đầu mô phỏng** — nhấn Enter khi trạng thái `READY`; xe Entering được gán slot và tìm đường, xe Exiting được gán lộ trình ra cổng.
7. **Tìm đường** — `ParkingManager.find_slot()` chọn slot; `find_path()` (router) tính path; slot được reserve.
8. **Xe di chuyển** — `VehicleManager` di chuyển từng ô mỗi `VEHICLE_MOVE_INTERVAL` (0.3s); `TrafficController` xử lý xung đột và ùn tắc.
9. **Cập nhật trạng thái** — xe chuyển `MOVING` → `ARRIVED` → `PARKED`; hoặc `WAITING` / `REROUTING` khi bị chặn; guard can thiệp khi vi phạm.
10. **Reset hoặc kịch bản khác** — Reset xóa toàn bộ; Traffic Jam hoặc Place Vehicle để thử tình huống mới; quay Main Menu khi cần.

---

## 8. Cấu trúc thư mục

```text
smart_parking_pygame/
|-- main.py                  # Điểm vào chương trình, load data/map_layout.json
|-- config.py                # Hằng số: kích thước, FPS, ngưỡng traffic, UI
|-- requirements.txt         # Dependency chính: pygame>=2.6.0
|-- README.md
|
|-- core/                    # Logic mô phỏng chính
|   |-- game_controller.py   # Điều phối spawn, path, manual, guard, scenario
|   |-- map_manager.py       # Load map .json/.txt, kiểm tra ô hợp lệ
|   |-- vehicle_manager.py   # Quản lý xe và di chuyển theo path
|   |-- parking_manager.py   # Gán slot, validate đỗ xe, occupy/release
|   |-- traffic_controller.py # Ùn tắc, xung đột, nhường đường, reroute
|   |-- pathfinding_metrics.py # Thống kê thời gian/bộ nhớ thuật toán
|   |-- scenario_manager.py  # Tạo kịch bản Traffic Jam
|   |-- vehicle_placement.py # Đặt xe thủ công lên map
|   `-- simulation_state.py  # Trạng thái mô phỏng và kế hoạch xe
|
|-- models/                  # Dataclass và enum
|   |-- enums.py             # CellType, VehicleType, VehicleStatus, AlgorithmType, WaitReason
|   |-- vehicle.py           # Model xe
|   |-- guard.py             # Model guard
|   |-- map_state.py         # Trạng thái bản đồ
|   `-- parking_slot.py      # Model ô đỗ
|
|-- ai/                      # Pathfinding và decision rules
|   |-- pathfinding/         # BFS, DFS, Greedy, A*, router, heuristic
|   `-- decision/            # Slot scoring và priority rule
|
|-- ui/                      # Giao diện Pygame
|   |-- pygame_app.py        # Vòng lặp game, scene Menu/Game
|   |-- main_menu.py         # Start menu
|   |-- renderer.py          # Vẽ map, xe, path, guard, overlay
|   |-- sidebar.py           # Panel điều khiển và Algorithm Metrics
|   |-- input_handler.py     # Bàn phím, chuột, sidebar actions
|   |-- hud_overlay.py       # Wrapper gọi draw_sidebar
|   |-- map_tile_renderer.py # Vẽ tile/decor
|   |-- sprite_loader.py     # Load/cache sprite Kenney, TopDown, retro
|   |-- view_transform.py    # Viewport và map pixel <-> screen
|   |-- ui_layout.py         # Kích thước cửa sổ tối thiểu
|   |-- button.py            # Nút UI tái sử dụng
|   `-- colors.py            # Bảng màu
|
|-- utils/                   # Grid utils, logger, debug
|-- data/                    # map_layout.json và default_map.txt
|-- assets/                  # Ảnh map, UI, Kenney sprites
|-- tests/                   # Unit tests
|-- tools/                   # map_annotator.py, map_layout_viewer.py
|-- retro-vechicle-sprites-64x64/ # Asset moto retro nguồn
`-- TopDown Vehicles v1.17/        # Asset xe top-down nguồn
```

### Loại ô trên bản đồ

| Ký hiệu | Ý nghĩa |
|---|---|
| `G` | Cổng vào/ra |
| `R` | Đường |
| `I` | Ngã tư |
| `X` | Chướng ngại vật |
| `B` | Block động (runtime) |
| `P` | Ô đỗ chung |
| `C` | Ô đỗ ô tô |
| `M` | Ô đỗ xe máy |

---

## 9. Hướng dẫn cài đặt và chạy

### Yêu cầu

- Python 3.11+ (khuyến nghị 3.13 nếu dùng Windows launcher `py`)
- pip

### Cài đặt

```bash
# Clone hoặc mở thư mục dự án
cd smart_parking_pygame

# (Tuỳ chọn) Tạo môi trường ảo
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
# source .venv/bin/activate

# Cài dependency
pip install -r requirements.txt
```

### Chạy game

```bash
py -3.13 main.py
```

Nếu interpreter mặc định đã cài Pygame, cũng có thể chạy:

```bash
python main.py
```

### Chạy công cụ gán map

Từ thư mục gốc dự án:

```bash
python tools/map_annotator.py
python tools/map_annotator.py --tile-size 64
```

Công cụ cho phép vẽ loại ô lên ảnh nền và lưu ra `data/map_layout.json` (phím `S`).

### Chạy công cụ xem map đã đánh dấu

```bash
python tools/map_layout_viewer.py
```

Công cụ này chỉ dùng để kiểm tra ảnh nền và các ô logic trong `data/map_layout.json`; không chạy mô phỏng.

### Chạy kiểm thử

```bash
python -m compileall -q .
python -m unittest discover -s tests
```

### Phím tắt trong game

| Phím / Thao tác | Chức năng |
|---|---|
| `Enter` / `Space` (menu) | Vào game |
| `Enter` (game, trạng thái READY) | Bắt đầu mô phỏng |
| `Enter` (xe manual) | Xác nhận đỗ xe |
| `1` / `2` / `3` / `4` | BFS / DFS / Greedy / A* |
| `C` / `M` | Chọn Car / Motorbike; nếu chưa ở Place Vehicle thì spawn xe vào bãi |
| `T` | Bật/tắt auto spawn tại cổng vào |
| `J` | Traffic Jam Mode |
| `R` | Reset mô phỏng |
| `N` | Next step (Step Mode) |
| `P` | Previous step (quay lại một bước trong Step Mode) |
| `F11` | Fullscreen |
| Click trái xe | Chọn xe, chuyển manual mode |
| Click phải xe | Cho xe rời bãi |
| `W/A/S/D` hoặc mũi tên | Di chuyển xe manual |
| `Esc` | Bỏ chọn xe |

Sidebar cung cấp thêm các nút tương ứng: chọn thuật toán, Place Vehicle, Reset, tốc độ, Step Mode, Main Menu.

---

## Giới hạn hiện tại

- Xe di chuyển theo từng ô (discrete step), chưa có animation nội suy mượt giữa các cell.
- Logic ùn tắc và reroute ở mức rule-based; guard không còn điều phối traffic mà chỉ xử lý vi phạm đỗ xe.
- Log chỉ hiển thị trên console, chưa có panel log trong UI game.
- Map mặc định 30×40; map text `default_map.txt` là 20×32 — kích thước phụ thuộc file được load.

## License assets

Sprite trong `assets/kenney_pixel_vehicle_pack/` thuộc **Kenney Pixel Vehicle Pack**, license **CC0**. Các asset `TopDown Vehicles v1.17` và `retro-vechicle-sprites-64x64` được dùng làm nguồn sprite xe/moto; cần giữ đúng license đi kèm asset nếu phân phối lại.
