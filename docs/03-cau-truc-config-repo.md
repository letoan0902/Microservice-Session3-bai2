# 03 - Cấu trúc kho cấu hình tập trung của FoodX

> Bài 2 - Tổ chức Centralized Configuration cho hệ thống FoodX
> Môn Microservice - Session 03: Configuration, Service Registration và Discovery

---

## 1. Sơ đồ cây thư mục

Kho Git cấu hình tập trung của FoodX được đặt tại
`https://git.foodx.local/platform/foodx-config-repo` với cấu trúc phẳng:

```
foodx-config-repo/                          <- kho Git dùng chung cho toàn hệ thống
│
├── application.yml                         <- LỚP 1: chung cho MỌI service
│                                              (actuator, logging, timeout mặc định,
│                                               múi giờ, đơn vị tiền tệ)
│
├── application-dev.yml                     <- LỚP 2: chung cho mọi service, profile dev
├── application-prod.yml                    <- LỚP 2: chung cho mọi service, profile prod
│
├── restaurant-service.yml                  <- LỚP 3: riêng restaurant-service, mọi profile
├── restaurant-service-dev.yml              <- LỚP 4: riêng restaurant-service, profile dev
├── restaurant-service-prod.yml             <- LỚP 4: riêng restaurant-service, profile prod
│
├── order-service.yml                       <- LỚP 3: riêng order-service, mọi profile
├── order-service-dev.yml                   <- LỚP 4: riêng order-service, profile dev
├── order-service-prod.yml                  <- LỚP 4: riêng order-service, profile prod
│
├── delivery-service.yml                    <- LỚP 3: riêng delivery-service, mọi profile
├── delivery-service-dev.yml                <- LỚP 4: riêng delivery-service, profile dev
├── delivery-service-prod.yml               <- LỚP 4: riêng delivery-service, profile prod
│
└── README.md                               <- hướng dẫn sử dụng kho cấu hình
```

Tổng cộng **12 file cấu hình**: 3 file chung + 9 file riêng cho 3 service.

### Vì sao chọn cấu trúc phẳng

Spring Cloud Config Server hỗ trợ cả cấu trúc phẳng lẫn cấu trúc thư mục con
(qua `search-paths`). FoodX chọn cấu trúc phẳng vì:

- Đúng quy ước mặc định, không cần cấu hình `search-paths` thêm.
- Nhìn một lần thấy ngay toàn bộ bức tranh, dễ phát hiện file đặt sai tên.
- Với 3 service thì cấu trúc thư mục con là thừa thãi.

Khi hệ thống vượt khoảng 15-20 service, có thể chuyển sang cấu trúc thư mục con
theo miền nghiệp vụ:

```yaml
# Cấu hình phía Config Server khi số service tăng
spring:
  cloud:
    config:
      server:
        git:
          uri: https://git.foodx.local/platform/foodx-config-repo
          search-paths:
            - 'chung'
            - 'nha-hang/*'
            - 'don-hang/*'
            - 'giao-hang/*'
```

Lưu ý: dù dùng thư mục con thì **tên file vẫn phải giữ nguyên quy ước**
`{application}-{profile}.yml`.

---

## 2. Bảng ánh xạ service - file - profile

### 2.1. Bảng tổng hợp ba service

| Service | `spring.application.name` | Cổng | File mặc định | File dev | File prod | Cơ sở dữ liệu |
|---|---|---|---|---|---|---|
| Nhà hàng | `restaurant-service` | 8085 | `restaurant-service.yml` | `restaurant-service-dev.yml` | `restaurant-service-prod.yml` | `restaurants_db` |
| Đơn hàng | `order-service` | 8082 | `order-service.yml` | `order-service-dev.yml` | `order-service-prod.yml` | `orders_db` |
| Giao hàng | `delivery-service` | 8083 | `delivery-service.yml` | `delivery-service-dev.yml` | `delivery-service-prod.yml` | `deliveries_db` |
| (dùng chung) | - | - | `application.yml` | `application-dev.yml` | `application-prod.yml` | - |

### 2.2. Bảng ánh xạ request tới file được nạp

