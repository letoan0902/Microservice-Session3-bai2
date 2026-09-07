# -*- coding: utf-8 -*-
"""
build_docx.py

Sinh file Word docs/Bao-cao-Bai2.docx cho bài tập:
    Bài 2 - Tổ chức Centralized Configuration cho hệ thống FoodX
    Môn Microservice - Session 03

Cách chạy:
    pip install python-docx
    python tools/build_docx.py

Script đọc trực tiếp ba file cấu hình đã sửa trong config-repo/ và file lỗi gốc
trong docs/legacy/ để nhúng vào báo cáo, nhờ đó nội dung file Word luôn khớp
với nội dung thật của kho cấu hình.
"""

import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Cm

# Bảo đảm in được tiếng Việt có dấu ra console Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

GOC = Path(__file__).resolve().parent.parent
THU_MUC_CONFIG = GOC / "config-repo"
THU_MUC_DOCS = GOC / "docs"
FILE_XUAT = THU_MUC_DOCS / "Bao-cao-Bai2.docx"

MAU_XANH_DAM = RGBColor(0x1F, 0x3A, 0x5F)
MAU_XAM = RGBColor(0x44, 0x44, 0x44)
MAU_DO = RGBColor(0xB0, 0x1B, 0x1B)
MAU_XANH_LA = RGBColor(0x1B, 0x6B, 0x2E)


# ---------------------------------------------------------------------------
# Các hàm tiện ích định dạng
# ---------------------------------------------------------------------------

def doc_file(duong_dan: Path) -> str:
    """Đọc nội dung một file văn bản, trả về chuỗi rỗng nếu không tồn tại."""
    if not duong_dan.exists():
        print(f"  Cảnh báo: không tìm thấy {duong_dan}")
        return f"(Không tìm thấy file {duong_dan.name})"
    return duong_dan.read_text(encoding="utf-8")


def dat_font_mac_dinh(tai_lieu: Document) -> None:
    """Đặt font mặc định cho toàn bộ tài liệu."""
    kieu = tai_lieu.styles["Normal"]
    kieu.font.name = "Times New Roman"
    kieu.font.size = Pt(12)
    kieu.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    kieu.paragraph_format.space_after = Pt(6)
    kieu.paragraph_format.line_spacing = 1.15


def them_tieu_de(tai_lieu: Document, van_ban: str, cap: int = 1):
    """Thêm một tiêu đề với màu và cỡ chữ tự đặt."""
    doan = tai_lieu.add_heading(level=cap)
    lan = doan.add_run(van_ban)
    lan.font.name = "Times New Roman"
    lan.font.color.rgb = MAU_XANH_DAM
    lan.font.bold = True
    lan.font.size = Pt({1: 18, 2: 15, 3: 13}.get(cap, 12))
    return doan


def them_doan(tai_lieu: Document, van_ban: str, dam: bool = False,
              nghieng: bool = False, mau: RGBColor = None, co_chu: int = 12):
    """Thêm một đoạn văn thường."""
    doan = tai_lieu.add_paragraph()
    lan = doan.add_run(van_ban)
    lan.font.name = "Times New Roman"
    lan.font.size = Pt(co_chu)
    lan.bold = dam
    lan.italic = nghieng
    if mau is not None:
        lan.font.color.rgb = mau
    doan.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return doan


def them_gach_dau_dong(tai_lieu: Document, van_ban: str, cap: int = 1):
    """Thêm một mục gạch đầu dòng."""
    kieu = "List Bullet" if cap == 1 else "List Bullet 2"
    doan = tai_lieu.add_paragraph(style=kieu)
    lan = doan.add_run(van_ban)
    lan.font.name = "Times New Roman"
    lan.font.size = Pt(12)
    return doan


def them_danh_sach_so(tai_lieu: Document, van_ban: str):
    """Thêm một mục danh sách đánh số."""
    doan = tai_lieu.add_paragraph(style="List Number")
    lan = doan.add_run(van_ban)
    lan.font.name = "Times New Roman"
    lan.font.size = Pt(12)
    return doan


def to_nen(o_bang, ma_mau: str) -> None:
    """Tô màu nền cho một ô của bảng."""
    thuoc_tinh = o_bang._tc.get_or_add_tcPr()
    to = OxmlElement("w:shd")
    to.set(qn("w:val"), "clear")
    to.set(qn("w:color"), "auto")
    to.set(qn("w:fill"), ma_mau)
    thuoc_tinh.append(to)


def them_khoi_ma(tai_lieu: Document, noi_dung: str, co_chu: int = 8) -> None:
    """Thêm một khối mã nguồn với nền xám và font đều nét."""
    bang = tai_lieu.add_table(rows=1, cols=1)
    bang.style = "Table Grid"
    o = bang.rows[0].cells[0]
    to_nen(o, "F4F4F4")
    o.paragraphs[0].text = ""
    dong_dau = True
    for dong in noi_dung.rstrip("\n").split("\n"):
        doan = o.paragraphs[0] if dong_dau else o.add_paragraph()
        dong_dau = False
        lan = doan.add_run(dong if dong else " ")
        lan.font.name = "Consolas"
        lan.font.size = Pt(co_chu)
        lan.element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
        doan.paragraph_format.space_after = Pt(0)
        doan.paragraph_format.space_before = Pt(0)
        doan.paragraph_format.line_spacing = 1.0
    tai_lieu.add_paragraph()


def them_bang(tai_lieu: Document, tieu_de_cot, cac_dong, co_chu: int = 10):
    """Thêm một bảng có hàng tiêu đề được tô màu."""
    bang = tai_lieu.add_table(rows=1, cols=len(tieu_de_cot))
    bang.style = "Table Grid"
    bang.alignment = WD_TABLE_ALIGNMENT.CENTER

    hang_tieu_de = bang.rows[0]
    for chi_so, ten_cot in enumerate(tieu_de_cot):
        o = hang_tieu_de.cells[chi_so]
        to_nen(o, "1F3A5F")
        o.paragraphs[0].text = ""
        lan = o.paragraphs[0].add_run(ten_cot)
        lan.font.name = "Times New Roman"
        lan.font.size = Pt(co_chu)
        lan.font.bold = True
        lan.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for chi_so_dong, dong in enumerate(cac_dong):
        cac_o = bang.add_row().cells
        for chi_so_cot, gia_tri in enumerate(dong):
            o = cac_o[chi_so_cot]
            if chi_so_dong % 2 == 1:
                to_nen(o, "EEF2F7")
            o.paragraphs[0].text = ""
            lan = o.paragraphs[0].add_run(str(gia_tri))
            lan.font.name = "Times New Roman"
            lan.font.size = Pt(co_chu)
    tai_lieu.add_paragraph()
    return bang


def them_ghi_chu(tai_lieu: Document, nhan: str, noi_dung: str,
                 mau: RGBColor = MAU_DO) -> None:
    """Thêm một dòng ghi chú nổi bật dạng 'Nhãn: nội dung'."""
    doan = tai_lieu.add_paragraph()
    lan_nhan = doan.add_run(f"{nhan}: ")
    lan_nhan.font.name = "Times New Roman"
    lan_nhan.font.size = Pt(12)
    lan_nhan.bold = True
    lan_nhan.font.color.rgb = mau
    lan_noi_dung = doan.add_run(noi_dung)
    lan_noi_dung.font.name = "Times New Roman"
    lan_noi_dung.font.size = Pt(12)
    doan.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


# ---------------------------------------------------------------------------
# Các phần nội dung của báo cáo
# ---------------------------------------------------------------------------

