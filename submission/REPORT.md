# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: 4AM
- Repository URL: https://github.com/SAY265/Day13-K4-Observability
- Commit SHA cuối: `436ad3a`
- Thành viên và vai trò:
  - Vũ Quốc Anh - 2A202601080 (Logging & Middleware): Phụ trách CP1 (Middleware, Correlation ID, và gán log metadata).
  - Hà Xuân Sơn - 2A202601904 (Security & Compliance): Phụ trách CP1 (Uncomment processor, cấu hình regex patterns che PII và nâng cấp che PII toàn cục).
  - Chu Tuấn Việt - 2A202601082 (Metrics & Alerting): Phụ trách CP2 (Tích hợp Langfuse, đo đếm error_rate_pct, viết SLO, Alert rules và Runbook).
  - Giáp Quốc Anh - 2A202601522 (QA & Incident Analyst): Chạy load test sinh dữ liệu, thiết kế Dashboard Spec, chủ trì điều tra Challenge (CP3) và viết báo cáo REPORT.md.

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100 (tất cả 4 mục Basic JSON schema, Correlation ID propagation, Log enrichment, PII scrubbing đều PASSED)
- Tổng số traces: 10 (Langfuse API HTTP 200).
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: `config/dashboard.yaml` / `submission/evidence/cp2_dashboards.png`

## 3. Logging và tracing

- Evidence correlation ID: Chuỗi correlation IDs phát sinh từ middleware như `req-beb37343`, `req-f02927e2`, `req-19d4dc94`, `req-f7b05f93`, `req-7cef0ccd` xuất hiện đồng nhất trong cả HTTP Response Headers, Log entries và Trace metadata.
- Evidence PII redaction: Các thông tin nhạy cảm (Email, SĐT VN, Thẻ tín dụng) đã được lọc sạch trước khi ghi file log: `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CREDIT_CARD]`.
- Evidence trace waterfall: `submission/evidence/cp2_trace_verification.txt` (SDK v4 trace `fdedac458c1a2132167762bc3fc433eb`, span `run`).
- Giải thích một span đáng chú ý: Span `run` của `LabAgent` bao bọc toàn bộ luồng xử lý RAG retrieval và LLM generation, cho phép theo dõi thời gian phản hồi (latency), số token (in/out), chi phí tính toán (cost_usd) và điểm đánh giá chất lượng (quality_score).

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: `qa-v1` / `production`
- Version/label candidate: `qa-v2` / `staging`
- Trace v1/baseline: `bc8ae307ccbc7bf4949bc654db2d0daf`; trace v2/candidate: `48b353bbcb3e282dbbb60bddd469e9a5`.
- Trace sau rollback về production/v1: `589f7965cc31b14a692f0aa8bff85b2e`.
- Bằng chứng metadata và đổi label/rollback: `submission/evidence/prompt_version_rollback.txt`; ảnh giao diện Langfuse: `submission/evidence/cp2_tracing.png`.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: HỢP LỆ — 6/6 panel (`traffic`, `latency`, `error_rate`, `cost`, `quality`, `pii_leaks`).
- Evidence dashboard: `submission/evidence/cp2_metrics.json` và `submission/evidence/cp2_dashboard_validator.txt`.
- SLO đã chọn và lý do: Giữ ngưỡng lab mặc định trong `config/slo.yaml` để làm baseline đo latency (< 2000ms), error (< 5%), cost và quality (> 0.7).
- Alert rules và runbook: 3 symptom-based alerts đã điền trong `config/alert_rules.yaml` và `docs/alerts.md`.

## 6. Điều tra challenge