| Request tới Config Server | Các file được nạp (từ ưu tiên cao xuống thấp) |
|---|---|
| `GET /restaurant-service/dev` | `restaurant-service-dev.yml`, `restaurant-service.yml`, `application-dev.yml`, `application.yml` |
| `GET /restaurant-service/prod` | `restaurant-service-prod.yml`, `restaurant-service.yml`, `application-prod.yml`, `application.yml` |
| `GET /order-service/dev` | `order-service-dev.yml`, `order-service.yml`, `application-dev.yml`, `application.yml` |
| `GET /order-service/prod` | `order-service-prod.yml`, `order-service.yml`, `application-prod.yml`, `application.yml` |
| `GET /delivery-service/dev` | `delivery-service-dev.yml`, `delivery-service.yml`, `application-dev.yml`, `application.yml` |
| `GET /delivery-service/prod` | `delivery-service-prod.yml`, `delivery-service.yml`, `application-prod.yml`, `application.yml` |
| `GET /restaurant-service/default` | `restaurant-service.yml`, `application.yml` |
| `GET /config/dev` (tên file sai của thực tập sinh) | Không file nào - `propertySources` rỗng |

### 2.3. Bảng phân bổ nội dung theo từng lớp

| Loại cấu hình | `application.yml` | `application-{profile}.yml` | `{app}.yml` | `{app}-{profile}.yml` |
|---|---|---|---|---|
| Múi giờ, tiền tệ, ngôn ngữ | Có | | | |
| Endpoint Actuator | Có (danh sách cơ bản) | Có (mở/đóng theo môi trường) | | |
| Mức ghi log | Có (mặc định INFO) | Có (DEBUG ở dev, WARN ở prod) | | Có (theo gói của service) |
| `server.port` | | | Có | |
| `spring.application.name` | | | Có | |
| `spring.datasource.url` | | | Có (mặc định) | Có (theo môi trường) |
| Mật khẩu `{cipher}` | | | Có | Có |
| Kích thước pool kết nối | | | Có (mặc định) | Có (theo tải) |
| Timeout gọi liên service | Có (mặc định chung) | Có (theo môi trường) | Có (riêng service) | Có (riêng và theo môi trường) |
| Cờ tính năng | | | Có (giá trị an toàn) | Có (bật thử nghiệm ở dev) |
| Tham số nghiệp vụ | | | Có | Có (khi khác nhau theo môi trường) |
| Địa chỉ service liên quan | | | Có (tên logic) | Có (localhost ở dev) |

Nguyên tắc phân bổ: **giá trị càng dùng chung thì càng đặt ở lớp thấp**. Nếu
một giá trị giống nhau ở cả ba service thì phải nằm ở `application.yml`, không
lặp lại ba lần.

---

## 3. Thứ tự ưu tiên override

### 3.1. Sơ đồ bốn lớp

```
   Độ ưu tiên THẤP                                              Độ ưu tiên CAO
   (nền tảng chung)                                            (cụ thể nhất)
        |                                                             |
        v                                                             v
  +-----------------+   +-------------------------+   +-------------+   +-------------------+
  | application.yml | < | application-{profile}   | < | {app}.yml   | < | {app}-{profile}   |
  |                 |   | .yml                    |   |             |   | .yml              |
  | Chung mọi       |   | Chung mọi service,      |   | Riêng 1     |   | Riêng 1 service,  |
  | service,        |   | riêng 1 profile         |   | service,    |   | riêng 1 profile   |
  | mọi profile     |   |                         |   | mọi profile |   |                   |
  +-----------------+   +-------------------------+   +-------------+   +-------------------+
        LỚP 1                     LỚP 2                    LỚP 3               LỚP 4

  Quy tắc: lớp bên PHẢI ghi đè lớp bên TRÁI khi trùng khóa.
```

Cách nhớ đơn giản: **cấu hình càng cụ thể thì càng thắng**. File dành riêng cho
một service ở một môi trường cụ thể là cụ thể nhất, nên có quyền cao nhất.

### 3.2. Ví dụ minh họa cụ thể với khóa `connect-timeout-ms`

