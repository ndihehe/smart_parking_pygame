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

## 23. Sửa slot lifecycle, reroute, collision, UI debug và map 20x32

Người dùng yêu cầu sửa các lỗi logic chính trước khi phát triển tiếp:

- xe sau bị kẹt khi xe manual đỗ sai tạo dynamic block;
- slot cần tách reserved và occupied;
- A* cần tránh xe đang đứng;
- WAITING/REROUTING cần có wait_reason;
- traffic cần xét occupied positions;
- phím A bị trùng auto spawn và move left;
- UI cần debug rõ hơn;
- map cần mở rộng 20x32, CELL_SIZE 32;
- thêm smoke tests.

Các thay đổi đã thực hiện:

- `models/parking_slot.py`: thêm `is_reserved`, `reserved_by`, giữ `is_occupied`, `occupied_by`.
- `models/vehicle.py`: thêm `wait_reason`.
- `models/enums.py`: thêm `VehicleStatus.ARRIVED` để phân biệt xe AI vừa tới slot trước khi chuyển PARKED.
- `core/parking_manager.py`: `assign_slot` giờ chỉ reserve; thêm release theo vehicle và occupy khi xe đỗ thật.
- `core/vehicle_manager.py`: xe không đi vào ô có xe khác, không đi vào slot reserved/occupied bởi xe khác; khi hết path chuyển `ARRIVED`.
- `ai/pathfinding/astar.py`: nhận `blocked_positions` và tránh vị trí xe khác; cũng tránh slot reserved/occupied nếu không phải goal.
- `core/game_controller.py`: retry xe WAITING theo `wait_reason`, reroute fail thì release slot cũ, tìm slot mới, assign lại và tìm path mới; manual override release reservation; violation release reservation và tạo dynamic block.
- `core/traffic_controller.py`: xét occupied positions khi kiểm tra blocked direction, set wait_reason `YIELDING`, reroute bằng A* có blocked positions.
- `ui/input_handler.py`: đổi auto spawn từ `A` sang `T`; `A` chỉ còn move left trong manual.
- `ui/renderer.py`: hiển thị nhãn G/I/X/B/P-C/P-M, vẽ CAR/MOTO khác nhau, label C/M theo id, highlight selected vehicle, highlight assigned slot, sidebar hiển thị id/type/status/wait_reason/position/assigned_slot/path length.
- `config.py`: `CELL_SIZE = 32`, `MAP_ROWS = 20`, `MAP_COLS = 32`.
- `data/maps/default_map.txt`: cập nhật map 20x32 với nhiều road/intersection/slot/obstacle/gate hơn.
- `tests/`: thêm smoke tests cho map load, đúng loại slot, release slot cũ, A* tránh xe, không đi xuyên xe, manual đỗ sai tạo block, reroute fail tìm slot khác, phím `T` toggle auto spawn.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 8 tests OK.

## 24. Layout slot theo dãy và guard xử lý đỗ sai loại

Người dùng đề xuất đổi map thành 2 dãy liên tiếp cho ô tô và 2 dãy liên tiếp cho xe máy, mỗi dãy có 20 vị trí đỗ. Người dùng cũng yêu cầu khi xe đỗ sai vị trí, ví dụ xe máy đỗ vào ô ô tô, hệ thống log lỗi và có một entity bảo vệ đi từ góc tới xe đó để đưa xe về vị trí đúng.

Các thay đổi đã thực hiện:

- `data/maps/default_map.txt`: đổi layout map 20x32 thành 2 dãy `C` liên tiếp, mỗi dãy 20 slot, và 2 dãy `M` liên tiếp, mỗi dãy 20 slot.
- `models/guard.py`: thêm dataclass `Guard` để biểu diễn entity bảo vệ.
- `core/game_controller.py`: thêm `self.guard`, guard timer, dispatch guard khi confirm parking sai loại/sai vị trí.
- Khi `confirm_parking()` trả `WRONG_TYPE`, xe được log vi phạm, guard được dispatch tới xe, sau đó xe được assign lại slot đúng loại và tìm path mới.
- Với `ILLEGAL_ROAD` hoặc `BLOCKING_INTERSECTION`, vị trí vẫn được thêm vào `dynamic_blocks`, guard tới xe rồi giải phóng block và đưa xe đi tìm slot đúng.
- `ai/pathfinding/astar.py`: cho phép guard đi tới goal đang bị dynamic block để tiếp cận xe vi phạm.
- `ui/renderer.py`: vẽ guard bằng entity `SEC` và tiếp tục hiển thị debug map/vehicle.
- `tests/test_map_manager.py`: kiểm tra đúng 2 dãy C và 2 dãy M, mỗi dãy 20 slot.
- `tests/test_traffic_controller.py`: thêm test motorbike đỗ sai vào car slot, guard dispatch và xe được assign lại về motorbike slot.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 10 tests OK.

