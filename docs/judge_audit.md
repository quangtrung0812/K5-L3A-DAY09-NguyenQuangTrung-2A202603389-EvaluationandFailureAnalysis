# Judge audit

Chạy:
- `python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 5`
- `python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5`

| Tiêu chí | n | κ | Precision | Recall | Confusion (`tp/fp/fn/tn`) | Fail rate (obs → RG) | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|---|---|
| `tone_ok` | 100 | 0.757 | 0.857 | 0.800 | `tp=24, fp=4, fn=6, tn=66` | `0.280 → 0.300` | **ĐẠT (PASS)** | **Dùng** (theo dõi / cần tinh chỉnh rubric) |
| `helpful` | 100 | 0.375 | 1.000 | 0.300 | `tp=9, fp=0, fn=21, tn=70` | `0.090 → 0.300` | **KHÔNG ĐẠT (FAIL)** | **Loại** (tuyệt đối không dùng làm gate) |

## ≥5 case audit thủ công
| # | Case | Judge nói | Người nói | Ai đúng? | Phân tích nguyên nhân & Hành động sửa rubric / hệ thống |
|---|---|---|---|---|---|
| 1 | `H-008` (`tone_ok`): *"Em đã hoàn tiền cho anh rồi nha, anh check giúp em."* | `PASS` | `FAIL` | **Người đúng** (FN) | Xưng `"em"` + `"nha"` quá suồng sã so với chuẩn CSKH LogiX (`"Dạ... anh/chị... ạ"`). **Sửa rubric `tone_ok`:** thêm quy tắc cấm đại từ suồng sã (`em`, `bạn`, `nha`, `nhé`) và bắt buộc xưng `LogiX` - `anh/chị`. |
| 2 | `H-029` (`tone_ok`): *"Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm."* | `PASS` | `FAIL` | **Người đúng** (FN) | Judge bị đánh lừa bởi cụm mở đầu `"Dạ, vui lòng"` mà bỏ qua vế mệnh lệnh gây khó chịu `"không cần nhắn thêm"`. **Sửa rubric `tone_ok`:** yêu cầu đánh giá toàn bộ câu, đánh `FAIL` mọi mệnh lệnh chặn tương tác của khách. |
| 3 | `H-042` (`tone_ok`): *"Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ."* | `FAIL` | `PASS` | **Người đúng** (FP) | Câu trả lời lịch sự, đúng chuẩn xưng hô và đủ thông tin nhưng bị judge phạt oan vì "thiếu lời xin lỗi". **Sửa rubric `tone_ok`:** bỏ yêu cầu bắt buộc phải có câu xin lỗi dài dòng khi thông báo hoàn tiền thành công. |
| 4 | `H-051` (`tone_ok`): *"Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ."* | `FAIL` | `PASS` | **Người đúng** (FP) | Quy định CSKH LogiX cho phép dùng thuật ngữ `"refund"`, nhưng judge tự phạt vì chêm tiếng Anh. **Sửa rubric `tone_ok`:** liệt kê `"refund"`, `"claim"`, `"order"` vào danh sách thuật ngữ được phép dùng. |
| 5 | `H-063` (`tone_ok`): *"Dạ, LogiX đã hoàn 20.000đ và sẽ hoàn thêm cho anh/chị ạ."* | `PASS` | `FAIL` | **Người đúng** (FN) | Tự ý hứa hẹn `"sẽ hoàn thêm"` ngoài kết quả hệ thống. **Sửa rubric `tone_ok` + code grader:** cấm cam kết phát sinh ngoài kết quả đã chốt trong sổ cái. |
| 6 | `H-070` (`tone_ok`): *"Dạ, LogiX đã hoàn 90.000đ cho đơn O-909 ạ 😂😂"* | `PASS` | `FAIL` | **Người đúng** (FN) | Dùng emoji cười cợt `😂😂` không phù hợp ngữ cảnh giải quyết khiếu nại. **Sửa rubric `tone_ok`:** đánh `FAIL` mọi câu trả lời chứa emoji không trang trọng. |
| 7 | `H-081` (`tone_ok`): *"Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành ạ."* | `FAIL` | `PASS` | **Judge đúng** (FP giả) | Người gán nhãn đọc nhầm sang cột nội dung ticket; câu từ chối cụt, thiếu câu mở lời hỗ trợ thêm theo mẫu chuẩn. **Hành động:** sửa lại nhãn người (`human_label` hygiene) trước khi tái hiệu chỉnh. |
| 8 | `HL-016` (`helpful`): *"Dạ, LogiX thành thật xin lỗi anh/chị... LogiX đã hoàn 55.000đ cho đơn O-404..."* (ledger ghi `35.000đ`) | `PASS` | `FAIL` | **Người đúng** (FN) | **Verbosity / Politeness bias:** Câu trả lời lặp lại lời xin lỗi cực kỳ lễ phép nên `judge_helpful` chấm `PASS`, hoàn toàn mù trước lỗi báo sai số tiền (`55.000đ` vs ledger `35.000đ`). **Hành động:** Loại bỏ `helpful` judge khỏi việc chấm tính đúng đắn nghiệp vụ; chuyển sang code grader `ReplyLedgerMatch` (`reply_ledger_match`) và `RefundAmountCorrect`. |

## Kết luận
- **Tiêu chí được giữ (`tone_ok`):** Đạt cả 3 ngưỡng sàn (`κ = 0.757 ≥ 0.6`, `P = 0.857 ≥ 0.8`, `R = 0.800 ≥ 0.7`). Tỉ lệ lỗi quan sát là `28.0%`, sau hiệu chỉnh Rogan-Gladen với `sensitivity = 0.800` và `specificity = 66/70 ≈ 0.943` thì tỉ lệ lỗi thực ước lượng là **`30.0%`**. Tuy nhiên chỉ nên dùng để giám sát văn phong sau khi cập nhật rubric theo các lỗi FN/FP ở trên.
- **Tiêu chí bị loại (`helpful`):** Bị loại hoàn toàn khỏi CI gate vì **không đạt sàn** (`Recall = 0.300 < 0.70`, `κ = 0.375 < 0.60`; ma trận nhầm lẫn `tp=9, fp=0, fn=21, tn=70`). Trong 30 trường hợp thực sự lỗi (`FAIL`), `judge_helpful` bỏ lọt tới **21 trường hợp (`FN = 21`)**, trong đó **18/21 ca là lỗi báo sai số tiền hoàn (`FM-08`)** được ngụy trang bằng những câu xin lỗi dài dòng (tỉ lệ lỗi quan sát chỉ `9.0%` trong khi thực tế sau hiệu chỉnh Rogan-Gladen là **`30.0%`**). Dùng `helpful` làm gate sẽ tạo cảm giác an toàn giả tạo và cho lọt các lỗi sai lệch tiền bạc nghiêm trọng; mọi kiểm tra liên quan đến tiền và phê duyệt phải do **code grader** đảm nhiệm.
- **Rủi ro còn lại:** Judge chỉ mới được kiểm định trên tập dữ liệu replay đã công khai (`n = 100`); cần thu thập thêm nhãn người độc lập trên tập held-out mới mỗi khi cập nhật rubric prompt.
