# client-sample - Cấu hình phía service để lấy config từ Config Server

Thư mục này chứa ví dụ cấu hình **nằm trong source code** của ba service FoodX.
Mục đích là minh họa ranh giới rõ ràng giữa hai nơi:

| Nằm trong source code (thư mục này) | Nằm trong kho cấu hình tập trung (`config-repo/`) |
|---|---|
| `spring.application.name` - service tự xưng tên gì | `server.port` |
| `spring.config.import` - lấy cấu hình ở đâu | `spring.datasource.*` kể cả mật khẩu đã mã hóa |
| `spring.profiles.active` - chạy môi trường nào | Timeout, cờ tính năng, tham số nghiệp vụ |
| `spring.cloud.config.label` - nhánh nào | Địa chỉ các service liên quan, khóa API |

Nguyên tắc: **file trong source code càng mỏng càng tốt**. Nếu phải sửa file này
để đổi một giá trị nghiệp vụ thì nghĩa là đã vi phạm nguyên tắc Centralized
Configuration, vì mỗi lần đổi lại phải build và triển khai lại toàn bộ service.

## Cấu trúc

```
client-sample/
├── restaurant-service/src/main/resources/
│   ├── application.yml            <- CÁCH ĐÚNG (Spring Boot 3)
│   └── bootstrap.yml.legacy       <- cách cũ, chỉ để đối chiếu
├── order-service/src/main/resources/
│   ├── application.yml
│   └── bootstrap.yml.legacy
└── delivery-service/src/main/resources/
    ├── application.yml
    └── bootstrap.yml.legacy
```

## Spring Boot 3 dùng `spring.config.import`, không dùng `bootstrap.yml`

Đây là điểm khác biệt quan trọng nhất cần nhớ khi làm việc với
Spring Boot 3.2.5 và Spring Cloud 2023.0.1.

**Cách cũ (Spring Boot 2.3 trở về trước) - `bootstrap.yml`:**

```yaml
spring:
  application:
    name: restaurant-service
  cloud:
    config:
      uri: http://localhost:8888
      label: main
      profile: dev
```

Cách này cần thêm phụ thuộc `spring-cloud-starter-bootstrap` và tạo ra một
"bootstrap context" chạy trước ApplicationContext chính. Hai ngữ cảnh chồng
nhau khiến thứ tự ưu tiên khó đoán và rất khó gỡ lỗi.

**Cách mới (Spring Boot 2.4 trở lên, bắt buộc với Spring Boot 3) - `application.yml`:**

```yaml
spring:
  application:
    name: restaurant-service
  config:
    import: "optional:configserver:http://localhost:8888"
  profiles:
    active: dev
  cloud:
    config:
      label: main
      fail-fast: true
```

Không cần phụ thuộc thêm, chỉ có một luồng nạp cấu hình duy nhất, thứ tự
ưu tiên rõ ràng theo thứ tự khai báo trong `spring.config.import`.

## Về tiền tố `optional:`

| Cách viết | Hành vi khi Config Server không phản hồi |
|---|---|
| `optional:configserver:http://localhost:8888` | Service vẫn khởi động, bỏ qua cấu hình từ xa |
| `configserver:http://localhost:8888` | Service dừng ngay với lỗi rõ ràng |

Khuyến nghị của FoodX:

- Môi trường **dev**: giữ `optional:` để lập trình viên vẫn chạy được service
  khi chưa bật Config Server ở máy cá nhân.
- Môi trường **prod**: **bỏ** `optional:` và đặt `spring.cloud.config.fail-fast: true`.
  Ở môi trường thật, việc service khởi động với cấu hình rỗng còn nguy hiểm
  hơn nhiều so với việc nó không khởi động, vì lỗi sẽ chỉ lộ ra khi có khách
  hàng thật đặt đơn.

## Cách chạy thử

```bash
# 1. Bật Config Server (cổng 8888), trỏ vào kho cấu hình config-repo
# 2. Chạy service với profile mong muốn
java -jar restaurant-service.jar --spring.profiles.active=dev

# 3. Kiểm chứng service đã nhận đúng cấu hình từ Config Server
curl http://localhost:8081/actuator/env | grep configserver
```

## Ghi chú về phụ thuộc Maven

Ba service đều cần đúng một phụ thuộc phía client:

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-config</artifactId>
</dependency>
```

với `spring-cloud-dependencies` phiên bản `2023.0.1` khai báo trong
`dependencyManagement`, tương thích Spring Boot `3.2.5`.
**Không** thêm `spring-cloud-starter-bootstrap` - đó là dấu hiệu của cách làm cũ.