def trang_bia(tai_lieu: Document) -> None:
    for _ in range(4):
        tai_lieu.add_paragraph()

    doan = tai_lieu.add_paragraph()
    doan.alignment = WD_ALIGN_PARAGRAPH.CENTER
    lan = doan.add_run("BÁO CÁO BÀI TẬP")
    lan.font.name = "Times New Roman"
    lan.font.size = Pt(16)
    lan.bold = True
    lan.font.color.rgb = MAU_XAM

    doan = tai_lieu.add_paragraph()
    doan.alignment = WD_ALIGN_PARAGRAPH.CENTER
    lan = doan.add_run("MÔN MICROSERVICE")
    lan.font.name = "Times New Roman"
    lan.font.size = Pt(16)
    lan.bold = True
    lan.font.color.rgb = MAU_XAM

    tai_lieu.add_paragraph()

    doan = tai_lieu.add_paragraph()
    doan.alignment = WD_ALIGN_PARAGRAPH.CENTER
    lan = doan.add_run("BÀI 2")
    lan.font.name = "Times New Roman"
    lan.font.size = Pt(26)
    lan.bold = True
    lan.font.color.rgb = MAU_XANH_DAM

    doan = tai_lieu.add_paragraph()
    doan.alignment = WD_ALIGN_PARAGRAPH.CENTER
    lan = doan.add_run("TỔ CHỨC CENTRALIZED CONFIGURATION\nCHO HỆ THỐNG FOODX")
    lan.font.name = "Times New Roman"
    lan.font.size = Pt(20)
    lan.bold = True
    lan.font.color.rgb = MAU_XANH_DAM

    for _ in range(3):
        tai_lieu.add_paragraph()

    thong_tin = [
        ("Session", "03 - Configuration, Service Registration và Discovery"),
        ("Cấp độ", "Vận dụng cơ bản"),
        ("Nền tảng", "Spring Boot 3.2.5, Spring Cloud 2023.0.1, Java 17"),
        ("Hệ thống", "FoodX - Nền tảng đặt và giao đồ ăn"),
        ("Số service", "3 service: restaurant-service, order-service, delivery-service"),
        ("Kho cấu hình", "foodx-config-repo (12 file YAML)"),
    ]
    for nhan, gia_tri in thong_tin:
        doan = tai_lieu.add_paragraph()
        doan.alignment = WD_ALIGN_PARAGRAPH.CENTER
        lan_nhan = doan.add_run(f"{nhan}: ")
        lan_nhan.font.name = "Times New Roman"
        lan_nhan.font.size = Pt(12)
        lan_nhan.bold = True
        lan_gia_tri = doan.add_run(gia_tri)
        lan_gia_tri.font.name = "Times New Roman"
        lan_gia_tri.font.size = Pt(12)

    tai_lieu.add_page_break()


def phan_muc_luc(tai_lieu: Document) -> None:
    them_tieu_de(tai_lieu, "MỤC LỤC", 1)
    muc = [
        "1. Mục tiêu kiến thức và tình huống nghiệp vụ",
        "2. Phân tích lỗi đặt tên file cấu hình",
        "3. Phân tích rủi ro lưu mật khẩu dạng chữ thô",
        "4. Cấu trúc kho cấu hình tập trung của FoodX",
        "5. Ba file cấu hình đã sửa",
        "6. Cấu hình phía service để lấy config",
        "7. Hướng dẫn kiểm tra bằng curl và actuator",
        "8. Kết luận và bài học rút ra",
    ]
    for dong in muc:
        doan = tai_lieu.add_paragraph()
        lan = doan.add_run(dong)
        lan.font.name = "Times New Roman"
        lan.font.size = Pt(12)
    tai_lieu.add_page_break()


def phan_1_muc_tieu(tai_lieu: Document) -> None:
    them_tieu_de(tai_lieu, "1. Mục tiêu kiến thức và tình huống nghiệp vụ", 1)

    them_tieu_de(tai_lieu, "1.1. Mục tiêu kiến thức", 2)
    them_doan(tai_lieu, "Vận dụng đúng nguyên tắc Centralized Configuration:")
    them_gach_dau_dong(tai_lieu, "Tách cấu hình ra khỏi source code, đưa vào một kho Git dùng chung.")
    them_gach_dau_dong(tai_lieu, "Tổ chức file cấu hình đúng quy ước để Config Server phục vụ đúng service.")
    them_gach_dau_dong(tai_lieu, "Bảo vệ bí mật trong kho cấu hình bằng cú pháp mã hóa {cipher}.")

    them_tieu_de(tai_lieu, "1.2. Tình huống nghiệp vụ", 2)
    them_doan(
        tai_lieu,
        "FoodX chuẩn bị tách cấu hình ra khỏi source code sang một Git repository "
        "dùng chung. Một thực tập sinh đã tạo thử file cấu hình cho restaurant-service "
        "nhưng mắc hai lỗi nghiêm trọng: đặt sai tên file và lưu mật khẩu ở dạng chữ thô. "
        "Nội dung file gốc trên kho Git như sau:"
    )
    them_khoi_ma(tai_lieu, doc_file(THU_MUC_DOCS / "legacy" / "config.yml.old").split(
        "# --- NỘI DUNG GỐC NGUYÊN VĂN CỦA THỰC TẬP SINH ------------------------------\n"
    )[-1])

    them_tieu_de(tai_lieu, "1.3. Bảng tóm tắt lỗi và cách sửa", 2)
    them_bang(
        tai_lieu,
        ["#", "Lỗi phát hiện", "Hậu quả", "Cách sửa"],
        [
            ["1",
             "Tên file config.yml không khớp spring.application.name (restaurant-service)",
             "Config Server không bao giờ đọc file, trả propertySources rỗng, service lỗi khởi tạo bean hoặc âm thầm dùng giá trị mặc định trong jar",
             "Đổi tên thành restaurant-service.yml, bổ sung bản -dev và -prod"],
            ["2",
             "Mật khẩu RestaurantPass123 lưu dạng chữ thô",
             "Ai clone kho cũng đọc được, lịch sử Git giữ vĩnh viễn, rò rỉ qua log và CI, vi phạm least privilege",
             "Mã hóa bằng POST /encrypt, lưu dạng {cipher}AQA..., khóa để ngoài kho"],
            ["3",
             "Không tách cấu hình theo profile",
             "Không phân biệt được dev và prod",
             "Tách thành {app}.yml, {app}-dev.yml, {app}-prod.yml"],
            ["4",
             "Không có lớp cấu hình dùng chung",
             "Cấu hình giống nhau bị lặp ở mọi service",
             "Bổ sung application.yml và application-{profile}.yml"],
        ],
        co_chu=9,
    )
    tai_lieu.add_page_break()


