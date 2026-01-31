
import json
import os

# Helper to generate starter code for various languages
def get_starter_code(func_signature, return_type, code_body):
    # This is a simplified helper. For 50 diverse problems, we might need custom templates.
    # We will use a dictionary-based approach for flexibility.
    pass

problems = []

# Collected final problems list
final_data = []

# --- Level 1: Nhập xuất & Tính toán cơ bản (Easy) ---
level_1 = [
    {
        "title": "Tính diện tích hình chữ nhật",
        "description": "Viết chương trình nhập vào chiều dài `a` và chiều rộng `b` của hình chữ nhật. Tính và in ra diện tích.\n\n**Input:**\n- Hai số nguyên `a`, `b` trên 2 dòng.\n\n**Output:**\n- Diện tích hình chữ nhật.",
        "difficulty": "Easy",
        "test_cases": [
            {"input": "5\n3", "output": "15"},
            {"input": "10\n10", "output": "100"},
            {"input": "0\n5", "output": "0"},
            {"input": "100\n1", "output": "100"},
            {"input": "1\n1", "output": "1"}
        ],
        "hint": "Diện tích = a * b"
    },
    {
        "title": "Chu vi hình tròn",
        "description": "Viết chương trình nhập vào bán kính `r` (số thực). Tính chu vi hình tròn (lấy PI = 3.14). In kết quả làm tròn 2 chữ số thập phân.\n\n**Input:**\n- Số thực `r`\n\n**Output:**\n- Chu vi (formatted 2 decimal places)",
        "difficulty": "Easy",
        "test_cases": [
            {"input": "1", "output": "6.28"},
            {"input": "5", "output": "31.40"},
            {"input": "0", "output": "0.00"},
            {"input": "10", "output": "62.80"},
            {"input": "2", "output": "12.56"}
        ],
        "hint": "C: `printf(\"%.2f\", 2 * 3.14 * r)` | Python: `print(f\"{2 * 3.14 * r:.2f}\")`"
    },
    {
        "title": "Đổi đơn vị độ dài",
        "description": "Nhập vào số km. Đổi sang mét.\n\n**Input:**\n- Số thực `km`\n\n**Output:**\n- Số mét (số thực)",
        "difficulty": "Easy",
        "test_cases": [
            {"input": "1.5", "output": "1500"},
            {"input": "0.1", "output": "100"},
            {"input": "0", "output": "0"},
            {"input": "5.75", "output": "5750"},
            {"input": "2", "output": "2000"}
        ],
        "hint": "1 km = 1000 m"
    },
    {
        "title": "Trung bình cộng 3 số",
        "description": "Nhập 3 số nguyên a, b, c. Tính trung bình cộng của chúng (kết quả lấy phần nguyên).\n\n**Input:**\n- 3 số nguyên trên 3 dòng\n\n**Output:**\n- Trung bình cộng (số nguyên)",
        "difficulty": "Easy",
        "test_cases": [
            {"input": "2\n4\n6", "output": "4"},
            {"input": "1\n2\n4", "output": "2"},
            {"input": "10\n20\n30", "output": "20"},
            {"input": "5\n5\n6", "output": "5"},
            {"input": "10\n10\n10", "output": "10"}
        ],
        "hint": "(a + b + c) / 3"
    },
    {
        "title": "Tìm phần dư",
        "description": "Nhập hai số nguyên `a` và `b`. In ra phần dư của phép chia `a` cho `b`.\n\n**Input:**\n- Hai số a, b\n\n**Output:**\n- Phần dư",
        "difficulty": "Easy",
        "test_cases": [
            {"input": "7\n3", "output": "1"},
            {"input": "10\n5", "output": "0"},
            {"input": "10\n2", "output": "0"},
            {"input": "5\n7", "output": "5"},
            {"input": "20\n3", "output": "2"}
        ],
        "hint": "Toán tử `%`"
    },
    {
        "title": "Bình phương số",
        "description": "Nhập một số nguyên n. In ra bình phương của nó.\n\n**Input:**\n- Số nguyên n\n\n**Output:**\n- n*n",
        "difficulty": "Easy",
        "test_cases": [
            {"input": "5", "output": "25"},
            {"input": "-2", "output": "4"},
            {"input": "0", "output": "0"},
            {"input": "10", "output": "100"},
            {"input": "1", "output": "1"}
        ],
        "hint": "n * n"
    },
    {
        "title": "Chuyển giờ sang phút",
        "description": "Nhập vào số giờ (số nguyên). In ra số phút tương ứng.\n\n**Input:**\n- Số giờ `h`\n\n**Output:**\n- Số phút",
        "difficulty": "Easy",
        "test_cases": [
            {"input": "2", "output": "120"},
            {"input": "0", "output": "0"},
            {"input": "1", "output": "60"},
            {"input": "24", "output": "1440"},
            {"input": "10", "output": "600"}
        ],
        "hint": "h * 60"
    },
    {
        "title": "Tính tuổi",
        "description": "Nhập năm sinh. Tính tuổi hiện tại (giả sử năm hiện tại là 2025).\n\n**Input:**\n- Năm sinh\n\n**Output:**\n- Tuổi",
        "difficulty": "Easy",
        "test_cases": [
            {"input": "2000", "output": "25"},
            {"input": "1990", "output": "35"},
            {"input": "2025", "output": "0"},
            {"input": "1900", "output": "125"},
            {"input": "2010", "output": "15"}
        ],
        "hint": "2025 - year"
    },
    {
        "title": "Gấp đôi số",
        "description": "Nhập vào 1 số. In ra số đó nhân 2.\n\n**Input:**\n- Số nguyên n\n\n**Output:**\n- 2*n",
        "difficulty": "Easy",
        "test_cases": [
            {"input": "15", "output": "30"},
            {"input": "0", "output": "0"},
            {"input": "-5", "output": "-10"},
            {"input": "10", "output": "20"},
            {"input": "1", "output": "2"}
        ],
        "hint": "n * 2"
    },
    {
        "title": "Hiệu hai số",
        "description": "Nhập a, b. Tính a - b.\n\n**Input:**\n- a, b\n\n**Output:**\n- a - b",
        "difficulty": "Easy",
        "test_cases": [
            {"input": "10\n3", "output": "7"},
            {"input": "5\n10", "output": "-5"},
            {"input": "100\n0", "output": "100"},
            {"input": "0\n0", "output": "0"},
            {"input": "10\n10", "output": "0"}
        ],
        "hint": "a - b"
    }
]

# --- Level 2: Cấu trúc rẽ nhánh (Easy-Medium) ---
level_2 = [
    {
        "title": "Kiểm tra chẵn lẻ",
        "description": "Nhập số nguyên n. Nếu chẵn in \"Chan\", lẻ in \"Le\".\n\n**Input:**\n- Số nguyên n\n\n**Output:**\n- \"Chan\" hoặc \"Le\"",
        "difficulty": "Easy",
        "test_cases": [
            {"input": "4", "output": "Chan"},
            {"input": "7", "output": "Le"},
            {"input": "0", "output": "Chan"},
            {"input": "-2", "output": "Chan"},
            {"input": "99", "output": "Le"}
        ],
        "hint": "Use `n % 2 == 0`"
    },
    {
        "title": "Tìm số lớn nhất",
        "description": "Nhập 2 số nguyên a, b. In ra số lớn hơn.\n\n**Input:**\n- a, b\n\n**Output:**\n- max(a, b)",
        "difficulty": "Easy",
        "test_cases": [
            {"input": "5\n10", "output": "10"},
            {"input": "5\n-1", "output": "5"},
            {"input": "10\n10", "output": "10"},
            {"input": "-5\n-2", "output": "-2"},
            {"input": "0\n0", "output": "0"}
        ],
        "hint": "if (a > b) print a else print b"
    },
    {
        "title": "Tìm max 3 số",
        "description": "Nhập 3 số nguyên a, b, c. In ra số lớn nhất.\n\n**Input:**\n- a, b, c\n\n**Output:**\n- Max value",
        "difficulty": "Medium",
        "test_cases": [
            {"input": "1\n5\n3", "output": "5"},
            {"input": "10\n10\n5", "output": "10"},
            {"input": "5\n5\n5", "output": "5"},
            {"input": "1\n2\n2", "output": "2"},
            {"input": "1\n2\n3", "output": "3"}
        ],
        "hint": "So sánh lần lượt"
    },
    {
        "title": "Kiểm tra số dương",
        "description": "Nhập số n. Nếu n > 0 in \"Duong\", n < 0 in \"Am\", n = 0 in \"Khong\".\n\n**Input:**\n- n\n\n**Output:**\n- Duong | Am | Khong",
        "difficulty": "Easy",
        "test_cases": [
            {"input": "5", "output": "Duong"},
            {"input": "-2", "output": "Am"},
            {"input": "0", "output": "Khong"},
            {"input": "-100", "output": "Am"},
            {"input": "99", "output": "Duong"}
        ],
        "hint": "if / else if / else"
    },
    {
        "title": "Năm nhuận",
        "description": "Nhập năm (year). Kiểm tra có phải năm nhuận không. (Năm nhuận chia hết cho 400 HOẶC (chia hết cho 4 và KHÔNG chia hết cho 100)). Nếu có in \"Yes\", không in \"No\".\n\n**Input:**\n- year\n\n**Output:**\n- Yes / No",
        "difficulty": "Medium",
        "test_cases": [
            {"input": "2000", "output": "Yes"},
            {"input": "2023", "output": "No"},
            {"input": "2024", "output": "Yes"},
            {"input": "1900", "output": "No"},
            {"input": "2100", "output": "No"}
        ],
        "hint": "((y % 400 == 0) || (y % 4 == 0 && y % 100 != 0))"
    },
    {
        "title": "Xếp loại học lực",
        "description": "Nhập điểm trung bình (0-10). Nếu >= 8: \"Gioi\", >= 6.5: \"Kha\", >= 5: \"Trung binh\", < 5: \"Yeu\".\n\n**Input:**\n- score\n\n**Output:**\n- Xếp loại",
        "difficulty": "Easy",
        "test_cases": [
            {"input": "9", "output": "Gioi"},
            {"input": "7", "output": "Kha"},
            {"input": "4", "output": "Yeu"},
            {"input": "5", "output": "Trung binh"},
            {"input": "6.5", "output": "Kha"}
        ],
        "hint": "if / else if chains"
    },
    {
        "title": "Kiểm tra chia hết",
        "description": "Nhập a, b. Nếu a chia hết cho b in \"Yes\", ngược lại \"No\".\n\n**Input:**\n- a, b\n\n**Output:**\n- Yes / No",
        "difficulty": "Easy",
        "test_cases": [
            {"input": "10\n5", "output": "Yes"},
            {"input": "10\n3", "output": "No"},
            {"input": "5\n10", "output": "No"},
            {"input": "0\n5", "output": "Yes"},
            {"input": "15\n3", "output": "Yes"}
        ],
        "hint": "a % b == 0"
    },
    {
        "title": "Kiểm tra tam giác",
        "description": "Nhập 3 cạnh a, b, c. Kiểm tra xem có tạo thành tam giác không (Tổng 2 cạnh bất kỳ > cạnh còn lại). In \"Yes\" hoặc \"No\".\n\n**Input:**\n- a, b, c\n\n**Output:**\n- Yes / No",
        "difficulty": "Medium",
        "test_cases": [
            {"input": "3\n4\n5", "output": "Yes"},
            {"input": "1\n1\n5", "output": "No"},
            {"input": "1\n1\n1", "output": "Yes"},
            {"input": "3\n4\n10", "output": "No"},
            {"input": "5\n12\n13", "output": "Yes"}
        ],
        "hint": "a+b>c && a+c>b && b+c>a"
    },
    {
        "title": "Giải phương trình bậc 1",
        "description": "Giải pt: ax + b = 0. Nhập a, b. In ra x (lấy 2 số thập phân). Nếu a=0, b!=0 in \"Vo nghiem\", a=0, b=0 in \"Vo so nghiem\".\n\n**Input:**\n- a, b\n\n**Output:**\n- x hoặc message",
        "difficulty": "Medium",
        "test_cases": [
            {"input": "2\n-4", "output": "2.00"},
            {"input": "0\n5", "output": "Vo nghiem"},
            {"input": "1\n0", "output": "0.00"},
            {"input": "0\n0", "output": "Vo so nghiem"},
            {"input": "1\n-1", "output": "1.00"}
        ],
        "hint": "Biện luận theo a và b"
    },
    {
        "title": "Tính cước taxi",
        "description": "Nhập số km đi được. 1km đầu: 10000. Từ km thứ 2 đến 30: 12000/km. Từ km 31 trở đi: 11000/km. Tính tổng tiền.\n\n**Input:**\n- km\n\n**Output:**\n- Tổng tiền",
        "difficulty": "Medium",
        "test_cases": [
            {"input": "1", "output": "10000"},
            {"input": "2", "output": "22000"},
            {"input": "0", "output": "0"},
            {"input": "31", "output": "369000"},
            {"input": "30", "output": "358000"}
        ],
        "hint": "Tính từng khoảng"
    }
]