Giả sử `restaurant-service` chạy với profile `dev`:

| Lớp | File | Giá trị khai báo | Có thắng không |
|---|---|---|---|
| 1 | `application.yml` | `foodx.http.connect-timeout-ms: 3000` | Bị ghi đè |
| 2 | `application-dev.yml` | `foodx.http.connect-timeout-ms: 10000` | Bị ghi đè |
| 3 | `restaurant-service.yml` | `foodx.restaurant.timeout.connect-timeout-ms: 3000` | Bị ghi đè |
| 4 | `restaurant-service-dev.yml` | `foodx.restaurant.timeout.connect-timeout-ms: 10000` | **Thắng** |

Giá trị cuối cùng service nhận được cho khóa
`foodx.restaurant.timeout.connect-timeout-ms` là **10000**.

### 3.3. Ví dụ với cờ tính năng

Khóa `foodx.restaurant.feature.goi-y-mon-bang-ai`:

| Môi trường | Giá trị ở `restaurant-service.yml` | Giá trị ở file profile | Kết quả cuối |
|---|---|---|---|
| dev | `false` | `restaurant-service-dev.yml`: `true` | `true` - đội phát triển thử nghiệm được |
| prod | `false` | `restaurant-service-prod.yml`: `false` | `false` - khách hàng thật không bị ảnh hưởng |

Đây chính là giá trị thực tiễn của cấu hình phân lớp: cùng một bản jar, chỉ đổi
profile là hành vi thay đổi, không cần build lại.

### 3.4. Các nguồn cấu hình bên ngoài kho

Cần lưu ý rằng ngoài bốn lớp trên, Spring Boot còn có các nguồn khác với độ ưu
tiên **cao hơn cả Config Server**:

| Ưu tiên | Nguồn |
|---|---|
| 1 (cao nhất) | Tham số dòng lệnh, ví dụ `--server.port=9090` |
| 2 | Biến môi trường của hệ điều hành |
| 3 | Cấu hình từ Config Server (bốn lớp đã trình bày) |
| 4 (thấp nhất) | `application.yml` nằm trong jar của service |

Điều này có nghĩa: khi cần xử lý sự cố khẩn cấp, có thể ghi đè tạm bằng tham số
dòng lệnh mà chưa cần sửa kho cấu hình. Nhưng phải coi đó là biện pháp tạm thời
và ghi lại thành thay đổi chính thức trong kho ngay sau đó, nếu không cấu hình
thực tế sẽ trôi khỏi cấu hình được khai báo.

---

## 4. Quy ước nhánh (label)

Trong Spring Cloud Config, `{label}` là nhánh, thẻ hoặc mã commit của kho Git.
Nó cho phép các môi trường khác nhau đọc các phiên bản cấu hình khác nhau **từ
cùng một kho**.

### 4.1. Mô hình nhánh của FoodX

| Nhánh | Mục đích | Ai được ghi | Cơ chế bảo vệ |
|---|---|---|---|
| `main` | Cấu hình đang chạy ở môi trường thật | Chỉ qua pull request đã duyệt | Nhánh được bảo vệ, cần 2 người duyệt, cấm force-push |
| `staging` | Cấu hình cho môi trường kiểm thử trước khi lên thật | Đội phát triển qua pull request | Cần 1 người duyệt |
| `dev` | Cấu hình cho môi trường phát triển | Đội phát triển đẩy trực tiếp | Không bảo vệ |
| `feature/*` | Thử nghiệm cấu hình cho một tính năng | Người tạo nhánh | Không bảo vệ, xóa sau khi merge |

### 4.2. Cách chỉ định label

Phía service khai báo trong `application.yml`:

```yaml
spring:
  cloud:
    config:
      label: main
```

Hoặc truyền khi chạy:

```bash
java -jar restaurant-service.jar \
  --spring.profiles.active=prod \
  --spring.cloud.config.label=main
```

Gọi trực tiếp qua endpoint có label:

```bash
curl http://localhost:8888/main/restaurant-service-prod.yml
curl http://localhost:8888/dev/restaurant-service-dev.yml
```

