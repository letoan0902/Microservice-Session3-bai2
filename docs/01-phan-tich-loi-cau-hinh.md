# 01 - Phân tích lỗi đặt tên file cấu hình

> Bài 2 - Tổ chức Centralized Configuration cho hệ thống FoodX
> Môn Microservice - Session 03: Configuration, Service Registration và Discovery

---

## 1. Mô tả lỗi

Một thực tập sinh của FoodX đã tạo file cấu hình cho `restaurant-service` trên
kho Git dùng chung với tên là **`config.yml`**:

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

Nhìn qua thì file này có vẻ hợp lệ: cú pháp YAML đúng, các khóa đều là khóa
chuẩn của Spring Boot, giá trị cũng hợp lý. Chính vì vậy mà lỗi rất dễ bị bỏ
sót khi duyệt mã. Vấn đề **không nằm ở nội dung mà nằm ở tên file**.

Tên `config.yml` không khớp với `spring.application.name` của service. Service
tự xưng tên là `restaurant-service`, nên theo quy ước của Spring Cloud Config
Server, file cấu hình bắt buộc phải tên là `restaurant-service.yml`.

---

## 2. Quy ước đặt tên của Spring Cloud Config Server

Config Server không đọc file theo kiểu "quét cả thư mục rồi gộp lại". Nó ánh
xạ **một cách máy móc** từ tên service sang tên file. Quy ước gồm hai dạng:

| Dạng file | Ý nghĩa | Ví dụ cho restaurant-service |
|---|---|---|
| `{application}.yml` | Cấu hình mặc định của một service, áp dụng cho mọi profile | `restaurant-service.yml` |
| `{application}-{profile}.yml` | Cấu hình riêng của một service ở một profile | `restaurant-service-dev.yml` |
| `application.yml` | Cấu hình dùng chung cho mọi service | `application.yml` |
| `application-{profile}.yml` | Cấu hình dùng chung cho mọi service ở một profile | `application-dev.yml` |

Trong đó:

- `{application}` chính là giá trị của `spring.application.name` mà service khai báo.
- `{profile}` chính là giá trị của `spring.profiles.active`.
- Từ khóa `application` (không có phần tên service) là tên **dành riêng** cho
  lớp cấu hình dùng chung, không được dùng cho một service cụ thể.

Config Server hỗ trợ cả `.yml`, `.yaml`, `.properties` và định dạng JSON, nhưng
phần **tên file trước phần mở rộng** thì bắt buộc phải theo đúng quy ước trên.

---

## 3. Endpoint của Config Server và cơ chế tìm file

Config Server phơi ra các endpoint theo dạng:

```
/{application}/{profile}
/{application}/{profile}/{label}
/{application}-{profile}.yml
/{label}/{application}-{profile}.yml
/{application}-{profile}.properties
/{label}/{application}-{profile}.properties
```

Trong đó `{label}` là nhánh (branch), thẻ (tag) hoặc mã commit của kho Git,
mặc định là `main`.

### Điều gì thực sự xảy ra khi restaurant-service khởi động

Service khai báo `spring.application.name: restaurant-service` và
`spring.profiles.active: dev`, nên nó gửi đúng một request:

```
GET http://localhost:8888/restaurant-service/dev
```

Config Server nhận request này và đi tìm **đúng bốn file**, theo thứ tự ưu tiên
từ cao xuống thấp:

| Thứ tự | Tên file được tìm | Vai trò |
|---|---|---|
| 1 (ưu tiên cao nhất) | `restaurant-service-dev.yml` | Riêng service, riêng profile |
| 2 | `restaurant-service.yml` | Riêng service, chung mọi profile |
| 3 | `application-dev.yml` | Chung mọi service, riêng profile dev |
| 4 (ưu tiên thấp nhất) | `application.yml` | Chung mọi service, chung mọi profile |

**File `config.yml` không có mặt trong danh sách này.** Config Server không hề
biết đến sự tồn tại của nó, và cũng **không** báo lỗi "tìm thấy file lạ". Với
Config Server, `config.yml` chỉ là một file vô nghĩa nằm trong kho Git, giống
như một file `ghi-chu.txt` bất kỳ.