# --- Create all levels data ---
all_problems_data = level_1 + level_2 
# (Simplifying for brevity in this response, ideally we add all 50. 
# I'll create a generating loop for the rest to reach 50 quickly if needed, or define specific ones.)
# Let's add more Level 3 (Loops) and 4 (Arrays) to fill up.

level_3 = [
    {
        "title": "In từ 1 đến N",
        "description": "Nhập n. In các số từ 1 đến n trên cùng 1 dòng, cách nhau bởi khoảng trắng.\n\n**Input:**\n- n\n\n**Output:**\n- 1 2 ... n",
        "difficulty": "Easy",
        "test_cases": [
            {"input": "5", "output": "1 2 3 4 5"},
            {"input": "1", "output": "1"},
            {"input": "0", "output": ""},
            {"input": "3", "output": "1 2 3"},
            {"input": "2", "output": "1 2"}
        ],
        "hint": "For loop"
    },
    {
        "title": "Tổng 1 đến N",
        "description": "Nhập n. Tính tổng S = 1 + 2 + ... + n.\n\n**Input:**\n- n\n\n**Output:**\n- Tổng S",
        "difficulty": "Easy",
        "test_cases": [
            {"input": "5", "output": "15"},
            {"input": "10", "output": "55"},
            {"input": "1", "output": "1"},
            {"input": "0", "output": "0"},
            {"input": "3", "output": "6"}
        ],
        "hint": "Loop or formula n*(n+1)/2"
    },
    {
        "title": "Giai thừa",
        "description": "Nhập n. Tính n!.\n\n**Input:**\n- n\n\n**Output:**\n- n!",
        "difficulty": "Medium",
        "test_cases": [
            {"input": "5", "output": "120"},
            {"input": "3", "output": "6"},
            {"input": "0", "output": "1"},
            {"input": "1", "output": "1"},
            {"input": "2", "output": "2"}
        ],
        "hint": "Loop multiply"
    },
    {
        "title": "Bảng cửu chương",
        "description": "Nhập n (1-9). In bảng cửu chương n. Mỗi dòng: \"n x i = result\".\n\n**Input:**\n- n\n\n**Output:**\n- 10 dòng",
        "difficulty": "Easy",
        "test_cases": [
            {"input": "2", "output": "2 x 1 = 2\n2 x 2 = 4\n2 x 3 = 6\n2 x 4 = 8\n2 x 5 = 10\n2 x 6 = 12\n2 x 7 = 14\n2 x 8 = 16\n2 x 9 = 18\n2 x 10 = 20"},
            {"input": "5", "output": "5 x 1 = 5\n5 x 2 = 10\n5 x 3 = 15\n5 x 4 = 20\n5 x 5 = 25\n5 x 6 = 30\n5 x 7 = 35\n5 x 8 = 40\n5 x 9 = 45\n5 x 10 = 50"},
            {"input": "3", "output": "3 x 1 = 3\n3 x 2 = 6\n3 x 3 = 9\n3 x 4 = 12\n3 x 5 = 15\n3 x 6 = 18\n3 x 7 = 21\n3 x 8 = 24\n3 x 9 = 27\n3 x 10 = 30"},
            {"input": "7", "output": "7 x 1 = 7\n7 x 2 = 14\n7 x 3 = 21\n7 x 4 = 28\n7 x 5 = 35\n7 x 6 = 42\n7 x 7 = 49\n7 x 8 = 56\n7 x 9 = 63\n7 x 10 = 70"},
            {"input": "9", "output": "9 x 1 = 9\n9 x 2 = 18\n9 x 3 = 27\n9 x 4 = 36\n9 x 5 = 45\n9 x 6 = 54\n9 x 7 = 63\n9 x 8 = 72\n9 x 9 = 81\n9 x 10 = 90"}
        ],
        "hint": "Loop 1 to 10"
    },
    {
        "title": "Đếm ước số",
        "description": "Nhập n. Đếm xem n có bao nhiêu ước số dương.\n\n**Input:**\n- n\n\n**Output:**\n- Số lượng ước",
        "difficulty": "Medium",
        "test_cases": [
            {"input": "10", "output": "4"},
            {"input": "7", "output": "2"},
            {"input": "1", "output": "1"},
            {"input": "12", "output": "6"},
            {"input": "6", "output": "4"}
        ],
        "hint": "Loop 1 to n, check n%i==0"
    }
]

# Simple filler for remaining to ensure we deliver "50 problems" or at least a structure for it.
# Code below will auto-generate variations to reach 50 if list is short, but best to have real quality ones.
# I will supply ~25 high quality ones manually defined above + below, and maybe auto-gen some variants? 
# The user asked for 50. I should try to provide 50 distinct ones.

# ... Continuing Level 3
level_3.extend([
    {"title": "Tổng số chẵn", "description": "Tổng các số chẵn từ 1 đến N.", "difficulty": "Easy", "test_cases": [{"input": "5", "output": "6"}, {"input": "1", "output": "0"}, {"input": "10", "output": "30"}, {"input": "2", "output": "2"}, {"input": "6", "output": "12"}], "hint": "Loop if i%2==0"},
    {"title": "Số nguyên tố", "description": "Kiểm tra N có phải số nguyên tố. In Yes/No.", "difficulty": "Medium", "test_cases": [{"input": "7", "output": "Yes"}, {"input": "4", "output": "No"}, {"input": "1", "output": "No"}, {"input": "2", "output": "Yes"}, {"input": "13", "output": "Yes"}], "hint": "Loop 2 to sqrt(n)"},
    {"title": "Tổng chữ số", "description": "Nhập N. Tính tổng các chữ số của N.", "difficulty": "Medium", "test_cases": [{"input": "123", "output": "6"}, {"input": "0", "output": "0"}, {"input": "12345", "output": "15"}, {"input": "10", "output": "1"}, {"input": "999", "output": "27"}], "hint": "While n>0: sum += n%10; n/=10"},
    {"title": "Số đảo ngược", "description": "In số đảo ngược của N.", "difficulty": "Medium", "test_cases": [{"input": "123", "output": "321"}, {"input": "505", "output": "505"}, {"input": "9", "output": "9"}, {"input": "121", "output": "121"}, {"input": "1203", "output": "3021"}], "hint": "While..."},
    {"title": "Dãy Fibonacci", "description": "In N số Fibonacci đầu tiên.", "difficulty": "Medium", "test_cases": [{"input": "5", "output": "0 1 1 2 3"}, {"input": "1", "output": "0"}, {"input": "2", "output": "0 1"}, {"input": "3", "output": "0 1 1"}, {"input": "4", "output": "0 1 1 2"}], "hint": "Loop"}
])

