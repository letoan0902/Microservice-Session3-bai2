# 02 - Bảo mật mật khẩu trong kho cấu hình tập trung

> Bài 2 - Tổ chức Centralized Configuration cho hệ thống FoodX
> Môn Microservice - Session 03: Configuration, Service Registration và Discovery

---

## 1. Mô tả lỗi

File cấu hình gốc của thực tập sinh lưu mật khẩu cơ sở dữ liệu ở **dạng chữ thô**
(plaintext), không hề mã hóa:

```yaml
spring:
  datasource:
    url: jdbc:mysql://foodx-cluster.local:3306/restaurants_db
    username: restaurant_service_user
    # Mật khẩu lưu thẳng dạng chữ, không mã hóa
    password: RestaurantPass123
```

Chuỗi `RestaurantPass123` là mật khẩu truy cập cơ sở dữ liệu `restaurants_db`
chứa toàn bộ dữ liệu nhà hàng, thực đơn và giá món của FoodX. Nó đang nằm
nguyên văn trong một kho Git dùng chung cho cả đội.

Đáng chú ý là chính dòng chú thích trong file đã ghi rõ "không mã hóa" - người
viết **biết** đây là vấn đề nhưng vẫn commit lên. Đây là tình huống rất phổ
biến trong thực tế: rủi ro được nhận ra nhưng bị bỏ qua vì "để sau sửa".

---

## 2. Rủi ro của việc lưu mật khẩu dạng chữ thô

### 2.1. Ai clone được kho là đọc được mật khẩu

Kho cấu hình tập trung theo định nghĩa là **dùng chung**. Danh sách những
người có thể đọc được `RestaurantPass123` bao gồm:

- Toàn bộ lập trình viên trong công ty, kể cả những người làm ở các nhóm không
  liên quan gì tới nghiệp vụ nhà hàng.
- Thực tập sinh, cộng tác viên, nhà thầu ngoài được cấp quyền tạm thời.
- Nhân viên **đã nghỉ việc** nhưng còn bản clone trên máy cá nhân. Thu hồi
  quyền truy cập kho Git không xóa được bản sao đã nằm trên máy họ.
- Bất kỳ ai chiếm được tài khoản Git của một người trong danh sách trên.

Điều này vi phạm trực tiếp nguyên tắc **least privilege** (đặc quyền tối thiểu):
chỉ những chủ thể thực sự cần mới được truy cập một tài nguyên. Ở đây, một lập
trình viên frontend không có lý do gì để biết mật khẩu cơ sở dữ liệu sản xuất,
nhưng vẫn đọc được nó chỉ vì kho cấu hình là chung.

### 2.2. Lịch sử Git giữ mật khẩu vĩnh viễn

Đây là rủi ro bị đánh giá thấp nhất nhưng nghiêm trọng nhất.

Giả sử ba tháng sau đội phát hiện lỗi và sửa lại:

```bash
git commit -m "Ma hoa mat khau CSDL"
git push
```

Mật khẩu đã **không hề biến mất**. Nó vẫn còn nguyên trong lịch sử và ai cũng
lấy lại được:

```bash
# Xem lại nội dung file ở commit cũ
git show a1b2c3d:config.yml

# Tìm mọi commit từng chạm vào file đó
git log --all --full-history -- config.yml

# Truy vết một chuỗi cụ thể qua toàn bộ lịch sử
git log -S "RestaurantPass123" --all
```

Muốn xóa thật sự khỏi lịch sử phải viết lại toàn bộ lịch sử kho bằng
`git filter-repo` hoặc `BFG Repo-Cleaner`, rồi force-push. Việc này:

- Làm hỏng mọi bản clone hiện có, tất cả thành viên phải clone lại.
- Không xử lý được các bản fork, bản mirror, bản sao lưu đã tạo trước đó.
- Không xử lý được bản đã được các dịch vụ lập chỉ mục (GitHub, GitLab) lưu cache.

**Kết luận thực tế: một khi mật khẩu đã được commit, phải coi như nó đã bị lộ
vĩnh viễn. Cách duy nhất đúng là đổi mật khẩu đó ngay lập tức.**

### 2.3. Rò rỉ qua nhật ký, CI/CD và các kênh phụ

Mật khẩu chữ thô rò rỉ ra nhiều nơi ngoài kho Git:

