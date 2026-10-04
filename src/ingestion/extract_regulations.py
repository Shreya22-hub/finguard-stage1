import os
import json

REGULATORY_DOCUMENTS = [
    {
        "doc_id": "REG_FIN_001",
        "title": "Securities Market Conduct & Fraud Prevention Directives",
        "regulator": "CSRC/Financial Regulator",
        "category_hint": "Market Manipulation & Fraud",
        "clauses": [
            {
                "section": "Article 3(1)",
                "title": "Prohibition of Market Manipulation and Pump-and-Dump Schemes",
                "text": "No entity or individual shall manipulate market prices through concerted trading, false signals, spoofing, wash sales, or spreading misleading rumors to artificially influence transaction volume or equity valuation."
            },
            {
                "section": "Article 5(2)",
                "title": "Prohibition of Front-Running and Order Anticipation",
                "text": "Market intermediaries, asset management personnel, and brokers are strictly prohibited from trading ahead of pending client orders or institutional bulk purchases for personal gain or related party benefit."
            }
        ]
    },
    {
        "doc_id": "REG_FIN_002",
        "title": "Insider Information & Material Non-Public Disclosure Rules",
        "regulator": "CSRC/Financial Regulator",
        "category_hint": "Insider Trading & UPSI",
        "clauses": [
            {
                "section": "Regulation 4(1)",
                "title": "Prohibition of Insider Trading on Material Non-Public Information",
                "text": "Insiders, corporate officers, auditors, and temporary tippees possessing material non-public information (MNPI) regarding earnings, mergers, or restructuring shall not trade, recommend transactions, or disclose MNPI to unauthorized third parties prior to public announcement."
            },
            {
                "section": "Regulation 7(3)",
                "title": "Pre-Clearance and Trading Window Closure",
                "text": "Designated persons shall observe trading window closures prior to financial results declaration and obtain mandatory pre-clearance for equity transactions exceeding prescribed financial thresholds."
            }
        ]
    },
    {
        "doc_id": "REG_FIN_003",
        "title": "Financial Investment Advisory & License Compliance Directives",
        "regulator": "CSRC/Financial Regulator",
        "category_hint": "Unlicensed Advisory & Finfluencers",
        "clauses": [
            {
                "section": "Clause 8(A)",
                "title": "Mandatory Registration for Investment Advice",
                "text": "Providing personalized stock recommendations, target price guarantees, or portfolio management advice to the public without valid regulatory license registration is unlawful."
            },
            {
                "section": "Clause 12(B)",
                "title": "Prohibition of Profit Sharing and Guaranteed Returns",
                "text": "Regulated advisory entities and independent financial analysts shall not offer guaranteed return schemes, profit-sharing arrangements, or assurance of capital protection to retail investors."
            }
        ]
    },
    {
        "doc_id": "REG_FIN_004",
        "title": "Anti-Money Laundering (AML) & Know Your Customer (KYC) Norms",
        "regulator": "FIU / Financial Regulator",
        "category_hint": "AML / KYC Compliance",
        "clauses": [
            {
                "section": "Section 12(1)",
                "title": "Customer Due Diligence and Beneficial Ownership Verification",
                "text": "Financial institutions must perform comprehensive Customer Due Diligence (CDD), verify ultimate beneficial ownership (UBO), and refrain from opening anonymous accounts or accounts under fictitious names."
            },
            {
                "section": "Section 15(4)",
                "title": "Suspicious Transaction Reporting (STR) Timelines",
                "text": "Intermediaries must file Suspicious Transaction Reports (STR) with the financial intelligence authority within 7 working days of detecting transactions involving structured deposits, shell entities, or unexplained fund flows."
            }
        ]
    },
    {
        "doc_id": "REG_FIN_005",
        "title": "Algorithmic Trading & High-Frequency Risk Controls",
        "regulator": "CSRC/Financial Regulator",
        "category_hint": "Algorithmic & HFT Controls",
        "clauses": [
            {
                "section": "Directive 19(2)",
                "title": "Pre-Trade Risk Controls and Kill-Switch Requirements",
                "text": "All algorithmic trading strategies must incorporate pre-trade risk controls including order limits, price checks, order-to-trade ratio limits, and automated kill-switch functionality to prevent runaway execution."
            }
        ]
    },
    {
        "doc_id": "REG_FIN_006",
        "title": "Corporate Disclosure & Material Event Notification Rules",
        "regulator": "CSRC/Financial Regulator",
        "category_hint": "Corporate Disclosures",
        "clauses": [
            {
                "section": "Section 30(2)",
                "title": "Timely Disclosure of Material Events",
                "text": "Listed companies must disclose material events including acquisitions, key executive resignations, litigation, or major debt defaults within 12 to 24 hours of occurrence to stock exchanges."
            }
        ]
    }
]

def extract_and_save_regulations(output_path="data/processed/regulations.json"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    extracted_clauses = []
    
    for doc in REGULATORY_DOCUMENTS:
        for idx, clause in enumerate(doc["clauses"]):
            clause_record = {
                "clause_id": f"{doc['doc_id']}_C{idx+1:02d}",
                "doc_id": doc["doc_id"],
                "doc_title": doc["title"],
                "regulator": doc["regulator"],
                "section": clause["section"],
                "title": clause["title"],
                "text": clause["text"],
                "category_hint": doc["category_hint"]
            }
            extracted_clauses.append(clause_record)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(extracted_clauses, f, indent=2, ensure_ascii=False)
        
    print(f"Extracted {len(extracted_clauses)} regulatory clauses to {output_path}")
    return extracted_clauses

if __name__ == "__main__":
    extract_and_save_regulations()