def phan_2_loi_ten_file(tai_lieu: Document) -> None:
    them_tieu_de(tai_lieu, "2. Phân tích lỗi đặt tên file cấu hình", 1)

    them_tieu_de(tai_lieu, "2.1. Mô tả lỗi", 2)
    them_doan(
        tai_lieu,
        "Nhìn qua thì file config.yml có vẻ hợp lệ: cú pháp YAML đúng, các khóa đều "
        "là khóa chuẩn của Spring Boot, giá trị cũng hợp lý. Chính vì vậy mà lỗi rất "
        "dễ bị bỏ sót khi duyệt mã. Vấn đề không nằm ở nội dung mà nằm ở tên file. "
        "Tên config.yml không khớp với spring.application.name của service. Service "
        "tự xưng tên là restaurant-service, nên theo quy ước của Spring Cloud Config "
        "Server, file cấu hình bắt buộc phải tên là restaurant-service.yml."
    )

    them_tieu_de(tai_lieu, "2.2. Quy ước đặt tên của Spring Cloud Config Server", 2)
    them_bang(
        tai_lieu,
        ["Dạng file", "Ý nghĩa", "Ví dụ cho restaurant-service"],
        [
            ["{application}.yml", "Cấu hình mặc định của một service, áp dụng cho mọi profile", "restaurant-service.yml"],
            ["{application}-{profile}.yml", "Cấu hình riêng của một service ở một profile", "restaurant-service-dev.yml"],
            ["application.yml", "Cấu hình dùng chung cho mọi service", "application.yml"],
            ["application-{profile}.yml", "Cấu hình dùng chung cho mọi service ở một profile", "application-dev.yml"],
        ],
    )
    them_doan(
        tai_lieu,
        "Trong đó {application} chính là giá trị của spring.application.name mà "
        "service khai báo, còn {profile} chính là giá trị của spring.profiles.active."
    )

    them_tieu_de(tai_lieu, "2.3. Endpoint và cơ chế tìm file của Config Server", 2)
    them_doan(tai_lieu, "Config Server phơi ra các endpoint theo dạng:")
    them_khoi_ma(tai_lieu,
                 "/{application}/{profile}\n"
                 "/{application}/{profile}/{label}\n"
                 "/{application}-{profile}.yml\n"
                 "/{label}/{application}-{profile}.yml\n"
                 "/{application}-{profile}.properties")
    them_doan(
        tai_lieu,
        "Khi restaurant-service khởi động với profile dev, nó gửi đúng một request "
        "GET /restaurant-service/dev. Config Server đi tìm đúng bốn file sau, theo "
        "thứ tự ưu tiên từ cao xuống thấp:"
    )
    them_bang(
        tai_lieu,
        ["Thứ tự", "Tên file được tìm", "Vai trò"],
        [
            ["1 (cao nhất)", "restaurant-service-dev.yml", "Riêng service, riêng profile"],
            ["2", "restaurant-service.yml", "Riêng service, chung mọi profile"],
            ["3", "application-dev.yml", "Chung mọi service, riêng profile dev"],
            ["4 (thấp nhất)", "application.yml", "Chung mọi service, chung mọi profile"],
        ],
    )
    them_ghi_chu(
        tai_lieu, "Điểm mấu chốt",
        "File config.yml không có mặt trong danh sách này. Config Server không hề "
        "biết đến sự tồn tại của nó và cũng không báo lỗi. Với Config Server, "
        "config.yml chỉ là một file vô nghĩa nằm trong kho Git."
    )

    them_tieu_de(tai_lieu, "2.4. Hậu quả khi Config Server không tìm thấy đúng file", 2)
    them_doan(
        tai_lieu,
        "Đây là phần nguy hiểm nhất: lỗi này không gây ra thông báo lỗi rõ ràng. "
        "Config Server trả về HTTP 200 với propertySources rỗng, chứ không trả 404."
    )
    them_khoi_ma(tai_lieu,
                 '{\n'
                 '  "name": "restaurant-service",\n'
                 '  "profiles": ["dev"],\n'
                 '  "label": null,\n'
                 '  "version": "a1b2c3d4e5f6",\n'
                 '  "propertySources": []\n'
                 '}')

    them_tieu_de(tai_lieu, "Hậu quả 1 - Service không khởi động được, lỗi khởi tạo bean", 3)
    them_doan(
        tai_lieu,
        "Vì spring.datasource.url không có giá trị, Spring Boot không dựng được "
        "DataSource bean và ứng dụng dừng lại với ngoại lệ:"
    )
    them_khoi_ma(tai_lieu,
                 "***************************\n"
                 "APPLICATION FAILED TO START\n"
                 "***************************\n\n"
                 "Description:\n"
                 "Failed to configure a DataSource: 'url' attribute is not specified\n"
                 "and no embedded datasource could be configured.\n\n"
                 "Reason: Failed to determine a suitable driver class")
    them_doan(
        tai_lieu,
        "Đây thực ra là kịch bản may mắn nhất vì lỗi lộ ra ngay. Đáng tiếc là lập "
        "trình viên thường hiểu nhầm nguyên nhân, đi kiểm tra cơ sở dữ liệu và mạng, "
        "trong khi lỗi thật nằm ở tên file trong kho cấu hình."
    )

    them_tieu_de(tai_lieu, "Hậu quả 2 - Service khởi động nhưng âm thầm dùng giá trị mặc định trong jar", 3)
    them_doan(
        tai_lieu,
        "Nếu trong src/main/resources/application.yml của service còn sót giá trị dự "
        "phòng, service sẽ khởi động bình thường, không một dòng cảnh báo. Nhật ký "
        "sạch sẽ, /actuator/health báo UP, API vẫn phản hồi, nhưng dữ liệu đang được "
        "ghi vào sai cơ sở dữ liệu. Lỗi chỉ lộ ra sau vài ngày khi khách hàng phản "
        "ánh, và lúc đó việc truy vết đã cực kỳ tốn kém."
    )

    them_tieu_de(tai_lieu, "Hậu quả 3 - Nguy hiểm nhất: chạy nhầm cấu hình dev trên prod", 3)
    them_doan(tai_lieu, "Khi lớp cấu hình riêng của service bị rỗng trên môi trường thật, có thể xảy ra:")
    them_gach_dau_dong(tai_lieu, "ddl-auto: update khiến Hibernate tự động sửa lược đồ cơ sở dữ liệu sản xuất.")
    them_gach_dau_dong(tai_lieu, "Toàn bộ endpoint quản trị bị phơi ra Internet, kể cả /actuator/heapdump chứa dữ liệu nhạy cảm.")
    them_gach_dau_dong(tai_lieu, "Các cờ tính năng thử nghiệm bị bật nhầm cho khách hàng thật.")
    them_gach_dau_dong(tai_lieu, "Timeout của dev (15 giây) áp lên prod, giữ luồng quá lâu, gây sập dây chuyền khi tải cao.")
    them_ghi_chu(tai_lieu, "Kết luận", "Một lỗi đặt tên file có thể dẫn tới sự cố toàn hệ thống.")

    them_tieu_de(tai_lieu, "2.5. Bảng so sánh trước và sau khi sửa", 2)
    them_bang(
        tai_lieu,
        ["Tiêu chí", "TRƯỚC (sai)", "SAU (đúng)"],
        [
            ["Tên file trong kho", "config.yml", "restaurant-service.yml"],
            ["spring.application.name", "restaurant-service", "restaurant-service"],
            ["Có khớp quy ước không", "Không khớp", "Khớp"],
            ["Config Server có đọc không", "Không bao giờ đọc", "Đọc và phục vụ đúng"],
            ["Kết quả GET /restaurant-service/dev", "propertySources rỗng", "4 nguồn cấu hình theo đúng thứ tự"],
            ["Mật khẩu", "RestaurantPass123 (chữ thô)", "{cipher}AQAxZ3J0... (đã mã hóa)"],
            ["server.port", "8085 (giữ nguyên)", "8085 (đề bài không yêu cầu đổi cổng)"],
            ["Tách theo profile", "Không có", "Có -dev.yml và -prod.yml"],
            ["Timeout, cờ tính năng", "Không có", "Đầy đủ theo nghiệp vụ nhà hàng"],
            ["Số file trong kho", "1 file duy nhất, sai tên", "12 file đúng quy ước cho 3 service"],
        ],
        co_chu=9,
    )
    tai_lieu.add_page_break()