Muốn `config.yml` được phục vụ, phải có một service khai báo
`spring.application.name: config` - điều này hoàn toàn không đúng với ý định
của thực tập sinh.

---

## 4. Hậu quả khi Config Server không tìm thấy đúng file cấu hình

Đây là phần nguy hiểm nhất: **lỗi này không gây ra thông báo lỗi rõ ràng**.
Config Server trả về HTTP 200 với một `propertySources` rỗng, chứ không trả về
404. Về mặt kỹ thuật thì "không có cấu hình nào" là một câu trả lời hợp lệ.

```json
{
  "name": "restaurant-service",
  "profiles": ["dev"],
  "label": null,
  "version": "a1b2c3d4e5f6",
  "state": null,
  "propertySources": []
}
```

Chuỗi `"propertySources": []` rỗng chính là dấu hiệu của lỗi. Từ đây có ba
kịch bản hậu quả, xếp theo mức độ nguy hiểm tăng dần.

### Hậu quả 1 - Service không khởi động được, lỗi khởi tạo bean

Vì `spring.datasource.url` không có giá trị, Spring Boot không dựng được
`DataSource` bean. Ứng dụng dừng lại với ngoại lệ dạng:

```
***************************
APPLICATION FAILED TO START
***************************

Description:
Failed to configure a DataSource: 'url' attribute is not specified and no
embedded datasource could be configured.

Reason: Failed to determine a suitable driver class
```

Đây thực ra là kịch bản **may mắn nhất**, vì lỗi lộ ra ngay và rất dễ nhận
biết. Đáng tiếc là lập trình viên thường hiểu nhầm nguyên nhân, đi kiểm tra
xem cơ sở dữ liệu có chạy không, mật khẩu có đúng không, mạng có thông không,
trong khi lỗi thật lại nằm ở tên file trong kho cấu hình.

### Hậu quả 2 - Service khởi động nhưng âm thầm dùng giá trị mặc định trong jar

Nếu trong `src/main/resources/application.yml` của service vẫn còn sót lại giá
trị dự phòng - chẳng hạn một `datasource` trỏ vào H2 trong bộ nhớ hoặc vào
`localhost` - thì service sẽ khởi động **bình thường**, không một dòng cảnh báo.

Đây là kịch bản tệ hơn hẳn:

- Nhật ký khởi động sạch sẽ, `/actuator/health` báo `UP`.
- API vẫn phản hồi, kiểm thử khói (smoke test) vẫn xanh.
- Nhưng dữ liệu đang được ghi vào **sai cơ sở dữ liệu**. Nhà hàng cập nhật
  thực đơn thì thay đổi biến mất sau khi khởi động lại (H2 trong bộ nhớ), hoặc
  ghi vào một CSDL cũ mà không ai còn theo dõi.
- Lỗi chỉ lộ ra sau vài ngày, khi khách hàng phản ánh, và lúc đó việc truy vết
  nguyên nhân đã cực kỳ tốn kém.

Đây chính là lý do tại sao nên đặt `spring.cloud.config.fail-fast: true` và bỏ
tiền tố `optional:` ở môi trường thật.

### Hậu quả 3 - Nguy hiểm nhất: chạy nhầm cấu hình dev trên môi trường prod

Giả sử kho cấu hình có `application.yml` và `application-dev.yml` đặt đúng tên,
nhưng cấu hình riêng của restaurant-service lại nằm trong `config.yml`. Khi
triển khai lên môi trường thật với `spring.profiles.active=prod`,
Config Server sẽ ghép được `application.yml` và `application-prod.yml`, nhưng
lớp riêng của service thì rỗng.

Hệ quả có thể xảy ra:

- Service dùng các giá trị mặc định chung, trong đó có thể sót lại cấu hình
  hướng dev, ví dụ `ddl-auto: update` khiến Hibernate **tự động sửa lược đồ
  cơ sở dữ liệu sản xuất**.
- `management.endpoints.web.exposure.include: "*"` bị áp dụng trên prod, phơi
  bày toàn bộ endpoint quản trị ra Internet, kể cả `/actuator/heapdump` chứa
  dữ liệu nhạy cảm trong bộ nhớ.