# --- Level 4: Mảng (Arrays) ---
level_4 = [
    {"title": "Nhập xuất mảng", "description": "Nhập N và mảng N phần tử. In mảng ra.", "difficulty": "Easy", "test_cases": [{"input": "3\n1 2 3", "output": "1 2 3"}, {"input": "1\n10", "output": "10"}, {"input": "5\n1 2 3 4 5", "output": "1 2 3 4 5"}, {"input": "2\n5 6", "output": "5 6"}, {"input": "4\n1 1 1 1", "output": "1 1 1 1"}], "hint": "Array/List"},
    {"title": "Tổng mảng", "description": "Nhập N và mảng A. Tính tổng các phần tử.", "difficulty": "Easy", "test_cases": [{"input": "3\n1 2 3", "output": "6"}, {"input": "1\n99", "output": "99"}, {"input": "5\n1 1 1 1 1", "output": "5"}, {"input": "2\n10 20", "output": "30"}, {"input": "4\n1 2 3 4", "output": "10"}], "hint": "Sum loop"},
    {"title": "Max min mảng", "description": "Tìm max và min trong mảng.", "difficulty": "Easy", "test_cases": [{"input": "3\n1 5 2", "output": "5 1"}, {"input": "1\n7", "output": "7 7"}, {"input": "4\n-1 -5 0 2", "output": "2 -5"}, {"input": "2\n-1 -1", "output": "-1 -1"}, {"input": "5\n1 2 3 4 5", "output": "5 1"}], "hint": "Compare loop"},
    {"title": "Đếm số chẵn mảng", "description": "Đếm số phần tử chẵn trong mảng.", "difficulty": "Medium", "test_cases": [{"input": "4\n1 2 3 4", "output": "2"}, {"input": "3\n1 3 5", "output": "0"}, {"input": "5\n2 4 6 8 0", "output": "5"}, {"input": "1\n1", "output": "0"}, {"input": "2\n2 3", "output": "1"}], "hint": "Count if"},
    {"title": "Tìm k trong mảng", "description": "Nhập N, mảng A và số k. Tìm vị trí đầu tiên của k. Nếu không có in -1.", "difficulty": "Medium", "test_cases": [{"input": "3\n1 5 2\n5", "output": "2"}, {"input": "4\n1 2 3 4\n5", "output": "-1"}, {"input": "3\n5 5 5\n5", "output": "1"}, {"input": "2\n1 2\n3", "output": "-1"}, {"input": "5\n1 2 3 4 5\n3", "output": "3"}], "hint": "Linear search (-1 if not found)"},
    {"title": "Mảng đảo ngược", "description": "In mảng theo thứ tự ngược lại.", "difficulty": "Easy", "test_cases": [{"input": "3\n1 2 3", "output": "3 2 1"}, {"input": "1\n5", "output": "5"}, {"input": "4\n1 3 3 7", "output": "7 3 3 1"}, {"input": "2\n1 2", "output": "2 1"}, {"input": "5\n1 2 3 4 5", "output": "5 4 3 2 1"}], "hint": "Loop N-1 to 0"},
    {"title": "Sắp xếp tăng dần", "description": "Sắp xếp mảng tăng dần.", "difficulty": "Medium", "test_cases": [{"input": "3\n3 1 2", "output": "1 2 3"}, {"input": "1\n10", "output": "10"}, {"input": "5\n5 4 3 2 1", "output": "1 2 3 4 5"}, {"input": "2\n2 1", "output": "1 2"}, {"input": "4\n4 3 2 1", "output": "1 2 3 4"}], "hint": "Bubble sort / built-in sort"},
    {"title": "Trung bình cộng mảng", "description": "Tính TBC các giá trị trong mảng (2 số lẻ).", "difficulty": "Medium", "test_cases": [{"input": "3\n1 2 4", "output": "2.33"}, {"input": "1\n1", "output": "1.00"}, {"input": "4\n2 2 3 3", "output": "2.50"}, {"input": "2\n1 1", "output": "1.00"}, {"input": "5\n1 2 3 4 5", "output": "3.00"}], "hint": "Sum / N"},
    {"title": "Số lớn thứ 2", "description": "Tìm số lớn thứ 2 trong mảng.", "difficulty": "Medium", "test_cases": [{"input": "4\n1 5 2 5", "output": "2"}, {"input": "3\n10 10 10", "output": "10"}, {"input": "5\n1 2 3 4 5", "output": "4"}, {"input": "2\n1 2", "output": "1"}, {"input": "4\n1 1 2 2", "output": "1"}], "hint": "Sort or scan"}, 
    {"title": "Chèn phần tử", "description": "Chèn x vào vị trí k trong mảng.", "difficulty": "Hard", "test_cases": [{"input": "3\n1 2 3\n5 1", "output": "1 5 2 3"}, {"input": "2\n1 2\n10 0", "output": "10 1 2"}, {"input": "3\n1 2 3\n9 3", "output": "1 2 3 9"}, {"input": "1\n1\n5 0", "output": "5 1"}, {"input": "2\n1 2\n7 2", "output": "1 2 7"}], "hint": "Array shift"}
]

# --- Level 5: Nâng cao ---
level_5 = [
    {"title": "UCLN và BCNN", "description": "Tìm UCLN và BCNN của 2 số.", "difficulty": "Medium", "test_cases": [{"input": "2 4", "output": "2 4"}, {"input": "5 10", "output": "5 10"}, {"input": "7 13", "output": "1 91"}, {"input": "12 18", "output": "6 36"}, {"input": "10 25", "output": "5 50"}], "hint": "GCD Alg"},
    {"title": "Kiểm tra đối xứng", "description": "Chuỗi/Mảng đối xứng (Palindrome).", "difficulty": "Medium", "test_cases": [{"input": "madam", "output": "Yes"}, {"input": "a", "output": "Yes"}, {"input": "1221", "output": "Yes"}, {"input": "racecar", "output": "Yes"}, {"input": "aba", "output": "Yes"}], "hint": "Check ends"},
    {"title": "Tháp hình sao", "description": "In tam giác sao cân chiều cao h.", "difficulty": "Hard", "test_cases": [{"input": "3", "output": "  *\n ***\n*****"}, {"input": "1", "output": "*"}, {"input": "2", "output": " *\n***"}, {"input": "4", "output": "   *\n  ***\n *****\n*******"}, {"input": "5", "output": "    *\n   ***\n  *****\n *******\n*********"}], "hint": "Nested loops space/star"},
    {"title": "Ma trận chuyển vị", "description": "Nhập ma trận NxM. In chuyển vị.", "difficulty": "Hard", "test_cases": [{"input": "2 2\n1 2\n3 4", "output": "1 3\n2 4"}, {"input": "1 1\n5", "output": "5"}, {"input": "2 3\n1 2 3\n4 5 6", "output": "1 4\n2 5\n3 6"}, {"input": "3 1\n1\n2\n3", "output": "1 2 3\n"}, {"input": "1 3\n1 2 3", "output": "1\n2\n3\n"}], "hint": "Matrix logic"},
    {"title": "Tính tổ hợp chập k của n", "description": "Tính nCk.", "difficulty": "Medium", "test_cases": [{"input": "5 2", "output": "10"}, {"input": "5 1", "output": "5"}, {"input": "5 0", "output": "1"}, {"input": "5 5", "output": "1"}, {"input": "10 2", "output": "45"}], "hint": "Recursion or formula"},
    {"title": "Liệt kê số nguyên tố < N", "description": "Sàng Eratosthenes hoặc in hết.", "difficulty": "Hard", "test_cases": [{"input": "10", "output": "2 3 5 7"}, {"input": "2", "output": ""}, {"input": "5", "output": "2 3"}, {"input": "3", "output": "2"}, {"input": "20", "output": "2 3 5 7 11 13 17 19"}], "hint": "Sieve"},
    {"title": "Chuyển nhị phân", "description": "Đổi số thập phân sang nhị phân.", "difficulty": "Medium", "test_cases": [{"input": "5", "output": "101"}, {"input": "0", "output": "0"}, {"input": "10", "output": "1010"}, {"input": "1", "output": "1"}, {"input": "8", "output": "1000"}], "hint": "Div mod 2"},
    {"title": "Đếm từ trong chuỗi", "description": "Đếm số từ trong câu.", "difficulty": "Medium", "test_cases": [{"input": "Hello World", "output": "2"}, {"input": "  ", "output": "0"}, {"input": "A B C", "output": "3"}, {"input": "A", "output": "1"}, {"input": "One Two Three Four", "output": "4"}], "hint": "Split space"},
    {"title": "Tổng đường chéo chính", "description": "Tổng đường chéo ma trận vuông.", "difficulty": "Medium", "test_cases": [{"input": "2\n1 2\n3 4", "output": "5"}, {"input": "1\n5", "output": "5"}, {"input": "3\n1 0 0\n0 1 0\n0 0 1", "output": "3"}, {"input": "2\n0 0\n0 0", "output": "0"}, {"input": "2\n1 1\n1 1", "output": "2"}], "hint": "Loop i,i"},
    {"title": "Sắp xếp tên", "description": "Sắp xếp danh sách tên theo alphabet.", "difficulty": "Hard", "test_cases": [{"input": "2\nB\nA", "output": "A\nB"}, {"input": "1\nZ", "output": "Z"}, {"input": "3\nC\nB\nA", "output": "A\nB\nC"}, {"input": "2\nJohn\nAlice", "output": "Alice\nJohn"}, {"input": "3\nCat\nDog\nBat", "output": "Bat\nCat\nDog"}], "hint": "String compare"}
]


# Assign Levels and Starter Codes
for i, p in enumerate(all_problems_data):
    p["id"] = i + 1
    
    # Assign Category based on list membership
    # Note: Logic here is implicit because we concatenated lists. 
    # Better to iterate separate lists if we want perfect mapping, but simple range check or direct assignment during list creation is cleaner.
    # Let's simple re-assign category based on where the problem came from.
    pass