def phan_3_bao_mat(tai_lieu: Document) -> None:
    them_tieu_de(tai_lieu, "3. Phân tích rủi ro lưu mật khẩu dạng chữ thô", 1)

    them_tieu_de(tai_lieu, "3.1. Mô tả lỗi", 2)
    them_doan(
        tai_lieu,
        "Chuỗi RestaurantPass123 là mật khẩu truy cập cơ sở dữ liệu restaurants_db "
        "chứa toàn bộ dữ liệu nhà hàng, thực đơn và giá món của FoodX. Nó đang nằm "
        "nguyên văn trong một kho Git dùng chung cho cả đội. Đáng chú ý là chính dòng "
        "chú thích trong file đã ghi rõ không mã hóa - người viết biết đây là vấn đề "
        "nhưng vẫn commit lên."
    )

    them_tieu_de(tai_lieu, "3.2. Bảy nhóm rủi ro", 2)
    them_danh_sach_so(
        tai_lieu,
        "Ai clone được kho là đọc được mật khẩu. Bao gồm mọi lập trình viên trong "
        "công ty, thực tập sinh, nhà thầu ngoài, và cả nhân viên đã nghỉ việc còn giữ "
        "bản clone trên máy cá nhân. Vi phạm trực tiếp nguyên tắc least privilege.")
    them_danh_sach_so(
        tai_lieu,
        "Lịch sử Git giữ mật khẩu vĩnh viễn. Kể cả khi sau này sửa lại, ai cũng lấy "
        "được bằng git show hoặc git log -S. Muốn xóa thật phải viết lại toàn bộ lịch "
        "sử, làm hỏng mọi bản clone, và vẫn không xử lý được các bản fork và sao lưu.")
    them_danh_sach_so(
        tai_lieu,
        "Rò rỉ qua nhật ký CI/CD, endpoint /actuator/env, /actuator/heapdump, log "
        "ngoại lệ, chia sẻ màn hình, ảnh chụp đính kèm phiếu lỗi, công cụ tìm kiếm mã "
        "và các bản sao lưu.")
    them_danh_sach_so(
        tai_lieu,
        "Không xoay vòng được. Chi phí tìm hết mọi nơi mật khẩu xuất hiện quá cao "
        "khiến đội ngũ né tránh việc đổi định kỳ, mật khẩu bị dùng nguyên nhiều năm.")
    them_danh_sach_so(
        tai_lieu,
        "Không có nhật ký kiểm toán. Không trả lời được câu hỏi ai đã đọc mật khẩu "
        "này và vào lúc nào, vì git clone không để lại dấu vết.")
    them_danh_sach_so(
        tai_lieu,
        "Kho có thể bị lộ ra ngoài do cấu hình sai quyền hoặc tài khoản bị chiếm, dẫn "
        "tới mất toàn bộ dữ liệu nhà hàng, thực đơn và giá món.")
    them_danh_sach_so(
        tai_lieu,
        "Vi phạm chuẩn tuân thủ. FoodX xử lý thanh toán nên chịu ràng buộc PCI DSS; "
        "lưu thông tin xác thực chữ thô trong kho mã nguồn có thể dẫn tới trượt kiểm "
        "toán và mất quyền xử lý thanh toán thẻ.")

    them_tieu_de(tai_lieu, "3.3. Bảng đánh giá mức độ rủi ro", 2)
    them_bang(
        tai_lieu,
        ["Rủi ro", "Mức độ", "Khả năng xảy ra", "Hệ quả với FoodX"],
        [
            ["Người trong công ty đọc được", "Cao", "Chắc chắn", "Mọi lập trình viên chạm được CSDL nhà hàng"],
            ["Lịch sử Git giữ vĩnh viễn", "Rất cao", "Chắc chắn", "Không thể xóa, buộc phải đổi mật khẩu"],
            ["Rò rỉ qua log và CI", "Cao", "Rất dễ", "Mật khẩu lan sang hệ thống bảo vệ thấp hơn"],
            ["Không xoay vòng được", "Trung bình", "Chắc chắn", "Mật khẩu dùng nhiều năm không kiểm soát"],
            ["Không có nhật ký kiểm toán", "Trung bình", "Chắc chắn", "Không điều tra được khi có sự cố"],
            ["Kho bị lộ ra ngoài", "Rất cao", "Ít nhưng có thật", "Mất toàn bộ dữ liệu nhà hàng"],
            ["Vi phạm PCI DSS", "Cao", "Khi bị kiểm toán", "Bị phạt, mất quyền xử lý thanh toán"],
        ],
        co_chu=9,
    )

    them_tieu_de(tai_lieu, "3.4. Cách sửa bằng cú pháp {cipher}", 2)
    them_khoi_ma(tai_lieu,
                 "spring:\n"
                 "  datasource:\n"
                 "    url: jdbc:mysql://foodx-cluster.local:3306/restaurants_db?useSSL=true\n"
                 "    username: restaurant_service_user\n"
                 "    # Mật khẩu đã được mã hóa bằng POST /encrypt của Config Server\n"
                 '    password: "{cipher}AQAxZ3J0UmVzdGF1cmFudFBhc3NFbmNyeXB0ZWRTYW1wbGU="')
    them_ghi_chu(
        tai_lieu, "Lưu ý về bài làm này",
        "Chuỗi sau {cipher} trong toàn bộ kho config-repo là chuỗi base64 giả lập, "
        "chỉ nhằm minh họa đúng cú pháp theo yêu cầu của đề bài. Trong dự án thật, "
        "chuỗi này phải được sinh ra bằng chính Config Server của hệ thống."
    )

    them_tieu_de(tai_lieu, "3.5. Cơ chế encrypt và decrypt", 2)
    them_doan(
        tai_lieu,
        "Điểm cốt lõi cần hiểu: việc giải mã diễn ra ở phía Config Server, không phải "
        "ở phía service. Config Server đọc file YAML từ kho Git, thấy giá trị bắt đầu "
        "bằng tiền tố {cipher} thì giải mã bằng khóa đã cấu hình, rồi trả về cho "
        "service giá trị đã giải mã sẵn. Nhờ đó khóa giải mã chỉ tồn tại ở đúng một "
        "nơi là Config Server, thay vì phải phân phát cho tất cả các service."
    )
    them_khoi_ma(tai_lieu,
                 "  Kho Git                Config Server            restaurant-service\n"
                 " +-----------+         +------------------+      +-------------------+\n"
                 " | password: |  đọc    | Thấy tiền tố     | HTTP | password đã là    |\n"
                 " | {cipher}  |-------->| {cipher}, giải mã|----->| chuỗi rõ, dùng    |\n"
                 " | AQAxZ3J0..|         | bằng encrypt.key |      | ngay để kết nối   |\n"
                 " +-----------+         +------------------+      +-------------------+\n"
                 "                                ^\n"
                 "                       encrypt.key nạp từ biến môi trường\n"
                 "                       hoặc keystore - KHÔNG nằm trong kho Git")

    them_tieu_de(tai_lieu, "3.6. Lệnh sinh bản mã và cấu hình khóa", 2)
    them_khoi_ma(tai_lieu,
                 "# Mã hóa một giá trị, dùng kết quả để dán vào file cấu hình\n"
                 "curl -X POST http://localhost:8888/encrypt -d 'RestaurantPass123'\n"
                 "# Kết quả: AQAxZ3J0UmVzdGF1cmFudFBhc3NFbmNyeXB0ZWRTYW1wbGU=\n\n"
                 "# Kiểm tra ngược lại\n"
                 "curl -X POST http://localhost:8888/decrypt -d 'AQAxZ3J0...'\n"
                 "# Kết quả: RestaurantPass123")
    them_doan(tai_lieu, "Khóa được khai báo trong application.yml của chính Config Server:")
    them_khoi_ma(tai_lieu,
                 "# Cách 1 - khóa đối xứng, phù hợp môi trường học tập và dev\n"
                 "encrypt:\n"
                 "  key: ${ENCRYPT_KEY}\n\n"
                 "# Cách 2 - khóa bất đối xứng bằng keystore, khuyến nghị cho prod\n"
                 "encrypt:\n"
                 "  key-store:\n"
                 "    location: file:/etc/foodx/config-server.jks\n"
                 "    password: ${KEYSTORE_PASSWORD}\n"
                 "    alias: foodx-config-key\n"
                 "    secret: ${KEY_SECRET}")

    them_tieu_de(tai_lieu, "3.7. Bảy lưu ý bắt buộc khi dùng {cipher}", 2)
    them_danh_sach_so(tai_lieu, "Khóa mã hóa tuyệt đối không nằm trong kho cấu hình, nếu không việc mã hóa mất hoàn toàn ý nghĩa.")
    them_danh_sach_so(tai_lieu, "Luôn bọc giá trị trong dấu nháy kép vì chuỗi base64 có thể chứa ký tự =, + và /.")
    them_danh_sach_so(tai_lieu, "Bảo vệ endpoint /encrypt và /decrypt, chỉ cho truy cập từ mạng nội bộ.")
    them_danh_sach_so(tai_lieu, "Mỗi môi trường dùng một khóa riêng, khóa dev không giải mã được bí mật prod.")
    them_danh_sach_so(tai_lieu, "Mã hóa cả bí mật của môi trường dev, không có ngoại lệ.")
    them_danh_sach_so(tai_lieu, "Mã hóa mọi loại bí mật: khóa cổng thanh toán, khóa dịch vụ bản đồ, cấu hình SASL của Kafka.")
    them_danh_sach_so(tai_lieu, "Mật khẩu đã từng bị commit chữ thô phải được đổi ngay, mã hóa lại giá trị cũ là không đủ.")

    them_tieu_de(tai_lieu, "3.8. So sánh các phương án quản lý bí mật", 2)
    them_bang(
        tai_lieu,
        ["Tiêu chí", "Chữ thô", "{cipher}", "Biến môi trường", "Vault", "AWS Secrets Manager"],
        [
            ["Mức độ an toàn", "Rất thấp", "Trung bình khá", "Trung bình", "Rất cao", "Rất cao"],
            ["Độ phức tạp triển khai", "Không có", "Thấp", "Thấp", "Cao", "Trung bình"],
            ["Chi phí", "Không", "Không", "Không", "Cao", "Theo bí mật/tháng"],
            ["Bí mật nằm trong Git", "Có, chữ thô", "Có, đã mã hóa", "Không", "Không", "Không"],
            ["Xoay vòng bí mật", "Rất khó", "Thủ công", "Thủ công", "Tự động", "Tự động"],
            ["Nhật ký kiểm toán", "Không", "Không", "Không", "Đầy đủ", "Qua CloudTrail"],
            ["Phân quyền theo bí mật", "Không", "Không", "Theo tiến trình", "Rất chi tiết", "Theo IAM"],
            ["Thu hồi tức thời", "Không thể", "Phải mã lại hết", "Phải triển khai lại", "Có", "Có"],
            ["Cập nhật nóng", "Không", "Có, qua refresh", "Không", "Có", "Có"],
            ["Phù hợp FoodX hiện tại", "Không bao giờ", "ĐANG CHỌN", "Bổ trợ khóa gốc", "Giai đoạn sau", "Nếu lên AWS"],
        ],
        co_chu=8,
    )
    tai_lieu.add_page_break()


