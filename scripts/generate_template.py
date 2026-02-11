import pandas as pd
import os

# Create directory if not exists
os.makedirs("d:/00.Code/VietMy/LuyenTapCode/static/admin", exist_ok=True)

columns = [
    "Mã sinh viên", "Họ và tên", "Lớp", "Ngành học", "Ngày sinh", 
    "Số điện thoại", "Email trường", "Email cá nhân", "CCCD", "Dân tộc", 
    "Địa chỉ", "Họ tên cha", "SĐT cha", "Email cha", "Họ tên mẹ", "SĐT mẹ", "Email mẹ"
]
df = pd.DataFrame(columns=columns)

# Add a sample row
df.loc[0] = [
    "SV001", "Nguyễn Văn A", "20IT1", "Công nghệ thông tin", "2002-01-01",
    "0987654321", "a.nv@school.edu.vn", "vana@gmail.com", "123456789", "Kinh",
    "Hà Nội", "Nguyễn Văn B", "0912345678", "b.nv@gmail.com", "Lê Thị C", "0921345678", "c.lt@gmail.com"
]

output_path = "d:/00.Code/VietMy/LuyenTapCode/static/admin/student_import_template.xlsx"
df.to_excel(output_path, index=False, sheet_name='Students')
print(f"Template generated at {output_path}")