- Challenge ID: `day13-k4-observability-v1`
- Triệu chứng từ metrics: P95 Latency của dịch vụ tăng đột biến từ ~150ms lên **~2650ms** (vượt xa ngưỡng `latency_threshold_ms = 2000ms` trong `config/challenge.json`), trong khi tỷ lệ lỗi `error_rate_pct` vẫn giữ ở mức 0%.
- Trace ID liên quan: Các request mang Correlation IDs thuộc challenge bao gồm `req-beb37343`, `req-f02927e2`, `req-19d4dc94`, `req-f7b05f93`, `req-7cef0ccd` (xem file bằng chứng tại [submission/evidence/cp3_challenge_evidence.txt](file:///c:/Lab/Day13-K4-Observability/submission/evidence/cp3_challenge_evidence.txt)).
- Log line/correlation ID liên quan: Log warning event `incident_enabled` kích hoạt sự cố `rag_slow` tại thời điểm `ts: 2026-08-11T08:50:49.943873Z`, làm toàn bộ request thuộc feature `monitoring` sau đó bị trễ 2.5s.
- Root cause: Sự cố `rag_slow` được bật trong `app/incidents.py` khiến hàm `retrieve()` trong `app/mock_rag.py` thực thi lệnh `time.sleep(2.5)` cho mọi truy vấn liên quan đến feature `monitoring`.
- Fix action: Gửi request `POST /incidents/rag_slow/disable` hoặc gọi hàm `disable("rag_slow")` để tắt incident và đưa latency RAG về mức bình thường (~150ms).
- Preventive measure: Cấu hình Timeout tối đa cho bước truy xuất dữ liệu RAG (vd: timeout 1000ms), áp dụng Pattern Circuit Breaker và bổ sung Alert Rule tự động cảnh báo khi span RAG retrieval vượt ngưỡng 1000ms.

## 7. Đóng góp cá nhân

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Vũ Quốc Anh - 2A202601080 | Cấu hình `app/middleware.py`, tạo `correlation_id` và gán metadata request context (`user_id_hash`, `session_id`, `feature`, `model`) | `0682a8f471903e70efc91159b32dc0c39926981b` | Cách truyền vết Correlation ID xuyên suốt qua Structlog Contextvars và HTTP Headers. |
| Hà Xuân Sơn - 2A202601904 | Hoàn thiện Regex `app/pii.py`, cấu hình processor `scrub_event` trong `app/logging_config.py` | `c17869f8c8daf03d8bc66babc3066adf694be043` | Cách cấu hình pipeline lọc dữ liệu nhạy cảm PII tự động trước khi ghi log. |
| Chu Tuấn Việt - 2A202601082 | Tích hợp Langfuse SDK, cấu hình Prompt Versioning, xây dựng `config/slo.yaml` và `config/alert_rules.yaml` | `7cc95b8de0a713bbbc1f8d7ac7784c499365dafb` | Cách quản lý phiên bản prompt thực tế và đo đếm SLO / Alerting cho AI API. |
| Giáp Quốc Anh - 2A202601522 | Giả lập Load test, thiết kế Dashboard Spec, thực thi bài Challenge CP3 và tổng hợp báo cáo `REPORT.md` | `6b626f1b7157b6948f1050a2be51986083c2d1bb` | Cách phối hợp 3 trụ cột Observability (Metrics ➔ Traces ➔ Logs) để tìm Root Cause sự cố. |

## Bonus

- Cost optimization: bật giới hạn output trong `app/mock_llm.py` qua `COST_OPTIMIZATION_ENABLED=true` và `MAX_OUTPUT_TOKENS=180`. Cùng 10 truy vấn với incident `cost_spike`, tổng cost giảm từ `$0.0816` xuống `$0.0280` (giảm khoảng `65.7%`); token output giảm `5372` xuống `1800`. Evidence: `submission/evidence/bonus_cost_before.json`, `bonus_cost_after.json`, `bonus_cost_comparison.md`.
- Audit log: các sự kiện bật/tắt incident và thay đổi cấu hình được ghi JSONL vào `AUDIT_LOG_PATH` (mặc định `data/audit.jsonl`). Evidence đã loại bỏ thông tin nhạy cảm tại `submission/evidence/bonus_audit.jsonl`.
- Custom automation: `scripts/detect_anomalies.py` quét logs, SLO và PII; chạy bằng `python scripts/detect_anomalies.py`. Kết quả hiện tại phát hiện `error_rate_above_slo` trong dữ liệu lịch sử; xem `submission/evidence/bonus_anomaly_report.json`.
