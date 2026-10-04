import os
import json

def process_compliance_points(input_path="data/processed/regulations.json", output_path="data/processed/compliance_points.json"):
    if not os.path.exists(input_path):
        from src.ingestion.extract_regulations import extract_and_save_regulations
        extract_and_save_regulations(input_path)

    with open(input_path, "r", encoding="utf-8") as f:
        clauses = json.load(f)

    compliance_points = []
    
    for clause in clauses:
        text = clause["text"]
        title = clause["title"]
        
        # Rule classification logic based on compliance verbs
        if "shall not" in text.lower() or "prohibited" in text.lower() or "unlawful" in text.lower():
            obligation_type = "MUST_NOT"
        elif "must" in text.lower() or "shall observe" in text.lower() or "shall incorporate" in text.lower():
            obligation_type = "MUST"
        else:
            obligation_type = "DISCLOSE"

        point = {
            "rule_id": f"RULE_{clause['clause_id']}",
            "source_section": clause["section"],
            "source_doc": clause["doc_title"],
            "clause_title": title,
            "obligation_type": obligation_type,
            "compliance_point": f"{clause['section']}: {title} - {text}",
            "category_hint": clause["category_hint"],
            "risk_if_violated": f"Regulatory penalty, license cancellation, or statutory sanction under {clause['regulator']}"
        }
        compliance_points.append(point)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(compliance_points, f, indent=2, ensure_ascii=False)

    print(f"Processed {len(compliance_points)} compliance points to {output_path}")
    return compliance_points

if __name__ == "__main__":
    process_compliance_points()
