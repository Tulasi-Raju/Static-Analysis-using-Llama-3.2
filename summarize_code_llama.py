import os
import requests

HOSPITAL_SRC_DIR = r"C:\Users\vigne\Downloads\spotbugs"

OLLAMA_MODEL = "llama3.2"

OLLAMA_URL = "http://localhost:11434/api/generate"


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


def build_comprehension_prompt(project_code: str) -> str:
    """
    Builds the text prompt that instructs the LLM to act as a code comprehension tool
    and return a human-readable HTML explanation of the project.
    """
    prompt = f"""
You are a senior Java engineer helping a student understand a small hospital
management system project.

I will give you the full source code of several .java files. Each file in the
text is prefixed with:

=== FILE: <FileName>.java ===

Your task: produce a clear, human-readable explanation of the project that can
be shown directly on a web page.

REQUIREMENTS FOR YOUR OUTPUT:

1. Output must be VALID HTML FRAGMENT (no <html>, <head>, or <body> tags).
2. Use headings and paragraphs:
   - Start with an <h1> overall title for the project.
   - Then for each file, use an <h2> with the file name (e.g. <h2>Doctor.java</h2>).
   - Under each <h2>, write 3–7 <p> paragraphs that explain:
       * What this file/class is for.
       * Important fields and methods in simple language.
       * How it interacts with other files/classes.
       * Explain the functionality of this file into the whole application.
3. You may also use <ul>/<li> for short bullet lists of important methods or
   responsibilities if it makes the explanation clearer.
4. The tone should be friendly and explanatory, as if you are writing learning
   material for someone who knows basic Java but not this project.
5. Do NOT output JSON, markdown, or code fences. Only HTML tags and text.

Now here is the complete project code.
Each file starts with a '=== FILE: <name> ===' marker:

{project_code}
"""
    return prompt


def call_ollama(prompt: str) -> str:
    """
    Calls the local Ollama /api/generate endpoint with stream=false.
    We expect the model's 'response' field to be an HTML fragment as plain text.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        # Do NOT set "format": "json" because we want free-form HTML text.
        "stream": False,
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
    resp.raise_for_status()
    data = resp.json()

    # 'response' contains the model's text output (an HTML fragment).
    html_fragment = data["response"]
    return html_fragment


def build_html_page(body_html: str) -> str:
    """
    Wraps the HTML fragment returned by the model into a full HTML page
    with some minimal styling.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Hospital System Code Comprehension</title>
    <style>
        body {{
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            margin: 2rem auto;
            max-width: 960px;
            line-height: 1.6;
            padding: 0 1rem;
            background: #f7f7f7;
        }}
        h1, h2 {{
            color: #333;
        }}
        h1 {{
            border-bottom: 2px solid #ccc;
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }}
        h2 {{
            margin-top: 2rem;
            border-bottom: 1px solid #ddd;
            padding-bottom: 0.25rem;
        }}
        p {{
            margin: 0.5rem 0;
        }}
        ul {{
            margin: 0.5rem 0 0.5rem 1.5rem;
        }}
        li {{
            margin: 0.2rem 0;
        }}
        .container {{
            background: #ffffff;
            padding: 1.5rem 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        }}
    </style>
</head>
<body>
    <div class="container">
{body_html}
    </div>
</body>
</html>
"""


def main():
    print(f"Loading Java files from: {HOSPITAL_SRC_DIR}")
    project_code = load_project_source(HOSPITAL_SRC_DIR)

    print("Building comprehension prompt for Ollama (HTML output)...")
    prompt = build_comprehension_prompt(project_code)

    print(f"Calling Ollama model '{OLLAMA_MODEL}' via {OLLAMA_URL} ...")
    html_fragment = call_ollama(prompt)

    full_html = build_html_page(html_fragment)

    output_path = "code_comprehension.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"Saved code comprehension page to {output_path}")
    print("Open this file in your browser to view the explanation.")


if __name__ == "__main__":
    main()