def phan_4_cau_truc(tai_lieu: Document) -> None:
    them_tieu_de(tai_lieu, "4. Cấu trúc kho cấu hình tập trung của FoodX", 1)

    them_tieu_de(tai_lieu, "4.1. Sơ đồ cây thư mục", 2)
    them_doan(
        tai_lieu,
        "Kho Git cấu hình tập trung đặt tại "
        "https://git.foodx.local/platform/foodx-config-repo với cấu trúc phẳng gồm "
        "12 file YAML: 3 file chung và 9 file riêng cho 3 service."
    )
    them_khoi_ma(tai_lieu,
                 "foodx-config-repo/\n"
                 "|\n"
                 "|-- application.yml                 <- LỚP 1: chung mọi service, mọi profile\n"
                 "|-- application-dev.yml             <- LỚP 2: chung mọi service, profile dev\n"
                 "|-- application-prod.yml            <- LỚP 2: chung mọi service, profile prod\n"
                 "|\n"
                 "|-- restaurant-service.yml          <- LỚP 3: riêng nhà hàng, cổng 8085\n"
                 "|-- restaurant-service-dev.yml      <- LỚP 4\n"
                 "|-- restaurant-service-prod.yml     <- LỚP 4\n"
                 "|\n"
                 "|-- order-service.yml               <- LỚP 3: riêng đơn hàng, cổng 8082\n"
                 "|-- order-service-dev.yml           <- LỚP 4\n"
                 "|-- order-service-prod.yml          <- LỚP 4\n"
                 "|\n"
                 "|-- delivery-service.yml            <- LỚP 3: riêng giao hàng, cổng 8083\n"
                 "|-- delivery-service-dev.yml        <- LỚP 4\n"
                 "`-- delivery-service-prod.yml       <- LỚP 4")

    them_tieu_de(tai_lieu, "4.2. Bảng ánh xạ service - file - profile", 2)
    them_bang(
        tai_lieu,
        ["Service", "spring.application.name", "Cổng", "Cơ sở dữ liệu", "File trong kho"],
        [
            ["Nhà hàng", "restaurant-service", "8085", "restaurants_db",
             "restaurant-service.yml, -dev.yml, -prod.yml"],
            ["Đơn hàng", "order-service", "8082", "orders_db",
             "order-service.yml, -dev.yml, -prod.yml"],
            ["Giao hàng", "delivery-service", "8083", "deliveries_db",
             "delivery-service.yml, -dev.yml, -prod.yml"],
            ["(dùng chung)", "-", "-", "-",
             "application.yml, application-dev.yml, application-prod.yml"],
        ],
        co_chu=9,
    )

    them_tieu_de(tai_lieu, "4.3. Thứ tự ưu tiên override", 2)
    them_khoi_ma(tai_lieu,
                 "application.yml < application-{profile}.yml < {app}.yml < {app}-{profile}.yml\n"
                 "  ưu tiên thấp nhất                                    ưu tiên cao nhất")
    them_doan(tai_lieu, "Quy tắc ghi nhớ: cấu hình càng cụ thể thì càng thắng. Ví dụ minh họa với khóa timeout khi restaurant-service chạy profile dev:")
    them_bang(
        tai_lieu,
        ["Lớp", "File", "Giá trị khai báo", "Kết quả"],
        [
            ["1", "application.yml", "connect-timeout-ms: 3000", "Bị ghi đè"],
            ["2", "application-dev.yml", "connect-timeout-ms: 10000", "Bị ghi đè"],
            ["3", "restaurant-service.yml", "connect-timeout-ms: 3000", "Bị ghi đè"],
            ["4", "restaurant-service-dev.yml", "connect-timeout-ms: 10000", "THẮNG"],
        ],
    )

    them_tieu_de(tai_lieu, "4.4. Bảng ánh xạ request tới file được nạp", 2)
    them_bang(
        tai_lieu,
        ["Request tới Config Server", "Các file được nạp (ưu tiên cao xuống thấp)"],
        [
            ["GET /restaurant-service/dev",
             "restaurant-service-dev.yml, restaurant-service.yml, application-dev.yml, application.yml"],
            ["GET /restaurant-service/prod",
             "restaurant-service-prod.yml, restaurant-service.yml, application-prod.yml, application.yml"],
            ["GET /order-service/prod",
             "order-service-prod.yml, order-service.yml, application-prod.yml, application.yml"],
            ["GET /delivery-service/dev",
             "delivery-service-dev.yml, delivery-service.yml, application-dev.yml, application.yml"],
            ["GET /config/dev (tên sai của thực tập sinh)",
             "Không file nào - propertySources rỗng"],
        ],
        co_chu=9,
    )

    them_tieu_de(tai_lieu, "4.5. Quy ước nhánh (label)", 2)
    them_doan(
        tai_lieu,
        "Label là nhánh, thẻ hoặc mã commit của kho Git, cho phép các môi trường "
        "khác nhau đọc các phiên bản cấu hình khác nhau từ cùng một kho."
    )
    them_bang(
        tai_lieu,
        ["Nhánh", "Mục đích", "Ai được ghi", "Cơ chế bảo vệ"],
        [
            ["main", "Cấu hình đang chạy ở môi trường thật", "Chỉ qua pull request đã duyệt", "Được bảo vệ, cần 2 người duyệt, cấm force-push"],
            ["staging", "Cấu hình môi trường kiểm thử", "Đội phát triển qua PR", "Cần 1 người duyệt"],
            ["dev", "Cấu hình môi trường phát triển", "Đội phát triển đẩy trực tiếp", "Không bảo vệ"],
            ["feature/*", "Thử nghiệm cấu hình một tính năng", "Người tạo nhánh", "Xóa sau khi merge"],
        ],
        co_chu=9,
    )
    them_doan(tai_lieu, "Phân biệt label và profile - hai khái niệm rất dễ nhầm:")
    them_bang(
        tai_lieu,
        ["", "label", "profile"],
        [
            ["Bản chất", "Nhánh/thẻ/commit của Git", "Hậu tố trong tên file cấu hình"],
            ["Trả lời câu hỏi", "Lấy phiên bản nào của kho", "Lấy file nào trong phiên bản đó"],
            ["Ví dụ giá trị", "main, dev, v1.4.2, a1b2c3d", "dev, prod, staging"],
            ["Khai báo ở đâu", "spring.cloud.config.label", "spring.profiles.active"],
        ],
    )

    them_tieu_de(tai_lieu, "4.6. Quy trình làm việc khi thay đổi cấu hình", 2)
    them_danh_sach_so(tai_lieu, "Tạo nhánh riêng và sửa file YAML, commit ghi rõ service nào, khóa nào, giá trị cũ sang giá trị mới.")
    them_danh_sach_so(tai_lieu, "Tạo pull request, người duyệt kiểm tra tên file, bí mật chữ thô, đúng profile, ngưỡng giá trị và cú pháp YAML.")
    them_danh_sach_so(tai_lieu, "Merge vào nhánh đích. Config Server đọc trực tiếp từ Git nên bản mới sẵn sàng ngay.")
    them_danh_sach_so(tai_lieu, "Làm mới cấu hình cho service bằng /actuator/refresh, hoặc /actuator/busrefresh qua Spring Cloud Bus.")
    them_danh_sach_so(tai_lieu, "Kiểm chứng bằng /actuator/env rằng service đã nhận giá trị mới và đúng nguồn.")
    them_doan(tai_lieu, "Lưu ý: không phải cấu hình nào cũng làm mới nóng được.")
    them_bang(
        tai_lieu,
        ["Loại cấu hình", "Refresh nóng được không"],
        [
            ["Khóa trong bean có @RefreshScope", "Có"],
            ["Khóa trong @ConfigurationProperties", "Có"],
            ["Mức ghi log (logging.level.*)", "Có"],
            ["Cờ tính năng", "Có"],
            ["server.port", "Không, phải khởi động lại"],
            ["spring.datasource.url, username, password", "Không (pool đã dựng), phải khởi động lại"],
            ["Kích thước pool HikariCP", "Không, phải khởi động lại"],
            ["spring.application.name", "Không, phải khởi động lại"],
        ],
        co_chu=9,
    )

    them_tieu_de(tai_lieu, "4.7. Phân quyền trên kho cấu hình", 2)
    them_bang(
        tai_lieu,
        ["Vai trò", "Đọc kho", "Ghi dev", "Ghi main", "Duyệt PR", "Giữ encrypt.key prod"],
        [
            ["Thực tập sinh", "Có", "Có", "Không", "Không", "Không"],
            ["Lập trình viên", "Có", "Có", "Chỉ qua PR", "Không", "Không"],
            ["Trưởng nhóm kỹ thuật", "Có", "Có", "Chỉ qua PR", "Có", "Không"],
            ["Đội nền tảng", "Có", "Có", "Có", "Có", "Có"],
            ["Đội bảo mật", "Có", "Không", "Không", "Có (bắt buộc với PR bí mật)", "Có"],
            ["Tài khoản Config Server", "Chỉ đọc", "Không", "Không", "Không", "-"],
            ["Tài khoản CI/CD", "Chỉ đọc", "Không", "Không", "Không", "Không"],
        ],
        co_chu=8,
    )
    tai_lieu.add_page_break()


