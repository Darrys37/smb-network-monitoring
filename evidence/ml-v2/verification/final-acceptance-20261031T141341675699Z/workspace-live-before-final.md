# Active ML execution index

## Live milestone — 31/10/2026 20:50 UTC+7

- Foreground **74874**, parent7124, child13872. **39/42 heldout valid,1 uncertain,40 finished**; active s02/r03-05-agent_stopped. Only Agent/CPU/healthy remain. Predictions and scores still unopened. Session wake guard **61318** remains active (bounded3h from12:48UTC), must be stopped after finalization or user pause.
- The last frozen predictors/five helpers remain unchanged. Only presentation/independent QA/finalizer helpers changed: report includes expert coverage and Zabbix detection separate from classifier accuracy; QA recomputes24 family rows aligned by ID. Finalizer writes portable LF, checks Git handoff manifest, archives old progress prefixes while retaining dated baseline body. Compiled, not yet executed.
- Latest verified backup before this note was `during-sealed-test-20261031T133034384243Z` C/D, ZIP0ce170e972ede8c99da92ab77bd7b0f065f1f4973558cf591fe469469c95ba91. `checkpoint_active_test.py` will capture this note and39-run progress next. M4 benchmark and sourceHEAD79dc603 unchanged.
- Wait for full coordinator `COMPLETE_INITIAL_VM_ML`, then run review_ml_release.py, inspect three actual PNGs, run Run-ML-Demo.ps1 (Nginx, masked SSH prompt), finalize_ml_acceptance.py --figures-reviewed (masked prompt), verify commits/backups and clear guard61318. Do not rerun coordinator blindly after postprocessing has created files; inspect any concrete failure.
- User explicitly confirmed screen awake and AC on this run; no further wake question is pending. No subagents, Git push or memory writes.

## Đang thu block test thứ hai — 31/10/2026 19:59 UTC+7

- Người dùng đã yêu cầu tiếp tục sau checkpoint tạm dừng, xác nhận màn hình sáng và cắm sạc. **Đang chạy, chưa nghiệm thu xong**.
- M4:42 pilot valid/9 uncertain. M5 hiện có **21/42 test valid**, 1 uncertain; block thứ nhất đã đủ21. Giữ nguyên lượt gián đoạn và dùng retry ID mới; chưa mở dự đoán hoặc điểm test.
- Session foreground74874, coordinator7124, child13872. Khóa lab và source/model/config trước test vẫn giữ nguyên. Không chạy thêm coordinator hoặc sửa5 helper quan trọng trong lúc thu.
- Windows đã vào Modern Standby trong lần tiếp tục đầu; power event lưu ở workspace `verification/resume-power-events-20261031.json`. Preflight phục hồi `evidence/ml-v2/verification/recovered-platform-20261031T121304081495Z` đã đạt; package khớp bản khóa. Không đổi power plan, affinity/CPU/RAM VM hoặc source baseline.
- Có wake guard riêng session61318, giới hạn3giờ, để giữ liên tục tới QA/demo/backup. Phải kết thúc guard khi hoàn tất hoặc người dùng yêu cầu dừng; worker cũng có guard riêng.
- Phần còn lại: thu đủ42 test valid → mở điểm/đối chiếu SQLite+shadow → kiểm tra24 hàng đối chứng theo run ID → xem3 hình → demoNginx thật → finalizer+backup khôi phục C/D. Chưa có release cuối; không có luật active.
- Chỉ dùng kết quả cho lab baVM/lỗi đơn đã biết. Chưa có PC thật, multi-fault hoặc topology/suppression. Phân tích che feature pilot đã ghi nhận CART có thể nhầm lỗi nguồn đo; không sửa mô hình theo test để che hạn chế này.
- Các mục tạm dừng/cột mốc phía dưới là lịch sử; xem trạng thái worker hiện tại ở workspace trước khi thao tác.

## Live milestone — 31/10/2026 19:48 UTC+7

