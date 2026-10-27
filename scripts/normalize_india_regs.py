import json

path = "data/jurisdictions/india/regulations.json"
with open(path, "r", encoding="utf-8") as f:
    clauses = json.load(f)

for cl in clauses:
    if "title" not in cl:
        cl["title"] = cl.get("heading", cl.get("section", "Clause"))
    if "doc_title" not in cl:
        cl["doc_title"] = cl.get("document", "SEBI/RBI Regulation")

with open(path, "w", encoding="utf-8") as f:
    json.dump(clauses, f, indent=2)

print(f"Normalized {len(clauses)} clauses in {path}")
