# Bài 2 - Tổ chức Centralized Configuration cho hệ thống FoodX

**Môn học:** Microservice
**Session 03:** Configuration, Service Registration và Discovery
**Cấp độ:** Vận dụng cơ bản
**Công nghệ:** Spring Boot 3.2.5, Spring Cloud 2023.0.1, Java 17

---

## 1. Mục tiêu kiến thức

Vận dụng đúng nguyên tắc **Centralized Configuration**:

- Tách cấu hình ra khỏi source code, đưa vào một kho Git dùng chung.
- Tổ chức file cấu hình đúng quy ước để Config Server phục vụ đúng service.
- Bảo vệ bí mật trong kho cấu hình bằng cú pháp mã hóa `{cipher}`.

## 2. Tình huống nghiệp vụ

FoodX chuẩn bị tách cấu hình ra khỏi source code sang một Git repository dùng
chung. Một thực tập sinh đã tạo thử file cấu hình cho `restaurant-service`
nhưng mắc **hai lỗi nghiêm trọng**: đặt sai tên file và lưu mật khẩu ở dạng
chữ thô.

File cấu hình có vấn đề trên Git repository:

```yaml
# Tên file hiện tại: config.yml
# (restaurant-service có spring.application.name = "restaurant-service")
spring:
  datasource:
    url: jdbc:mysql://foodx-cluster.local:3306/restaurants_db
    username: restaurant_service_user
    # Mật khẩu lưu thẳng dạng chữ, không mã hóa
    password: RestaurantPass123
server:
  port: 8085
```

---

## 3. Bảng tóm tắt lỗi và cách sửa

| # | Lỗi phát hiện | Vì sao sai | Hậu quả | Cách sửa |
|---|---|---|---|---|
| 1 | Tên file `config.yml` không khớp `spring.application.name` | Quy ước bắt buộc là `{spring.application.name}.yml`, tức `restaurant-service.yml` | Config Server không bao giờ đọc file này, trả `propertySources` rỗng, service lỗi khởi tạo bean hoặc âm thầm dùng giá trị mặc định trong jar, nguy hiểm nhất là chạy nhầm cấu hình dev trên prod | Đổi tên thành `restaurant-service.yml`, bổ sung `restaurant-service-dev.yml` và `restaurant-service-prod.yml` |
| 2 | Mật khẩu `RestaurantPass123` lưu dạng chữ thô | Ai clone kho cũng đọc được, lịch sử Git giữ vĩnh viễn, rò rỉ qua log/CI, không xoay vòng được, vi phạm least privilege | Lộ toàn bộ quyền truy cập cơ sở dữ liệu nhà hàng, vi phạm chuẩn tuân thủ PCI DSS | Mã hóa bằng `POST /encrypt` của Config Server, lưu dạng `{cipher}AQA...`, khóa giải mã đặt ngoài kho |
| 3 | Không tách cấu hình theo profile | Một file duy nhất cho mọi môi trường | Không thể phân biệt dev và prod, phải sửa file mỗi lần đổi môi trường | Tách thành `{app}.yml`, `{app}-dev.yml`, `{app}-prod.yml` |
| 4 | Không có lớp cấu hình dùng chung | Cấu hình giống nhau bị lặp ở mọi service | Sửa một giá trị chung phải sửa nhiều nơi, dễ sót | Bổ sung `application.yml`, `application-dev.yml`, `application-prod.yml` |

---

## 4. Cấu trúc thư mục bài làm

```
Microservice-Session3-bai2/
│
├── README.md                                   <- tài liệu này
│
├── config-repo/                                <- MÔ PHỎNG GIT REPOSITORY CẤU HÌNH TẬP TRUNG
│   ├── application.yml                             cấu hình chung cho MỌI service
│   ├── application-dev.yml                         cấu hình chung, profile dev
│   ├── application-prod.yml                        cấu hình chung, profile prod
│   ├── restaurant-service.yml                      FILE ĐÃ SỬA từ config.yml của thực tập sinh
│   ├── restaurant-service-dev.yml
│   ├── restaurant-service-prod.yml
│   ├── order-service.yml
│   ├── order-service-dev.yml
│   ├── order-service-prod.yml
│   ├── delivery-service.yml
│   ├── delivery-service-dev.yml
│   └── delivery-service-prod.yml
│
├── client-sample/                              <- CẤU HÌNH PHÍA SERVICE (nằm trong source code)
│   ├── README.md                                   so sánh spring.config.import và bootstrap.yml
│   ├── restaurant-service/src/main/resources/
│   │   ├── application.yml                         cách đúng của Spring Boot 3
│   │   └── bootstrap.yml.legacy                    cách cũ, chỉ để đối chiếu
│   ├── order-service/src/main/resources/
│   │   ├── application.yml
│   │   └── bootstrap.yml.legacy
│   └── delivery-service/src/main/resources/
│       ├── application.yml
│       └── bootstrap.yml.legacy
│
├── config-server-sample/                       <- CẤU HÌNH CỦA CHÍNH CONFIG SERVER
│   └── application.yml                             nơi khai báo encrypt.key cho {cipher}
│
├── docs/                                       <- TÀI LIỆU PHÂN TÍCH
│   ├── 01-phan-tich-loi-cau-hinh.md                phân tích lỗi đặt tên file
│   ├── 02-bao-mat-mat-khau.md                      phân tích rủi ro plaintext và cách sửa
│   ├── 03-cau-truc-config-repo.md                  cấu trúc kho, ưu tiên override, quy trình
│   ├── Bao-cao-Bai2.docx                           bản nộp dạng Word
│   └── legacy/
│       └── config.yml.old                          file lỗi gốc, giữ lại để đối chiếu
│
└── tools/
    └── build_docx.py                           <- script python-docx sinh file Word
```

