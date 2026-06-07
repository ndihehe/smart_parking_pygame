# History - Smart Parking Pygame

File này ghi lại toàn bộ tiến trình chính của dự án đến thời điểm hiện tại.

## 1. Khởi tạo yêu cầu ban đầu

Dự án bắt đầu từ file đặc tả hệ thống bãi đỗ xe thông minh. Mục tiêu ban đầu không phải triển khai toàn bộ chức năng, mà là đọc đặc tả, tóm tắt mục tiêu, đề xuất cấu trúc Python + Pygame, phân tách rõ các nhóm `core logic`, `models`, `AI/pathfinding`, `traffic controller`, `UI`, `utils`, `data/maps`, `tests`, sau đó tạo skeleton class/function.

Yêu cầu quan trọng ban đầu:

- Không triển khai toàn bộ chức năng ngay.
- Không dùng Machine Learning, Deep Learning, Computer Vision.
- Không viết thuật toán trong UI.
- Chỉ tạo file khung và cấu trúc dễ mở rộng.

## 2. Tạo dự án Python + Pygame mới

Trong workspace đã tồn tại một thư mục Godot cũ tên `smart_parking_ai`. Người dùng yêu cầu bỏ qua thư mục đó và thiết kế một folder mới. Vì vậy dự án mới được tạo tại:

```text
smart_parking_pygame/
```

Ban đầu scaffold được tạo theo mô hình package `src/smart_parking`, sau đó người dùng yêu cầu đổi sang cấu trúc flat đúng đặc tả:

```text
smart_parking_pygame/
├── main.py
├── config.py
├── core/
├── models/
├── ai/
├── ui/
├── utils/
├── data/
└── tests/
```

Sau đó toàn bộ scaffold cũ trong `src/` được xóa và thay bằng cấu trúc mới.

## 3. Git repository

Repo local được tạo trong `d:\AI\smart_parking_pygame`.

Các bước đã làm:

- `git init`
- đổi branch mặc định sang `main`
- tạo `.gitignore`
- commit scaffold đầu tiên
- thêm remote GitHub:

```text
https://github.com/ndihehe/smart_parking_pygame.git
```

- push branch `main`

Commit đã có trước đó:

```text
a8930cd Initial smart parking pygame scaffold
cc8ca17 Restructure pygame project skeleton
```

## 4. Làm rõ vấn đề .env và .gitignore

Người dùng hỏi vì sao push cả `env`. Đã kiểm tra bằng `git ls-files` và xác nhận repo không track `env/`, `venv/`, `.venv/` hoặc `.env`.

`.gitignore` có rule:

```gitignore
.venv/
venv/
env/
.env
```

Giải thích đã được đưa ra: dòng `.env` trong `.gitignore` là rule bỏ qua file `.env`, không phải file `.env` bị push.

## 5. Chuẩn hóa models

Các file model đã được chỉnh theo spec chặt chẽ.

### `models/enums.py`

Đã định nghĩa đúng các enum:

- `CellType`
- `VehicleType`
- `VehicleStatus`
- `AlgorithmType`

Yêu cầu đã áp dụng:

- chỉ import `from enum import Enum`
- dùng `Enum`, không dùng `str, Enum`
- không thêm enum hoặc value ngoài spec

### `models/vehicle.py`

Đã tạo dataclass `Vehicle` với các field:

- `id`
- `type`
- `position`
- `assigned_slot`
- `path`
- `status`
- `wait_time`
- `priority_score`
- `direction`

Không thêm method/property.

### `models/parking_slot.py`

Đã tạo dataclass `ParkingSlot` với:

- `position`
- `slot_type`
- `is_occupied`
- `occupied_by`

Không có method thừa.

### `models/map_state.py`

Đã tạo dataclass `MapState` với:

- `grid`
- `rows`
- `cols`
- `gate_cells`
- `parking_slots`
- `static_obstacles`
- `dynamic_blocks`

## 6. Chuẩn hóa config

`config.py` được thay bằng constants đúng spec, gồm các nhóm:

- Map
- Simulation
- Traffic
- Scoring
- Priority
- UI

Các giá trị chính:

- `CELL_SIZE = 64`
- `MAP_ROWS = 8`
- `MAP_COLS = 12`
- `FPS = 30`
- `VEHICLE_MOVE_INTERVAL = 0.3`
- `AUTO_SPAWN_INTERVAL = 5.0`
- `SIDEBAR_WIDTH = 320`

Không có import, class, function hoặc constant ngoài spec.

## 7. Tạo map mặc định

File `data/maps/default_map.txt` được tạo theo map 8 dòng x 12 cột.

Map đáp ứng:

- có gate `G` trên border
- có road `R`
- có intersection `I`
- có obstacle `X`
- có car slot `C`
- có motorbike slot `M`
- không có block động `B` trong map ban đầu

Đã kiểm tra số dòng/cột và số lượng cell cơ bản.

## 8. Utils

### `utils/logger.py`

Đã tạo class `Logger` với `_logs` cấp class và các static methods:

- `log`
- `get_logs`
- `clear`

Log có format:

```text
[HH:MM:SS] {message}
```

Có giới hạn theo `LOG_MAX_LINES` và print ra stdout.

### `utils/grid_utils.py`

Đã tạo các hàm:

- `get_neighbors`
- `manhattan_distance`
- `is_within_bounds`
- `cell_to_pixel`

`get_neighbors` trả về tối đa 4 hướng theo thứ tự UP, DOWN, LEFT, RIGHT.

### `utils/debug.py`

Đã tạo:

- `DEBUG_MODE = False`
- `debug_print(message)`

Không có import, class hoặc function khác.

## 9. Map manager

`core/map_manager.py` được triển khai theo spec.

Chức năng hiện có:

- load map từ file text
- convert symbol sang `CellType`
- populate `gate_cells`
- populate `parking_slots`
- populate `static_obstacles`
- reset `dynamic_blocks`
- `get_state`
- `add_dynamic_block`
- `remove_dynamic_block`
- `is_passable`
- `_validate_connectivity` bằng DFS nội bộ

Đã smoke test load map mặc định thành công:

- 8 rows
- 12 cols
- 4 gates
- 20 parking slots

## 10. Vehicle manager

`core/vehicle_manager.py` được triển khai theo spec.

Chức năng hiện có:

- spawn vehicle
- remove vehicle
- get vehicle
- get all vehicles
- set status
- set path
- set manual
- update movement theo `VEHICLE_MOVE_INTERVAL`

Movement hiện tại là cell-by-cell, chưa có animation mượt.

## 11. Parking manager

`core/parking_manager.py` được triển khai theo spec.

Chức năng hiện có:

- tìm slot phù hợp theo `vehicle.type`
- bỏ qua slot occupied hoặc dynamic block
- score slot bằng distance + congestion penalty + obstacle penalty
- assign slot
- release slot
- validate parking

Các kết quả validate:

- `OK`
- `DIFFERENT_SLOT`
- `WRONG_TYPE`
- `ILLEGAL_ROAD`
- `BLOCKING_INTERSECTION`
- `UNKNOWN`

## 12. Pathfinding

Các file pathfinding đã được triển khai đúng chữ ký spec.

### `ai/pathfinding/heuristic.py`

Có một hàm:

- `manhattan`

### `ai/pathfinding/path_utils.py`

Có một hàm:

- `reconstruct_path`

Path trả về không gồm start, có gồm goal.

### `ai/pathfinding/bfs.py`

Có một hàm:

- `bfs(start, goal, map_manager)`

Dùng queue và `map_manager.is_passable`.

### `ai/pathfinding/dfs.py`

Có một hàm:

- `dfs(start, goal, map_manager)`

Dùng stack, không recursion.

### `ai/pathfinding/greedy.py`

Có một hàm:

- `greedy(start, goal, map_manager)`

Dùng priority queue theo Manhattan heuristic.

### `ai/pathfinding/astar.py`

Có một hàm:

- `astar(start, goal, map_manager)`

