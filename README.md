# Advanced Software Engineering
# Static Analysis using LLMs

## Requirements <br>
## Software <br>
Python  <br>
Java JDK 8+ <br>
IntelliJ IDEA (for running the HospitalSystem project & SpotBugs plugin) <br>
Ollama installed locally - https://ollama.com/download <br>
Llama 3.2 - ollama run llama3.2 <br>

# Python Libraries

pandas <br>
json <br>

Store the java file in a folder named Hospital System and the python files in a folder named LLM Analysis (could be anything as well)

## Create and activate a Python virtual environment
Type these commands on the terminal in VS Code to create a virtual environment - <br>

>cd "LLM Analysis"
>python -m venv venv <br>
>venv\Scripts\activate <br>
>pip install requests pandas <br>

## Install and test Ollama
After installing Ollama from the above given url follow these commands in a local terminal - 

>ollama pull llama3.2 <br>
>ollama run llama3.2 <br>

## Running LLM-Based Static Analysis (Llama 3.2)
Open terminal in VS Code and follow the commands - 

>python analyze_llama.py <br>

Loads all .java files from the configured project directory <br>
Builds Llama 3.2 analysis prompt <br>
Sends it to Ollama <br>
Extracts JSON from the response <br>

Saves results to: <br>
llm_issues.json <br>
llm_issues_report.html <br>

## Generating Code Comprehension HTML
Follow the below command in the same terminal - 

> python summarize_code_llama.py

Generates a html file which can be viewed on a browser for the result.

## Comparing LLM Results with SpotBugs
Follow the command below in the same terminal - 

> python evaluate_results.py

Loads llm_issues.json <br>
Loads spotbugs_issues.csv <br>
Normalizes categories <br>

Identifies: <br>
Issues found by both tools <br>
Issues found only by LLM <br>
Issues found only by SpotBugs <br>

