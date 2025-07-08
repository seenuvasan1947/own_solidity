

from asyncio import sleep
# import google.generativeai as genai
import os
import re
import requests
import subprocess
import openai

# 1. Set your Gemini API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# genai.configure(api_key=GOOGLE_API_KEY)
retry_atempt = 1
openai.api_key = os.getenv("OPENAI_API_KEY")

with open("SolidityParser.g4", "r") as f:
    code = f.read()
# with open("test_contracts/FrontRunningDetector_bad.sol", "r") as f:
#     result_responce = f.read()
subprocess.run(f"rm  test_result.txt", shell=True)
try:
    with open("test_result.txt", 'r') as f:
        data = f.read()
except FileNotFoundError:
    data = "" 
    
    
def git_push():
    
    commands = [
    ["git", "add", "."],
    ["git", "commit", "-m", "Auto commit from Python"],
    ["git", "push"]
]
    repo_path = "/home/finstein-emp/cyber_product/own/own_source_code_analyser/own_solidity"
    for cmd in commands:
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
        print(f"Running: {' '.join(cmd)}")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)    

def create_files(response):

        # json_response = response.json()
        # text = json_response["candidates"][0]["content"]["parts"][0]["text"]
    text = response.choices[0].message.content
    # print(text)

    # 5. Split the response by section markers
    # print(text)
    sections = {}
    # for part in text.split("# ==="):
    #     if not part.strip():
    #         continue
    #     # print(part)
    #     header, code = part.strip().split("\n", 1)
    #     sections[header.strip()] = code.strip() 
    # sections = {}
    for part in text.split("# ==="):
        lines = part.strip().split("\n", 1)
        if len(lines) < 2:
            continue  # skip malformed sections
        header, code = lines
        normalized_key = header.strip().replace("===", "").strip()
        clean_code = (
            code.strip()
            .replace("```python", "")
            .replace("```solidity", "")
            .replace("```", "")
        ).strip()
        sections[normalized_key] = clean_code


    # 6. Save to files
    os.makedirs("rules", exist_ok=True)
    os.makedirs("test_contracts", exist_ok=True)
    os.makedirs("tests", exist_ok=True)
    global class_name 
    class_name = None
    # print(sections)
    # print(sections["RULE CLASS"])
    if "RULE CLASS" in sections:
        match = re.search(r"class\s+(\w+)\s*\(", sections["RULE CLASS"])
        print("--------------------------------")
        print(sections["RULE CLASS"])
        print("--------------------------------")
        if match:
            class_name = match.group(1)

            print(f"Class name: {class_name}")
        else:
            print("No class name found in RULE CLASS section")
            raise ValueError("No class name found in RULE CLASS section")
        with open(f"rules/{class_name}.py", "w") as f:
            f.write(sections["RULE CLASS"])

    if "BAD CONTRACT" in sections:
        with open(f"test_contracts/{class_name}_bad.sol", "w") as f:
            f.write(sections["BAD CONTRACT"])

    if "GOOD CONTRACT" in sections:
        with open(f"test_contracts/{class_name}_good.sol", "w") as f:
            f.write(sections["GOOD CONTRACT"])

    if "UNIT TEST" in sections:
        with open(f"tests/test_{class_name}.py", "w") as f:
            f.write(sections["UNIT TEST"])

    print("✅ Files saved successfully!")


    print(f"Running test for {class_name}")

def run_test():

    system_call = f"python3 -m unittest /home/finstein-emp/cyber_product/own/own_source_code_analyser/own_solidity/tests/test_{class_name}.py "

    result = subprocess.run(system_call, shell=True, capture_output=True, text=True)

    print(result)

    with open ("test_result.txt",'w') as f:
        # f.write(result)
        f.write(result.stdout)
        f.write(result.stderr)