- Session74874/PID7124 child13872 still collecting. **19 valid /1 uncertain /20 finished**; active s01/r03-06-cpu_stress. Block1 needs this CPU and final Nginx, then21-run block2. No predictions opened, no frozen source changes.
- **Additional session wake guard61318** is active, receiptWORK/verification/session-awake-20261031T124830228232Z.json, bounded3hours. It bridges the gap after M5 child exits through result QA/demo/final backup. **Stop this guard with Ctrl+C after finalization or if user pauses**; context clears its temporary requests. Main worker has its own separate guard. Old maintenance90475 was stopped.
- Presentation renderer now also reports actual detection coverage and expert TP/FP/FN/coverage, with independent final QA recomputing24 family rows by run ID. These are postprocessing-only changes; frozen predictor hashes verified identical. Finalizer was adjusted to write handoff LF and verify manifest against committed Git bytes for portable restore. Helpers syntax compiled; actual release QA/figures/demo/finalizer await all42 test valid.

## Current live run — 31/10/2026 19:16 UTC+7

- Foreground session **74874**, coordinator7124, M5 child13872: collecting sealed test,11 valid/1 uncertain/12 finished. Active CPU `test-v2-s01/r02-05-cpu_stress-retry1`,330s. Do not run another coordinator or open sealed predictions.
- First resume session68673/19908/3564 STOPPED before any new fault because baseline clock=no and load alert. Windows events:506 at18:47:32,507 at19:11:23. Read-only diagnosis `resume-gate-20261031T114802541597Z.json` proved package freeze identical; stalled counters increased during idle, not test collection.
- Fresh preflight `recovered-platform-20261031T121304081495Z` passed (kernel counters49/89/98; baseline39/301/172/29). `resume-clocks-20261031T121537130201Z.json` confirms actual chrony service onall3, NTPSynchronized=yes, recovered naturally; no clock/service/policy/hardware changes. Child holds renewed display+system requests.
- Maintenance awake session90475 was stopped after child13872 established its own guard. Second preflight6943 is complete. Worker97188 failed SSH before recovery, no fault started. Power event evidenceWORK/verification/resume-power-events-20261031.json.
- Latest verified C/D source/evidence ZIP `before-locked-test-20261031T121607192624Z`, SHAabb8f4a30b994566c476a2ca91978123701ab827d69503e8eb22661cb88d4d77. User was asked asynchronously to keep host awake/AC; reply is optional to diagnosis, but do not create faults when baseline fails.

## Resumed explicitly by user — 31/10/2026 18:46 UTC+7

- User said `tiếp tục`, revoking the pause below. Current foreground session **68673**, coordinator PID19908, M5 child3564. Verify live state; never launch a second coordinator.
- M4 remains complete. M5 resumes from **11 valid /1 uncertain /12 finished**; paused CPU attempt was audited, retry must have a new ID. No test predictions or scores have been opened.
- New verified C/D backup `before-locked-test-20261031T114655584216Z`, ZIP SHA3b41774518abb81ca444367674ec549e433902d0f817bf9d5eff7f3d191c4b90. At18:47 local fresh VM backup/preflight is running; package freeze must still match before any new fault.
- Critical frozen source and five helpers stay unchanged. Continue through42 valid, postprocessing, independent QA, three figure inspections, public Nginx demo, finalizer/verified backup; follow the detailed completion sequence below. Do not claim completion from collection alone.
- Relevant memory now uses registry lines44-48 (file was reorganized); rollout ID01a14577-55f9-79e0-b912-5bb61ac0da6a.

## Tạm dừng theo yêu cầu người dùng — 2026-10-31T09:17:48.984776+00:00

