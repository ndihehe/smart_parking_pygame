# Lịch sử cập nhật

Tài liệu này tổng hợp các thay đổi gần đây của **Smart Parking Simulator** theo cách dễ theo dõi và trình bày khi demo.

## 21/06/2026 - Hoàn thiện map, giao diện và mô phỏng

### 1. Map bãi đỗ xe 20x20

- Chuyển sang map 20x20 được mô tả trong `data/maps/default_map.txt`.
- Đồng bộ dữ liệu map sang `data/map_layout.json`.
- Sử dụng các tile có sẵn trong `assets/maps` để ghép map thay vì tự tạo hình nền khác.
- Bố trí một khu vào và một khu ra, mỗi khu gồm hai làn xe.
- Map hiện có 56 vị trí đỗ ô tô, 72 vị trí đỗ xe máy và 26 trụ đèn.
- Thêm cây, bụi cây, hàng rào, trụ đèn và các vật cản vào dữ liệu map.
- Tăng diện tích đường nội bộ, giảm các ô cỏ không cần thiết và cải thiện khả năng lưu thông.
- Hỗ trợ đọc map từ cả file TXT và JSON.
- Đổi tên các ảnh tile theo đúng nội dung để dễ tìm, thay thế và bảo trì.

### 2. Bãi đỗ hai hàng

- Xe máy có thể đỗ thành hai hàng liên tiếp.
- Ô tô cũng có thể đỗ thành hai hàng liên tiếp như xe máy.
- Hệ thống phân biệt vị trí bên trong và vị trí bên ngoài của từng cặp ô đỗ.
- Nếu xe bên trong cần ra nhưng xe bên ngoài đang chắn, bảo vệ sẽ tạm thời đưa xe bên ngoài ra, cho xe bên trong thoát rồi đưa xe còn lại về vị trí hợp lệ.
- Không cấp ô bên trong khi ô bên ngoài đã bị chiếm và không còn đường tiếp cận.

### 3. Hiển thị xe và trạng thái

- Xe đỗ đúng vị trí có khung phát sáng màu xanh lá.
- Xe đỗ sai vị trí có khung phát sáng màu đỏ.
- Xe đang được chọn có khung phát sáng màu xanh dương rõ hơn.
- Khung trạng thái được nâng chất lượng hiển thị, giảm vỡ ảnh và tăng hiệu ứng phát sáng.
- Khi chọn xe khác, xe được chọn trước tự động trở lại chế độ AI.
- Khi trả xe về chế độ tự lái, khung xanh dương được xóa đúng trạng thái.
- Xe tự xoay theo hướng di chuyển và nằm đúng chiều của ô đỗ.
- Xe điều khiển thủ công cũng xoay đầu, chuyển frame và nội suy chuyển động theo hướng bấm phím.

### 4. Chế độ ngày và đêm

- Thêm nút chuyển đổi giữa chế độ ngày và đêm.
- Thêm tile trụ đèn đường vào map bằng ký tự `L`.
- Mỗi trụ đèn chiếu sáng khu vực khoảng bốn ô xung quanh.
- Ánh sáng được vẽ theo lớp radial mềm để trông tự nhiên và phù hợp phong cách 2D cổ điển.
- Xe đang chạy trong chế độ đêm có đèn pha.
- Vùng sáng của đèn pha đi theo vị trí và góc quay của xe.

### 5. Giao diện điều khiển

- Đổi tiêu đề thành **Smart Parking Simulator**, tăng kích thước và căn giữa trong khung.
- Chia thanh điều khiển thành ba tab: `Simulation`, `Add Vehicle` và `Scenarios`.
- Giảm số nút hiện cùng lúc để thao tác dễ hiểu hơn.
- Nhật ký thuật toán vẫn được hiển thị khi chuyển tab.
- Chế độ đặt xe được bật hoặc tắt bằng cùng một nút. Nút hiển thị `Place on Map` khi chưa bật và `Finish Placement` khi đang đặt xe.
- Khi đang ở chế độ đặt xe, người dùng có thể đặt nhiều xe liên tiếp.
- Lựa chọn `Exiting` chỉ hoạt động trong chế độ đặt xe.
- Rút gọn bảng thông tin xe đang chọn để không che map.