| Kênh rò rỉ | Cơ chế |
|---|---|
| Nhật ký CI/CD | Bước build in ra nội dung file cấu hình để gỡ lỗi, log CI thường được lưu lâu và nhiều người xem được |
| `/actuator/env` | Endpoint này hiển thị giá trị cấu hình, nếu không đặt `show-values: never` thì mật khẩu hiện nguyên văn qua HTTP |
| `/actuator/heapdump` | Ảnh chụp bộ nhớ chứa mọi chuỗi đang có, kể cả mật khẩu |
| Log ngoại lệ | Thông điệp lỗi kết nối CSDL đôi khi in cả chuỗi kết nối kèm mật khẩu |
| Chia sẻ màn hình | Buổi họp review code, buổi hướng dẫn thực tập sinh |
| Ảnh chụp màn hình | Đính kèm trong phiếu lỗi (ticket), gửi qua chat công ty |
| Công cụ tìm kiếm mã | Sourcegraph, tính năng tìm kiếm của GitLab lập chỉ mục toàn bộ nội dung |
| Sao lưu | Bản sao lưu kho Git nằm trên kho lưu trữ có mức bảo vệ thấp hơn |

Đặc điểm chung: mật khẩu chữ thô **lan rộng một cách thụ động**, không ai cố ý
làm lộ nhưng nó cứ tự nhân bản ra khắp nơi.

### 2.4. Không xoay vòng (rotate) được

Chính sách bảo mật thường yêu cầu đổi mật khẩu định kỳ 90 ngày một lần. Với
mật khẩu chữ thô nằm rải rác, mỗi lần xoay vòng phải:

- Tìm cho ra **tất cả** nơi mật khẩu đang xuất hiện. Không có cách nào chắc
  chắn tìm hết.
- Sửa và commit vào kho cấu hình, tạo thêm một bản ghi lịch sử chứa mật khẩu mới.
- Triển khai lại toàn bộ service liên quan.

Chi phí cao khiến đội ngũ dần né tránh việc xoay vòng, và mật khẩu bị dùng
nguyên trong nhiều năm. Khi có sự cố lộ lọt, không ai biết mật khẩu đã bị lộ từ
bao giờ và những ai đã từng thấy nó.

### 2.5. Không có nhật ký kiểm toán

Với mật khẩu chữ thô, không thể trả lời được câu hỏi cơ bản của điều tra sự cố:
"Ai đã đọc mật khẩu này, vào lúc nào?" Một thao tác `git clone` bình thường
không để lại dấu vết nào cho thấy người đó đã đọc bí mật.

### 2.6. Vi phạm chuẩn tuân thủ

FoodX xử lý thanh toán của khách hàng nên chịu ràng buộc của các chuẩn như
PCI DSS. Lưu thông tin xác thực dạng chữ thô trong kho mã nguồn là vi phạm rõ
ràng, có thể dẫn tới trượt kiểm toán, bị phạt và mất quyền xử lý thanh toán thẻ.

### 2.7. Tổng hợp mức độ rủi ro

| Rủi ro | Mức độ | Khả năng xảy ra | Hệ quả cụ thể với FoodX |
|---|---|---|---|
| Người trong công ty đọc được | Cao | Chắc chắn xảy ra | Vi phạm least privilege, mọi lập trình viên chạm được CSDL nhà hàng |
| Lịch sử Git giữ vĩnh viễn | Rất cao | Chắc chắn xảy ra | Không thể xóa, buộc phải đổi mật khẩu |
| Rò rỉ qua log/CI | Cao | Rất dễ xảy ra | Mật khẩu lan sang hệ thống có mức bảo vệ thấp hơn |
| Không xoay vòng được | Trung bình | Chắc chắn xảy ra | Mật khẩu dùng nhiều năm, không kiểm soát được |
| Không có nhật ký kiểm toán | Trung bình | Chắc chắn xảy ra | Không điều tra được khi có sự cố |
| Kho bị lộ ra ngoài | Rất cao | Ít nhưng có thật | Mất toàn bộ dữ liệu nhà hàng, thực đơn, giá món |
| Vi phạm PCI DSS | Cao | Khi bị kiểm toán | Bị phạt, mất quyền xử lý thanh toán |

---

## 3. Cách sửa - Mã hóa bằng cú pháp `{cipher}...`

### 3.1. Kết quả sau khi sửa

```yaml
spring:
  datasource:
    url: jdbc:mysql://foodx-cluster.local:3306/restaurants_db?useSSL=true&serverTimezone=Asia/Ho_Chi_Minh
    username: restaurant_service_user
    # Mật khẩu đã được mã hóa bằng POST /encrypt của Config Server
    password: "{cipher}AQAxZ3J0UmVzdGF1cmFudFBhc3NFbmNyeXB0ZWRTYW1wbGVCYXNlNjRTdHJpbmdGb29kWDAxMjM0NTY3ODlBQkNERUY="
```