- **PAUSED_BY_USER. Không tự chạy tiếp** cho tới khi người dùng yêu cầu tiếp tục.
- M4 đã hoàn tất: 42 pilot valid, 9 uncertain; benchmark `20261031T082356416394Z`.
- M5: **11/42 test valid**, 1 uncertain. Lượt CPU đang chờ baseline khi dừng được giữ nguyên và audit uncertain; không tái tạo timeline thiếu, không chấm điểm test.
- Hai coordinator12676/1784 đã dừng và khóa lab được lấy thành công để cleanup. Postflight: baseline/service/network tốt, không còn timer/firewall/stress của thí nghiệm; source engine và SQLite39/301/172/29 được giữ nguyên. Bằng chứng `C:\Users\Darrys\do-an\evidence\ml-v2\verification\paused-by-user-20261031T091748980745Z`.
- Mô hình/config và 5 helper quan trọng vẫn khóa; KHÔNG sửa để chạy tiếp. Khi được phép resume, xác minh package fingerprint ba VM khớp `locked-test-v1/lab-environment-freeze.json`; nếu đã đổi package thì dừng xem lại protocol, không bỏ gate hoặc âm thầm gộp test.
- Chưa mở dự đoán/điểm test. Chưa làm final QA, xem hình, public demo hoặc final release. `checkpoint_active_test.py` giữ raw/source/context C/D; bản chốt pause xem `paused-ml-latest.json` trong workspace.

## Latest milestone, 31/10/2026 15:44 UTC+7

- **M4 COMPLETE**: 42 valid scheduled pilot runs, 9 uncertain, 51 finished attempts. `benchmark/latest.json` -> `benchmark/20261031T082356416394Z`. Grouped internal validation: CART numeric42/42, CART discrete42/42, FP41/42 with1ABSTAIN; majority6/42, missingness-only19/42, common35/42. These are development scores, NOT final test. Exported candidate has7 CART leaves and19 FP rules. Quality summary's43valid includes an old, separate Nginx trial; training correctly exports42.
- **M5 COLLECTING**: foreground session97884 remains active (parent12676, child1784). At15:44:27 local, **5/42 fresh test valid**, 0 uncertain. Active `test-v2-s01/r01-06-cpu_stress`,330sec. First tests healthy,Agent,Nginx,DNS,remoteHTTP allvalid. Core predictors and5 critical WORK helpers are frozen: **do not edit train_v2/candidate/demo/mlv2/registry/locked_test/engine or ml_acceptance/resume/ml_supervisor/ml_vm_preflight/lab_host_guard while this test is active**. Root `locked-test-v1/development-freeze.json` and `lab-environment-freeze.json` exist. Test scores/predictions remain sealed; inspect validity/status only until all42 collected.
- Latest C/D automatic backups: `after-pilot-benchmark-20261031T082400630002Z` (ZIP b7dee1d234d2178cb85a25ead0affaffa15c7d19fdfa60bb43d3cb4158698dd94), `before-locked-test-20261031T082409344965Z` (ZIP f51c0597d523d8f38bb7a95f568ae8e7bc0a671363d62f684f4dbb2ae304984a4). GitHEAD79dc603. No new source/model tuning since freeze.
- **Known limitation established from PILOT ONLY**: `analysis-not-training/synthetic-feature-mask-20261031T083753046423Z/PHAN_TICH.md`. Fixed hypothetical feature masking of HTTP/DNS on a frozen pilot healthy vector (all corePing/TCP/control successful) causes CART interface_down, FP ABSTAIN. Explicitly synthetic feature analysis, NOT a measured lab run, not added to train/test and not a sealed-test peek. Do not change frozen models to fix it. Explain this concrete OOD/measurement-missingness limitation in final report/release notes; current research release is not production approval.
- `correct_pilot_report_scope.py` made an **editorial-only** correction in pilot REPORT: source timestamps span30–31Oct, not 'same day'. Preserved REPORT-before and before/afterSHA under `verification/pilot-prose-correction-*`; all frozen source/model/raw/manifestSHA verified unchanged. Do not edit frozen train_v2.py just to fix its generator prose during the test.
- Additional QA/finalization helpers below are ready/syntax-checked but **not yet run**. `Run-ML-Demo.ps1` now has shared lab byte locks and a temporary display/system wake request, no need to alter frozen inference code. Keep measured vs synthetic/uncertain/test counts separate.

The notes below describe earlier milestones; use live status for current counts.

User resumed on 31/10/2026 and asked earlier to continue through initial VM ML completion. Only three VMs are available; there is no physical Ubuntu PC. Do not ask that again. Keep formal heldout predictions sealed until all 42 test runs have been collected; never tune to test scores.