- Các cờ tính năng thử nghiệm (`goi-y-mon-bang-ai`) bị bật nhầm cho khách hàng
  thật.
- Timeout của dev (15 giây) được áp lên prod, khiến các luồng bị giữ quá lâu
  và gây sập dây chuyền khi tải cao.

Nói cách khác: **một lỗi đặt tên file có thể dẫn tới sự cố toàn hệ thống.**

---

## 5. Cách kiểm chứng

### 5.1. Kiểm chứng phía Config Server bằng curl

Cách nhanh nhất là hỏi thẳng Config Server xem nó phục vụ được gì.

```bash
# Trường hợp SAI - kho chỉ có file config.yml
curl http://localhost:8888/restaurant-service/dev
```

Kết quả trả về `propertySources` rỗng:

```json
{
  "name": "restaurant-service",
  "profiles": ["dev"],
  "propertySources": []
}
```

```bash
# Trường hợp ĐÚNG - sau khi đổi tên thành restaurant-service.yml
curl http://localhost:8888/restaurant-service/dev
```

Kết quả trả về danh sách các nguồn cấu hình, **xếp theo đúng thứ tự ưu tiên
từ cao xuống thấp**:

```json
{
  "name": "restaurant-service",
  "profiles": ["dev"],
  "label": "main",
  "propertySources": [
    { "name": "...config-repo/restaurant-service-dev.yml", "source": { "server.port": 8085, "...": "..." } },
    { "name": "...config-repo/restaurant-service.yml",     "source": { "...": "..." } },
    { "name": "...config-repo/application-dev.yml",        "source": { "...": "..." } },
    { "name": "...config-repo/application.yml",            "source": { "...": "..." } }
  ]
}
```

Có thể lấy trực tiếp dạng YAML đã được gộp và giải mã sẵn:

```bash
curl http://localhost:8888/restaurant-service-dev.yml
```

Và kiểm tra cả trên một nhánh (label) cụ thể:

```bash
curl http://localhost:8888/main/restaurant-service-dev.yml
```

Thử với tên sai để thấy rõ sự khác biệt - Config Server vẫn trả 200 nhưng rỗng:

```bash
curl http://localhost:8888/config/dev
```

### 5.2. Kiểm chứng phía service bằng Actuator

Sau khi service đã khởi động, endpoint `/actuator/env` cho biết **giá trị đang
dùng thực sự đến từ nguồn nào**:

```bash
# Xem toàn bộ các nguồn cấu hình mà service đã nạp
curl http://localhost:8085/actuator/env | jq '.propertySources[].name'
```

Nếu cấu hình được nạp đúng, trong danh sách phải có các dòng chứa
`configserver:` như sau:

```
"configserver:https://git.foodx.local/platform/foodx-config-repo/restaurant-service-dev.yml"
"configserver:https://git.foodx.local/platform/foodx-config-repo/restaurant-service.yml"
"configserver:https://git.foodx.local/platform/foodx-config-repo/application-dev.yml"
"configserver:https://git.foodx.local/platform/foodx-config-repo/application.yml"
```

Nếu **không có dòng nào chứa `configserver:`** thì chắc chắn service đang chạy
bằng cấu hình trong jar, tức là đã dính đúng lỗi đang phân tích.

Kiểm tra giá trị của một khóa cụ thể và xuất xứ của nó:

```bash
curl http://localhost:8085/actuator/env/server.port
curl http://localhost:8085/actuator/env/spring.datasource.url
```

Kết quả cho thấy rõ khóa đó được lấy từ file nào:

```json
{
  "property": { "source": "configserver:...restaurant-service-dev.yml", "value": "8085" },
  "activeProfiles": ["dev"]
}
```

Ngoài ra `/actuator/configprops` cho phép xem các lớp `@ConfigurationProperties`
đã được nạp giá trị hay chưa.

### 5.3. Dấu hiệu nhận biết trong nhật ký khởi động

Khi mọi thứ đúng, nhật ký của service phải có dòng:

```
Fetching config from server at : http://localhost:8888
Located environment: name=restaurant-service, profiles=[dev], label=main, version=a1b2c3d
```

Nếu thấy `propertySources` rỗng hoặc không thấy dòng `Located environment` thì
cần kiểm tra lại tên file trong kho cấu hình ngay.

---

## 6. Bảng so sánh trước và sau khi sửa

### 6.1. So sánh về tên file

| Tiêu chí | TRƯỚC (sai) | SAU (đúng) |
|---|---|---|
| Tên file trong kho | `config.yml` | `restaurant-service.yml` |
| `spring.application.name` | `restaurant-service` | `restaurant-service` |
| Có khớp quy ước không | Không khớp | Khớp |
| Config Server có đọc không | Không bao giờ đọc | Đọc và phục vụ đúng |
| Kết quả `GET /restaurant-service/dev` | `propertySources: []` | 4 nguồn cấu hình theo đúng thứ tự |
| Cấu hình theo profile | Không thể làm được | `restaurant-service-dev.yml`, `restaurant-service-prod.yml` |
| Khả năng mở rộng cho service khác | Đụng tên, không mở rộng được | Mỗi service một file riêng, rõ ràng |

### 6.2. So sánh về nội dung file

| Khóa cấu hình | TRƯỚC (sai) | SAU (đúng) |
|---|---|---|
| Tên file | `config.yml` | `restaurant-service.yml` |
| `spring.application.name` | Không khai báo | `restaurant-service` |
| `spring.datasource.url` | `jdbc:mysql://foodx-cluster.local:3306/restaurants_db` | Giữ nguyên, bổ sung `useSSL=true` và múi giờ |
| `spring.datasource.username` | `restaurant_service_user` | Giữ nguyên |
| `spring.datasource.password` | `RestaurantPass123` (chữ thô) | `{cipher}AQAxZ3J0...` (đã mã hóa) |
| `server.port` | `8085` (giữ nguyên) | `8085` (giữ nguyên, đề bài không yêu cầu đổi) |
| Tách theo profile | Không có | Có `-dev.yml` và `-prod.yml` |
| Timeout, cờ tính năng | Không có | Đầy đủ theo nghiệp vụ nhà hàng |

### 6.3. So sánh toàn bộ kho cấu hình

| TRƯỚC (sai) | SAU (đúng) |
|---|---|
| `config.yml` (một file duy nhất, sai tên, chỉ cho một service) | `application.yml` |
| | `application-dev.yml` |
| | `application-prod.yml` |
| | `restaurant-service.yml` |
| | `restaurant-service-dev.yml` |
| | `restaurant-service-prod.yml` |
| | `order-service.yml` |
| | `order-service-dev.yml` |
| | `order-service-prod.yml` |
| | `delivery-service.yml` |
| | `delivery-service-dev.yml` |
| | `delivery-service-prod.yml` |

---

## 7. Kết luận và bài học rút ra

1. Tên file trong kho cấu hình tập trung **không phải là chuyện thẩm mỹ**, nó
   là một phần của hợp đồng kỹ thuật giữa service và Config Server. Đặt sai
   tên thì cấu hình không bao giờ tới được service.
2. Quy tắc cần thuộc lòng: **tên file phải bằng đúng `spring.application.name`**,
   thêm hậu tố `-{profile}` khi cần tách môi trường.
3. Lỗi này thuộc loại **thất bại thầm lặng** - Config Server vẫn trả HTTP 200,
   không có ngoại lệ nào được ném ra. Vì vậy bắt buộc phải chủ động kiểm chứng
   bằng `curl` tới Config Server và bằng `/actuator/env` phía service.
4. Ở môi trường thật, luôn đặt `spring.cloud.config.fail-fast: true` và bỏ tiền
   tố `optional:`. Thà service không khởi động còn hơn nó khởi động với cấu
   hình sai.
5. Nên thêm một bước kiểm tra tự động trong quy trình CI của kho cấu hình: đối
   chiếu danh sách tên file với danh sách `spring.application.name` của các
   service đang có, và từ chối merge nếu xuất hiện file lạ.