# 2. Load the Gemini model
# model = genai.GenerativeModel("models/gemini-1.5-flash")
endpoint="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
# 3. Define your prompt
prompt =f"""
You are an expert in smart contract security and static code analysis using ANTLR in Python.

I am building an automated engine to detect vulnerabilities in Solidity smart contracts.

Given the following vulnerability metadata:

---
ID: SOL-AM-DA-1 
Category: Initialization
Question: "Are important state variables initialized properly?"  
Description: "Overlooking explicit initialization of state variables can lead to critical issues."  
Remediation: "Make sure to initialize all state variables correctly."
---

Generate the following:

1. A Python rule class named your wish but properly named that uses the Solidity ANTLR parser to find above bug is present in that code and return the line number and reason.
     
   example:
   
   ```
   from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from SolidityParserListener import SolidityParserListener

class SelfDestructDetector(SolidityParserListener):
    def __init__(self):
        self.in_public_function = False
        self.in_modifier = False
        self.violations = []



    def enterFunctionDefinition(self, ctx):
        # Check all visibility specifiers
        self.in_public_function = False
        i = 0
        while True:
            vis = ctx.visibility(i)
            if vis is None:
                break
            vis_text = vis.getText()
            if vis_text in ["public", "external"]:
                self.in_public_function = True
                break
            i += 1

    def exitFunctionDefinition(self, ctx):
        self.in_public_function = False

    def enterModifierInvocation(self, ctx):
        if ctx.getText().lower() in ["onlyowner", "isowner"]:
            self.in_modifier = True

    def exitModifierInvocation(self, ctx):
        self.in_modifier = False

    def enterFunctionCall(self, ctx):
        if self.in_public_function and not self.in_modifier:
            if ctx.getText().startswith("selfdestruct"):
                line = ctx.start.line
                self.violations.append(f"❌ Unsafe selfdestruct() at line {{line}}: {{ctx.getText()}}")

    def get_violations(self):
        return self.violations
```
2. A vulnerable Solidity contract  which triggers this detection.

  example:
   ```
   pragma solidity ^0.8.0;

contract BadContract {{
    function destroy() public {{
        selfdestruct(payable(msg.sender));
    }}
}}
```



3. A safe Solidity contract  that should NOT trigger this detection.

    example:
    ```
    pragma solidity ^0.8.0;

contract GoodContract {{
    address owner;
    constructor() {{
        owner = msg.sender;
    }}

    function destroy() public {{
        require(msg.sender == owner, "Not owner");
        selfdestruct(payable(owner));
    }}
}}
```
4. A Python unittest file  that tests the rule class on both contracts using `unittest`.


   example:
   
     ```
     import unittest
from antlr4 import *
from SolidityLexer import SolidityLexer
from SolidityParser import SolidityParser
from rules.SelfDestructDetector import SelfDestructDetector  # import your rule

def run_rule_on_file(filepath, rule_class):
    input_stream = FileStream(filepath)
    lexer = SolidityLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = SolidityParser(stream)
    tree = parser.sourceUnit()

    rule_instance = rule_class()
    walker = ParseTreeWalker()
    walker.walk(rule_instance, tree)

    return rule_instance.get_violations()

class TestSelfDestructDetector(unittest.TestCase):
    def test_detects_selfdestruct(self):
        violations = run_rule_on_file("test_contracts/SelfDestructDetector_bad.sol", SelfDestructDetector)
        self.assertTrue(any("selfdestruct" in v for v in violations))

    def test_ignores_safe_contract(self):
        violations = run_rule_on_file("test_contracts/SelfDestructDetector_good.sol", SelfDestructDetector)
        # self.assertEqual(len(violations), 0)
        self.assertEqual(len(violations), 1, f"Expected 0 or 1 minor violation, got: {{violations}}")

if __name__ == "__main__":
    unittest.main()

 ```
Please return all files clearly separated with markers:

- # === RULE CLASS ===  
- # === BAD CONTRACT ===  
- # === GOOD CONTRACT ===  
- # === UNIT TEST ===

Each section must be valid Python or Solidity, ready to be saved directly into a `.py` or `.sol` file. Use standard imports like `from antlr4 import *`.

Make the code production-quality.

⚠️ Do NOT wrap the code blocks with triple backticks like ```python or ```solidity. Just include raw valid code under each section marker.

make sure every thing is stricly following the prompt.  like the class name and file name. and no extra text. ans also section `# === RULE CLASS ===  `

and for grammer use the grammer file provided.

{code}

and  i got it as responce while test 

{data}

IMPORTANT: 
file name is important. so make sure it works fine and usige of filename at test is also be consious 

especially for test 

from rules.SelfDestructDetector import SelfDestructDetector

import is used in test file 

rules is need to be in rules folder

and SelfDestructDetector is class name 

"""


payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                        
                    ]
                }
            ],
            
        }

# 4. Call Gemini
# response = model.generate_content(prompt)
# text = response.text

# print(code)

for i in range(retry_atempt):
    print(f"Running test for {i} attempt")
    try:
        with open("test_result.txt", 'r') as f:
            data = f.read()
    except FileNotFoundError:
            data = ""
    if "OK" in data:
        print(f"Success at {i} attempt")
        break
    else:   
        # response = requests.post(endpoint, params={"key": GOOGLE_API_KEY}, json=payload)
        # response.raise_for_status()
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or another appropriate model
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in smart contract security and static code analysis using ANTLR in Python."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7
        )
        create_files(response)
        run_test()
        git_push()