### 6. Thống kê thuật toán

- Giữ bảng số liệu cho bốn thuật toán BFS, DFS, Greedy và A*.
- Thêm biểu đồ `AVG MS` để so sánh thời gian tìm đường trung bình. Cột thấp hơn nghĩa là thuật toán chạy nhanh hơn.
- Thêm biểu đồ `LAST KB` để so sánh bộ nhớ của lần chạy gần nhất. Cột thấp hơn nghĩa là dùng ít bộ nhớ hơn.
- Thêm ghi chú ngắn ngay dưới biểu đồ để người dùng hiểu ý nghĩa các chỉ số.
- Thuật toán đang được chọn được đánh dấu riêng trên bảng và biểu đồ.

### 7. Di chuyển và xử lý ùn tắc

- Tăng tốc độ vẽ lên 60 FPS.
- Giảm thời gian mỗi bước di chuyển từ 0,3 giây xuống 0,18 giây để xe chạy liền mạch hơn.
- Xe tự động được sinh mới sau mỗi 2 giây khi bật auto-spawn.
- Giảm thời gian phát hiện xe bị kẹt xuống 1,5 giây.
- Bắt đầu xử lý ùn tắc giao lộ sau 3 giây.
- Buộc xe tìm lại đường sau 2 giây chờ mà không thể tiếp tục.
- Xe đang nhường đường không bị tìm lại đường liên tục khi vật cản sắp được giải phóng.
- Ngăn một xe bị xử lý lặp bởi nhiều ô giao nhau trong cùng một frame.
- Cải thiện xử lý xung đột khi nhiều xe cùng muốn đi vào một ô hoặc đi đối đầu.

### 8. Đỗ sai vị trí và bảo vệ

- Phát hiện xe đỗ trên đường, tại giao lộ hoặc sai loại ô đỗ.
- Vị trí đỗ sai được xem như vật cản động để các xe khác tìm đường tránh.
- Bảo vệ có thể xử lý nhiều xe vi phạm và đưa xe về vị trí hợp lệ.
- Nếu xe đang trên đường ra bị người dùng đỗ sai, bảo vệ sẽ đưa xe tiếp tục ra cổng thay vì đưa xe quay lại bãi đỗ.
- Bảo vệ hủy nhiệm vụ khi xe thủ công đã tự rời khỏi vị trí vi phạm.

### 9. Tài nguyên hình ảnh

Thư mục `assets/maps` đã được chuẩn hóa tên file, bao gồm:

- Tile mặt đường, cỏ, cây, bụi cây, hàng rào và cổng chắn.
- Tile ô đỗ ô tô và hai hướng ô đỗ xe máy.
- Tile trụ đèn đường.
- Ảnh map hoàn chỉnh 20x20.
- Khung xanh lá cho xe đỗ đúng.
- Khung đỏ cho xe vi phạm.
- Khung xanh dương cho xe đang được chọn.
- Contact sheet tổng hợp các tài nguyên map.

### 10. Kiểm thử và ổn định

- Cập nhật test để dùng dữ liệu và tọa độ động của map 20x20.
- Bỏ các giả định cũ gắn với map 20x32.
- Thêm test cho bãi đỗ hai hàng của ô tô và xe máy.
- Thêm test cho xe đang ra cổng nhưng bị đỗ sai vị trí.
- Kiểm tra các luồng tìm đường, đỗ xe, ùn tắc, điều khiển thủ công, bảo vệ và thoát bãi.
- Kết quả hiện tại: **53/53 test vượt qua**.
- Toàn bộ mã Python đã được compile thành công bằng **Python 3.13.1**.

## Cách chạy

```powershell
py -3.13 main.py
```

## Cách chạy test

```powershell
py -3.13 -m unittest discover -s tests -v
```