**Lưu ý quan trọng về bài làm này:** chuỗi sau `{cipher}` trong toàn bộ kho
`config-repo/` là **chuỗi base64 giả lập, chỉ nhằm minh họa đúng cú pháp** theo
yêu cầu của đề bài. Đây không phải bản mã thật và không giải mã ra giá trị nào
có ý nghĩa. Trong dự án thật, chuỗi này phải được sinh ra bằng chính Config
Server của hệ thống, như hướng dẫn ở mục 3.4.

### 3.2. Cơ chế encrypt/decrypt của Config Server

Điểm cốt lõi cần hiểu: **việc giải mã diễn ra ở phía Config Server, không phải
ở phía service.**

```
   Kho Git (config-repo)                Config Server                  restaurant-service
  +----------------------+          +--------------------+          +--------------------+
  | restaurant-service   |          |                    |          |                    |
  | .yml                 |  đọc     |  Nhận file YAML    |  HTTP    |  Nhận cấu hình     |
  |                      | -------> |  Thấy tiền tố      | -------> |  password đã là    |
  | password:            |          |  {cipher}          |          |  chuỗi rõ, dùng    |
  |  {cipher}AQAxZ3J0... |          |  Giải mã bằng      |          |  ngay để kết nối   |
  |                      |          |  encrypt.key       |          |  CSDL              |
  +----------------------+          +--------------------+          +--------------------+
                                              ^
                                              |
                                    encrypt.key nạp từ
                                    biến môi trường hoặc
                                    keystore - KHÔNG
                                    nằm trong kho Git
```

Các bước cụ thể:

1. Config Server đọc file YAML từ kho Git.
2. Với mỗi giá trị bắt đầu bằng tiền tố `{cipher}`, nó lấy phần chuỗi phía sau
   và giải mã bằng khóa đã cấu hình.
3. Config Server trả về cho service giá trị **đã giải mã sẵn**.
4. Service nhận được `password: RestaurantPass123` như bình thường, hoàn toàn
   không cần biết gì về cơ chế mã hóa và không cần giữ khóa.

Nhờ đó, khóa giải mã chỉ tồn tại ở đúng một nơi là Config Server, thay vì phải
phân phát cho tất cả các service.

Trường hợp muốn service tự giải mã (ít dùng hơn), có thể đặt
`spring.cloud.config.server.encrypt.enabled: false` để Config Server trả về
nguyên chuỗi `{cipher}...`, khi đó mỗi service phải tự có khóa - cách này làm
tăng số nơi phải giữ khóa nên FoodX không dùng.

### 3.3. Cấu hình khóa cho Config Server

**Cách 1 - Khóa đối xứng, đơn giản, phù hợp môi trường học tập và dev:**

```yaml
# Trong application.yml của Config Server (KHÔNG phải trong config-repo)
encrypt:
  key: ${ENCRYPT_KEY}
```

Khóa được nạp từ biến môi trường khi chạy:

```bash
# Windows PowerShell
$env:ENCRYPT_KEY = "khoa-bi-mat-rat-dai-va-kho-doan-cua-foodx"
java -jar config-server.jar

# Linux / macOS
export ENCRYPT_KEY="khoa-bi-mat-rat-dai-va-kho-doan-cua-foodx"
java -jar config-server.jar
```

**Cách 2 - Khóa bất đối xứng bằng keystore, khuyến nghị cho môi trường thật:**

```bash
# Sinh cặp khóa RSA
keytool -genkeypair -alias foodx-config-key \
  -keyalg RSA -keysize 4096 \
  -dname "CN=FoodX Config Server,OU=Platform,O=FoodX,L=Ha Noi,C=VN" \
  -keypass "${KEY_SECRET}" \
  -keystore config-server.jks \
  -storepass "${KEYSTORE_PASSWORD}" \
  -validity 3650
```

```yaml
encrypt:
  key-store:
    location: file:/etc/foodx/config-server.jks
    password: ${KEYSTORE_PASSWORD}
    alias: foodx-config-key
    secret: ${KEY_SECRET}
```

Ưu điểm của khóa bất đối xứng: có thể phát khóa công khai cho đội phát triển để
họ tự mã hóa bí mật mới, trong khi khóa riêng dùng để giải mã chỉ nằm trên máy
chủ Config Server sản xuất.

### 3.4. Lệnh sinh bản mã và kiểm tra

Config Server phơi ra hai endpoint chuyên dụng:

```bash
# Mã hóa một giá trị - dùng kết quả để dán vào file cấu hình
curl -X POST http://localhost:8888/encrypt -d 'RestaurantPass123'
```