def phan_5_ba_file_cau_hinh(tai_lieu: Document) -> None:
    them_tieu_de(tai_lieu, "5. Ba file cấu hình đã sửa", 1)
    them_doan(
        tai_lieu,
        "Dưới đây là nội dung đầy đủ của ba file cấu hình mặc định cho ba service "
        "của FoodX. Cả ba đều đặt đúng tên theo quy ước "
        "{spring.application.name}.yml và không chứa bất kỳ mật khẩu chữ thô nào. "
        "Mỗi service đều có datasource, server.port, timeout, cờ tính năng và các "
        "tham số nghiệp vụ riêng theo miền giao đồ ăn."
    )

    cac_file = [
        ("5.1. restaurant-service.yml (file đã sửa từ config.yml)",
         "restaurant-service.yml",
         "Đây chính là file sửa lỗi của thực tập sinh: đổi tên từ config.yml thành "
         "restaurant-service.yml, mã hóa mật khẩu bằng {cipher}, giữ nguyên cổng 8085 "
         "và bổ sung timeout, cờ tính năng cùng tham số nghiệp vụ nhà hàng."),
        ("5.2. order-service.yml",
         "order-service.yml",
         "Cấu hình cho service đặt đơn, cổng 8082, cơ sở dữ liệu orders_db. Ngoài "
         "datasource còn có cấu hình Kafka để phát sự kiện đơn hàng, các tham số "
         "nghiệp vụ về giá trị đơn, số món và phương thức thanh toán."),
        ("5.3. delivery-service.yml",
         "delivery-service.yml",
         "Cấu hình cho service giao hàng, cổng 8083, cơ sở dữ liệu deliveries_db. "
         "Có thêm Redis để lưu vị trí tài xế theo thời gian thực và các tham số "
         "nghiệp vụ về bán kính tìm tài xế, phí giao và thời gian cam kết."),
    ]

    for tieu_de, ten_file, mo_ta in cac_file:
        them_tieu_de(tai_lieu, tieu_de, 2)
        them_doan(tai_lieu, mo_ta)
        them_khoi_ma(tai_lieu, doc_file(THU_MUC_CONFIG / ten_file), co_chu=7)
        tai_lieu.add_page_break()

    them_tieu_de(tai_lieu, "5.4. Các file cấu hình theo profile", 2)
    them_doan(
        tai_lieu,
        "Ngoài ba file mặc định trên, kho còn có sáu file theo profile cho ba service "
        "và ba file dùng chung. Bảng sau tóm tắt điểm khác biệt chính giữa profile "
        "dev và prod:"
    )
    them_bang(
        tai_lieu,
        ["Khía cạnh", "Profile dev", "Profile prod"],
        [
            ["Cơ sở dữ liệu", "localhost, CSDL riêng có hậu tố _dev", "Cụm foodx-cluster.local, bật SSL bắt buộc"],
            ["Kích thước pool", "5 kết nối", "40 đến 60 kết nối tùy service"],
            ["Hibernate ddl-auto", "update", "validate"],
            ["Endpoint Actuator", "Mở toàn bộ", "Chỉ health, info, metrics, prometheus, refresh"],
            ["Mức ghi log", "DEBUG và TRACE", "WARN và INFO, ghi ra file"],
            ["Timeout", "Nới rộng để tiện gỡ lỗi", "Siết chặt để lỗi lộ ra nhanh"],
            ["Cờ tính năng thử nghiệm", "Bật để kiểm thử", "Tắt hoàn toàn"],
            ["Ngưỡng nghiệp vụ", "Hạ thấp để dễ tái hiện kịch bản", "Giá trị thật theo nghiệp vụ"],
            ["Dịch vụ bên ngoài", "Bản sandbox, không tốn hạn mức", "Bản chính thức"],
            ["Mật khẩu", "Vẫn dùng {cipher}, không ngoại lệ", "Dùng {cipher} với khóa riêng của prod"],
        ],
        co_chu=9,
    )
    tai_lieu.add_page_break()