# Valid solution generator helper
def generate_solution(p, lang):
    t = p['title'].lower()
    
    # Generic templates
    c_tmpl = "#include <stdio.h>\n\nint main() {{\n{body}\n    return 0;\n}}"
    cpp_tmpl = "#include <iostream>\nusing namespace std;\n\nint main() {{\n{body}\n    return 0;\n}}"
    py_tmpl = "{body}"
    java_tmpl = "import java.util.Scanner;\n\npublic class Main {{\n    public static void main(String[] args) {{\n        Scanner sc = new Scanner(System.in);\n{body}\n    }}\n}}"
    cs_tmpl = "using System;\nusing System.Linq;\nusing System.Collections.Generic;\n\nclass Program {{\n    static void Main() {{\n{body}\n    }}\n}}"

    # Pattern Matching for logic
    body_c = ""
    body_cpp = ""
    body_py = ""
    body_java = ""
    body_cs = ""
    
    # --- Level 1: Basic Math ---
    if "diện tích hình chữ nhật" in t:
        body_c = '    int a, b;\n    scanf("%d %d", &a, &b);\n    printf("%d", a * b);'
        body_cpp = '    int a, b;\n    cin >> a >> b;\n    cout << a * b;'
        body_py = "a = int(input())\nb = int(input())\nprint(a * b)"
        body_java = '        int a = sc.nextInt();\n        int b = sc.nextInt();\n        System.out.println(a * b);'
        body_cs = '        int a = int.Parse(Console.ReadLine());\n        int b = int.Parse(Console.ReadLine());\n        Console.WriteLine(a * b);'
    elif "chu vi hình tròn" in t:
        body_c = '    float r;\n    scanf("%f", &r);\n    printf("%.2f", 2 * 3.14 * r);'
        body_cpp = '    float r;\n    cin >> r;\n    printf("%.2f", 2 * 3.14 * r);'
        body_py = "r = float(input())\nprint(f'{2 * 3.14 * r:.2f}')"
        body_java = '        double r = sc.nextDouble();\n        System.out.printf("%.2f", 2 * 3.14 * r);'
        body_cs = '        double r = double.Parse(Console.ReadLine());\n        Console.WriteLine((2 * 3.14 * r).ToString("F2"));'
    elif "đổi đơn vị độ dài" in t:
        body_c = '    float km;\n    scanf("%f", &km);\n    printf("%.0f", km * 1000);'
        body_cpp = '    float km;\n    cin >> km;\n    cout << (int)(km * 1000);'
        body_py = "km = float(input())\nprint(int(km * 1000))"
        body_java = '        double km = sc.nextDouble();\n        System.out.println((int)(km * 1000));'
        body_cs = '        double km = double.Parse(Console.ReadLine());\n        Console.WriteLine((int)(km * 1000));'
    elif "trung bình cộng 3 số" in t:
        body_c = '    int a, b, c;\n    scanf("%d %d %d", &a, &b, &c);\n    printf("%d", (a + b + c) / 3);'
        body_cpp = '    int a, b, c;\n    cin >> a >> b >> c;\n    cout << (a + b + c) / 3;'
        body_py = "a = int(input())\nb = int(input())\nc = int(input())\nprint((a+b+c)//3)"
        body_java = '        int a = sc.nextInt();\n        int b = sc.nextInt();\n        int c = sc.nextInt();\n        System.out.println((a + b + c) / 3);'
        body_cs = '        int a = int.Parse(Console.ReadLine());\n        int b = int.Parse(Console.ReadLine());\n        int c = int.Parse(Console.ReadLine());\n        Console.WriteLine((a + b + c) / 3);'
    elif "tìm phần dư" in t:
        body_c = '    int a, b;\n    scanf("%d %d", &a, &b);\n    printf("%d", a % b);'
        body_cpp = '    int a, b;\n    cin >> a >> b;\n    cout << a % b;'
        body_py = "a = int(input())\nb = int(input())\nprint(a % b)"
        body_java = '        int a = sc.nextInt();\n        int b = sc.nextInt();\n        System.out.println(a % b);'
        body_cs = '        int a = int.Parse(Console.ReadLine());\n        int b = int.Parse(Console.ReadLine());\n        Console.WriteLine(a % b);'
    elif "bình phương số" in t:
        body_c = '    int n;\n    scanf("%d", &n);\n    printf("%d", n * n);'
        body_cpp = '    int n;\n    cin >> n;\n    cout << n * n;'
        body_py = "n = int(input())\nprint(n * n)"
        body_java = '        int n = sc.nextInt();\n        System.out.println(n * n);'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        Console.WriteLine(n * n);'
    elif "chuyển giờ sang phút" in t:
        body_c = '    int h;\n    scanf("%d", &h);\n    printf("%d", h * 60);'
        body_cpp = '    int h;\n    cin >> h;\n    cout << h * 60;'
        body_py = "h = int(input())\nprint(h * 60)"
        body_java = '        int h = sc.nextInt();\n        System.out.println(h * 60);'
        body_cs = '        int h = int.Parse(Console.ReadLine());\n        Console.WriteLine(h * 60);'
    elif "tính tuổi" in t:
        body_c = '    int y;\n    scanf("%d", &y);\n    printf("%d", 2025 - y);'
        body_cpp = '    int y;\n    cin >> y;\n    cout << 2025 - y;'
        body_py = "y = int(input())\nprint(2025 - y)"
        body_java = '        int y = sc.nextInt();\n        System.out.println(2025 - y);'
        body_cs = '        int y = int.Parse(Console.ReadLine());\n        Console.WriteLine(2025 - y);'
    elif "gấp đôi số" in t:
        body_c = '    int n;\n    scanf("%d", &n);\n    printf("%d", n * 2);'
        body_cpp = '    int n;\n    cin >> n;\n    cout << n * 2;'
        body_py = "n = int(input())\nprint(n * 2)"
        body_java = '        int n = sc.nextInt();\n        System.out.println(n * 2);'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        Console.WriteLine(n * 2);'
    elif "hiệu hai số" in t:
        body_c = '    int a, b;\n    scanf("%d %d", &a, &b);\n    printf("%d", a - b);'
        body_cpp = '    int a, b;\n    cin >> a >> b;\n    cout << a - b;'
        body_py = "a = int(input())\nb = int(input())\nprint(a - b)"
        body_java = '        int a = sc.nextInt();\n        int b = sc.nextInt();\n        System.out.println(a - b);'
        body_cs = '        int a = int.Parse(Console.ReadLine());\n        int b = int.Parse(Console.ReadLine());\n        Console.WriteLine(a - b);'

    # --- Level 2: Conditions ---
    elif "kiểm tra chẵn lẻ" in t:
        body_c = '    int n;\n    scanf("%d", &n);\n    if(n % 2 == 0) printf("Chan");\n    else printf("Le");'
        body_cpp = '    int n;\n    cin >> n;\n    if(n % 2 == 0) cout << "Chan";\n    else cout << "Le";'
        body_py = "n = int(input())\nprint('Chan' if n % 2 == 0 else 'Le')"
        body_java = '        int n = sc.nextInt();\n        if(n % 2 == 0) System.out.println("Chan");\n        else System.out.println("Le");'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        if(n % 2 == 0) Console.WriteLine("Chan");\n        else Console.WriteLine("Le");'
    elif "tìm số lớn nhất" in t:
        body_c = '    int a, b;\n    scanf("%d %d", &a, &b);\n    if(a > b) printf("%d", a);\n    else printf("%d", b);'
        body_cpp = '    int a, b;\n    cin >> a >> b;\n    cout << (a > b ? a : b);'
        body_py = "a = int(input())\nb = int(input())\nprint(max(a, b))"
        body_java = '        int a = sc.nextInt();\n        int b = sc.nextInt();\n        System.out.println(Math.max(a, b));'
        body_cs = '        string[] inputs = Console.ReadLine().Split();\n        int a = int.Parse(inputs[0]);\n        int b = int.Parse(inputs[1]);\n        Console.WriteLine(Math.Max(a, b));'
    elif "năm nhuận" in t:
        body_c = '    int y;\n    scanf("%d", &y);\n    if((y % 400 == 0) || (y % 4 == 0 && y % 100 != 0)) printf("Yes");\n    else printf("No");'
        body_cpp = '    int y;\n    cin >> y;\n    if((y % 400 == 0) || (y % 4 == 0 && y % 100 != 0)) cout << "Yes";\n    else cout << "No";'
        body_py = "y = int(input())\nif (y % 400 == 0) or (y % 4 == 0 and y % 100 != 0):\n    print('Yes')\nelse:\n    print('No')"
        body_java = '        int y = sc.nextInt();\n        if((y % 400 == 0) || (y % 4 == 0 && y % 100 != 0)) System.out.println("Yes");\n        else System.out.println("No");'
        body_cs = '        int y = int.Parse(Console.ReadLine());\n        if((y % 400 == 0) || (y % 4 == 0 && y % 100 != 0)) Console.WriteLine("Yes");\n        else Console.WriteLine("No");'
    elif "max 3 số" in t:
        body_c = '    int a, b, c; scanf("%d %d %d", &a, &b, &c);\n    int max = a; if(b>max) max=b; if(c>max) max=c; printf("%d", max);'
        body_cpp = '    int a, b, c; cin >> a >> b >> c;\n    int m = a; if(b>m) m=b; if(c>m) m=c; cout << m;'
        body_py = "a = int(input()); b = int(input()); c = int(input()); print(max(a, b, c))"
        body_java = '        int a = sc.nextInt(), b = sc.nextInt(), c = sc.nextInt();\n        System.out.println(Math.max(a, Math.max(b, c)));'
        body_cs = '        int a = int.Parse(Console.ReadLine()); int b = int.Parse(Console.ReadLine()); int c = int.Parse(Console.ReadLine());\n        Console.WriteLine(Math.Max(a, Math.Max(b, c)));'
    elif "kiểm tra số dương" in t:
        body_c = '    int n; scanf("%d", &n);\n    if(n>0) printf("Duong"); else if(n<0) printf("Am"); else printf("Khong");'
        body_cpp = '    int n; cin >> n;\n    if(n>0) cout << "Duong"; else if(n<0) cout << "Am"; else cout << "Khong";'
        body_py = "n = int(input())\nif n > 0: print('Duong')\nelif n < 0: print('Am')\nelse: print('Khong')"
        body_java = '        int n = sc.nextInt();\n        if(n > 0) System.out.println("Duong"); else if(n < 0) System.out.println("Am"); else System.out.println("Khong");'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        if(n > 0) Console.WriteLine("Duong"); else if(n < 0) Console.WriteLine("Am"); else Console.WriteLine("Khong");'
    elif "xếp loại học lực" in t:
        body_c = '    float s; scanf("%f", &s);\n    if(s>=8) printf("Gioi"); else if(s>=6.5) printf("Kha"); else if(s>=5) printf("Trung binh"); else printf("Yeu");'
        body_cpp = '    float s; cin >> s;\n    if(s>=8) cout << "Gioi"; else if(s>=6.5) cout << "Kha"; else if(s>=5) cout << "Trung binh"; else cout << "Yeu";'
        body_py = "s = float(input())\nif s >= 8: print('Gioi')\nelif s >= 6.5: print('Kha')\nelif s >= 5: print('Trung binh')\nelse: print('Yeu')"
        body_java = '        double s = sc.nextDouble();\n        if(s>=8) System.out.println("Gioi"); else if(s>=6.5) System.out.println("Kha"); else if(s>=5) System.out.println("Trung binh"); else System.out.println("Yeu");'
        body_cs = '        double s = double.Parse(Console.ReadLine());\n        if(s>=8) Console.WriteLine("Gioi"); else if(s>=6.5) Console.WriteLine("Kha"); else if(s>=5) Console.WriteLine("Trung binh"); else Console.WriteLine("Yeu");'
    elif "chia hết" in t:
        body_c = '    int a, b; scanf("%d %d", &a, &b); if(a%b==0) printf("Yes"); else printf("No");'
        body_cpp = '    int a, b; cin >> a >> b; if(a%b==0) cout << "Yes"; else cout << "No";'
        body_py = "a = int(input()); b = int(input()); print('Yes' if a % b == 0 else 'No')"
        body_java = '        int a = sc.nextInt(), b = sc.nextInt(); System.out.println(a % b == 0 ? "Yes" : "No");'
        body_cs = '        int a = int.Parse(Console.ReadLine()); int b = int.Parse(Console.ReadLine()); Console.WriteLine(a % b == 0 ? "Yes" : "No");'
    elif "tam giác" in t:
        body_c = '    int a, b, c; scanf("%d %d %d", &a, &b, &c);\n    if(a+b>c && a+c>b && b+c>a) printf("Yes"); else printf("No");'
        body_cpp = '    int a, b, c; cin >> a >> b >> c;\n    if(a+b>c && a+c>b && b+c>a) cout << "Yes"; else cout << "No";'
        body_py = "a = int(input()); b = int(input()); c = int(input())\nprint('Yes' if a+b>c and a+c>b and b+c>a else 'No')"
        body_java = '        int a = sc.nextInt(), b = sc.nextInt(), c = sc.nextInt();\n        System.out.println(a+b>c && a+c>b && b+c>a ? "Yes" : "No");'
        body_cs = '        int a = int.Parse(Console.ReadLine()); int b = int.Parse(Console.ReadLine()); int c = int.Parse(Console.ReadLine());\n        Console.WriteLine(a+b>c && a+c>b && b+c>a ? "Yes" : "No");'
    elif "giải phương trình bậc 1" in t:
        body_c = '    float a, b; scanf("%f %f", &a, &b);\n    if(a==0) { if(b==0) printf("Vo so nghiem"); else printf("Vo nghiem"); }\n    else printf("%.2f", -b/a);'
        body_cpp = '    float a, b; cin >> a >> b;\n    if(a==0) { if(b==0) cout << "Vo so nghiem"; else cout << "Vo nghiem"; }\n    else printf("%.2f", -b/a);'
        body_py = "a = float(input()); b = float(input())\nif a == 0:\n    print('Vo so nghiem' if b == 0 else 'Vo nghiem')\nelse:\n    print(f'{-b/a:.2f}')"
        body_java = '        double a = sc.nextDouble(), b = sc.nextDouble();\n        if(a==0) System.out.println(b==0 ? "Vo so nghiem" : "Vo nghiem");\n        else System.out.printf("%.2f", -b/a);'
        body_cs = '        double a = double.Parse(Console.ReadLine()); double b = double.Parse(Console.ReadLine());\n        if(a==0) Console.WriteLine(b==0 ? "Vo so nghiem" : "Vo nghiem");\n        else Console.WriteLine((-b/a).ToString("F2"));'
    elif "taxi" in t:
        body_c = '    int km; scanf("%d", &km); long long total=0;\n    if(km>=1) total += 10000;\n    if(km>1) { int d = (km>30?29:km-1); total += d*12000; }\n    if(km>30) total += (long long)(km-30)*11000;\n    printf("%lld", total);'
        body_cpp = '    int km; cin >> km; long long total=0;\n    if(km>=1) total += 10000;\n    if(km>1) { int d = (km>30?29:km-1); total += d*12000; }\n    if(km>30) total += (long long)(km-30)*11000;\n    cout << total;'
        body_py = "km = int(input())\ntotal = 0\nif km >= 1: total += 10000\nif km > 1: total += min(km-1, 29) * 12000\nif km > 30: total += (km-30) * 11000\nprint(total)"
        body_java = '        int km = sc.nextInt(); long total = 0;\n        if(km >= 1) total += 10000;\n        if(km > 1) total += (long)Math.min(km-1, 29) * 12000;\n        if(km > 30) total += (long)(km-30) * 11000;\n        System.out.println(total);'
        body_cs = '        int km = int.Parse(Console.ReadLine()); long total = 0;\n        if(km >= 1) total += 10000;\n        if(km > 1) total += (long)Math.Min(km-1, 29) * 12000;\n        if(km > 30) total += (long)(km-30) * 11000;\n        Console.WriteLine(total);'

    # --- Level 3: Loops ---
    elif "in từ 1 đến n" in t:
        body_c = '    int n;\n    scanf("%d", &n);\n    for(int i=1; i<=n; i++) printf("%d ", i);'
        body_cpp = '    int n;\n    cin >> n;\n    for(int i=1; i<=n; i++) cout << i << " ";'
        body_py = "n = int(input())\nprint(*range(1, n+1))"
        body_java = '        int n = sc.nextInt();\n        for(int i=1; i<=n; i++) System.out.print(i + " ");'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        for(int i=1; i<=n; i++) Console.Write(i + " ");'
    elif "tổng 1 đến n" in t:
        body_c = '    int n;\n    scanf("%d", &n);\n    long long s = 0;\n    for(int i=1; i<=n; i++) s += i;\n    printf("%lld", s);'
        body_cpp = '    int n;\n    cin >> n;\n    long long s = 0;\n    for(int i=1; i<=n; i++) s += i;\n    cout << s;'
        body_py = "n = int(input())\nprint(sum(range(1, n+1)))"
        body_java = '        int n = sc.nextInt();\n        long s = 0;\n        for(int i=1; i<=n; i++) s += i;\n        System.out.println(s);'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        long s = 0;\n        for(int i=1; i<=n; i++) s += i;\n        Console.WriteLine(s);'
    elif "giai thừa" in t:
        body_c = '    int n;\n    scanf("%d", &n);\n    long long gt = 1;\n    for(int i=1; i<=n; i++) gt *= i;\n    printf("%lld", gt);'
        body_cpp = '    int n;\n    cin >> n;\n    long long gt = 1;\n    for(int i=1; i<=n; i++) gt *= i;\n    cout << gt;'
        body_py = "import math\nn = int(input())\nprint(math.factorial(n))"
        body_java = '        int n = sc.nextInt();\n        long gt = 1;\n        for(int i=1; i<=n; i++) gt *= i;\n        System.out.println(gt);'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        long gt = 1;\n        for(int i=1; i<=n; i++) gt *= i;\n        Console.WriteLine(gt);'
    elif "bảng cửu chương" in t:
        body_c = '    int n;\n    scanf("%d", &n);\n    for(int i=1; i<=10; i++) printf("%d x %d = %d\\n", n, i, n*i);'
        body_cpp = '    int n;\n    cin >> n;\n    for(int i=1; i<=10; i++) cout << n << " x " << i << " = " << n*i << endl;'
        body_py = "n = int(input())\nfor i in range(1, 11):\n    print(f'{n} x {i} = {n*i}')"
        body_java = '        int n = sc.nextInt();\n        for(int i=1; i<=10; i++) System.out.println(n + " x " + i + " = " + (n*i));'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        for(int i=1; i<=10; i++) Console.WriteLine($"{n} x {i} = {n*i}");'
    elif "đếm ước số" in t:
        body_c = '    int n, count = 0;\n    scanf("%d", &n);\n    for(int i=1; i<=n; i++) if(n%i==0) count++;\n    printf("%d", count);'
        body_cpp = '    int n, count = 0;\n    cin >> n;\n    for(int i=1; i<=n; i++) if(n%i==0) count++;\n    cout << count;'
        body_py = "n = int(input())\nprint(sum(1 for i in range(1, n+1) if n % i == 0))"
        body_java = '        int n = sc.nextInt();\n        int count = 0;\n        for(int i=1; i<=n; i++) if(n % i == 0) count++;\n        System.out.println(count);'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        int count = 0;\n        for(int i=1; i<=n; i++) if(n % i == 0) count++;\n        Console.WriteLine(count);'
    elif "tổng số chẵn" in t:
        body_c = '    int n; scanf("%d", &n);\n    long long sum = 0;\n    for(int i=2; i<=n; i+=2) sum += i;\n    printf("%lld", sum);'
        body_cpp = '    int n; cin >> n;\n    long long sum = 0;\n    for(int i=2; i<=n; i+=2) sum += i;\n    cout << sum;'
        body_py = "n = int(input())\nprint(sum(i for i in range(2, n+1, 2)))"
        body_java = '        int n = sc.nextInt();\n        long sum = 0;\n        for(int i=2; i<=n; i+=2) sum += i;\n        System.out.println(sum);'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        long sum = 0;\n        for(int i=2; i<=n; i+=2) sum += i;\n        Console.WriteLine(sum);'
    elif "số nguyên tố" in t:
        body_c = '    int n; scanf("%d", &n);\n    if(n<2) { printf("No"); return 0; }\n    for(int i=2; i*i<=n; i++) {\n        if(n%i==0) { printf("No"); return 0; }\n    }\n    printf("Yes");'
        body_cpp = '    int n; cin >> n;\n    if(n<2) { cout << "No"; return 0; }\n    for(int i=2; i*i<=n; i++) {\n        if(n%i==0) { cout << "No"; return 0; }\n    }\n    cout << "Yes";'
        body_py = "n = int(input())\nif n < 2:\n    print('No')\nelse:\n    is_prime = True\n    for i in range(2, int(n**0.5)+1):\n        if n % i == 0:\n            is_prime = False\n            break\n    print('Yes' if is_prime else 'No')"
        body_java = '        int n = sc.nextInt();\n        if(n < 2) { System.out.println("No"); return; }\n        boolean isPrime = true;\n        for(int i=2; i*i<=n; i++) if(n%i==0) { isPrime = false; break; }\n        System.out.println(isPrime ? "Yes" : "No");'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        if(n < 2) { Console.WriteLine("No"); return; }\n        bool isPrime = true;\n        for(int i=2; i*i<=n; i++) if(n%i==0) { isPrime = false; break; }\n        Console.WriteLine(isPrime ? "Yes" : "No");'
    elif "tổng chữ số" in t:
        body_c = '    int n; scanf("%d", &n);\n    int sum = 0;\n    while(n > 0) { sum += n % 10; n /= 10; }\n    printf("%d", sum);'
        body_cpp = '    int n; cin >> n;\n    int sum = 0;\n    while(n > 0) { sum += n % 10; n /= 10; }\n    cout << sum;'
        body_py = "n = input()\nprint(sum(int(c) for c in n))"
        body_java = '        int n = sc.nextInt();\n        int sum = 0;\n        while(n > 0) { sum += n % 10; n /= 10; }\n        System.out.println(sum);'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        int sum = 0;\n        while(n > 0) { sum += n % 10; n /= 10; }\n        Console.WriteLine(sum);'
    elif "số đảo ngược" in t:
        body_c = '    int n; scanf("%d", &n);\n    int rev = 0;\n    while(n > 0) { rev = rev * 10 + n % 10; n /= 10; }\n    printf("%d", rev);'
        body_cpp = '    int n; cin >> n;\n    int rev = 0;\n    while(n > 0) { rev = rev * 10 + n % 10; n /= 10; }\n    cout << rev;'
        body_py = "print(input()[::-1])"
        body_java = '        int n = sc.nextInt();\n        int rev = 0;\n        while(n > 0) { rev = rev * 10 + n % 10; n /= 10; }\n        System.out.println(rev);'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        int rev = 0;\n        while(n > 0) { rev = rev * 10 + n % 10; n /= 10; }\n        Console.WriteLine(rev);'
    elif "fibonacci" in t:
        body_c = '    int n; scanf("%d", &n);\n    int f0=0, f1=1;\n    for(int i=0; i<n; i++) {\n        printf("%d ", f0);\n        int next = f0 + f1;\n        f0 = f1; f1 = next;\n    }'
        body_cpp = '    int n; cin >> n;\n    int f0=0, f1=1;\n    for(int i=0; i<n; i++) {\n        cout << f0 << " ";\n        int next = f0 + f1;\n        f0 = f1; f1 = next;\n    }'
        body_py = "n = int(input())\na, b = 0, 1\nfor _ in range(n):\n    print(a, end=' ')\n    a, b = b, a+b"
        body_java = '        int n = sc.nextInt();\n        int a = 0, b = 1;\n        for(int i=0; i<n; i++) {\n            System.out.print(a + " ");\n            int next = a + b;\n            a = b; b = next;\n        }'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        int a = 0, b = 1;\n        for(int i=0; i<n; i++) {\n            Console.Write(a + " ");\n            int next = a + b;\n            a = b; b = next;\n        }'

    # --- Level 4: Arrays ---
    elif "nhập xuất mảng" in t:
        body_c = '    int n; scanf("%d", &n);\n    int a[100];\n    for(int i=0; i<n; i++) scanf("%d", &a[i]);\n    for(int i=0; i<n; i++) printf("%d ", a[i]);'
        body_cpp = '    int n; cin >> n;\n    int a[100];\n    for(int i=0; i<n; i++) cin >> a[i];\n    for(int i=0; i<n; i++) cout << a[i] << " ";'
        body_py = "n = int(input())\narr = list(map(int, input().split()))\nprint(*arr)"
        body_java = '        int n = sc.nextInt();\n        int[] a = new int[n];\n        for(int i=0; i<n; i++) a[i] = sc.nextInt();\n        for(int i=0; i<n; i++) System.out.print(a[i] + " ");'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        string[] line = Console.ReadLine().Split();\n        for(int i=0; i<n; i++) Console.Write(line[i] + " ");'
    elif "tổng mảng" in t:
        body_c = '    int n; scanf("%d", &n);\n    long long sum = 0; int x;\n    for(int i=0; i<n; i++) { scanf("%d", &x); sum += x; }\n    printf("%lld", sum);'
        body_cpp = '    int n; cin >> n;\n    long long sum = 0; int x;\n    for(int i=0; i<n; i++) { cin >> x; sum += x; }\n    cout << sum;'
        body_py = "input(); print(sum(map(int, input().split())))"
        body_java = '        int n = sc.nextInt();\n        long sum = 0;\n        for(int i=0; i<n; i++) sum += sc.nextInt();\n        System.out.println(sum);'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        string[] line = Console.ReadLine().Split();\n        long sum = 0;\n        for(int i=0; i<n; i++) sum += int.Parse(line[i]);\n        Console.WriteLine(sum);'
    elif "max min mảng" in t:
        body_c = '    int n; scanf("%d", &n);\n    int a[100];\n    for(int i=0; i<n; i++) scanf("%d", &a[i]);\n    int min=a[0], max=a[0];\n    for(int i=1; i<n; i++) {\n        if(a[i]<min) min=a[i];\n        if(a[i]>max) max=a[i];\n    }\n    printf("%d %d", max, min);'
        body_cpp = '    int n; cin >> n;\n    int a[100];\n    for(int i=0; i<n; i++) cin >> a[i];\n    int min=a[0], max=a[0];\n    for(int i=1; i<n; i++) {\n        if(a[i]<min) min=a[i];\n        if(a[i]>max) max=a[i];\n    }\n    cout << max << " " << min;'
        body_py = "input(); arr = list(map(int, input().split())); print(max(arr), min(arr))"
        body_java = '        int n = sc.nextInt();\n        int[] a = new int[n];\n        for(int i=0; i<n; i++) a[i] = sc.nextInt();\n        int min=a[0], max=a[0];\n        for(int x : a) { if(x < min) min = x; if(x > max) max = x; }\n        System.out.println(max + " " + min);'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        string[] line = Console.ReadLine().Split();\n        int[] a = Array.ConvertAll(line, int.Parse);\n        int max = a[0], min = a[0];\n        foreach(int x in a) { if(x > max) max = x; if(x < min) min = x; }\n        Console.WriteLine(max + " " + min);'
    elif "đếm số chẵn mảng" in t:
        body_c = '    int n; scanf("%d", &n); int count = 0, x;\n    for(int i=0; i<n; i++) { scanf("%d", &x); if(x%2==0) count++; }\n    printf("%d", count);'
        body_cpp = '    int n; cin >> n; int count = 0, x;\n    for(int i=0; i<n; i++) { cin >> x; if(x%2==0) count++; }\n    cout << count;'
        body_py = "input(); arr = list(map(int, input().split())); print(sum(1 for x in arr if x % 2 == 0))"
        body_java = '        int n = sc.nextInt(); int count = 0;\n        for(int i=0; i<n; i++) if(sc.nextInt() % 2 == 0) count++;\n        System.out.println(count);'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        string[] line = Console.ReadLine().Split();\n        int count = 0;\n        foreach(var s in line) if(int.Parse(s) % 2 == 0) count++;\n        Console.WriteLine(count);'
    elif "tìm k trong mảng" in t:
        body_c = '    int n; scanf("%d", &n);\n    int a[100]; for(int i=0; i<n; i++) scanf("%d", &a[i]);\n    int k; scanf("%d", &k);\n    int pos = -1;\n    for(int i=0; i<n; i++) if(a[i]==k) { pos=i+1; break; }\n    printf("%d", pos);'
        body_cpp = '    int n; cin >> n; int a[100]; for(int i=0; i<n; i++) cin >> a[i];\n    int k; cin >> k; int pos = -1;\n    for(int i=0; i<n; i++) if(a[i]==k) { pos=i+1; break; }\n    cout << pos;'
        body_py = "n = int(input()); arr = list(map(int, input().split())); k = int(input())\ntry: print(arr.index(k) + 1)\nexcept: print(-1)"
        body_java = '        int n = sc.nextInt(); int[] a = new int[n]; for(int i=0; i<n; i++) a[i] = sc.nextInt();\n        int k = sc.nextInt(); int pos = -1;\n        for(int i=0; i<n; i++) if(a[i]==k) { pos=i+1; break; }\n        System.out.println(pos);'
        body_cs = '        int n = int.Parse(Console.ReadLine()); string[] line = Console.ReadLine().Split(); int[] a = Array.ConvertAll(line, int.Parse);\n        int k = int.Parse(Console.ReadLine()); int pos = -1;\n        for(int i=0; i<n; i++) if(a[i]==k) { pos=i+1; break; }\n        Console.WriteLine(pos);'
    elif "mảng đảo ngược" in t:
        body_c = '    int n; scanf("%d", &n);\n    int a[100];\n    for(int i=0; i<n; i++) scanf("%d", &a[i]);\n    for(int i=n-1; i>=0; i--) printf("%d ", a[i]);'
        body_cpp = '    int n; cin >> n;\n    int a[100];\n    for(int i=0; i<n; i++) cin >> a[i];\n    for(int i=n-1; i>=0; i--) cout << a[i] << " ";'
        body_py = "input(); arr = input().split(); print(*arr[::-1])"
        body_java = '        int n = sc.nextInt();\n        int[] a = new int[n];\n        for(int i=0; i<n; i++) a[i] = sc.nextInt();\n        for(int i=n-1; i>=0; i--) System.out.print(a[i] + " ");'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        string[] line = Console.ReadLine().Split();\n        for(int i=n-1; i>=0; i--) Console.Write(line[i] + " ");'
    elif "sắp xếp tăng dần" in t:
        body_c = '    int n; scanf("%d", &n);\n    int a[100];\n    for(int i=0; i<n; i++) scanf("%d", &a[i]);\n    for(int i=0; i<n-1; i++) for(int j=i+1; j<n; j++) if(a[i]>a[j]) {int t=a[i]; a[i]=a[j]; a[j]=t;}\n    for(int i=0; i<n; i++) printf("%d ", a[i]);'
        body_cpp = '    int n; cin >> n;\n    int a[100];\n    for(int i=0; i<n; i++) cin >> a[i];\n    for(int i=0; i<n-1; i++) for(int j=i+1; j<n; j++) if(a[i]>a[j]) swap(a[i], a[j]);\n    for(int i=0; i<n; i++) cout << a[i] << " ";'
        body_py = "input(); arr = list(map(int, input().split())); arr.sort(); print(*arr)"
        body_java = '        int n = sc.nextInt();\n        int[] a = new int[n];\n        for(int i=0; i<n; i++) a[i] = sc.nextInt();\n        java.util.Arrays.sort(a);\n        for(int x : a) System.out.print(x + " ");'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        string[] line = Console.ReadLine().Split();\n        int[] a = Array.ConvertAll(line, int.Parse);\n        Array.Sort(a);\n        foreach(int x in a) Console.Write(x + " ");'
    elif "trung bình cộng mảng" in t:
        body_c = '    int n; scanf("%d", &n);\n    double sum = 0; int x;\n    for(int i=0; i<n; i++) { scanf("%d", &x); sum += x; }\n    printf("%.2f", sum/n);'
        body_cpp = '    int n; cin >> n;\n    double sum = 0; int x;\n    for(int i=0; i<n; i++) { cin >> x; sum += x; }\n    printf("%.2f", sum/n);'
        body_py = "n = int(input()); arr = list(map(int, input().split())); print(f'{sum(arr)/n:.2f}')"
        body_java = '        int n = sc.nextInt();\n        double sum = 0;\n        for(int i=0; i<n; i++) sum += sc.nextInt();\n        System.out.printf("%.2f", sum/n);'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        string[] line = Console.ReadLine().Split();\n        double sum = 0;\n        foreach(var s in line) sum += int.Parse(s);\n        Console.WriteLine((sum/n).ToString("F2"));'
    elif "số lớn thứ 2" in t:
        body_c = '    int n; scanf("%d", &n);\n    int a[100];\n    for(int i=0; i<n; i++) scanf("%d", &a[i]);\n    for(int i=0; i<n-1; i++) for(int j=i+1; j<n; j++) if(a[i]<a[j]) {int t=a[i]; a[i]=a[j]; a[j]=t;}\n    int first = a[0];\n    for(int i=1; i<n; i++) if(a[i] < first) { printf("%d", a[i]); return 0; }'
        body_cpp = '    int n; cin >> n;\n    int a[100];\n    for(int i=0; i<n; i++) cin >> a[i];\n    for(int i=0; i<n-1; i++) for(int j=i+1; j<n; j++) if(a[i]<a[j]) swap(a[i], a[j]);\n    int first = a[0];\n    for(int i=1; i<n; i++) if(a[i] < first) { cout << a[i]; return 0; }'
        body_py = "input(); arr = sorted(list(set(map(int, input().split()))), reverse=True)\nprint(arr[1] if len(arr) > 1 else arr[0])"
        body_java = '        int n = sc.nextInt();\n        java.util.TreeSet<Integer> set = new java.util.TreeSet<>();\n        for(int i=0; i<n; i++) set.add(sc.nextInt());\n        if(set.size() < 2) System.out.println(set.first());\n        else { set.pollLast(); System.out.println(set.last()); }'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        string[] line = Console.ReadLine().Split();\n        int[] a = Array.ConvertAll(line, int.Parse);\n        var sortedUnique = a.Distinct().OrderByDescending(x => x).ToArray();\n        Console.WriteLine(sortedUnique.Length > 1 ? sortedUnique[1] : sortedUnique[0]);'
    elif "chèn phần tử" in t:
        body_c = '    int n, a[100], x, k;\n    scanf("%d", &n);\n    for(int i=0; i<n; i++) scanf("%d", &a[i]);\n    scanf("%d %d", &x, &k);\n    for(int i=n; i>k; i--) a[i] = a[i-1];\n    a[k] = x;\n    for(int i=0; i<=n; i++) printf("%d ", a[i]);'
        body_cpp = '    int n, a[100], x, k;\n    cin >> n;\n    for(int i=0; i<n; i++) cin >> a[i];\n    cin >> x >> k;\n    for(int i=n; i>k; i--) a[i] = a[i-1];\n    a[k] = x;\n    for(int i=0; i<=n; i++) cout << a[i] << " ";'
        body_py = "n = int(input()); arr = input().split(); x, k = input().split(); arr.insert(int(k), x); print(*arr)"
        body_java = '        int n = sc.nextInt();\n        java.util.ArrayList<Integer> list = new java.util.ArrayList<>();\n        for(int i=0; i<n; i++) list.add(sc.nextInt());\n        int x = sc.nextInt(), k = sc.nextInt();\n        list.add(k, x);\n        for(int val : list) System.out.print(val + " ");'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        var list = new List<string>(Console.ReadLine().Split());\n        string[] add = Console.ReadLine().Split();\n        list.Insert(int.Parse(add[1]), add[0]);\n        Console.WriteLine(string.Join(" ", list));'

    # --- Level 5: Algorithms ---
    elif "ucln" in t:
        body_c = '    int a, b; scanf("%d %d", &a, &b);\n    int mul = a*b;\n    while(b!=0){int r=a%b; a=b; b=r;}\n    printf("%d %d", a, mul/a);'
        body_cpp = '    int a, b; cin >> a >> b;\n    int mul = a*b;\n    while(b!=0){int r=a%b; a=b; b=r;}\n    cout << a << " " << mul/a;'
        body_py = "import math\na, b = map(int, input().split())\ngcd = math.gcd(a, b)\nprint(gcd, (a*b)//gcd)"
        body_java = '        int a = sc.nextInt(); int b = sc.nextInt();\n        int mul = a*b; int temp_a = a, temp_b = b;\n        while(temp_b!=0){int r=temp_a%temp_b; temp_a=temp_b; temp_b=r;}\n        System.out.println(temp_a + " " + (mul/temp_a));'
        body_cs = '        string[] line = Console.ReadLine().Split();\n        int a = int.Parse(line[0]); int b = int.Parse(line[1]);\n        int mul = a * b; int temp_a = a, temp_b = b;\n        while(temp_b != 0) { int r = temp_a % temp_b; temp_a = temp_b; temp_b = r; }\n        Console.WriteLine(temp_a + " " + (mul / temp_a));'
    elif "đối xứng" in t:
        body_c = '    char s[100]; scanf("%s", s);\n    int n=0; while(s[n]) n++;\n    for(int i=0; i<n/2; i++) if(s[i]!=s[n-1-i]) { printf("No"); return 0; }\n    printf("Yes");'
        body_cpp = '    string s; cin >> s;\n    for(int i=0; i<s.length()/2; i++) if(s[i]!=s[s.length()-1-i]) { cout << "No"; return 0; }\n    cout << "Yes";'
        body_py = "s = input()\nprint('Yes' if s == s[::-1] else 'No')"
        body_java = '        String s = sc.next();\n        boolean ok = true;\n        for(int i=0; i<s.length()/2; i++) if(s.charAt(i)!=s.charAt(s.length()-1-i)) ok = false;\n        System.out.println(ok ? "Yes" : "No");'
        body_cs = '        string s = Console.ReadLine();\n        bool ok = true;\n        for(int i=0; i<s.Length/2; i++) if(s[i] != s[s.Length-1-i]) ok = false;\n        Console.WriteLine(ok ? "Yes" : "No");'
    elif "đếm từ" in t or "đếm từ trong" in t:
        body_c = '    char s[1000]; if(!fgets(s, sizeof(s), stdin)) { printf("0"); return 0; }\n    int count = 0; char *p = strtok(s, " \t\n"); while(p) { count++; p = strtok(NULL, " \t\n"); }\n    printf("%d", count);'
        body_cpp = '    string s; getline(cin, s); int cnt = 0; bool inw = false;\n    for(char c: s) { if(!isspace((unsigned char)c) && !inw) { inw = true; cnt++; } else if(isspace((unsigned char)c)) inw = false; }\n    cout << cnt;'
        body_py = "s = input().strip()\nprint(0 if not s else len(s.split()))"
        body_java = '        String s = sc.nextLine().trim();\n        if(s.isEmpty()) System.out.println(0); else System.out.println(s.split("\\\\s+").length);'
        body_cs = "        string s = Console.ReadLine();\n        if(string.IsNullOrWhiteSpace(s)) Console.WriteLine(0); else Console.WriteLine(s.Split(new char[]{' ', '\\t'}, StringSplitOptions.RemoveEmptyEntries).Length);"
    elif "sắp xếp tên" in t:
        body_c = '    int n; if(scanf("%d", &n)!=1) return 0; char tmp[100]; char names[100][100];\n    getchar();\n    for(int i=0; i<n; i++) { fgets(names[i], 100, stdin); int l = strlen(names[i]); if(l && names[i][l-1]==\'\\n\') names[i][l-1] = 0; }\n    for(int i=0; i<n-1; i++) for(int j=i+1; j<n; j++) if(strcmp(names[i], names[j])>0) { strcpy(tmp, names[i]); strcpy(names[i], names[j]); strcpy(names[j], tmp); }\n    for(int i=0; i<n; i++) printf("%s\n", names[i]);'
        body_cpp = '    int n; if(!(cin >> n)) return 0; vector<string> a(n); string line; getline(cin, line);\n    for(int i=0; i<n; i++) { getline(cin, a[i]); } sort(a.begin(), a.end()); for(auto &s: a) cout << s << "\\n";'
        body_py = "n = int(input())\nnames = [input().strip() for _ in range(n)]\nnames.sort()\nprint('\n'.join(names))"
        body_java = '        int n = Integer.parseInt(sc.nextLine());\n        String[] a = new String[n];\n        for(int i=0; i<n; i++) a[i] = sc.nextLine();\n        java.util.Arrays.sort(a);\n        for(String s : a) System.out.println(s);'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        string[] a = new string[n];\n        for(int i=0; i<n; i++) a[i] = Console.ReadLine();\n        Array.Sort(a);\n        foreach(var s in a) Console.WriteLine(s);'
    elif "tháp hình sao" in t:
        body_c = '    int n; scanf("%d", &n);\n    for(int i=1; i<=n; i++) {\n        for(int j=0; j<n-i; j++) printf(" ");\n        for(int j=0; j<2*i-1; j++) printf("*");\n        printf("\\n");\n    }'
        body_cpp = '    int n; cin >> n;\n    for(int i=1; i<=n; i++) {\n        for(int j=0; j<n-i; j++) cout << " ";\n        for(int j=0; j<2*i-1; j++) cout << "*";\n        cout << endl;\n    }'
        body_py = "n = int(input())\nfor i in range(1, n+1):\n    print(' '*(n-i) + '*'*(2*i-1))"
        body_java = '        int n = sc.nextInt();\n        for(int i=1; i<=n; i++) {\n            for(int j=0; j<n-i; j++) System.out.print(" ");\n            for(int j=0; j<2*i-1; j++) System.out.print("*");\n            System.out.println();\n        }'
        body_cs = '        int n = int.Parse(Console.ReadLine());\n        for(int i=1; i<=n; i++) {\n            for(int j=0; j<n-i; j++) Console.Write(" ");\n            for(int j=0; j<2*i-1; j++) Console.Write("*");\n            Console.WriteLine();\n        }'
    elif "ma trận chuyển vị" in t:
        body_c = '    int r, c; scanf("%d %d", &r, &c); int a[10][10];\n    for(int i=0; i<r; i++) for(int j=0; j<c; j++) scanf("%d", &a[i][j]);\n    for(int j=0; j<c; j++) { for(int i=0; i<r; i++) printf("%d ", a[i][j]); printf("\\n"); }'
        body_cpp = '    int r, c; cin >> r >> c; int a[10][10];\n    for(int i=0; i<r; i++) for(int j=0; j<c; j++) cin >> a[i][j];\n    for(int j=0; j<c; j++) { for(int i=0; i<r; i++) cout << a[i][j] << " "; cout << endl; }'
        body_py = "r, c = map(int, input().split()); a = [input().split() for _ in range(r)];\nfor j in range(c): print(*(a[i][j] for i in range(r)))"
        body_java = '        int r = sc.nextInt(), c = sc.nextInt(); int[][] a = new int[r][c];\n        for(int i=0; i<r; i++) for(int j=0; j<c; j++) a[i][j] = sc.nextInt();\n        for(int j=0; j<c; j++) { for(int i=0; i<r; i++) System.out.print(a[i][j] + " "); System.out.println(); }'
        body_cs = '        string[] dim = Console.ReadLine().Split(); int r = int.Parse(dim[0]), c = int.Parse(dim[1]);\n        int[,] a = new int[r, c]; for(int i=0; i<r; i++) { string[] row = Console.ReadLine().Split(); for(int j=0; j<c; j++) a[i,j] = int.Parse(row[j]); }\n        for(int j=0; j<c; j++) { for(int i=0; i<r; i++) Console.Write(a[i,j] + " "); Console.WriteLine(); }'
    elif "tổ hợp" in t:
        body_c = '    int n, k; scanf("%d %d", &n, &k); long long res=1;\n    for(int i=1; i<=k; i++) res = res * (n-i+1) / i; printf("%lld", res);'
        body_cpp = '    int n, k; cin >> n >> k; long long res=1;\n    for(int i=1; i<=k; i++) res = res * (n-i+1) / i; cout << res;'
        body_py = "from math import comb; n, k = map(int, input().split()); print(comb(n, k))"
        body_java = '        int n = sc.nextInt(), k = sc.nextInt(); long res = 1;\n        for(int i=1; i<=k; i++) res = res * (n-i+1) / i; System.out.println(res);'
        body_cs = '        string[] line = Console.ReadLine().Split(); int n = int.Parse(line[0]), k = int.Parse(line[1]); long res = 1;\n        for(int i=1; i<=k; i++) res = res * (n-i+1) / i; Console.WriteLine(res);'
    elif "liệt kê số nguyên tố" in t:
        body_c = '    int n; scanf("%d", &n);\n    for(int i=2; i<n; i++) { int ok=1; for(int j=2; j*j<=i; j++) if(i%j==0) { ok=0; break; } if(ok) printf("%d ", i); }'
        body_cpp = '    int n; cin >> n; for(int i=2; i<n; i++) { bool ok=true; for(int j=2; j*j<=i; j++) if(i%j==0) { ok=false; break; } if(ok) cout << i << " "; }'
        body_py = "n = int(input()); print(*(i for i in range(2, n) if all(i % j != 0 for j in range(2, int(i**0.5)+1))))"
        body_java = '        int n = sc.nextInt(); for(int i=2; i<n; i++) { boolean ok=true; for(int j=2; j*j<=i; j++) if(i%j==0) { ok=false; break; } if(ok) System.out.print(i + " "); }'
        body_cs = '        int n = int.Parse(Console.ReadLine()); for(int i=2; i<n; i++) { bool ok=true; for(int j=2; j*j<=i; j++) if(i%j==0) { ok=false; break; } if(ok) Console.Write(i + " "); }'
    elif "chuyển nhị phân" in t:
        body_c = '    int n; scanf("%d", &n); if(n==0) printf("0");\n    int b[32], i=0; while(n>0){ b[i++]=n%2; n/=2; } for(int j=i-1; j>=0; j--) printf("%d", b[j]);'
        body_cpp = '    int n; cin >> n; if(n==0) cout << "0"; int b[32], i=0; while(n>0){ b[i++]=n%2; n/=2; } for(int j=i-1; j>=0; j--) cout << b[j];'
        body_py = "print(bin(int(input()))[2:])"
        body_java = '        int n = sc.nextInt(); System.out.println(Integer.toBinaryString(n));'
        body_cs = '        int n = int.Parse(Console.ReadLine()); Console.WriteLine(Convert.ToString(n, 2));'
    elif "tổng đường chéo chính" in t:
        body_c = '    int n; scanf("%d", &n); int sum=0, x;\n    for(int i=0; i<n; i++) for(int j=0; j<n; j++) { scanf("%d", &x); if(i==j) sum+=x; }\n    printf("%d", sum);'
        body_cpp = '    int n; cin >> n; int sum=0, x;\n    for(int i=0; i<n; i++) for(int j=0; j<n; j++) { cin >> x; if(i==j) sum+=x; }\n    cout << sum;'
        body_py = "n = int(input()); sum_d = 0\nfor i in range(n):\n    row = list(map(int, input().split()))\n    sum_d += row[i]\nprint(sum_d)"
        body_java = '        int n = sc.nextInt(); int sum = 0;\n        for(int i=0; i<n; i++) for(int j=0; j<n; j++) { int x = sc.nextInt(); if(i==j) sum += x; }\n        System.out.println(sum);'
        body_cs = '        int n = int.Parse(Console.ReadLine()); int sum = 0;\n        for(int i=0; i<n; i++) { string[] row = Console.ReadLine().Split(); sum += int.Parse(row[i]); }\n        Console.WriteLine(sum);'

    else:
        # Generic Placeholder
        body_c = '    // Code logic here\n    int n; if(scanf("%d", &n)) printf("%d", n);'
        body_cpp = '    int n; if(cin >> n) cout << n;'
        body_py = "n = input()\nprint(n)"
        body_java = '        if(sc.hasNext()) System.out.println(sc.next());'
        body_cs = '        Console.WriteLine(Console.ReadLine());'

    # Build full code
    if lang == 'c': return c_tmpl.format(body=body_c)
    if lang == 'cpp': return cpp_tmpl.format(body=body_cpp)
    if lang == 'python': return py_tmpl.format(body=body_py)
    if lang == 'java': return java_tmpl.format(body=body_java)
    if lang == 'csharp': return cs_tmpl.format(body=body_cs)
    
    return ""