## 25. Nhiều guard, guard quay về buồng và guard điều phối giao thông

Người dùng bổ sung yêu cầu:

- Sau khi đưa xe về đúng vị trí, entity bảo vệ phải quay về buồng/gate của mình.
- Nếu có nhiều hơn một xe đỗ sai cùng lúc thì phải có nhiều hơn một guard ra hỗ trợ.
- Trên tuyến đường không được xảy ra va chạm; nếu nhiều xe tranh đường thì xe có thể nhường đường.
- Nếu tắc nghẽn thì phải phân tích xe nào được đi trước, và việc điều phối này do guard đảm nhiệm.

Các thay đổi đã thực hiện:

- `models/guard.py`: mở rộng guard với `id`, `task`, `target_position`, `move_timer`.
- `core/game_controller.py`: thay guard đơn thành danh sách `self.guards`.
- Khi có nhiều vi phạm cùng lúc, hệ thống dùng guard đang `IDLE`; nếu không có guard rảnh thì tạo guard mới từ buồng/gate đầu tiên.
- Guard xử lý vi phạm xong sẽ chuyển sang task `RETURNING` và đi theo A* về `home_position`. Khi về tới nơi, guard chuyển `IDLE`.
- `core/traffic_controller.py`: nhận danh sách guards; khi nhiều xe muốn vào cùng một ô, hệ thống chọn xe ưu tiên, xe còn lại `WAITING/YIELDING`, và dispatch guard rảnh tới vị trí đó để điều phối.
- Khi congestion kéo dài, guard cũng được dispatch tới intersection/tắc nghẽn để điều phối.
- `ui/renderer.py`: vẽ nhiều guard bằng nhãn `S{id}` thay vì một `SEC` duy nhất.
- `ui/pygame_app.py`: truyền `self.gc.guards` cho renderer.
- `tests/test_traffic_controller.py`: thêm test nhiều xe sai loại cùng lúc tạo nhiều guard; thêm test conflict cùng target cell dispatch guard và xe thua nhường đường.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 12 tests OK.

## 26. Sửa xe WAITING bị kẹt và xử lý slot bị mất

Người dùng báo xe bị đứng ngoài ở trạng thái cam `WAITING` khi slot muốn vào bị mất/chiếm, kể cả sau khi guard xuống hỗ trợ.

Các thay đổi đã thực hiện:

- `core/game_controller.py`: thêm recover cho xe `WAITING` với các reason `YIELDING`, `GUARD_ESCORT`, `NO_SLOT`, `NO_PATH`, `BLOCKED_BY_VEHICLE`, `CONGESTION`.
- Nếu xe đang reroute nhưng slot cũ đã bị chiếm/reserved bởi xe khác, hệ thống release slot cũ, tìm slot phù hợp khác và tạo path mới.
- Xe đang `YIELDING` sẽ chạy lại khi ô kế tiếp đã trống, thay vì đứng chờ vĩnh viễn.
- `core/vehicle_manager.py` và `core/traffic_controller.py`: reset `wait_time`/`wait_reason` khi xe được phép chạy lại.
- `tests/test_traffic_controller.py`: thêm test xe `YIELDING` resume và test slot assigned không còn available thì đổi slot.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 14 tests OK.

## 27. Kiểm tra đầy bãi, cổng vào trái và cổng ra phải

Người dùng bổ sung yêu cầu:

- Khi toàn bộ slot của một loại xe đã đầy/reserved, không spawn thêm xe loại đó và ghi log.
- Hướng vào bãi dùng 2 cổng bên trái.
- Hướng ra khỏi bãi dùng 2 cổng bên phải.
- Click chuột trái vào xe bất kỳ sẽ chuyển xe sang lộ trình rời bãi.

Các thay đổi đã thực hiện:

- `core/game_controller.py`: kiểm tra slot trống theo `VehicleType` trước khi spawn; nếu đầy thì log `car lot full` hoặc `motorbike lot full` và không tạo xe.
- `core/game_controller.py`: spawn chỉ chọn 2 gate ở cột trái; xe rời bãi chọn gate khả dụng gần nhất ở cột phải.
- `core/game_controller.py`: thêm luồng `start_exit`, release slot đang giữ, tìm path đến cổng phải, và remove xe khỏi simulation khi tới cổng ra.
- `core/vehicle_manager.py`: giữ `wait_reason="EXITING"` khi xe tới đích để `GameController` biết đây là xe rời bãi, không phải xe vừa tới slot đỗ.
- `ui/input_handler.py`: click chuột trái vào xe gọi `start_exit` thay vì chuyển sang manual mode.
- `README.md`: cập nhật lại phần điều khiển và mô tả cổng vào/cổng ra.
- `tests/test_traffic_controller.py`: thêm test đầy bãi không spawn, spawn chỉ ở cổng trái, click xe đi cổng phải, và xe được remove khi tới cổng ra.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 18 tests OK.

## 28. Sửa input chuột và giảm reroute loop khi xe chắn nhau

Người dùng báo:

- Click chuột trái trước đó bị đổi thành xe rời bãi, nhưng chức năng đúng là chuyển xe sang manual mode.
- Xe rời bãi nên dùng chuột phải.
- Có trường hợp 2 xe còn 2 slot trống nhưng liên tục chắn/va chạm nhau và không tới được vị trí đỗ.

Các thay đổi đã thực hiện:

- `ui/input_handler.py`: click trái vào xe chuyển sang manual mode; click phải vào xe mới gọi luồng rời bãi `start_exit`.
- `core/game_controller.py`: chuyển thứ tự update để `TrafficController` phân xử tranh chấp trước khi `VehicleManager` cho xe bước sang cell tiếp theo.
- `core/vehicle_manager.py`: nếu ô tiếp theo bị xe khác chiếm thì xe chuyển `WAITING/YIELDING` và giữ nguyên path, thay vì chuyển `REROUTING` liên tục.
- `core/vehicle_manager.py`: vẫn giữ `REROUTING` cho block thật như dynamic block, static obstacle hoặc slot không khả dụng.
- `README.md`: cập nhật lại điều khiển chuột trái/chuột phải.
- `tests/test_traffic_controller.py`: thêm test click trái manual, click phải exit, và xe bị xe khác chắn thì yield thay vì reroute loop.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 20 tests OK.

## 29. Rà soát ổn định và vá YIELDING reroute sớm

Người dùng yêu cầu rà soát lại chương trình để kiểm tra độ ổn định và bug tiềm ẩn.

Các kiểm tra đã thực hiện:

- Chạy compile toàn bộ project.
- Chạy toàn bộ unit tests.
- Chạy smoke simulation bằng `GameController` với spawn, update nhiều tick và cho xe rời bãi.
- Chạy Pygame render smoke bằng `SDL_VIDEODRIVER=dummy` để kiểm tra khởi tạo app/renderer không crash.
- Kiểm tra map `default_map.txt`: 20 hàng, mỗi hàng 32 cột, có 40 slot ô tô, 40 slot xe máy, 2 gate trái và 2 gate phải.

Bug tiềm ẩn đã phát hiện và sửa:

- Xe `YIELDING` vẫn có thể bị reroute sau `VEHICLE_MOVE_INTERVAL` nếu ô trước mặt còn xe khác chắn.
- Đã sửa `core/game_controller.py` để xe `YIELDING` tiếp tục chờ khi chưa quá `REROUTE_WAIT_THRESHOLD`; chỉ chạy lại khi ô kế tiếp trống hoặc reroute khi chờ quá lâu.
- `tests/test_traffic_controller.py`: thêm test đảm bảo `GameController.update()` không biến xe `YIELDING` thành reroute loop quá sớm.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 21 tests OK.

## 30. Tối ưu hiệu suất hệ thống

Người dùng yêu cầu triển khai các phần cần thiết để tối ưu hiệu suất hệ thống.

Các thay đổi đã thực hiện:

- `models/map_state.py`: thêm cache tĩnh cho `intersection_cells`, `intersection_neighbors`, `entry_gates`, `exit_gates`, `car_slots`, `motorbike_slots`.
- `core/map_manager.py`: build các cache này một lần khi load map.
- `core/traffic_controller.py`: bỏ scan toàn bộ grid mỗi frame để tìm intersection; dùng cache từ `MapState`.
- `core/traffic_controller.py`: tạo index `waiting_by_position` một lần mỗi frame thay vì mỗi intersection quét toàn bộ danh sách xe.
- `core/parking_manager.py`: chỉ duyệt danh sách slot đúng loại xe khi tìm slot.
- `core/game_controller.py`: dùng cache gate vào/ra và slot theo loại khi spawn/exit/capacity check.
- `ui/renderer.py`: cache map tĩnh thành `pygame.Surface`; mỗi frame chỉ overlay dynamic blocks, path, vehicles, guards và sidebar.
- `tests/test_map_manager.py`: thêm test xác nhận static indexes được tạo đúng.
- `README.md`: thêm mục mô tả tối ưu hiệu suất hiện tại.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 22 tests OK.

Đã chạy thêm smoke checks:

- Pygame render smoke với `SDL_VIDEODRIVER=dummy`: OK.
- Simulation smoke 500 ticks: OK.

## 31. Pathfinding router và chọn thuật toán runtime

Người dùng yêu cầu triển khai phase AI tiếp theo:

- Chuẩn hóa API cho BFS, DFS, Greedy Best First Search và A*.
- Tạo pathfinding router/facade.
- Cho phép chọn thuật toán runtime mà không sửa UI trong phase này.
- Thêm test tối thiểu cho 4 thuật toán, blocked positions và algorithm không hợp lệ.

Các thay đổi đã thực hiện:

- `ai/pathfinding/bfs.py`: thêm `blocked_positions` và kiểm tra slot reserved/occupied giống A*.
- `ai/pathfinding/dfs.py`: thêm `blocked_positions` và kiểm tra slot reserved/occupied giống A*.
- `ai/pathfinding/greedy.py`: thêm `blocked_positions` và kiểm tra slot reserved/occupied giống A*.
- `ai/pathfinding/router.py`: thêm `find_path()` facade và validate algorithm name.
- `core/game_controller.py`: thay direct `astar()` bằng `find_path()`; thêm `current_algorithm`, constructor param `algorithm`, và `set_pathfinding_algorithm()`.
- `core/traffic_controller.py`: thay direct `astar()` bằng `find_path()` cho congestion reroute, obstacle reroute và guard traffic path.
- `tests/test_pathfinding.py`: thêm test BFS/DFS/Greedy/A*, blocked positions, invalid algorithm và runtime algorithm trong `GameController`.
- `README.md`: cập nhật mô tả pathfinding runtime.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 29 tests OK.

## 32. UI chọn thuật toán runtime

Người dùng yêu cầu tiếp tục phase UI chọn thuật toán runtime:

- Phím `1`: BFS.
- Phím `2`: DFS.
- Phím `3`: Greedy Best First Search.
- Phím `4`: A*.
- Sidebar hiển thị thuật toán đang chọn.
- Không sửa logic BFS/DFS/Greedy/A*.

Các thay đổi đã thực hiện:

- `ui/input_handler.py`: thêm xử lý phím `1/2/3/4`, gọi `GameController.set_pathfinding_algorithm()`.
- `ui/renderer.py`: thêm hiển thị `Current Algorithm: ...` trong sidebar.
- `ui/pygame_app.py`: truyền `self.gc.current_algorithm` vào renderer.
- `tests/test_traffic_controller.py`: thêm test phím `1/2/3/4` đổi thuật toán runtime đúng.
- `README.md`: cập nhật phần điều khiển và pathfinding runtime.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 30 tests OK.

## 33. Chuẩn hóa nghiệp vụ xác nhận đỗ xe

Người dùng yêu cầu manual parking và auto parking đều phải đi qua cùng một hàm `validate_parking()`.

Các thay đổi đã thực hiện:

- `core/parking_manager.py`: bổ sung log cho mọi kết quả validate, gồm `OK`, `DIFFERENT_SLOT`, `WRONG_TYPE`, `ILLEGAL_ROAD`, `BLOCKING_INTERSECTION`, `UNKNOWN`.
- `core/game_controller.py`: thêm helper `_validate_and_apply_parking()` để xử lý chung kết quả validate.
- `core/game_controller.py`: `confirm_parking()` của manual mode gọi helper chung.
- `core/game_controller.py`: nhánh auto `ARRIVED` cũng gọi helper chung, không tự occupy slot trực tiếp nữa.
- `tests/test_parking_manager.py`: thêm test validate đúng assigned slot, khác slot hợp lệ, road, intersection, wrong type và auto arrived dùng validate.
- `README.md`: cập nhật slot lifecycle/parking validation.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 34 tests OK.

## 34. Enum hóa wait_reason

Người dùng yêu cầu thay các `wait_reason` dạng string bằng enum, không sửa pathfinding router và không sửa `validate_parking()`.

Các thay đổi đã thực hiện:

- `models/enums.py`: thêm `WaitReason` enum cho các lý do chờ/block/congestion/exit/violation.
- `models/vehicle.py`: đổi `wait_reason` từ `str | None` sang `WaitReason`, mặc định `WaitReason.NONE`.
- `core/vehicle_manager.py`, `core/game_controller.py`, `core/traffic_controller.py`: thay gán/so sánh string bằng `WaitReason`.
- `core/traffic_controller.py`: gán `WAITING_FOR_INTERSECTION` và `TRAFFIC_CONGESTION` bằng enum khi phát hiện xe chờ/nghẽn tại giao lộ.
- `ui/renderer.py`: sidebar vẫn hiển thị reason dạng text dễ đọc qua `.value`.
- `tests/test_traffic_controller.py`: cập nhật assertion theo `WaitReason`.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 34 tests OK. Render smoke headless cũng OK.

## 35. Rà soát và wire dead code có chọn lọc

Người dùng yêu cầu rà soát `SimulationState`, `slot_scoring`, `WAIT_THRESHOLD`, `vehicle.direction` và chỉ wire tối thiểu các phần phục vụ demo.

Phân loại:

- `SimulationState`: chưa được wire vào runtime; giữ lại cho phase sau nếu cần gom state app/simulation, chưa xóa để tránh refactor lớn.
- `slot_scoring`: nên dùng; đã wire `ParkingManager.find_slot()` gọi `score_slot()` thay vì duplicate công thức scoring.
- `WAIT_THRESHOLD`: nên dùng; đã wire vào `TrafficController` để xe chờ tại giao lộ quá ngưỡng được đánh dấu congestion.
- `vehicle.direction`: nên dùng; đã cập nhật khi xe di chuyển theo path để priority rule có dữ liệu `STRAIGHT`/`TURN`.

Không xóa file/code nào trong phase này.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 36 tests OK. Render smoke headless OK.

## 38. Guard walk animation

Người dùng yêu cầu tận dụng các mô hình di chuyển của người trong asset pack để guard không còn là ảnh tĩnh.

Các thay đổi đã thực hiện:

- Copy thêm `man_walk2.png` và `man_point.png` vào `assets/kenney_pixel_vehicle_pack/characters/`.
- `ui/sprite_loader.py`: load thêm `guard_walk2` và `guard_point`.
- `ui/renderer.py`: guard có animation theo frame `guard -> guard_walk -> guard_walk2 -> guard_walk` khi đang có path.
- `ui/renderer.py`: guard traffic dùng frame point; guard đang đi được flip/rotate theo hướng path.
- Không đổi logic guard, pathfinding, traffic hoặc map.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 36 tests OK. Guard animation smoke headless OK.

## 39. Vehicle sprite variants

Người dùng chỉ ra rằng asset đã đưa vào nhiều loại xe nhưng spawn vẫn nhìn như một loại duy nhất.

Các thay đổi đã thực hiện:

- `ui/renderer.py`: thêm `_get_vehicle_sprite_key()` để chọn sprite theo `vehicle.id`.
- CAR luân phiên giữa `car` và `car_alt`.
- MOTORBIKE luân phiên giữa `motorbike` và `motorbike_alt`.
- Không đổi model/core spawn logic; chỉ đổi cách render để entity nhìn đa dạng hơn.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 36 tests OK. Vehicle variant smoke headless OK.

## 40. Fix exit reroute và xe kẹt ở cổng ra

