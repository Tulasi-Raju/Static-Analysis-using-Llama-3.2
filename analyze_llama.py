import os
import json
import requests

HOSPITAL_SRC_DIR = r"C:\Users\vigne\Downloads\spotbugs"

OLLAMA_MODEL = "llama3.2"

OLLAMA_URL = "http://localhost:11434/api/generate"

JSON_ISSUES_FILE = "llm_issues.json"
HTML_REPORT_FILE = "llm_issues_report.html"


def load_project_source(src_dir: str) -> str:
    """
    Reads all .java files under src_dir and returns them as one big string.
    Each file is prefixed with a marker so the model knows which file is which:

    === FILE: Hospital.java ===
    ...code...

    === FILE: Doctor.java ===
    ...code...
    """
    parts = []
    for root, _, files in os.walk(src_dir):
        for fname in files:
            if fname.endswith(".java"):
                full_path = os.path.join(root, fname)
                with open(full_path, "r", encoding="utf-8") as f:
                    code = f.read()
                parts.append(f"=== FILE: {fname} ===\n{code}\n")
    if not parts:
        raise RuntimeError(f"No .java files found under {src_dir}")
    return "\n".join(parts)


def build_issues_prompt(project_code: str) -> str:
    """
    Builds the text prompt that instructs the LLM to behave like a static analyzer
    and return a JSON array of issues.
    """
    prompt = f"""
You are a static analysis tool for a small Java application.

The project is a hospital management system with these kinds of classes:
- UI (user interface)
- Hospital (core logic)
- Doctor, Patient, Person (domain classes)
- ExaminationRoom, Specialty (support classes)

I will give you the full source code of these files.

Your task: identify likely bugs and problems in the code, including:
- CORRECTNESS issues (null pointer risk, wrong logic, off-by-one, etc.)
- BAD_PRACTICE issues (unused fields, suspicious equals/hashCode, etc.)
- PERFORMANCE issues (unnecessary work in loops, inefficient data structures, etc.)
- SECURITY issues (unsafe exposure of state, mutable shared collections, etc.)
- STYLE issues (very minor design/code smells)

For EACH issue, return a JSON object with the following fields:

- "id": a unique short string, e.g. "ISSUE1", "ISSUE2", etc.
- "file": the file name, e.g. "Hospital.java"
- "line": approximate line number as an integer (best guess is fine)
- "category": one of ["CORRECTNESS", "BAD_PRACTICE", "PERFORMANCE", "SECURITY", "STYLE"]
- "severity": one of ["LOW", "MEDIUM", "HIGH"]
- "title": a short one-line summary of the problem
- "description": 2–4 sentences explaining why this is a problem in this context

IMPORTANT RULES:
- Only report issues you are reasonably confident are real.
- Only look at the code provided; do not invent files or methods.
- If there are no issues, return an empty JSON array: [].
- The ENTIRE response must be a JSON array (no extra commentary, no markdown).

Here is the complete project code.
Each file starts with a '=== FILE: <name> ===' marker:

{project_code}
"""
    return prompt


