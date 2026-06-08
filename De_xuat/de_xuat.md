# Đề xuất cải tiến — Smart Parking Pygame

> Rà soát vai trò: Business Analyst + Software Architect + QA Reviewer  
> Phạm vi: dự án sinh viên — mô phỏng bãi đỗ xe, thuật toán BFS / DFS / Greedy / A*  
> Không dùng ML, DL, Computer Vision  
> Ngày rà soát: 2026-06-07  
> Trạng thái: **Chỉ đề xuất — chưa sửa code**

---

## Mục lục

1. [Tóm tắt điều hành](#1-tóm-tắt-điều-hành)
2. [Hệ thống hiện tại: có / thiếu / sai](#2-hệ-thống-hiện-tại-có--thiếu--sai)
3. [Bảng đối chiếu nghiệp vụ ↔ code](#3-bảng-đối-chiếu-nghiệp-vụ--code)
4. [Đối chiếu thuật toán AI cơ bản](#4-đối-chiếu-thuật-toán-ai-cơ-bản)
5. [Lỗi logic quan trọng (QA)](#5-lỗi-logic-quan-trọng-qa)
6. [Lỗi kiến trúc quan trọng (Architect)](#6-lỗi-kiến-trúc-quan-trọng-architect)
7. [Dead code & config thừa](#7-dead-code--config-thừa)
8. [Khoảng trống test (QA)](#8-khoảng-trống-test-qa)
9. [Đề xuất sửa theo phase](#9-đề-xuất-sửa-theo-phase)
10. [Checklist demo báo cáo / bảo vệ](#10-checklist-demo-báo-cáo--bảo-vệ)
11. [Gợi ý cấu trúc file sau khi sửa](#11-gợi-ý-cấu-trúc-file-sau-khi-sửa)
12. [Kết luận](#12-kết-luận)

---

## 1. Tóm tắt điều hành

### Điểm mạnh

- Kiến trúc phân lớp rõ: `core/` · `models/` · `ai/` · `ui/` · `utils/`
- Luồng nghiệp vụ chính đã chạy được: spawn → gán slot → A* → di chuyển → đỗ / exit
- Manual override, vi phạm đỗ xe, guard SEC, dynamic block, congestion cơ bản
- Logger + sidebar Pygame; ~21 unit test (map, parking, traffic, A*)
- Slot lifecycle đúng hướng: **reserve → occupy**

### Gap lớn nhất so với đề bài

| Gap | Mức độ |
|-----|--------|
| **Chỉ A* chạy runtime** — BFS / DFS / Greedy có file nhưng không tích hợp | 🔴 Critical |
| **Auto-park không validate** — bỏ qua `validate_parking()` | 🔴 Critical |
| **“Sinh bản đồ”** thực tế là load file, không generate | 🟡 Medium |
| Dead code, API pathfinding không thống nhất, race condition slot | 🟡 Medium |

### Khuyến nghị ưu tiên

1. **Phase 1** — Tích hợp 4 thuật toán + UI chọn (đáp ứng đề bài)
2. **Phase 2** — Sửa bug logic ảnh hưởng demo
3. **Phase 3** — DFS connectivity dùng module chung
4. **Phase 4** — Dọn dead code nhẹ
5. **Phase 5** — Polish (tùy thời gian)

---

## 2. Hệ thống hiện tại: có / thiếu / sai

### 2.1 Đã có (mức demo được)

| Nhóm | Chi tiết | File chính |
|------|----------|------------|
| Map 2D 20×32 | Parse từ `default_map.txt` | `MapManager`, `MapState` |
| Cache index | Gates, slots, intersections | `MapState` |
| Spawn xe | CAR/MOTO, cổng trái, auto spawn | `GameController`, `VehicleManager` |
| Phân loại xe | Enum `VehicleType` | `models/enums.py` |
| Gán slot | Scoring distance + penalty | `ParkingManager` |
| Pathfinding runtime | Chỉ **A*** | `ai/pathfinding/astar.py` |
| Di chuyển tự động | Cell-by-cell, 0.3s/step | `VehicleManager` |
| Manual mode | Click, WASD, Enter | `InputHandler`, `GameController` |
| Validate đỗ xe | OK / DIFFERENT_SLOT / WRONG_TYPE / ILLEGAL_ROAD / BLOCKING_INTERSECTION | `ParkingManager.validate_parking()` |
| Vật cản & reroute | Dynamic block + A* lại | `TrafficController`, `MapManager` |
| Ùn tắc | Yield, priority, reroute, guard traffic | `TrafficController` |
| Guard | Vi phạm + điều phối conflict | `Guard`, `GameController` |
| Log | Timestamp, sidebar | `Logger`, `Renderer` |

### 2.2 Thiếu so với nghiệp vụ

| Hạng mục | Ghi chú |
|----------|---------|
| Sinh bản đồ procedural | Chỉ load file; `data/scenarios/` trong README không tồn tại |
| BFS / DFS / Greedy trong runtime | Có implement, **không import** ở module nào |
| Chọn thuật toán | `AlgorithmType` enum không dùng |
| DFS connectivity (module) | Logic DFS nội bộ `_validate_connectivity()`, không gọi `dfs.py` |
| `slot_scoring.py` | Trùng `ParkingManager.find_slot()` |
| `SimulationState` | Không được wire |
| `WAIT_THRESHOLD` | Config khai báo, không dùng |
| `wait_reason = "CONGESTION"` | Recovery có list, runtime không gán |
| `vehicle.direction` | Không cập nhật → priority rule vô hiệu |

### 2.3 Sai / lệch nghiệp vụ

| # | Vấn đề | File |
|---|--------|------|
| S1 | Auto-park không qua `validate_parking()` | `GameController.update()` |
| S2 | `wait_reason` sai tên khi block bởi map/slot | `VehicleManager.update()` |
| S3 | A* goal miễn kiểm tra reservation | `astar.py` |
| S4 | `dynamic_block` intersection không tự gỡ | `TrafficController` |
| S5 | BFS/DFS/Greedy thiếu `blocked_positions` | `bfs.py`, `dfs.py`, `greedy.py` |
| S6 | `VehicleManager` không gọi `is_passable()` | `VehicleManager.update()` |
| S7 | Right-click exit không check `PARKED` | `InputHandler`, `start_exit()` |
| S8 | Congestion reroute dùng occupied set quá hẹp | `TrafficController._handle_congestion()` |

---

## 3. Bảng đối chiếu nghiệp vụ ↔ code

| # | Nghiệp vụ | Trạng thái | File / hàm | Ghi chú |
|---|-----------|------------|------------|---------|
| 1 | Sinh bản đồ ma trận 2D | ⚠️ Một phần | `MapManager.load_map()` | Parse OK; không generate map mới |
| 2 | Kiểm tra liên thông bằng DFS | ⚠️ Một phần | `_validate_connectivity()` | DFS nội bộ; không dùng `dfs.py` |
| 3 | Sinh xe tại cổng | ✅ Đạt | `spawn_vehicle()` | 2 cổng trái; chặn khi full / gate occupied |
| 4 | Nhận diện loại xe | ✅ Đạt | `VehicleType` | Spawn bằng phím C/M — đúng phạm vi đề |
| 5 | Gán ô đỗ phù hợp | ✅ Đạt | `find_slot()`, `assign_slot()` | Reserve trước, occupy sau |
| 6 | Tìm đường BFS / A* | ⚠️ Một phần | `astar.py` (runtime) | **Chỉ A* chạy**; BFS có file, không tích hợp |
| 7 | Di chuyển xe tự động | ✅ Đạt | `VehicleManager.update()` | Chặn xe khác; nhảy theo cell |
| 8 | Manual Override | ✅ Đạt | `InputHandler`, `move_manual()`, `confirm_parking()` | |
| 9 | Đỗ đúng | ⚠️ Manual OK / Auto thiếu | `validate_parking()` → `OK` | Auto bỏ qua validate |
| 10 | Đỗ sai loại slot | ✅ Manual | `WRONG_TYPE` + guard | Không thêm dynamic block |
| 11 | Đỗ trên đường | ✅ Manual | `ILLEGAL_ROAD` + dynamic block | Có test |
| 12 | Đỗ chắn ngã tư | ✅ Manual | `BLOCKING_INTERSECTION` | Chưa có test riêng |
| 13 | Phát hiện vật cản & tính lại đường | ✅ Đạt | `handle_obstacle()`, `_reroute_vehicle()` | |
| 14 | Phát hiện ùn tắc & reroute | ⚠️ Một phần | `_handle_congestion()` | `CONGESTION` reason không set; block không gỡ |
| 15 | Ghi log sự kiện | ✅ Đạt | `Logger.log()` | Max 20 dòng sidebar |

**Chú thích trạng thái:** ✅ Đạt · ⚠️ Một phần · ❌ Chưa có

---

## 4. Đối chiếu thuật toán AI cơ bản

| Thuật toán | File | Runtime | `blocked_positions` | Demo được? |
|------------|------|---------|---------------------|------------|
| **BFS** | `ai/pathfinding/bfs.py` | ❌ | ❌ | Chỉ khi tích hợp |
| **DFS** | `ai/pathfinding/dfs.py` | ❌ (trừ logic connectivity nội bộ) | ❌ | Chỉ khi tích hợp |
| **Greedy Best-First** | `ai/pathfinding/greedy.py` | ❌ | ❌ | Chỉ khi tích hợp |
| **A\*** | `ai/pathfinding/astar.py` | ✅ | ✅ | Đủ demo pathfinding chính |

**Kết luận BA:** Đề bài yêu cầu 4 thuật toán — hiện **chỉ đáp ứng 25% runtime**. Cần facade + UI chọn thuật toán để demo và báo cáo.

---

## 5. Lỗi logic quan trọng (QA)

### P0 — Ảnh hưởng demo / báo cáo

| ID | Lỗi | Vị trí | Hậu quả |
|----|-----|--------|---------|
| **L1** | Auto-park không validate | `GameController.update()` — nhánh `ARRIVED` | Xe auto có thể occupy sai ô |
| **L2** | BFS/DFS/Greedy không tích hợp | Toàn project | Không đáp ứng yêu cầu đề 4 thuật toán |
| **L3** | `wait_reason` / `status` không nhất quán | `VehicleManager` L118–128 | Block map/slot → `REROUTING` + `"BLOCKED_BY_VEHICLE"` (sai tên) |
| **L4** | Goal slot không check reservation | `astar.py` L37–45 | Race: nhiều xe cùng nhắm 1 slot |

### P1 — Ổn định mô phỏng

| ID | Lỗi | Hậu quả |
|----|-----|---------|
| **L5** | `dynamic_block` intersection không gỡ | Deadlock / slot unreachable |
| **L6** | Congestion reroute thiếu occupied toàn cục | Path đi xuyên xe đang chạy |
| **L7** | Xe `VIOLATION` loại khỏi `occupied_positions` | Xe khác path xuyên xe vi phạm |
| **L8** | `VehicleManager` không dùng `is_passable()` | Có thể đi qua cell type không hợp lệ (`B`, `.`) |

### P2 — UX / edge case

| ID | Lỗi | Hậu quả |
|----|-----|---------|
| **L9** | Right-click exit không check `PARKED` | Release slot giữa chừng |
| **L10** | `CONGESTION` wait_reason không bao giờ set | Recovery branch dead code |
| **L11** | `vehicle.direction` không update | Priority rule không phản ánh hướng |
| **L12** | `validate_parking` → `UNKNOWN` (gate, empty) | UI không xử lý rõ |

---

## 6. Lỗi kiến trúc quan trọng (Architect)

| ID | Vấn đề | Mô tả | Rủi ro |
|----|--------|-------|--------|
| **A1** | Thiếu Algorithm facade | 4 thuật toán rời rạc, không strategy/factory | Không demo so sánh BFS vs A* |
| **A2** | API pathfinding không thống nhất | Chỉ A* có `blocked_positions` | Tích hợp phải sửa 3 file hoặc wrapper |
| **A3** | God object `GameController` | ~510 dòng: spawn, path, parking, guard, exit, recovery | Khó test; dễ regression |
| **A4** | Dead code | `SimulationState`, `slot_scoring`, `AlgorithmType`, `WAIT_THRESHOLD`, `priority_score` | Báo cáo “có module” nhưng không chạy |
| **A5** | Thứ tự update 1 frame | Traffic → Vehicle move → Recovery | Race condition khó tái hiện |
| **A6** | String magic `wait_reason` | Không enum; `"CONGESTION"` listed nhưng never set | Typo / dead branch |
| **A7** | UI không biết thuật toán | Không layer chọn algo | Demo phụ thuộc đọc source |

### Điểm kiến trúc nên giữ

- Tách `core/` / `models/` / `ai/` / `ui/`
- Slot lifecycle: reserve → occupy
- `MapState` cache static indexes
- `Logger` tập trung; `Renderer` cache map surface

---

## 7. Dead code & config thừa

| Item | File | Hành động đề xuất |
|------|------|-------------------|
| `SimulationState` | `core/simulation_state.py` | Wire vào `PygameApp` hoặc xóa |
| `score_slot()` | `ai/decision/slot_scoring.py` | Gọi từ `ParkingManager.find_slot()` |
| `AlgorithmType` | `models/enums.py` | Dùng trong pathfinding facade |
| `WAIT_THRESHOLD` | `config.py` | Dùng hoặc xóa |
| `priority_score` field | `models/vehicle.py` | Populate hoặc xóa |
| `vehicle.direction` | `models/vehicle.py` | Cập nhật khi move hoặc bỏ bonus trong priority |
| BFS/DFS/Greedy | `ai/pathfinding/*.py` | Tích hợp qua facade |
| `data/scenarios/` | README | Tạo thư mục hoặc sửa README |

---

## 8. Khoảng trống test (QA)

### Đã có (~21 test)

- `test_map_manager.py` — kích thước, slot rows, cache
- `test_parking_manager.py` — loại slot, release khi đổi slot
- `test_traffic_controller.py` — vi phạm, guard, yield, exit, auto spawn, conflict
- `test_pathfinding.py` — A* tránh xe, không xuyên xe

### Chưa có — nên bổ sung

| Test | Mục đích |
|------|----------|
| BFS / DFS / Greedy tìm được path | Đáp ứng đề thuật toán |
| So sánh path length A* ≤ BFS | Giải thích heuristic |
| Connectivity — slot unreachable | DFS validation |
| Auto-park qua validate | Bug L1 |
| `BLOCKING_INTERSECTION` manual | Nghiệp vụ ngã tư |
| Chọn thuật toán runtime | Phase 1 |
| `dynamic_block` gỡ sau congestion | Bug L5 |

---

## 9. Đề xuất sửa theo phase

> Phạm vi sinh viên · dễ demo · dễ giải thích báo cáo  
> **Không** tách `GameController` thành nhiều service — quá scope

---

### Phase 1 — Tích hợp 4 thuật toán (ưu tiên cao nhất)

**Mục tiêu demo:** Nhấn `1/2/3/4` chọn BFS / DFS / Greedy / A*; xe mới dùng thuật toán đang chọn.

| Bước | Task | File |
|------|------|------|
| 1.1 | Tạo `find_path(algorithm, start, goal, map_manager, blocked)` | `ai/pathfinding/router.py` (mới) |
| 1.2 | Thêm `blocked_positions` cho BFS, DFS, Greedy (copy logic A*) | `bfs.py`, `dfs.py`, `greedy.py` |
| 1.3 | Thêm `current_algorithm: AlgorithmType` | `config.py` hoặc `GameController` |
| 1.4 | Phím `1`–`4` trong InputHandler | `ui/input_handler.py` |
| 1.5 | Hiển thị thuật toán trên sidebar | `ui/renderer.py` |
| 1.6 | Thay mọi `astar(...)` trực tiếp bằng `find_path(...)` | `game_controller.py`, `traffic_controller.py` |
| 1.7 | Unit test: BFS và A* cùng tìm path; length A* ≤ BFS | `tests/test_pathfinding.py` |

**Giải thích báo cáo:** *“Runtime dùng strategy pattern; mỗi thuật toán là module độc lập, facade `find_path()` điều phối.”*

**Effort ước tính:** 1–2 buổi

---

### Phase 2 — Sửa bug logic ảnh hưởng demo

| Bước | Task | File | Fix |
|------|------|------|-----|
| 2.1 | Auto-park qua `validate_parking()` | `game_controller.py` | L1 |
| 2.2 | Sửa mapping `wait_reason` | `vehicle_manager.py` | L3 — map/slot → `"BLOCKED_BY_MAP"` hoặc `"NO_PATH"` |
| 2.3 | Goal reservation check trong A* | `astar.py` | L4 |
| 2.4 | Gỡ `dynamic_block` intersection sau reroute OK hoặc timeout | `traffic_controller.py` | L5 |
| 2.5 | Congestion reroute dùng toàn bộ occupied positions | `traffic_controller.py` | L6 |
| 2.6 | `VIOLATION` vẫn tính occupied (hoặc dynamic block) | `traffic_controller.py` | L7 |
| 2.7 | `VehicleManager` gọi `map_manager.is_passable()` | `vehicle_manager.py` | L8 |

**Effort ước tính:** ~1 buổi

---

### Phase 3 — DFS connectivity đúng nghĩa đề bài

| Bước | Task | File |
|------|------|------|
| 3.1 | Refactor `_validate_connectivity()` dùng hàm DFS chung | `map_manager.py`, `dfs.py` hoặc `path_utils.py` |
| 3.2 | Test: map mặc định 0 slot unreachable | `tests/test_map_manager.py` |
| 3.3 | Test: map nhỏ slot cô lập → log warning | `tests/test_map_manager.py` |

**Giải thích báo cáo:** *“DFS dùng cho connectivity check; BFS / Greedy / A* dùng cho navigation.”*

**Effort ước tính:** ~ nửa buổi

---

### Phase 4 — Dọn kiến trúc nhẹ

| Bước | Task | File |
|------|------|------|
| 4.1 | `ParkingManager.find_slot()` gọi `score_slot()` | `parking_manager.py`, `slot_scoring.py` |
| 4.2 | Wire `SimulationState` hoặc xóa | `simulation_state.py`, `pygame_app.py` |
| 4.3 | Constants / enum cho `wait_reason` | `models/enums.py` hoặc `models/constants.py` |
| 4.4 | Set `CONGESTION` trong `TrafficController` | `traffic_controller.py` |
| 4.5 | Xóa hoặc dùng `WAIT_THRESHOLD` | `config.py` |

**Effort ước tính:** ~ nửa buổi

---

### Phase 5 — Polish demo (tùy thời gian)

| Bước | Task | Ghi chú |
|------|------|---------|
| 5.1 | Right-click exit chỉ khi `PARKED` hoặc `MANUAL` | L9 |
| 5.2 | Cập nhật `vehicle.direction` khi move | L11 |
| 5.3 | Map generator đơn giản (optional) | Không bắt buộc nếu có `default_map.txt` |
| 5.4 | Test BLOCKING_INTERSECTION, auto-park, chọn algo | QA |
| 5.5 | Cập nhật README — phím 1–4, wait reasons, slot lifecycle | Docs |
| 5.6 | Sửa README `data/scenarios/` hoặc tạo thư mục | Docs |

**Effort ước tính:** ~1 buổi (optional)

---

### Tóm tắt timeline đề xuất
Phase 1 ████████████░░░░░░░░ (Critical — đề bài thuật toán) Phase 2 ████████░░░░░░░░░░░░ (Critical — bug demo) Phase 3 ████░░░░░░░░░░░░░░░░ (Important — DFS connectivity) Phase 4 ███░░░░░░░░░░░░░░░░░ (Nice — dọn code) Phase 5 ██░░░░░░░░░░░░░░░░░░ (Optional — polish)

---

---

## 10. Checklist demo báo cáo / bảo vệ

| # | Kịch bản | Thao tác | Kỳ vọng sau Phase 1–2 |
|---|----------|----------|------------------------|
| 1 | Load map | Chạy `py -3.13 main.py` | Grid 20×32; log connectivity |
| 2 | Spawn xe | `C`, `M` | Đúng loại slot; path hiển thị |
| 3 | So sánh thuật toán | `1` BFS → `4` A* | Sidebar hiện algo; path có thể khác |
| 4 | Manual đỗ sai slot | Click trái → WASD → Enter (slot C cho MOTO) | Guard SEC + reassign |
| 5 | Manual đỗ trên đường | Enter trên ô `R` | Dynamic block + reroute |
| 6 | Manual đỗ ngã tư | Enter trên ô `I` | BLOCKING + dynamic block |
| 7 | Ùn tắc | Auto spawn `T`, nhiều xe | Yield / reroute; không deadlock vĩnh viễn |
| 8 | Full lot | Spawn khi hết slot | Log “lot full” |
| 9 | Exit | Right-click xe đã đỗ | Rời qua cổng phải; xe biến mất |
| 10 | Log | Quan sát sidebar | Timestamp + sự kiện rõ |

---

## 11. Gợi ý cấu trúc file sau khi sửa

```text
smart_parking_pygame/
├── main.py
├── config.py                          # + DEFAULT_ALGORITHM
├── core/
│   ├── game_controller.py             # dùng find_path(), auto validate
│   ├── map_manager.py                 # connectivity qua DFS module
│   ├── vehicle_manager.py             # is_passable, wait_reason fix
│   ├── parking_manager.py             # gọi score_slot()
│   └── traffic_controller.py          # CONGESTION reason, unblock intersection
├── models/
│   ├── enums.py                       # AlgorithmType, WaitReason (mới)
│   └── ...
├── ai/
│   ├── pathfinding/
│   │   ├── router.py                  # ★ find_path() facade
│   │   ├── bfs.py                     # + blocked_positions
│   │   ├── dfs.py
│   │   ├── greedy.py
│   │   └── astar.py                   # + goal reservation fix
│   └── decision/
│       ├── slot_scoring.py            # được dùng bởi ParkingManager
│       └── priority_rule.py
├── ui/
│   ├── input_handler.py               # phím 1–4 chọn algo
│   └── renderer.py                    # hiện algorithm + stats
├── tests/
│   ├── test_pathfinding.py            # + BFS/DFS/Greedy tests
│   └── ...
└── docs/
    └── DE_XUAT_CAI_TIEN.md            # file này