def phan_6_client(tai_lieu: Document) -> None:
    them_tieu_de(tai_lieu, "6. Cấu hình phía service để lấy config", 1)

    them_doan(
        tai_lieu,
        "Nguyên tắc: file cấu hình nằm trong source code càng mỏng càng tốt, chỉ khai "
        "báo service tên gì, lấy cấu hình ở đâu và chạy profile nào. Nếu phải sửa file "
        "này để đổi một giá trị nghiệp vụ thì đã vi phạm nguyên tắc Centralized "
        "Configuration, vì mỗi lần đổi lại phải build và triển khai lại service."
    )

    them_tieu_de(tai_lieu, "6.1. Ranh giới giữa hai nơi", 2)
    them_bang(
        tai_lieu,
        ["Nằm trong source code", "Nằm trong kho cấu hình tập trung"],
        [
            ["spring.application.name - service tự xưng tên gì", "server.port"],
            ["spring.config.import - lấy cấu hình ở đâu", "spring.datasource.* kể cả mật khẩu đã mã hóa"],
            ["spring.profiles.active - chạy môi trường nào", "Timeout, cờ tính năng, tham số nghiệp vụ"],
            ["spring.cloud.config.label - nhánh nào", "Địa chỉ service liên quan, khóa API"],
        ],
    )

    them_tieu_de(tai_lieu, "6.2. Cách đúng với Spring Boot 3 - spring.config.import", 2)
    them_khoi_ma(tai_lieu, doc_file(
        GOC / "client-sample" / "restaurant-service" / "src" / "main" / "resources" / "application.yml"
    ), co_chu=7)

    them_tieu_de(tai_lieu, "6.3. Cách cũ với Spring Boot 2.x - bootstrap.yml", 2)
    them_ghi_chu(
        tai_lieu, "Quan trọng",
        "Spring Boot 3 dùng spring.config.import THAY CHO bootstrap.yml. Phần dưới "
        "chỉ để đối chiếu, không dùng trong bài làm này.",
        mau=MAU_DO,
    )
    them_khoi_ma(tai_lieu,
                 "spring:\n"
                 "  application:\n"
                 "    name: restaurant-service\n"
                 "  cloud:\n"
                 "    config:\n"
                 "      uri: http://localhost:8888\n"
                 "      label: main\n"
                 "      profile: dev\n"
                 "      fail-fast: true")
    them_doan(
        tai_lieu,
        "Cách cũ cần thêm phụ thuộc spring-cloud-starter-bootstrap và tạo ra một "
        "bootstrap context chạy trước ApplicationContext chính. Hai ngữ cảnh chồng "
        "nhau khiến thứ tự ưu tiên khó đoán và rất khó gỡ lỗi."
    )
    them_bang(
        tai_lieu,
        ["Tiêu chí", "bootstrap.yml (cũ)", "spring.config.import (mới)"],
        [
            ["Phiên bản", "Spring Boot 2.3 trở về trước", "Spring Boot 2.4 trở lên, bắt buộc với Boot 3"],
            ["Phụ thuộc thêm", "spring-cloud-starter-bootstrap", "Không cần"],
            ["Ngữ cảnh", "Có bootstrap context riêng", "Dùng chung một ngữ cảnh"],
            ["Thứ tự nạp", "Khó đoán, dễ nhầm ưu tiên", "Rõ ràng theo thứ tự khai báo"],
            ["Chịu lỗi", "Phải cấu hình thêm", "Có sẵn tiền tố optional:"],
            ["Gỡ lỗi", "Khó, hai ngữ cảnh chồng nhau", "Dễ, một luồng nạp duy nhất"],
        ],
        co_chu=9,
    )

    them_tieu_de(tai_lieu, "6.4. Về tiền tố optional:", 2)
    them_bang(
        tai_lieu,
        ["Cách viết", "Hành vi khi Config Server không phản hồi"],
        [
            ["optional:configserver:http://localhost:8888", "Service vẫn khởi động, bỏ qua cấu hình từ xa"],
            ["configserver:http://localhost:8888", "Service dừng ngay với lỗi rõ ràng"],
        ],
    )
    them_doan(
        tai_lieu,
        "Khuyến nghị của FoodX: môi trường dev giữ optional: để lập trình viên vẫn "
        "chạy được service khi chưa bật Config Server; môi trường prod bỏ optional: "
        "và đặt fail-fast: true. Ở môi trường thật, việc service khởi động với cấu "
        "hình rỗng còn nguy hiểm hơn nhiều so với việc nó không khởi động, vì lỗi sẽ "
        "chỉ lộ ra khi có khách hàng thật đặt đơn."
    )
    tai_lieu.add_page_break()


def phan_7_kiem_tra(tai_lieu: Document) -> None:
    them_tieu_de(tai_lieu, "7. Hướng dẫn kiểm tra bằng curl và actuator", 1)

    them_tieu_de(tai_lieu, "7.1. Kiểm tra Config Server phục vụ đúng file", 2)
    them_khoi_ma(tai_lieu,
                 "# Lấy cấu hình của restaurant-service ở profile dev\n"
                 "curl http://localhost:8888/restaurant-service/dev\n\n"
                 "# Lấy dạng YAML đã gộp và giải mã sẵn\n"
                 "curl http://localhost:8888/restaurant-service-dev.yml\n\n"
                 "# Chỉ định nhánh (label) cụ thể\n"
                 "curl http://localhost:8888/main/restaurant-service-prod.yml\n\n"
                 "# Hai service còn lại\n"
                 "curl http://localhost:8888/order-service/prod\n"
                 "curl http://localhost:8888/delivery-service/dev")
    them_doan(tai_lieu, "Kết quả đúng phải có 4 phần tử trong propertySources, xếp theo thứ tự ưu tiên từ cao xuống thấp:")
    them_khoi_ma(tai_lieu,
                 '{\n'
                 '  "name": "restaurant-service",\n'
                 '  "profiles": ["dev"],\n'
                 '  "label": "main",\n'
                 '  "propertySources": [\n'
                 '    { "name": "...restaurant-service-dev.yml", "source": { "server.port": 8085 } },\n'
                 '    { "name": "...restaurant-service.yml",     "source": { } },\n'
                 '    { "name": "...application-dev.yml",        "source": { } },\n'
                 '    { "name": "...application.yml",            "source": { } }\n'
                 '  ]\n'
                 '}')

    them_tieu_de(tai_lieu, "7.2. Kiểm chứng lỗi tên file cũ", 2)
    them_khoi_ma(tai_lieu,
                 "# Gọi với tên sai, Config Server vẫn trả HTTP 200 nhưng rỗng\n"
                 "curl http://localhost:8888/config/dev\n\n"
                 "# Kết quả:\n"
                 "# { \"name\": \"config\", \"profiles\": [\"dev\"], \"propertySources\": [] }")
    them_ghi_chu(tai_lieu, "Dấu hiệu nhận biết",
                 "Chuỗi propertySources rỗng chính là dấu hiệu của lỗi đặt sai tên file.")

    them_tieu_de(tai_lieu, "7.3. Kiểm chứng phía service bằng actuator", 2)
    them_khoi_ma(tai_lieu,
                 "# Xem service đã nạp cấu hình từ những nguồn nào\n"
                 "curl http://localhost:8085/actuator/env | jq '.propertySources[].name'\n\n"
                 "# Kiểm tra một khóa cụ thể và xuất xứ của nó\n"
                 "curl http://localhost:8085/actuator/env/server.port\n"
                 "curl http://localhost:8085/actuator/env/spring.datasource.url")
    them_doan(tai_lieu, "Nếu cấu hình được nạp đúng, danh sách phải có các dòng chứa configserver:")
    them_khoi_ma(tai_lieu,
                 '"configserver:...foodx-config-repo/restaurant-service-dev.yml"\n'
                 '"configserver:...foodx-config-repo/restaurant-service.yml"\n'
                 '"configserver:...foodx-config-repo/application-dev.yml"\n'
                 '"configserver:...foodx-config-repo/application.yml"')
    them_ghi_chu(
        tai_lieu, "Cảnh báo",
        "Nếu không có dòng nào chứa configserver: thì chắc chắn service đang chạy "
        "bằng cấu hình trong jar, tức là đã dính đúng lỗi đang phân tích."
    )

    them_tieu_de(tai_lieu, "7.4. Dấu hiệu trong nhật ký khởi động", 2)
    them_khoi_ma(tai_lieu,
                 "Fetching config from server at : http://localhost:8888\n"
                 "Located environment: name=restaurant-service, profiles=[dev],\n"
                 "                     label=main, version=a1b2c3d")

    them_tieu_de(tai_lieu, "7.5. Làm mới cấu hình sau khi sửa", 2)
    them_khoi_ma(tai_lieu,
                 "# Làm mới một service\n"
                 "curl -X POST http://localhost:8085/actuator/refresh\n"
                 "# Kết quả trả về danh sách khóa đã thay đổi:\n"
                 '# ["foodx.restaurant.timeout.read-timeout-ms"]\n\n'
                 "# Làm mới hàng loạt qua Spring Cloud Bus\n"
                 "curl -X POST http://localhost:8085/actuator/busrefresh\n\n"
                 "# Chỉ làm mới đúng một thực thể\n"
                 "curl -X POST http://localhost:8085/actuator/busrefresh/restaurant-service:8085")
    tai_lieu.add_page_break()