---

## 5. Mô tả cấu trúc Git repository chứa cấu hình cho cả 3 service

Đây là nội dung cốt lõi mà đề bài yêu cầu. Kho cấu hình tập trung của FoodX
đặt tại `https://git.foodx.local/platform/foodx-config-repo`, cấu trúc phẳng
gồm **12 file YAML**.

### 5.1. Sơ đồ cây kho cấu hình

```
foodx-config-repo/
│
├── application.yml                 <- LỚP 1: chung mọi service, mọi profile
├── application-dev.yml             <- LỚP 2: chung mọi service, profile dev
├── application-prod.yml            <- LỚP 2: chung mọi service, profile prod
│
├── restaurant-service.yml          <- LỚP 3: riêng nhà hàng, cổng 8085
├── restaurant-service-dev.yml      <- LỚP 4
├── restaurant-service-prod.yml     <- LỚP 4
│
├── order-service.yml               <- LỚP 3: riêng đơn hàng, cổng 8082
├── order-service-dev.yml           <- LỚP 4
├── order-service-prod.yml          <- LỚP 4
│
├── delivery-service.yml            <- LỚP 3: riêng giao hàng, cổng 8083
├── delivery-service-dev.yml        <- LỚP 4
└── delivery-service-prod.yml       <- LỚP 4
```

### 5.2. Quy ước đặt tên

| Dạng file | Ý nghĩa | Ví dụ |
|---|---|---|
| `application.yml` | Chung cho mọi service, mọi profile | `application.yml` |
| `application-{profile}.yml` | Chung cho mọi service, một profile | `application-prod.yml` |
| `{spring.application.name}.yml` | Riêng một service, mọi profile | `restaurant-service.yml` |
| `{spring.application.name}-{profile}.yml` | Riêng một service, một profile | `restaurant-service-dev.yml` |

Trong đó `{spring.application.name}` là **chính xác** giá trị mà service khai
báo trong `application.yml` của nó. Đây là điểm mà thực tập sinh đã làm sai.

### 5.3. Bảng ánh xạ ba service

| Service | `spring.application.name` | Cổng | Cơ sở dữ liệu | File cấu hình trong kho |
|---|---|---|---|---|
| Nhà hàng | `restaurant-service` | 8085 | `restaurants_db` | `restaurant-service.yml`, `restaurant-service-dev.yml`, `restaurant-service-prod.yml` |
| Đơn hàng | `order-service` | 8082 | `orders_db` | `order-service.yml`, `order-service-dev.yml`, `order-service-prod.yml` |
| Giao hàng | `delivery-service` | 8083 | `deliveries_db` | `delivery-service.yml`, `delivery-service-dev.yml`, `delivery-service-prod.yml` |

### 5.4. Thứ tự ưu tiên override

```
application.yml  <  application-{profile}.yml  <  {app}.yml  <  {app}-{profile}.yml
   ưu tiên thấp nhất                                          ưu tiên cao nhất
```

Quy tắc ghi nhớ: **cấu hình càng cụ thể thì càng thắng**.

Khi `restaurant-service` chạy với profile `dev` và gọi
`GET /restaurant-service/dev`, Config Server ghép đúng 4 file theo thứ tự ưu
tiên từ cao xuống thấp:

1. `restaurant-service-dev.yml`
2. `restaurant-service.yml`
3. `application-dev.yml`
4. `application.yml`

File `config.yml` của thực tập sinh **không nằm trong danh sách này**, đó chính
là lý do nó không bao giờ được đọc.

### 5.5. Nội dung mỗi service có gì

Mỗi file cấu hình service đều bao gồm tối thiểu:

| Nhóm | Nội dung |
|---|---|
| Kết nối dữ liệu | `spring.datasource.url`, `username`, `password` dạng `{cipher}`, cấu hình pool HikariCP |
| Cổng | `server.port` khai báo riêng trong file của từng service (nhà hàng 8085, đơn hàng 8082, giao hàng 8083) |
| Timeout | Timeout kết nối, timeout đọc, và các timeout nghiệp vụ riêng |
| Cờ tính năng | Từ 5 đến 6 cờ, giá trị an toàn ở prod, mở thử nghiệm ở dev |
| Nghiệp vụ giao đồ ăn | Tham số riêng của từng miền, xem bảng dưới |
| Tích hợp | Địa chỉ các service liên quan, khóa API dạng `{cipher}` |

Các tham số nghiệp vụ đặc thù của từng service:

| Service | Ví dụ tham số nghiệp vụ |
|---|---|
| `restaurant-service` | Số đơn tối đa xử lý đồng thời, thời gian chuẩn bị món mặc định, số món tối đa mỗi thực đơn, điểm đánh giá tối thiểu, tỷ lệ hoa hồng, khung giờ cao điểm |
| `order-service` | Giá trị đơn tối thiểu và tối đa, số món tối đa mỗi đơn, số đơn tối đa mỗi giờ, phụ phí cao điểm, phương thức thanh toán, thời gian giữ chỗ chờ thanh toán |
| `delivery-service` | Bán kính tìm tài xế, quãng đường giao tối đa, số đơn tối đa mỗi tài xế, phí giao cơ bản, phí mỗi km vượt, thời gian giao cam kết, chu kỳ cập nhật vị trí |

### 5.6. Bảo mật trong kho

Toàn bộ mật khẩu và khóa API trong kho đều ở dạng `{cipher}...`:

```yaml
password: "{cipher}AQAxZ3J0UmVzdGF1cmFudFBhc3NFbmNyeXB0ZWRTYW1wbGVCYXNlNjRTdHJpbmdGb29kWDAxMjM0NTY3ODlBQkNERUY="
```

Các chuỗi này là **bản mã minh họa theo yêu cầu của đề bài**, không phải bản mã
thật. Trong dự án thật, chuỗi được sinh bằng:

```bash
curl -X POST http://localhost:8888/encrypt -d 'RestaurantPass123'
```

Khóa giải mã `encrypt.key` được khai báo trong
`config-server-sample/application.yml` và nạp từ biến môi trường, **tuyệt đối
không nằm trong kho cấu hình**.

---

## 6. Hướng dẫn kiểm tra bằng curl

### 6.1. Kiểm tra Config Server phục vụ đúng file

```bash
# Lấy cấu hình của restaurant-service ở profile dev
curl http://localhost:8888/restaurant-service/dev

# Lấy dạng YAML đã gộp và giải mã sẵn
curl http://localhost:8888/restaurant-service-dev.yml

# Chỉ định nhánh (label) cụ thể
curl http://localhost:8888/main/restaurant-service-prod.yml

# Hai service còn lại
curl http://localhost:8888/order-service/prod
curl http://localhost:8888/delivery-service/dev
```

Kết quả đúng phải có 4 phần tử trong `propertySources`, xếp theo thứ tự ưu tiên
từ cao xuống thấp.

### 6.2. Kiểm chứng lỗi tên file cũ

```bash
# Gọi với tên sai, Config Server vẫn trả HTTP 200 nhưng rỗng
curl http://localhost:8888/config/dev
```

```json
{
  "name": "config",
  "profiles": ["dev"],
  "propertySources": []
}
```

Chuỗi `"propertySources": []` rỗng chính là dấu hiệu của lỗi đặt sai tên file.

### 6.3. Kiểm chứng phía service

```bash
# Xem service đã nạp cấu hình từ những nguồn nào
curl http://localhost:8085/actuator/env | jq '.propertySources[].name'

# Kiểm tra một khóa cụ thể và xuất xứ của nó
curl http://localhost:8085/actuator/env/server.port
curl http://localhost:8085/actuator/env/spring.datasource.url
```

Nếu danh sách không có dòng nào chứa `configserver:` thì service đang chạy bằng
cấu hình trong jar, tức là cấu hình tập trung chưa hoạt động.

### 6.4. Mã hóa và giải mã bí mật

```bash
# Sinh bản mã để dán vào file cấu hình
curl -X POST http://localhost:8888/encrypt -d 'RestaurantPass123'

# Kiểm tra ngược lại
curl -X POST http://localhost:8888/decrypt -d 'AQAxZ3J0...'
```

### 6.5. Làm mới cấu hình sau khi sửa

```bash
# Làm mới một service
curl -X POST http://localhost:8085/actuator/refresh

# Làm mới hàng loạt qua Spring Cloud Bus
curl -X POST http://localhost:8085/actuator/busrefresh
```