### 4.3. Phân biệt label và profile

Đây là hai khái niệm rất dễ nhầm lẫn:

| | `label` | `profile` |
|---|---|---|
| Bản chất | Nhánh/thẻ/commit của Git | Hậu tố trong tên file cấu hình |
| Trả lời câu hỏi | Lấy **phiên bản nào** của kho | Lấy **file nào** trong phiên bản đó |
| Ví dụ giá trị | `main`, `dev`, `v1.4.2`, `a1b2c3d` | `dev`, `prod`, `staging` |
| Khai báo ở đâu | `spring.cloud.config.label` | `spring.profiles.active` |

Có thể phối hợp cả hai: label `main` với profile `prod` là cấu hình sản xuất
chính thức, còn label `dev` với profile `dev` là cấu hình đang thử nghiệm.

### 4.4. Dùng thẻ (tag) để khóa phiên bản cấu hình

Với môi trường sản xuất, một thực hành tốt là gắn thẻ cho mỗi lần phát hành:

```bash
git tag -a config-v1.4.2 -m "Cau hinh cho ban phat hanh 1.4.2"
git push origin config-v1.4.2
```

Sau đó cho service prod trỏ vào đúng thẻ đó:

```yaml
spring:
  cloud:
    config:
      label: config-v1.4.2
```

Lợi ích: cấu hình sản xuất được cố định, không bị thay đổi ngoài ý muốn khi có
người merge vào `main`. Khi cần quay lui chỉ việc trỏ về thẻ trước đó.

---

## 5. Quy trình làm việc khi thay đổi cấu hình

### 5.1. Sơ đồ tổng quát

```
  Lập trình viên          Kho Git                Config Server          Các service
       |                     |                        |                      |
       | 1. Sửa file YAML    |                        |                      |
       |-------------------->|                        |                      |
       | 2. Tạo pull request |                        |                      |
       |-------------------->|                        |                      |
       |                     | 3. Duyệt và merge      |                      |
       |                     |----------------------->|                      |
       |                     |    (Config Server tự   |                      |
       |                     |     kéo bản mới)       |                      |
       | 4. Gọi refresh      |                        |                      |
       |------------------------------------------------------------------->|
       |                     |                        | 5. Service hỏi lại   |
       |                     |                        |<---------------------|
       |                     |                        | 6. Trả cấu hình mới  |
       |                     |                        |--------------------->|
       | 7. Kiểm chứng qua /actuator/env                                     |
       |------------------------------------------------------------------->|
```

### 5.2. Các bước chi tiết

**Bước 1 - Tạo nhánh và sửa cấu hình**

```bash
git checkout -b config/tang-timeout-nha-hang
# Sửa file restaurant-service-prod.yml
git add restaurant-service-prod.yml
git commit -m "Tang read-timeout cua restaurant-service prod tu 4000 len 6000ms"
git push origin config/tang-timeout-nha-hang
```

Quy ước đặt tên commit: nêu rõ **service nào, khóa nào, giá trị cũ sang giá trị
mới**. Kho cấu hình là nơi lịch sử commit có giá trị điều tra sự cố rất cao.

**Bước 2 - Tạo pull request và duyệt**

Danh sách kiểm tra bắt buộc khi duyệt:

- Tên file có đúng `{application}-{profile}.yml` không.
- Có mật khẩu hay khóa API nào ở dạng chữ thô lọt vào không.
- Thay đổi có nhắm đúng profile không, có vô tình sửa nhầm `prod` không.
- Giá trị mới có nằm trong ngưỡng hợp lý không.
- Cú pháp YAML có hợp lệ không (đã có bước kiểm tra tự động trong CI).

**Bước 3 - Merge vào nhánh đích**

Config Server đọc trực tiếp từ Git nên sau khi merge là bản mới đã sẵn sàng.
Với cấu hình `force-pull: true` và `clone-on-start: true`, Config Server luôn
phục vụ nội dung mới nhất của nhánh.

Kiểm tra ngay rằng Config Server đã thấy bản mới:

```bash
curl http://localhost:8888/restaurant-service/prod | jq '.version'
# So sánh với mã commit vừa merge
```

**Bước 4 - Làm mới cấu hình cho service**

Có ba cách, xếp theo mức độ ưu tiên khi lựa chọn:

**Cách A - Làm mới từng service bằng `/actuator/refresh`:**

```bash
curl -X POST http://localhost:8085/actuator/refresh
```

Kết quả trả về danh sách các khóa đã thay đổi:

```json
["foodx.restaurant.timeout.read-timeout-ms"]
```

Cách này chỉ phù hợp khi số lượng service ít. Với 3 service ở mọi máy chủ thì
phải gọi lần lượt từng nơi, dễ sót.

**Cách B - Làm mới hàng loạt bằng Spring Cloud Bus:**

```bash
# Gọi một lần trên bất kỳ service nào, mọi service khác đều được làm mới
curl -X POST http://localhost:8085/actuator/busrefresh

# Chỉ làm mới đúng một service
curl -X POST http://localhost:8085/actuator/busrefresh/restaurant-service:8085
```

Spring Cloud Bus dùng một hàng đợi thông điệp (RabbitMQ hoặc Kafka) để phát sự
kiện làm mới tới tất cả các thực thể (instance). Đây là cách phù hợp nhất khi
số service tăng.

Phụ thuộc cần thêm:

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-bus-amqp</artifactId>
</dependency>
```

Hoàn thiện hơn nữa: cấu hình webhook từ Git tới
`POST /monitor` của Config Server để việc làm mới diễn ra **tự động** ngay khi
có commit, không cần ai gọi tay.

**Cách C - Khởi động lại service:**

Bắt buộc phải dùng khi thay đổi chạm vào những cấu hình **không refresh được**:

| Loại cấu hình | Có refresh nóng được không |
|---|---|
| Khóa trong bean có `@RefreshScope` | Có |
| Khóa trong `@ConfigurationProperties` | Có |
| Mức ghi log (`logging.level.*`) | Có |
| Cờ tính năng | Có |
| `server.port` | **Không**, phải khởi động lại |
| `spring.datasource.url`, `username`, `password` | **Không** (pool đã dựng), phải khởi động lại |
| Kích thước pool HikariCP | **Không**, phải khởi động lại |
| `spring.application.name` | **Không**, phải khởi động lại |

**Bước 5 - Kiểm chứng**

```bash
# Kiểm tra service đã nhận giá trị mới
curl http://localhost:8085/actuator/env/foodx.restaurant.timeout.read-timeout-ms

# Kiểm tra nguồn của giá trị đó
curl http://localhost:8085/actuator/env | jq '.propertySources[].name'
```

### 5.3. Cách dùng `@RefreshScope` phía mã nguồn

Để một bean nhận được giá trị mới sau khi gọi `/actuator/refresh`, bean đó phải
được đánh dấu:

```java
@RefreshScope
@Component
public class CauHinhNhaHang {

    @Value("${foodx.restaurant.timeout.read-timeout-ms}")
    private int readTimeoutMs;

    // Sau khi gọi POST /actuator/refresh, bean được tạo lại
    // và readTimeoutMs mang giá trị mới
}
```

Cách được khuyến nghị hơn là dùng `@ConfigurationProperties`, vì các lớp này
được làm mới sẵn mà không cần chú thích thêm:

```java
@Component
@ConfigurationProperties(prefix = "foodx.restaurant.timeout")
public class TimeoutNhaHangProperties {
    private int connectTimeoutMs;
    private int readTimeoutMs;
    private int xacNhanDonTimeoutGiay;
    // getter và setter
}
```

### 5.4. Quy trình quay lui khi cấu hình sai

```bash
# Xem lịch sử thay đổi của một file
git log --oneline -- restaurant-service-prod.yml

# Quay lui một commit cụ thể (tạo commit mới, giữ nguyên lịch sử)
git revert a1b2c3d
git push origin main