Kết quả trả về là một chuỗi base64, ví dụ:

```
AQAxZ3J0UmVzdGF1cmFudFBhc3NFbmNyeXB0ZWRTYW1wbGVCYXNlNjRTdHJpbmc=
```

Sau đó dán vào file cấu hình, **có thêm tiền tố `{cipher}` và bọc trong dấu
nháy kép**:

```yaml
password: "{cipher}AQAxZ3J0UmVzdGF1cmFudFBhc3NFbmNyeXB0ZWRTYW1wbGVCYXNlNjRTdHJpbmc="
```

Kiểm tra ngược lại xem có giải mã đúng không:

```bash
curl -X POST http://localhost:8888/decrypt \
  -d 'AQAxZ3J0UmVzdGF1cmFudFBhc3NFbmNyeXB0ZWRTYW1wbGVCYXNlNjRTdHJpbmc='
# Kết quả mong đợi: RestaurantPass123
```

Kiểm chứng rằng service nhận được giá trị đã giải mã:

```bash
curl http://localhost:8888/restaurant-service/prod | jq '.propertySources[0].source["spring.datasource.password"]'
```

### 3.5. Những lưu ý bắt buộc khi dùng `{cipher}`

1. **Khóa mã hóa tuyệt đối không nằm trong kho cấu hình.** Nếu khóa và bản mã
   nằm cùng một chỗ thì việc mã hóa mất hoàn toàn ý nghĩa, giống như khóa cửa
   rồi treo chìa ngay trên nắm đấm cửa. Khóa phải nạp qua biến môi trường,
   keystore đặt ngoài kho, hoặc hệ thống quản lý bí mật.
2. **Luôn bọc giá trị trong dấu nháy kép.** Chuỗi base64 có thể chứa ký tự `=`,
   `+`, `/` khiến trình phân tích YAML hiểu sai nếu không có nháy.
3. **Endpoint `/encrypt` và `/decrypt` phải được bảo vệ.** Nếu để mở, ai cũng
   gọi được `/decrypt` để lấy lại mật khẩu gốc. Cần bật Spring Security cho
   Config Server và chỉ cho phép truy cập từ mạng nội bộ.
4. **Mỗi môi trường dùng một khóa riêng.** Khóa của dev không giải mã được bí
   mật của prod. Nhờ đó lập trình viên có khóa dev vẫn không đọc được mật khẩu
   sản xuất.
5. **Mã hóa cả bí mật của môi trường dev.** Trong bài làm này, kể cả file
   `restaurant-service-dev.yml` cũng dùng `{cipher}`. Thói quen tốt phải được
   áp dụng đồng nhất, không có ngoại lệ.
6. **Mã hóa mọi loại bí mật, không chỉ mật khẩu CSDL.** Khóa API cổng thanh
   toán, khóa dịch vụ bản đồ, cấu hình SASL của Kafka đều phải mã hóa.
7. **Mật khẩu đã từng bị commit chữ thô phải được đổi ngay.** Mã hóa lại giá
   trị cũ không đủ, vì giá trị cũ vẫn nằm trong lịch sử Git.

---

## 4. So sánh các phương án quản lý bí mật

| Tiêu chí | Chữ thô trong Git | `{cipher}` của Config Server | Biến môi trường | HashiCorp Vault | AWS Secrets Manager |
|---|---|---|---|---|---|
| Mức độ an toàn | Rất thấp | Trung bình khá | Trung bình | Rất cao | Rất cao |
| Độ phức tạp triển khai | Không có | Thấp | Thấp | Cao | Trung bình |
| Chi phí | Không | Không | Không | Cao (tự vận hành) | Trả theo bí mật/tháng |
| Bí mật có nằm trong Git không | Có, chữ thô | Có, nhưng đã mã hóa | Không | Không | Không |
| Xoay vòng bí mật | Thủ công, rất khó | Thủ công, phải commit lại | Thủ công, phải triển khai lại | Tự động, có hỗ trợ động | Tự động theo lịch |
| Nhật ký kiểm toán | Không có | Không có | Không có | Đầy đủ, chi tiết | Đầy đủ qua CloudTrail |
| Phân quyền theo bí mật | Không | Không, ai có khóa đọc được hết | Theo quyền tiến trình | Rất chi tiết theo chính sách | Chi tiết theo IAM |
| Thu hồi tức thời | Không thể | Phải đổi khóa và mã lại tất cả | Phải triển khai lại | Có, tức thì | Có, tức thì |
| Bí mật động (sinh theo phiên) | Không | Không | Không | Có | Một phần |
| Phụ thuộc hạ tầng ngoài | Không | Không | Không | Có, cụm Vault | Có, khóa chặt vào AWS |
| Cập nhật nóng khi đổi giá trị | Không | Có, qua `/actuator/refresh` | Không, phải khởi động lại | Có | Có |
| Phù hợp với FoodX ở giai đoạn này | Không bao giờ | **Có - đang chọn** | Bổ trợ cho khóa gốc | Giai đoạn sau khi mở rộng | Nếu chuyển hẳn lên AWS |

