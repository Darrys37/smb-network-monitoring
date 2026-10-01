import argparse
import csv
import io
from contextlib import closing
import json
import sqlite3
from pathlib import Path

from repository import DEFAULT_DB_PATH


def load_report(incident_id, db_path=DEFAULT_DB_PATH):
    db_path = Path(db_path).resolve()
    if not db_path.is_file():
        raise ValueError(f"Database not found: {db_path}")

    with closing(sqlite3.connect(
        db_path.as_uri() + "?mode=ro", uri=True
    )) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("BEGIN")

        incident = connection.execute(
            "SELECT * FROM incidents WHERE id = ?",
            (incident_id,),
        ).fetchone()

        if incident is None:
            raise ValueError(f"Incident not found: {incident_id}")

        evidence = connection.execute(
            "SELECT * FROM evidence WHERE incident_id = ? ORDER BY id",
            (incident_id,),
        ).fetchall()

        diagnoses = connection.execute(
            "SELECT * FROM diagnoses WHERE incident_id = ? ORDER BY id",
            (incident_id,),
        ).fetchall()

        recovery = None
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='recoveries'").fetchone():
            row = connection.execute("SELECT * FROM recoveries WHERE incident_id=?", (incident_id,)).fetchone()
            if row:
                recovery = dict(row)
                recovery["problem"] = json.loads(recovery.pop("problem_json"))
                recovery["event"] = json.loads(recovery.pop("recovery_json"))

    incident = dict(incident)
    incident["hosts"] = json.loads(incident.pop("hosts_json"))

    evidence_records = []
    for row in evidence:
        record = dict(row)
        record["result"] = json.loads(record.pop("result_json"))
        evidence_records.append(record)

    diagnosis_records = []
    for row in diagnoses:
        record = dict(row)
        record["missing_info"] = json.loads(
            record.pop("missing_info_json")
        )
        record["next_actions"] = json.loads(
            record.pop("next_actions_json")
        )
        diagnosis_records.append(record)

    return {
        "schema_version": 2,
        "assessment_basis": (
            "Stored evidence from the diagnosis run; "
            "not necessarily the state at event time."
        ),
        "recovery_status": "verified" if recovery else "not_recorded",
        "lifecycle_status": "closed" if recovery else "unverified",
        "recovery": recovery,
        "has_evidence_and_diagnoses": bool(evidence and diagnoses),
        "incident": incident,
        "evidence": evidence_records,
        "diagnoses": diagnosis_records,
    }

def render_markdown(report):
    incident = report["incident"]
    lines = [
        f"# Hồ sơ sự cố #{incident['id']}",
        "",
        f"- Event ID: {incident['event_id']}",
        f"- Tên sự cố: {incident['name']}",
        f"- Mức độ severity: {incident['severity']}",
        f"- Thời điểm event (Unix): {incident['clock']}",
        f"- Số evidence: {len(report['evidence'])}",
        f"- Số kết quả luật: {len(report['diagnoses'])}",
        "",
        "> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; "
        "không mặc định phản ánh đúng trạng thái tại thời điểm event.",
        "",
        "> Hồ sơ chưa ghi nhận thông tin recovery. "
        "Điều này không xác nhận sự cố hiện vẫn đang diễn ra.",
        "",
        "## Kết quả chẩn đoán",
        "",
    ]

    if report.get("recovery"):
        recovery = report["recovery"]
        warning = "> Hồ sơ chưa ghi nhận thông tin recovery. Điều này không xác nhận sự cố hiện vẫn đang diễn ra."
        lines[lines.index(warning)] = (
            f"> Trạng thái hồ sơ: closed. Recovery event {recovery['recovery_event_id']}; "
            f"thời điểm Unix {recovery['recovery_clock']}; "
            f"khoảng cách hai event {recovery['recovery_clock'] - incident['clock']} giây. "
            "Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại."
        )
    for diagnosis in report["diagnoses"]:
        lines.extend([
            f"### {diagnosis['rule_id']} — {diagnosis['status']}",
            "",
            f"Nhận định: {diagnosis['reasoning']}",
            "",
        ])

        if diagnosis["probable_cause"]:
            lines.extend([
                f"Nguyên nhân khả dĩ: {diagnosis['probable_cause']}",
                "",
            ])

        for label, key in (
            ("Thông tin còn thiếu", "missing_info"),
            ("Kiểm tra tiếp theo", "next_actions"),
        ):
            if diagnosis[key]:
                lines.extend([f"**{label}:**", ""])
                lines.extend(f"- {item}" for item in diagnosis[key])
                lines.append("")

    lines.extend(["## Bằng chứng đã lưu", ""])

    for evidence in report["evidence"]:
        lines.extend([
            f"### Evidence #{evidence['id']} — {evidence['check_type']}",
            "",
            f"- Đích kiểm tra: {evidence['target']}",
            f"- Thời điểm thu thập (Unix): {evidence['collected_at']}",
            "",
            "```json",
            json.dumps(evidence["result"], ensure_ascii=False, indent=2),
            "```",
            "",
        ])

    return "\n".join(lines) + "\n"
def render_csv(report):
    """One row per diagnosis, with source evidence and recovery identity.

    Not an experiment summary: no invented Run ID, detection time or ground truth.
    """
    output = io.StringIO(newline="")
    fields = ["incident_id", "event_id", "problem_clock", "lifecycle_status",
              "recovery_event_id", "recovery_clock", "event_interval_seconds",
              "rule_id", "status", "probable_cause", "reasoning",
              "missing_info_json", "next_actions_json", "evidence_json"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    incident = report["incident"]
    recovery = report.get("recovery") or {}
    for diagnosis in report["diagnoses"]:
        row = {
            "incident_id": incident["id"], "event_id": incident["event_id"],
            "problem_clock": incident["clock"],
            "lifecycle_status": report["lifecycle_status"],
            "recovery_event_id": recovery.get("recovery_event_id", ""),
            "recovery_clock": recovery.get("recovery_clock", ""),
            "event_interval_seconds": (recovery["recovery_clock"] - incident["clock"]) if recovery else "",
            "rule_id": diagnosis["rule_id"], "status": diagnosis["status"],
            "probable_cause": diagnosis["probable_cause"] or "",
            "reasoning": diagnosis["reasoning"],
            "missing_info_json": json.dumps(diagnosis["missing_info"], ensure_ascii=False),
            "next_actions_json": json.dumps(diagnosis["next_actions"], ensure_ascii=False),
            "evidence_json": json.dumps(report["evidence"], ensure_ascii=False),
        }
        # Neutralize spreadsheet formula prefixes in user/API text.
        writer.writerow({k: ("'" + v if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@")) else v)
                         for k, v in row.items()})
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(
        description="Export a stored incident dossier as JSON."
    )
    parser.add_argument("--incident-id", type=int, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--format", choices=("json", "md", "csv"), default="json")
    args = parser.parse_args()

    try:
        report = load_report(args.incident_id, args.db)
        content = (render_markdown(report) if args.format == "md" else
                   render_csv(report) if args.format == "csv" else
                   json.dumps(report, ensure_ascii=False, indent=2))

        if args.output is None:
            print(content)
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            # Refuse to overwrite an existing report.
            with args.output.open("x", encoding="utf-8", newline="") as output:
                output.write(content + "\n")
            print("Report saved:", args.output)

    except (ValueError, sqlite3.Error, OSError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