Dùng `f(n) = g(n) + h(n)` với Manhattan heuristic.

Đã smoke test pathfinding với `default_map.txt` thành công.

## 13. Decision logic

### `ai/decision/slot_scoring.py`

Đã tạo một hàm:

- `score_slot(vehicle, slot_position, map_state)`

Tính score bằng:

```text
distance + congestion_penalty + obstacle_penalty
```

### `ai/decision/priority_rule.py`

Đã tạo đúng hai hàm:

- `calculate_priority(vehicle, goal)`
- `resolve_conflict(vehicles, goal)`

Formula:

```text
vehicle.wait_time * WAIT_TIME_WEIGHT - distance_to_target + direction_bonus - vehicle.id * 0.001
```

## 14. Traffic controller

`core/traffic_controller.py` được triển khai theo spec.

Chức năng hiện có:

- track `_intersection_timers`
- trong `update`, kiểm tra xe waiting gần intersection
- detect congestion theo số xe chờ hoặc tổng thời gian chờ
- resolve conflict khi nhiều xe cùng target next cell
- `_handle_congestion` xử lý priority hoặc reroute
- `handle_obstacle` thêm dynamic block và reroute xe bị ảnh hưởng

Mức hiện tại là rule-based cơ bản, chưa phải mô phỏng giao thông hoàn chỉnh.

## 15. Game controller

`core/game_controller.py` được triển khai theo spec.

Chức năng hiện có:

- load map qua `MapManager`
- quản lý `VehicleManager`, `ParkingManager`, `TrafficController`
- auto spawn toggle
- spawn vehicle từ gate
- assign slot và tìm path bằng A*
- update simulation
- confirm parking
- manual mode
- manual movement
- reroute vehicle

Đã smoke test spawn xe từ map mặc định thành công.

## 16. UI

### `ui/colors.py`

Đã chuẩn hóa constants màu RGB đúng spec cho:

- cell types
- vehicle statuses
- path/grid/sidebar/text

### `ui/ui_layout.py`

Đã tạo layout constants tính từ config:

- `MAP_WIDTH`
- `MAP_HEIGHT`
- `WINDOW_WIDTH`
- `WINDOW_HEIGHT`
- sidebar/log area positions

### `ui/renderer.py`

Đã triển khai renderer:

- vẽ map theo `CellType`
- override dynamic block bằng màu `BLOCKED`
- vẽ vehicle theo `VehicleStatus`
- vẽ path
- vẽ sidebar
- vẽ stats
- vẽ logs

UI vẫn ở mức demo/basic test, chưa phải UI game 2D hoàn thiện.

### `ui/input_handler.py`

Đã triển khai input:

- `C`: spawn car
- `M`: spawn motorbike
- `A`: toggle auto spawn
- `ENTER`: confirm parking
- `ESC`: bỏ chọn
- click trái vào xe: chọn xe và set manual
- manual movement bằng WASD hoặc arrow keys

### `ui/pygame_app.py`

Đã triển khai vòng lặp Pygame:

- init pygame
- tạo window
- tạo `GameController`
- xử lý input
- update logic
- render frame
- quit pygame

## 17. Main entrypoint

`main.py` đã được cập nhật tối giản:

```python
import os

from ui.pygame_app import PygameApp


if __name__ == "__main__":
    map_path = os.path.join("data", "maps", "default_map.txt")
    app = PygameApp(map_path)
    app.run()
```

Không có argparse, không override config.

## 18. Runtime test

Người dùng yêu cầu chạy app và chỉ sửa runtime errors.

Khi chạy:

```bash
python main.py
```

lỗi môi trường xuất hiện:

```text
ModuleNotFoundError: No module named 'pygame'
```

Nguyên nhân: lệnh `python` trong PowerShell đang trỏ tới MSYS Python:

```text
C:\msys64\mingw64\bin\python.exe
```

Interpreter này chưa có `pygame`.

Đã kiểm tra Python 3.13 bằng launcher `py` và thấy `pygame` có sẵn. Chạy bằng:

```bash
py -3.13 main.py
```

app mở được và không có exception.