### Nhận xét cho từng phương án

**Chữ thô trong Git** - không có tình huống nào chấp nhận được, kể cả với môi
trường dev, kể cả với dữ liệu giả. Thói quen xấu sẽ lan sang môi trường thật.

**`{cipher}` của Config Server** - đây là phương án FoodX chọn ở giai đoạn hiện
tại. Ưu điểm là không cần thêm hạ tầng nào, tích hợp sẵn với Spring Cloud
Config, đủ để chặn rủi ro lớn nhất là "ai clone kho cũng đọc được mật khẩu".
Hạn chế: bảo mật quy về một khóa duy nhất, không có nhật ký kiểm toán, và việc
xoay vòng vẫn phải làm thủ công.

**Biến môi trường** - không nên dùng thay thế mà nên dùng **bổ trợ**, cụ thể là
để nạp chính `encrypt.key` cho Config Server. Nếu dùng biến môi trường cho mọi
bí mật thì lại đánh mất lợi ích của cấu hình tập trung, vì cấu hình quay về nằm
rải rác ở từng script triển khai.

**HashiCorp Vault** - phương án mạnh nhất về mặt bảo mật: phân quyền chi tiết,
nhật ký kiểm toán đầy đủ, hỗ trợ bí mật động có thời hạn ngắn. Spring Cloud có
sẵn `spring-cloud-starter-vault-config`. Đổi lại, phải vận hành thêm một cụm
dịch vụ có tính sẵn sàng cao, cần quy trình unseal, sao lưu và khôi phục.
Phù hợp khi FoodX đã mở rộng đủ lớn.

**AWS Secrets Manager** - lựa chọn tốt nếu FoodX chạy toàn bộ trên AWS: tích
hợp sẵn với IAM, tự động xoay vòng bí mật cho RDS, kiểm toán qua CloudTrail.
Nhược điểm là khóa chặt vào một nhà cung cấp và tính phí theo từng bí mật.

### Lộ trình đề xuất cho FoodX

| Giai đoạn | Phương án | Lý do |
|---|---|---|
| Hiện tại | `{cipher}` + `encrypt.key` nạp qua biến môi trường | Chặn được rủi ro lớn nhất, không tốn thêm hạ tầng |
| Trung hạn | `{cipher}` với keystore bất đối xứng, tách khóa theo môi trường | Đội phát triển tự mã hóa được mà không chạm khóa prod |
| Dài hạn | Chuyển sang Vault hoặc Secrets Manager | Cần nhật ký kiểm toán và xoay vòng tự động khi số service tăng |

---

## 5. Kết luận

1. Mật khẩu `RestaurantPass123` trong file gốc phải được coi là **đã bị lộ vĩnh
   viễn**. Bước xử lý bắt buộc đầu tiên không phải là mã hóa nó, mà là **đổi
   mật khẩu đó trên cơ sở dữ liệu**, sau đó mới mã hóa giá trị mới.
2. Cú pháp `{cipher}...` cho phép lưu bí mật ngay trong kho Git một cách an
   toàn, vì việc giải mã do Config Server đảm nhiệm bằng khóa nằm ngoài kho.
3. Nguyên tắc bất di bất dịch: **khóa mã hóa không bao giờ nằm cùng chỗ với bản
   mã**. Khóa nạp qua biến môi trường hoặc keystore đặt ngoài kho cấu hình.
4. Áp dụng đồng nhất cho mọi môi trường và mọi loại bí mật, kể cả dev, kể cả
   khóa API của bên thứ ba.
5. `{cipher}` là điểm khởi đầu hợp lý chứ chưa phải đích đến. Khi hệ thống lớn
   lên và cần nhật ký kiểm toán cùng khả năng xoay vòng tự động, nên chuyển
   sang Vault hoặc AWS Secrets Manager.
6. Nên bổ sung công cụ quét bí mật (gitleaks, truffleHog) vào git hook và quy
   trình CI của kho cấu hình để chặn ngay từ đầu việc commit chữ thô, thay vì
   phát hiện sau khi đã lộ.