# Làm mới lại các service
curl -X POST http://localhost:8085/actuator/busrefresh
```

Luôn dùng `git revert` chứ không dùng `git reset --hard` trên nhánh chung, để
giữ lại dấu vết đầy đủ phục vụ điều tra sự cố.

---

## 6. Phân quyền trên kho cấu hình

Kho cấu hình chứa bí mật của toàn hệ thống nên phải được kiểm soát chặt hơn cả
kho mã nguồn.

### 6.1. Ma trận phân quyền

| Vai trò | Đọc kho | Ghi nhánh `dev` | Ghi nhánh `main` | Duyệt PR | Giữ `encrypt.key` prod |
|---|---|---|---|---|---|
| Thực tập sinh | Có | Có | Không | Không | Không |
| Lập trình viên | Có | Có | Không, chỉ qua PR | Không | Không |
| Trưởng nhóm kỹ thuật | Có | Có | Chỉ qua PR | Có | Không |
| Đội nền tảng (Platform) | Có | Có | Có | Có | Có |
| Đội bảo mật | Có | Không | Không | Có (bắt buộc với PR chạm bí mật) | Có |
| Tài khoản của Config Server | Chỉ đọc | Không | Không | Không | - |
| Tài khoản CI/CD | Chỉ đọc | Không | Không | Không | Không |

### 6.2. Các quy tắc bắt buộc

1. **Kho phải để chế độ riêng tư (private).** Không bao giờ đặt kho cấu hình ở
   chế độ công khai, kể cả khi mọi mật khẩu đã được mã hóa.
2. **Tài khoản Config Server chỉ có quyền đọc.** Config Server không bao giờ
   cần ghi vào kho, nên cấp quyền ghi là mở rộng bề mặt tấn công một cách vô ích.
3. **Nhánh `main` phải được bảo vệ.** Bắt buộc pull request, tối thiểu hai người
   duyệt, cấm đẩy trực tiếp, cấm force-push.
4. **Mọi thay đổi chạm tới giá trị `{cipher}` phải có đội bảo mật duyệt.**
5. **Khóa `encrypt.key` không nằm trong kho này** và chỉ đội nền tảng cùng đội
   bảo mật được biết.
6. **Bật quét bí mật tự động** trong CI của kho (gitleaks, truffleHog) để chặn
   ngay pull request có chứa chữ thô.
7. **Bật ghi nhật ký kiểm toán của Git** để biết ai clone, ai đẩy, vào lúc nào.
8. **Xem xét lại danh sách quyền định kỳ 3 tháng một lần**, thu hồi ngay quyền
   của người đã chuyển nhóm hoặc nghỉ việc.

### 6.3. Kiểm tra tự động đề xuất cho CI của kho cấu hình

```yaml
# Ví dụ các bước kiểm tra bắt buộc trước khi merge
kiem-tra:
  - Cú pháp YAML hợp lệ với mọi file
  - Tên file khớp danh sách spring.application.name đã đăng ký
  - Không có khóa password/secret/key nào thiếu tiền tố {cipher}
  - Không có địa chỉ IP hay tên miền lạ nằm ngoài danh sách cho phép
  - Mọi khóa bắt buộc đều có mặt trong file của từng service
```

---

## 7. Tổng kết

| Nội dung | Quy ước của FoodX |
|---|---|
| Tên kho | `foodx-config-repo` |
| Cấu trúc | Phẳng, 12 file YAML ở thư mục gốc |
| Quy ước tên file | `{spring.application.name}[-{profile}].yml` |
| Lớp chung | `application.yml`, `application-{profile}.yml` |
| Số profile | 2 profile chính: `dev` và `prod` |
| Thứ tự override | `application.yml` < `application-{profile}.yml` < `{app}.yml` < `{app}-{profile}.yml` |
| Nhánh sản xuất | `main`, được bảo vệ, cần 2 người duyệt |
| Bí mật | Bắt buộc dùng `{cipher}...`, khóa nằm ngoài kho |
| Làm mới cấu hình | `/actuator/refresh` cho từng service, `/actuator/busrefresh` cho hàng loạt |
| Quy trình đổi cấu hình | Nhánh riêng, pull request, duyệt, merge, refresh, kiểm chứng |
| Quyền của Config Server | Chỉ đọc |