---

## 7. Đối chiếu với yêu cầu của đề bài

| Yêu cầu | Đã thực hiện | Nằm ở đâu |
|---|---|---|
| Chỉ rõ lỗi đặt tên file không khớp `spring.application.name` | Có | `docs/01-phan-tich-loi-cau-hinh.md` mục 1, 2, 3 |
| Giải thích hậu quả khi Config Server không tìm thấy file | Có, 3 kịch bản hậu quả | `docs/01-phan-tich-loi-cau-hinh.md` mục 4 |
| Đổi lại tên file cho đúng quy ước | Có | `config-repo/restaurant-service.yml` |
| Chỉ rõ rủi ro lưu mật khẩu plaintext | Có, 7 nhóm rủi ro kèm bảng đánh giá | `docs/02-bao-mat-mat-khau.md` mục 2 |
| Sửa lại bằng cú pháp `{cipher}...` | Có | Toàn bộ file trong `config-repo/` |
| Tạo thêm cấu hình cho `order-service` | Có, 3 file theo profile | `config-repo/order-service*.yml` |
| Tạo thêm cấu hình cho `delivery-service` | Có, 3 file theo profile | `config-repo/delivery-service*.yml` |
| Đúng quy ước đặt tên, không plaintext | Có | Toàn bộ `config-repo/` |
| README mô tả cấu trúc thư mục Git repository cho cả 3 service | Có | Mục 5 của tài liệu này và `docs/03-cau-truc-config-repo.md` |
| File Word hoặc Markdown mô tả cấu trúc | Có cả hai định dạng | `docs/Bao-cao-Bai2.docx` và các file `.md` |

Các nội dung mở rộng theo hướng dẫn thực hiện:

| Nội dung | Đã thực hiện | Nằm ở đâu |
|---|---|---|
| Lớp cấu hình chung `application.yml` và theo profile | Có | `config-repo/application*.yml` |
| Mỗi service có datasource, port, timeout, feature flag, nghiệp vụ riêng | Có | 9 file service trong `config-repo/` |
| Ví dụ cấu hình phía client với `spring.config.import` | Có, cho cả 3 service | `client-sample/*/src/main/resources/application.yml` |
| Ví dụ `bootstrap.yml` theo cách cũ để đối chiếu | Có, kèm bảng so sánh | `client-sample/*/src/main/resources/bootstrap.yml.legacy` |
| Ghi rõ Spring Boot 3 dùng `spring.config.import` thay bootstrap | Có | `client-sample/README.md` |
| Endpoint và cách kiểm chứng bằng curl, actuator | Có | Mục 6 và `docs/01` mục 5 |
| Bảng trước/sau khi sửa | Có, 3 bảng | `docs/01-phan-tich-loi-cau-hinh.md` mục 6 |
| So sánh `{cipher}` với biến môi trường, Vault, Secrets Manager | Có, dạng bảng | `docs/02-bao-mat-mat-khau.md` mục 4 |
| Thứ tự ưu tiên override, quy ước nhánh, quy trình đổi cấu hình, phân quyền | Có | `docs/03-cau-truc-config-repo.md` mục 3, 4, 5, 6 |
| Giữ file lỗi gốc để đối chiếu | Có | `docs/legacy/config.yml.old` |
| File Word sinh bằng python-docx | Có, script chạy thật | `tools/build_docx.py` sinh ra `docs/Bao-cao-Bai2.docx` |

---

## 8. Ba bài học rút ra

1. **Tên file trong kho cấu hình là một phần của hợp đồng kỹ thuật.** Nó phải
   khớp chính xác với `spring.application.name`. Đặt sai tên không gây lỗi cú
   pháp nào, nhưng khiến cấu hình không bao giờ tới được service.

2. **Lỗi cấu hình thường là lỗi thầm lặng.** Config Server trả HTTP 200 với
   `propertySources` rỗng chứ không trả 404. Vì vậy phải chủ động kiểm chứng
   bằng `curl` và `/actuator/env`, đồng thời đặt `fail-fast: true` ở môi trường
   thật để service dừng ngay thay vì chạy sai.

3. **Bí mật đã commit là bí mật đã lộ.** Lịch sử Git giữ lại vĩnh viễn, nên
   việc đầu tiên khi phát hiện mật khẩu chữ thô là **đổi mật khẩu đó**, sau đó
   mới mã hóa giá trị mới bằng `{cipher}` với khóa đặt ngoài kho cấu hình.

---

## 9. Cách sinh lại file Word

```bash
pip install python-docx
python tools/build_docx.py
```

Script sẽ ghi đè `docs/Bao-cao-Bai2.docx` với nội dung tổng hợp phân tích và ba
file cấu hình đã sửa.
