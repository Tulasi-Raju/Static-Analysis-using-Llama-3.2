import json
import pandas as pd

LLM_JSON = "llm_issues.json"
SPOTBUGS_CSV = "spotbugs_issues.csv"


def map_spotbugs_category(row):
    cat = row["category"]
    bug_type = row["spotbugs_type"]

    if cat == "CORRECTNESS":
        return "CORRECTNESS"
    if cat == "PERFORMANCE":
        return "PERFORMANCE"
    if cat == "SECURITY":
        return "SECURITY"

    if cat in ("BAD_PRACTICE", "STYLE", "EXPERIMENTAL"):
        return "BAD_PRACTICE"

    return "BAD_PRACTICE"


def map_spotbugs_severity(row):
    priority = row["priority"]
    if pd.isna(priority):
        return "LOW"
    p = int(priority)
    if p == 1:
        return "HIGH"
    if p == 2:
        return "MEDIUM"
    return "LOW"


def load_llm_issues(path: str) -> pd.DataFrame:
    """
    Load llm_issues.json and normalize columns to:
    file, line, category, severity, title, description

    This function is defensive: it tries to handle different JSON shapes and
    different key names produced by the LLM.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        for key in ["issues", "bugs", "results"]:
            if key in data and isinstance(data[key], list):
                data = data[key]
                break

    if isinstance(data, dict):
        data = [data]

    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected JSON structure in {path}: {type(data)}")

    df = pd.DataFrame(data)
    print("Columns from llm_issues.json:", df.columns.tolist())

    col_map = {}

    for col in df.columns:
        lc = col.lower()
        if lc in ("file", "filename", "sourcefile", "source_file"):
            col_map[col] = "file"
        elif lc in ("line", "line_number", "lineno", "start_line"):
            col_map[col] = "line"
        elif lc in ("category", "issue_type", "type"):
            col_map[col] = "category"
        elif lc in ("severity", "level", "priority"):
            col_map[col] = "severity"
        elif lc in ("title", "summary", "short_description"):
            col_map[col] = "title"
        elif lc in ("description", "details", "long_description", "message"):
            col_map[col] = "description"

    df = df.rename(columns=col_map)

    if "file" not in df.columns:
        df["file"] = "UNKNOWN_FILE"
    if "line" not in df.columns:
        df["line"] = None
    if "category" not in df.columns:
        df["category"] = "UNKNOWN"
    if "severity" not in df.columns:
        df["severity"] = "MEDIUM"
    if "title" not in df.columns:
        df["title"] = ""
    if "description" not in df.columns:
        df["description"] = ""

    df["line"] = pd.to_numeric(df["line"], errors="coerce")

    return df[["file", "line", "category", "severity", "title", "description"]]



def load_spotbugs_issues(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["norm_category"] = df.apply(map_spotbugs_category, axis=1)
    df["norm_severity"] = df.apply(map_spotbugs_severity, axis=1)
    return df


def evaluate_overlap(llm_df: pd.DataFrame, spot_df: pd.DataFrame):
    """
    For simplicity, we define an "issue" by (file, category).
    You can refine this later to use (file, category, severity) or add line ranges.
    """
    llm_set = set(zip(llm_df["file"], llm_df["category"]))
    spot_set = set(zip(spot_df["file"], spot_df["norm_category"]))

    both = llm_set & spot_set
    only_llm = llm_set - spot_set
    only_spot = spot_set - llm_set

    print(f"LLM unique (file,category) issues: {len(llm_set)}")
    print(f"SpotBugs unique (file,category) issues: {len(spot_set)}")
    print(f"Overlap (both tools agree): {len(both)}")
    print(f"Only LLM: {len(only_llm)}")
    print(f"Only SpotBugs: {len(only_spot)}")

    print("\nExamples of overlap:")
    for item in list(both)[:5]:
        print("  ", item)

    print("\nExamples only in LLM:")
    for item in list(only_llm)[:5]:
        print("  ", item)

    print("\nExamples only in SpotBugs:")
    for item in list(only_spot)[:5]:
        print("  ", item)


def main():
    llm_df = load_llm_issues(LLM_JSON)
    spot_df = load_spotbugs_issues(SPOTBUGS_CSV)

    evaluate_overlap(llm_df, spot_df)


if __name__ == "__main__":
    main()