def phan_8_ket_luan(tai_lieu: Document) -> None:
    them_tieu_de(tai_lieu, "8. Kết luận và bài học rút ra", 1)

    them_tieu_de(tai_lieu, "8.1. Kết quả đạt được", 2)
    them_bang(
        tai_lieu,
        ["Yêu cầu của đề bài", "Kết quả"],
        [
            ["Chỉ rõ lỗi đặt tên file không khớp spring.application.name", "Đã phân tích quy ước và cơ chế tìm file của Config Server"],
            ["Giải thích hậu quả khi không tìm thấy file cấu hình", "Đã trình bày 3 kịch bản hậu quả theo mức độ nguy hiểm tăng dần"],
            ["Đổi lại tên file cho đúng quy ước", "config.yml đã thành restaurant-service.yml"],
            ["Chỉ rõ rủi ro lưu mật khẩu plaintext", "Đã phân tích 7 nhóm rủi ro kèm bảng đánh giá mức độ"],
            ["Sửa bằng cú pháp {cipher}", "Toàn bộ 12 file trong kho đều dùng {cipher}, không còn chữ thô"],
            ["Tạo cấu hình cho order-service", "3 file: mặc định, dev, prod - cổng 8082"],
            ["Tạo cấu hình cho delivery-service", "3 file: mặc định, dev, prod - cổng 8083"],
            ["README mô tả cấu trúc kho cho cả 3 service", "Có README tổng quan và tài liệu chuyên sâu 03"],
            ["Nộp bài dạng Word hoặc Markdown", "Có cả hai: file .docx này và các file .md"],
        ],
        co_chu=9,
    )

    them_tieu_de(tai_lieu, "8.2. Ba bài học rút ra", 2)

    them_danh_sach_so(
        tai_lieu,
        "Tên file trong kho cấu hình là một phần của hợp đồng kỹ thuật giữa service "
        "và Config Server, không phải chuyện thẩm mỹ. Nó phải khớp chính xác với "
        "spring.application.name. Đặt sai tên không gây lỗi cú pháp nào, nhưng khiến "
        "cấu hình không bao giờ tới được service.")
    them_danh_sach_so(
        tai_lieu,
        "Lỗi cấu hình thường là lỗi thầm lặng. Config Server trả HTTP 200 với "
        "propertySources rỗng chứ không trả 404. Vì vậy phải chủ động kiểm chứng bằng "
        "curl và /actuator/env, đồng thời đặt fail-fast: true ở môi trường thật để "
        "service dừng ngay thay vì chạy sai.")
    them_danh_sach_so(
        tai_lieu,
        "Bí mật đã commit là bí mật đã lộ. Lịch sử Git giữ lại vĩnh viễn, nên việc "
        "đầu tiên khi phát hiện mật khẩu chữ thô là đổi mật khẩu đó, sau đó mới mã "
        "hóa giá trị mới bằng {cipher} với khóa đặt ngoài kho cấu hình.")

    them_tieu_de(tai_lieu, "8.3. Đề xuất cải tiến tiếp theo", 2)
    them_gach_dau_dong(tai_lieu, "Thêm bước kiểm tra tự động trong CI của kho cấu hình: đối chiếu tên file với danh sách spring.application.name đã đăng ký, từ chối merge nếu có file lạ.")
    them_gach_dau_dong(tai_lieu, "Bổ sung công cụ quét bí mật (gitleaks, truffleHog) vào git hook và CI để chặn ngay việc commit chữ thô.")
    them_gach_dau_dong(tai_lieu, "Cấu hình webhook từ Git tới POST /monitor của Config Server để việc làm mới diễn ra tự động khi có commit.")
    them_gach_dau_dong(tai_lieu, "Chuyển từ khóa đối xứng sang keystore bất đối xứng, tách khóa riêng cho từng môi trường.")
    them_gach_dau_dong(tai_lieu, "Khi số service tăng, cân nhắc chuyển sang HashiCorp Vault hoặc AWS Secrets Manager để có nhật ký kiểm toán và xoay vòng tự động.")

    tai_lieu.add_paragraph()
    doan = tai_lieu.add_paragraph()
    doan.alignment = WD_ALIGN_PARAGRAPH.CENTER
    lan = doan.add_run("- HẾT -")
    lan.font.name = "Times New Roman"
    lan.font.size = Pt(12)
    lan.bold = True


# ---------------------------------------------------------------------------
# Hàm chính
# ---------------------------------------------------------------------------

def main() -> int:
    print("Đang sinh file báo cáo Word cho Bài 2...")
    print(f"  Thư mục gốc: {GOC}")

    THU_MUC_DOCS.mkdir(parents=True, exist_ok=True)

    tai_lieu = Document()
    dat_font_mac_dinh(tai_lieu)

    for phan in tai_lieu.sections:
        phan.top_margin = Cm(2.0)
        phan.bottom_margin = Cm(2.0)
        phan.left_margin = Cm(2.5)
        phan.right_margin = Cm(2.0)

    trang_bia(tai_lieu)
    phan_muc_luc(tai_lieu)
    phan_1_muc_tieu(tai_lieu)
    phan_2_loi_ten_file(tai_lieu)
    phan_3_bao_mat(tai_lieu)
    phan_4_cau_truc(tai_lieu)
    phan_5_ba_file_cau_hinh(tai_lieu)
    phan_6_client(tai_lieu)
    phan_7_kiem_tra(tai_lieu)
    phan_8_ket_luan(tai_lieu)

    tai_lieu.save(FILE_XUAT)

    kich_thuoc = FILE_XUAT.stat().st_size
    print(f"  Đã tạo: {FILE_XUAT}")
    print(f"  Kích thước: {kich_thuoc:,} byte")
    print("Hoàn tất.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
