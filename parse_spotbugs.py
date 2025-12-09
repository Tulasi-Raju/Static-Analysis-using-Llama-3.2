import xml.etree.ElementTree as ET
import csv

SPOTBUGS_XML = "spotbugs_report.xml"
OUTPUT_CSV = "spotbugs_issues.csv"


def parse_spotbugs_xml(xml_path: str, out_csv: str):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    rows = []

    for bug in root.iter("BugInstance"):
        bug_type = bug.get("type")
        category = bug.get("category")
        priority = bug.get("priority") 
        rank = bug.get("rank")

        source_line = bug.find("SourceLine")
        if source_line is None:
            continue

        source_file = source_line.get("sourcefile")
        start_line = source_line.get("start")

        rows.append({
            "file": source_file,
            "line": int(start_line) if start_line else None,
            "spotbugs_type": bug_type,
            "category": category,
            "priority": priority,
            "rank": rank
        })

    if not rows:
        print("No bugs found in SpotBugs XML (or parse failed).")
        return

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} SpotBugs issues to {out_csv}")


if __name__ == "__main__":
    parse_spotbugs_xml(SPOTBUGS_XML, OUTPUT_CSV)