Người dùng báo lỗi xe đang ra về bị xe khác chặn thì đứng im dù còn đường rẽ, và có trường hợp xe nằm yên ở cổng ra làm chắn lối về.

Nguyên nhân:

- Xe đang `EXITING` khi bị block bởi xe khác bị ghi đè `wait_reason` thành `YIELDING`.
- Khi recovery, hệ thống xử lý nó như xe đi tìm slot đỗ thay vì xe đang ra cổng.
- Nếu xe ở đúng exit gate nhưng status không phải `ARRIVED`, nó có thể chưa được remove.

Các thay đổi đã thực hiện:

- `core/vehicle_manager.py`: nếu xe đang `WaitReason.EXITING` bị block, giữ nguyên `EXITING` intent.
- `core/game_controller.py`: thêm recovery riêng cho xe `EXITING` đang `WAITING`.
- `core/game_controller.py`: xe `EXITING` bị `REROUTING` sẽ tìm lại path tới exit gate, không quay lại flow tìm slot.
- `core/game_controller.py`: xe `EXITING` đã nằm trên exit gate sẽ được remove khỏi simulation kể cả khi status đang `WAITING`.
- `tests/test_traffic_controller.py`: thêm test xe ra về reroute quanh xe chặn.
- `tests/test_traffic_controller.py`: thêm test xe ra về nằm ở exit gate được remove.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 38 tests OK. Exit reroute smoke headless OK.

## 41. Map visual upgrade pseudo-3D

Người dùng yêu cầu nâng cấp đồ họa map theo hướng đẹp hơn, dễ nhìn hơn, có cảm giác 2.5D nhẹ nhưng không thay đổi logic grid/pathfinding/business.

Phân tích trước khi sửa:

- `ui/renderer.py` đang vẽ map bằng màu phẳng, obstacle là ô đen/chữ `X`.
- Kenney pack có prop phù hợp cho obstacle/decor: `barrier`, `light`, `light_double`, `sign_red`, `sign_blue`.
- Pack chưa có cây/túi rác rõ ràng, nên cây cảnh/thùng rác được vẽ procedural bằng pygame trong đúng 1 tile.

Các thay đổi đã thực hiện:

- Copy thêm prop asset vào `assets/kenney_pixel_vehicle_pack/props/`.
- `ui/sprite_loader.py`: load thêm prop sprites `barrier`, `light`, `light_double`, `sign_red`, `sign_blue`.
- `ui/map_tile_renderer.py`: thêm renderer riêng cho tile/decor, chỉ phục vụ hiển thị.
- `ui/renderer.py`: delegate vẽ map tile sang `MapTileRenderer`, giữ nguyên logic entity/sidebar.
- ROAD, INTERSECTION, PARKING SLOT, GATE, OBSTACLE được vẽ rõ hơn bằng pseudo-3D/shadow/outline nhẹ.
- OBSTACLE vẫn là cell obstacle trong logic, nhưng hiển thị luân phiên bằng barrier/sign/light/chậu cây/thùng rác.

Không thay đổi:

- Không sửa map grid logic.
- Không sửa BFS/DFS/Greedy/A*.
- Không sửa pathfinding router.
- Không sửa validate parking, traffic handling hoặc vehicle state.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 38 tests OK. Map visual smoke headless OK.

## 37. Gate sprite

Người dùng hỏi có thể dùng asset gateway cho các cổng không.

Các thay đổi đã thực hiện:

- Copy `PNG/Props/highway.png` từ Kenney Pixel Vehicle Pack thành `assets/kenney_pixel_vehicle_pack/props/gate.png`.
- `ui/sprite_loader.py`: thêm key sprite `gate`.
- `ui/renderer.py`: render sprite gate lên các cell `CellType.GATE`; nếu asset lỗi thì fallback về chữ `G`.
- Không đổi logic map, pathfinding, traffic hoặc layout.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 36 tests OK. Render smoke headless OK.

## 36. UI entity sprites

Người dùng yêu cầu chỉ update UI cho entity trước, chưa làm map và giao diện tổng thể.

Các thay đổi đã thực hiện:

- Thêm asset folder tách biệt `assets/kenney_pixel_vehicle_pack/`.
- Copy các sprite entity cần dùng từ Kenney Pixel Vehicle Pack: car, motorbike, guard và license CC0.
- `ui/sprite_loader.py`: thêm loader nhỏ để load/scale sprite theo `CELL_SIZE`.
- `ui/renderer.py`: vẽ vehicle và guard bằng sprite, giữ fallback shape nếu asset load lỗi.
- `ui/renderer.py`: giữ map/sidebar/layout hiện tại; chỉ đổi phần entity.