def build_report_prompt(project_code: str, issues: list[dict]) -> str:
    """
    Builds a prompt asking the LLM to generate a detailed HTML report
    describing each issue and suggesting possible fixes.
    """
    issues_json = json.dumps(issues, indent=2)

    prompt = f"""
You are an expert Java developer and static analysis explainer.

You previously analyzed a small Java hospital management system and produced
a list of issues in JSON form. I will now give you:

1) The full project source code
2) The JSON list of issues that another tool already detected

Your job now is to generate a *detailed HTML report* about these issues.

----------------- PROJECT SOURCE CODE -----------------
{project_code}

----------------- JSON ISSUES LIST -----------------
{issues_json}

----------------- REPORT REQUIREMENTS -----------------

Produce a single, self-contained HTML5 page as plain text (no JSON, no markdown).
The HTML must have:

- A <head> section with:
  - <title>LLM Static Analysis Report</title>
  - A small <style> block for basic readability (fonts, spacing, simple colors).

- A <body> with:
  - An <h1> for the report title.
  - A short introduction explaining that the issues were found by an LLM static analysis.
  - A summary section that:
      - Shows the total number of issues.
      - Breaks down issues by category and severity in bullet points or a small table.
  - Then, for each issue in the JSON list, a section like this:
      - <h2>Issue ID – short title</h2>
      - A small metadata block (file, line, category, severity).
      - A paragraph restating the original description in your own words.
      - A subsection <h3>Root Cause</h3> with 2–4 sentences analyzing *why* this problem appears in the code.
      - A subsection <h3>Impact</h3> with 2–4 sentences explaining what could go wrong at runtime or in maintenance.
      - A subsection <h3>Suggested Fix</h3> with 2–4 sentences describing concrete steps to fix the bug or smell.
        If helpful, include a short <pre><code> Java snippet </code></pre> showing improved code.
  - A final conclusion section with next steps (e.g., prioritize high severity, add tests, etc.).

IMPORTANT:
- Use only the issues and code given; do not invent new files or extra issues.
- Keep the HTML valid and reasonably clean.
- Do NOT wrap the HTML in JSON. Return only the HTML document.
"""
    return prompt


def call_ollama_json(prompt: str):
    """
    Calls the local Ollama /api/generate endpoint with stream=false.
    We DO NOT use format="json" to avoid server-side 500 errors.
    Instead, we instruct the model via the prompt to output a JSON array,
    then we extract and parse that array from the response text.

    Returns: Python list of issue dicts.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
        # no "format": "json" here
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=300)

    if resp.status_code != 200:
        print("Ollama returned an error status code:", resp.status_code)
        print("Response body:\n", resp.text[:1000])  # print first 1000 chars for debugging
        resp.raise_for_status()

    data = resp.json()
    # The model's output text is stored in 'response'
    text = data.get("response", "").strip()

    # The prompt tells the model: "ENTIRE response must be a JSON array"
    # But just in case it adds some extra text, we extract the part between
    # the first '[' and the last ']'.
    start = text.find("[")
    end = text.rfind("]")

    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            "Model output did not contain a JSON array. "
            "Raw output (first 500 chars):\n" + text[:500]
        )

    json_str = text[start : end + 1]

    try:
        issues = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(
            "Failed to parse JSON from model output. "
            f"Error: {e}\nExtracted JSON string (first 500 chars):\n{json_str[:500]}"
        )

    return issues





def call_ollama_text(prompt: str) -> str:
    """
    Calls the local Ollama /api/generate endpoint, expecting plain text
    (here, an HTML document) in the 'response' field.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
        # NOTE: we intentionally do NOT set format="json" here
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
    resp.raise_for_status()
    data = resp.json()

    # 'response' contains the model's text output (expected to be HTML).
    html = data["response"]
    return html


def generate_html_report(project_code: str, issues: list[dict]) -> str:
    """
    Uses the LLM to generate a detailed HTML report for the given issues.
    Returns the HTML string.
    """
    report_prompt = build_report_prompt(project_code, issues)
    html_report = call_ollama_text(report_prompt)
    return html_report


def main():
    print(f"loading Java files from: {HOSPITAL_SRC_DIR}")
    project_code = load_project_source(HOSPITAL_SRC_DIR)

    issues_prompt = build_issues_prompt(project_code)

    print(f"using Ollama model '{OLLAMA_MODEL}' via {OLLAMA_URL} to detect issues...")
    issues = call_ollama_json(issues_prompt)

    # Save JSON issues
    print(f"Ollama reported {len(issues)} issues.")
    with open(JSON_ISSUES_FILE, "w", encoding="utf-8") as f:
        json.dump(issues, f, indent=2)
    print(f"Find LLM issues in {JSON_ISSUES_FILE}")

    # Generate detailed HTML report
    print("building html report...")
    html_report = generate_html_report(project_code, issues)

    with open(HTML_REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(html_report)
    print(f"Saved detailed HTML report to {HTML_REPORT_FILE}")


if __name__ == "__main__":
    main()