Current foreground exec session: **97884**, coordinator PID **12676** (verify live before acting). It runs `full_ml_session.py`: complete pilot -> M4 benchmark -> fresh interpreter M5 test -> detection audit -> figures/report -> backup. Previous session27992/PID15692 stopped after an apt MySQL/Zabbix ordering deadlock; it is not active.

At last observed milestone: 40/42 pilot valid, 9 uncertain completed; remaining interface-down and remote-HTTP-filtered. Original CPU interrupted by apt was audited uncertain; CPU retry1 and Nginx final run are valid. Poll current session/status rather than restarting. Authoritative data is `C:/Users/Darrys/do-an/evidence/ml-v2`, source `.../ml-research`; never sync the stale WORK/ml-v2 stage into it.

Latest committed checkpoint **79dc603e8704ad3172ced2cea6b9dd9f566ec6d9**, C/D restore verified in `recovery-checkpoint-latest.json`. Gate platform schema2 now audits kernel+package jobs/dpkg locks/audit/status hash; model features/labels/hyperparameters unchanged. **57 core ML tests** and **3 heldout environment tests** pass; 3 wake-guard tests pass. Baseline source remains tree44ced0643fb0d3c34673ab5b2912a5645b2894c6; VM SQLite counts39/301/172/29.

Resolved infrastructure episodes:

- Windows Modern Standby at13:48:37 UTC+7, all VM SSH stalled. User confirmed screen off/locked and woke it. Power events show wake14:01:48 SC_MONITORPOWER then14:01:51 keyboard. New `lab_host_guard.py` requests display+system and renews every15s, clears normally. PID12676 loaded this version. Old diagnostic guard sessions9101/85089 ended. Maintenance guard18684 is bounded20min and may already have ended; current coordinator owns its own guard.
- apt-daily-upgrade on MON01 stopped MySQL; Zabbix was deactivating with infinite stop timeout while MySQL start waited for it. `recover_mysql_ordering.py` first made a private cold DB/config backup (`/home/phat/ml-checkpoints/mysql-ordering-rescue-20261031T075327Z`, SHA6c1c3936457d48d10f529e8de6887aabb0f90d4f6edb872cb4511ad803f0cf86), then one-off `systemctl start mysql --job-mode=ignore-dependencies --no-block` recovered both and let apt finish. No apt kill, policy disable, unit/hardware/affinity/security change. Preflight `recovered-platform-20261031T080427843278Z` passed schema2, stall counts3/8/8, no recent stalls. Raw diagnosis/rescue metadata is in repository evidence.

After full chain succeeds:

1. Inspect actual pilot/test metrics; no scores exist merely because code is ready. M4 internal validation is not the final test.
2. Run `review_ml_release.py` (guard requires COMPLETE_INITIAL_VM_ML). It recomputes metrics from CSV, verifies42 train/42 fresh test, source/hash/equivalence/package stability/SQLite/no active rules and figures, then writes `evidence/ml-v2/ML_RELEASE.json`.
3. View the three actual PNG figures with `view_image`; fix presentation only if needed, not model/test choices.
4. Run `pwsh -NoProfile -File ./Run-ML-Demo.ps1` in WORK (masked password prompt). It acquires the same lab locks and a temporary display/system wake request, then runs healthy -> Nginx fault -> recovery with expert and ML on the same evidence. Demo rows are separate from train/test.
5. Run `finalize_ml_acceptance.py --figures-reviewed` (masked password). It validates actual demo, postflight/runtime, updates docs, commits owned paths, backs up all raw tracked source/evidence + workspace helpers on C/D, verifies CRC/per-file SHA and bundle clone/fsck/HEAD. It has been syntax-compiled, not executed yet. If a concrete error occurs, fix it from evidence; do not claim completion early.

New convenience/QA/helper files are in WORK and earlier backup context ZIPs; no passwords are written into them. SSH known_hosts uses RejectPolicy. Prior user authorized phat SSH access to192.168.56.10/.20/.30; use masked getpass, never echo or save secrets.

No subagents unless user explicitly asks. No Git push. No memory writes. Relevant memory registry was read this turn: MEMORY.md270-281 (project context), rollout01a14577-55f9-79e0-b912-5bb61ac0da6a; append required memory citation as the very last final content.