def process_level(level_list, category_name):
    for p in level_list:
        p["category"] = category_name
        
        # 0. Enrich Description with Examples
        original_desc = p["description"]
        if p["test_cases"]:
            first_tc = p["test_cases"][0]
            example_md = f"\n\n### Ví dụ:\n**Đầu vào:**\n```text\n{first_tc['input']}\n```\n**Đầu ra:**\n```text\n{first_tc['output']}\n```"
            p["description"] = original_desc + example_md

        # 1. STARTER CODE (Templates)
        # Python
        py_start = "# Viết code của bạn ở đây\n"
        if "Nhập" in p["description"]:
             py_start += "# import sys\n# input = sys.stdin.read\n"
        
        p["starter_code"] = {
            "python": py_start,
            "c": f"// {p['title']}\n#include <stdio.h>\n\nint main() {{\n    // Viết code của bạn ở đây\n    \n    return 0;\n}}",
            "cpp": f"// {p['title']}\n#include <iostream>\nusing namespace std;\n\nint main() {{\n    // Viết code của bạn ở đây\n    \n    return 0;\n}}",
            "java": f"// {p['title']}\nimport java.util.Scanner;\n\npublic class Main {{\n    public static void main(String[] args) {{\n        Scanner sc = new Scanner(System.in);\n        // Viết code của bạn ở đây\n    }}\n}}",
            "csharp": f"// {p['title']}\nusing System;\n\nclass Program {{\n    static void Main() {{\n        // Viết code của bạn ở đây\n    }}\n}}"
        }

        # 2. SOLUTION CODE (Correct Answer)
        p["solution_code"] = {
            "python": generate_solution(p, 'python'),
            "c": generate_solution(p, 'c'),
            "cpp": generate_solution(p, 'cpp'),
            "java": generate_solution(p, 'java'), # Naive
            "csharp": generate_solution(p, 'csharp')
        }
        
        final_data.append(p)

process_level(level_1, "Level 1: Nhập xuất & Tính toán")
process_level(level_2, "Level 2: Cấu trúc rẽ nhánh")
process_level(level_3, "Level 3: Vòng lặp")
process_level(level_4, "Level 4: Mảng & Chuỗi")
process_level(level_5, "Level 5: Giải thuật & Nâng cao")

# Assign IDs
for i, p in enumerate(final_data):
    p["id"] = i + 1

# Write to file
with open("problems.json", "w", encoding="utf-8") as f:
    json.dump(final_data, f, indent=2, ensure_ascii=False)

print(f"Generated {len(final_data)} problems in problems.json")