Đã chạy smoke test headless với `SDL_VIDEODRIVER=dummy`, giả lập phím `C` và `M`. Kết quả:

- spawn được 1 CAR
- spawn được 1 MOTORBIKE
- cả hai được assign slot
- path được tìm bằng A*
- xe di chuyển theo path
- render frame không crash

## 19. Đánh giá trạng thái hiện tại

Logic hiện tại đủ cho demo cơ bản:

```text
load map -> spawn vehicle -> find slot -> find path -> move vehicle -> render UI
```

Chưa thể gọi là hoàn chỉnh vì còn các giới hạn:

- traffic/congestion logic còn đơn giản
- collision/occupancy giữa nhiều xe chưa được siết đầy đủ
- UI mới ở mức test/demo
- chưa có sprite/tilemap 2D
- chưa có animation mượt
- tests vẫn cần viết thực chất

## 20. Hướng phát triển tiếp theo đã thảo luận

Nếu muốn nâng lên mức game basic:

1. highlight selected vehicle và assigned slot
2. thêm sidebar chi tiết xe
3. thêm legend màu
4. thêm reset/pause controls
5. thêm smooth movement
6. thêm visual warning cho violation/congestion

Nếu muốn nâng đồ họa 2D:

- thêm `assets/tiles/`
- thêm `assets/vehicles/`
- tạo asset loader
- render map bằng sprite thay vì rect màu
- render xe bằng sprite top-down
- thêm selection outline, warning pulse, path effect
- giữ toàn bộ logic grid trong core, không đưa thuật toán vào UI

## 21. Cập nhật chống xe đi xuyên và mở rộng map

Người dùng phát hiện hai vấn đề khi chạy demo:

- Xe đã vào ô đậu nhưng xe khác vẫn có thể chạy xuyên qua ô đó.
- Khi click chọn một xe để điều khiển manual trên đường, xe khác vẫn có thể chạy xuyên qua xe đang được chọn nếu xe đó chưa xác nhận đỗ bằng `ENTER`.
- Bãi đỗ 8x12 quá nhỏ để mô phỏng.

Các thay đổi đã thực hiện:

- `core/vehicle_manager.py`: khi xe `MOVING` chuẩn bị bước sang ô kế tiếp, hệ thống kiểm tra thêm các ô đang bị xe khác chiếm. Nếu ô kế tiếp có xe khác hoặc là slot đã bị xe khác giữ, xe không được đi xuyên qua.
- `core/game_controller.py`: manual movement cũng kiểm tra ô đang có xe khác hoặc slot bị xe khác giữ. Nếu không hợp lệ, xe không di chuyển và ghi log.
- `core/game_controller.py`: spawn xe không còn đè lên gate đang có xe. Nếu gate được chọn đang bị chiếm, hệ thống tìm gate trống khác; nếu không còn gate trống thì log `No gate available`.
- `config.py`: mở rộng map từ 8x12 lên 12x18.
- `data/maps/default_map.txt`: thay bằng map 12 dòng x 18 cột, có nhiều road, intersection, car slot và motorbike slot hơn.

Đã smoke test:

- tạo một xe đang đi;
- đặt một xe khác ở ô kế tiếp và chuyển sang manual;
- update simulation;
- xe đang đi không xuyên qua xe manual mà bị block/reroute.

## 22. Cập nhật hiển thị dễ nhìn hơn và fullscreen

Người dùng yêu cầu giảm kích thước ô để map rộng dễ quan sát hơn và cho phép fullscreen.

Các thay đổi đã thực hiện:

- `config.py`: giảm `CELL_SIZE` từ `64` xuống `48`, giúp map 12x18 hiển thị gọn hơn trong cửa sổ.
- `ui/pygame_app.py`: thêm trạng thái fullscreen và phím `F11` để bật/tắt fullscreen.
- Khi chuyển fullscreen/windowed, `Renderer` được cập nhật lại `screen` hiện tại để tiếp tục render đúng surface.
- `README.md`: cập nhật điều khiển `F11` và mô tả trạng thái UI mới.