Đã chạy:

```bash
py -3.13 -m compileall -q .
py -3.13 -m unittest discover -s tests
```

Kết quả: 36 tests OK. Render smoke headless OK.

## 42. Sửa bug moto tandem, cập nhật guard, metrics thuật toán và dọn code thừa

Người dùng báo nhiều lỗi nghiệp vụ sau khi bổ sung asset xe mới và mô phỏng xe máy đỗ hai hàng:

- Hai xe máy đỗ dạng trong/ngoài, xe bên trong không rời bãi được.
- Xe đã đỗ có thể bị gán lại slot khi xe mới spawn.
- Click chọn Car/Motorbike chưa cập nhật UI hoặc spawn đúng theo trạng thái place mode.
- Guard không nên đi điều phối kẹt xe; xe tự nhường đường và reroute theo traffic logic.
- Bảng `Status` cũ không hữu ích, cần thay bằng bảng so sánh metrics thuật toán.
- UI metrics bị tràn cột, cần chỉnh layout rõ ràng hơn.
- Dự án còn import/code thừa sau nhiều vòng sửa.

Các thay đổi đã thực hiện:

- `core/game_controller.py`: sửa luồng moto tandem. Xe ngoài tạm né sang ô hợp lệ, xe trong được ưu tiên thoát, slot trong được giữ cho xe ngoài quay vào, không reserve nhầm ô ngoài làm chặn đường thoát.
- `core/game_controller.py`, `core/traffic_controller.py`, `ai/decision/priority_rule.py`: giữ intent `EXITING`, ưu tiên xe đang rời bãi khi có xung đột, không để xe ra về bị gán lại slot.
- `core/parking_manager.py`, `core/game_controller.py`: không route lại xe đã `PARKED` hoặc đã có slot hợp lệ; xe mới chỉ được assign slot còn khả dụng.
- `ui/input_handler.py`, `core/game_controller.py`: tách chọn loại xe khỏi place mode. Click Car/Motorbike cập nhật UI ngay; ngoài place mode vẫn spawn xe.
- `core/traffic_controller.py`, `core/game_controller.py`, `ui/renderer.py`: bỏ luồng guard điều phối traffic. Guard chỉ còn xử lý xe vi phạm đỗ sai loại/vị trí; kẹt xe dùng priority/yield/reroute.
- `models/guard.py`, `core/game_controller.py`, `ui/renderer.py`: guard lưu `is_walking` và `facing_delta` để animation đi bộ không bị rơi về frame đứng khi path vừa hết.
- `core/pathfinding_metrics.py`: thêm metrics session cho BFS/DFS/Greedy/A*: số lần gọi, thời gian gần nhất, trung bình, nhanh nhất, chậm nhất, bộ nhớ KB và độ dài path.
- `ai/pathfinding/router.py`: bọc `find_path()` bằng đo thời gian/bộ nhớ bằng `perf_counter()` và `tracemalloc`.
- `ui/sidebar.py`, `ui/hud_overlay.py`, `ui/renderer.py`: thay bảng status bằng `Algorithm Metrics`, căn lại cột để không tràn khung.
- `ui/sprite_loader.py`, `ui/renderer.py`: dùng nhiều sprite xe TopDown/retro hơn và chọn frame theo hướng di chuyển để xe nhìn đa dạng hơn.
- `.gitignore`: ignore `assets/generated/sprite_cache/`; xóa `__pycache__` local.
- Dọn import thừa, `ParkingManager.__init__()` rỗng, metric `failures/reset` không còn dùng và code traffic guard dead path.

Đã chạy:

```bash
python -m py_compile <toàn bộ file .py>
python -m unittest tests.test_exit_intent tests.test_parking_manager tests.test_pathfinding tests.test_map_manager
```

Kết quả:

- Compile toàn bộ `.py`: OK.
- Focused tests: 26 tests OK.
- Full `unittest discover tests` vẫn bị chặn bởi môi trường Python hiện tại thiếu `pygame` cho `tests/test_traffic_controller.py`, không phải lỗi syntax/code.
