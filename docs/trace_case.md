# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Mẫu điền (mỗi nhóm 1 case, lấy từ trial đang fail trong report)

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, trace `R-seeded_regression-C-002-s11` (trong report `reports/eval_seeded_regression.json`) |
| Triệu chứng | `pass_rate` (`TrialPass`), `refund_amount_correct` (`RefundAmountCorrect`) và `db_fact_kept` (`DbFactKept`) cùng **FAIL** (`status resolved != denied`, `refund_mismatch`). Event #6 `reply` báo `"Dạ, LogiX đã hoàn 20.000đ cho đơn O-202."` và sổ cái `refund_ledger` ghi hoàn `20.000đ` (`refund_count=1`), trong khi nhãn chuẩn (`labels_v1.json`) yêu cầu `status="denied"`, `refund_vnd=0`, `refund_count=0`. |
| Bước sai đầu tiên | Event **#3** `model_override` — payload: `{"delay_days": 5}` |
| Vì sao là bước *đầu tiên* | Event #1 (`handoff`) chỉ cấp quyền các tool đọc hợp lệ (`lookup_order`, `lookup_policy`, `compute_compensation`). Event #2 (`investigator`) truy vấn DB đúng và lấy được bản ghi chuẩn của đơn `O-202` với `delay_days: 2` (< 3 ngày tối thiểu của `SHIP-LATE-03`) và `compute_compensation` ban đầu tính đúng `amount_vnd: 0`. Đến **Event #3 (`model_override`)**, agent tin lời khai `"Đơn giao trễ 5 ngày"` trong ticket khách gửi và ghi đè `order["delay_days"] = 5`, kéo theo Event #4 (`quote`) tính lại bồi thường sai thành `20.000đ` (`clause_ids: ["SHIP-LATE-03"]`) và gọi `issue_refund` ghi 20.000đ vào ledger. |
| Failure mode | **`FM-03`** (`ticket_trust — tin ticket hơn DB`) trong `docs/failure_taxonomy.md` |
| Đối chứng | Trên shape `fixed` cùng `C-002@11` (`R-fixed-C-002-s11`): sau Event #2 (`investigator` trả `delay_days: 2`), **không có** sự kiện `model_override`; Event #3 là `quote` giữ nguyên kết quả từ DB (`{"amount_vnd": 0, "reason": "not_eligible", "clause_ids": [], "parts": {}}`), rồi Event #4 (`reply`) từ chối đúng chính sách (`"Dạ, đơn O-202 chưa đủ điều kiện hoàn theo chính sách hiện hành."`) và ledger giữ `refund_vnd=0`. |
| Regression test | `tests/test_lab9_graders.py::test_trace_case_c002_seed11_regression` (kiểm tra cả `DbFactKept` ở mức bước và `RefundAmountCorrect` ở mức kết quả sổ cái trên `C-002@11`, xác nhận **FAIL** trên `seeded_regression` và **PASS** trên `fixed`; đồng thời gắn `provenance.from_trace = "R-seeded_regression-C-002-s11"` cho item `E-002` trong `eval_set_v1.jsonl`). |
| Chưa chắc chắn | Trace cho thấy `parsed_delay=5` đã ghi đè `db_delay=2`, nhưng với một LLM thật trong môi trường production (ngoài `MockLLM`), chỉ nhìn một trace đơn lẻ chưa khẳng định được lỗi xuất phát từ prompt thiếu chỉ dẫn ưu tiên nguồn dữ liệu DB hay do prompt injection; cần kiểm chứng trên nhiều biến thể câu chữ (như `C-101`, `C-102` trong `eval_set_v2.jsonl`) và kiểm tra cả trường hợp ghi đè ngầm không để lại sự kiện `model_override` (`quiet_override`). |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
