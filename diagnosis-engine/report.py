import argparse
import json
import sqlite3
from pathlib import Path

from repository import DEFAULT_DB_PATH


def load_report(incident_id, db_path=DEFAULT_DB_PATH):
    db_path = Path(db_path).resolve()
    if not db_path.is_file():
        raise ValueError(f"Database not found: {db_path}")

    with sqlite3.connect(
        db_path.as_uri() + "?mode=ro", uri=True
    ) as connection:
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
        "schema_version": 1,
        "assessment_basis": (
            "Stored evidence from the diagnosis run; "
            "not necessarily the state at event time."
        ),
        "recovery_status": "not_recorded",
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
def main():
    parser = argparse.ArgumentParser(
        description="Export a stored incident dossier as JSON."
    )
    parser.add_argument("--incident-id", type=int, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        report = load_report(args.incident_id)
        content = json.dumps(report, ensure_ascii=False, indent=2)

        if args.output is None:
            print(content)
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            # Refuse to overwrite an existing report.
            with args.output.open("x", encoding="utf-8") as output:
                output.write(content + "\n")
            print("Report saved:", args.output)

    except (ValueError, sqlite3.Error, OSError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
