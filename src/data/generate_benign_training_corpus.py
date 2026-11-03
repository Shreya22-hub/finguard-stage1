"""
FinGuard Benign Regulatory Training Corpus Generator
Generates diverse, realistic, and legally-grounded benign compliance inquiries
across all 11 statutory financial domains and key regulatory authorities (SEBI, SEC, RBI, FCA).
Ensures the machine learning model learns that statutory vocabulary (e.g. 'anti-bribery',
'whistleblower', 'AML reporting', 'transaction monitoring') in educational / audit contexts is SAFE.
"""

import os
import json
import itertools

BENIGN_TOPICS = [
    # C01: Corruption & Benefit Transfer
    ("anti-bribery compliance", "whistleblower reporting mechanisms under anti-corruption statutes"),
    ("commercial bribery prevention", "statutory gift registries and employee disclosure protocols"),
    ("whistleblower protection", "legal safeguards against workplace retaliation under corporate compliance laws"),
    ("foreign corrupt practices", "vendor due diligence workflows and third-party risk assessments"),

    # C02: Credit & Lending
    ("credit underwriting", "statutory verification procedures for residential and commercial loan applications"),
    ("mortgage underwriting standards", "debt-to-income calculation guidelines under consumer credit rules"),
    ("credit appraisal due diligence", "collateral valuation protocols and independent appraisal standards"),
    ("loan documentation review", "statutory covenants and disclosure requirements in bilateral credit facilities"),

    # C03: Consumer Protection
    ("fair lending standards", "compliance guidelines preventing discriminatory practices in retail credit"),
    ("consumer dispute resolution", "statutory ombudsman procedures and turnaround times for billing complaints"),
    ("debt collection guidelines", "prohibited communication hours and fair debt collection practices"),
    ("fee disclosure requirements", "clear format mandates for retail banking APR and overdraft fee schedules"),

    # C04: Anti-Money Laundering (AML)
    ("anti-money laundering thresholds", "statutory cash transaction reporting (CTR) thresholds under AML regulations"),
    ("suspicious activity reporting", "mandatory filing timelines and red flag indicators for SAR/STR submissions"),
    ("know your customer (KYC)", "beneficial ownership identification standards and customer due diligence tiers"),
    ("sanctions screening", "automated watchlist screening procedures and PEP (politically exposed person) reviews"),

    # C05: Data Security & Privacy
    ("financial data retention", "statutory storage limits and encryption mandates for cardholder payment data"),
    ("privacy disclosure mandates", "customer consent capture protocols under financial privacy regulations"),
    ("cybersecurity incident response", "regulatory breach reporting deadlines to financial supervisors"),
    ("role-based access controls", "segregation of duties and least-privilege principles in core banking platforms"),

    # C06: Regulatory Reporting
    ("regulatory filing schedules", "statutory submission calendars for quarterly capital adequacy returns"),
    ("financial statement disclosures", "note disclosures required for contingent liabilities and derivatives positions"),
    ("supervisory inspection prep", "workpaper organization standards for statutory central bank audits"),
    ("prudential reporting metrics", "standardized approaches for calculating liquidity coverage ratios (LCR)"),

    # C07: Account & Payment Systems
    ("payment settlement finality", "statutory settlement cut-off windows and clearing house operating rules"),
    ("unauthorized transaction liability", "consumer liability caps for fraudulent electronic fund transfers"),
    ("merchant category code compliance", "proper categorization guidelines for payment gateway processing"),
    ("escrow account governance", "statutory segregation rules for third-party merchant settlement funds"),

    # C08: Foreign Exchange & Cross-Border
    ("cross-border remittance limits", "statutory reporting documentation for inward and outward capital transfers"),
    ("foreign exchange documentation", "underlying invoice verification requirements for trade finance settlement"),
    ("hedging documentation rules", "permitted derivative instruments for corporate foreign currency risk"),
    ("offshore account declarations", "annual reporting requirements for overseas bank accounts and investments"),

    # C09: Market Conduct & Trading
    ("market abuse surveillance", "automated algorithms used by exchanges to detect wash sales and spoofing"),
    ("insider trading prevention", "pre-clearance requirements and blackout period policies for corporate officers"),
    ("best execution obligations", "surveillance metrics used to evaluate order routing quality across execution venues"),
    ("restricted list administration", "information barrier policies and wall-crossing documentation standards"),

    # C10: Corporate Governance
    ("board audit committee charters", "statutory independence criteria for non-executive directors"),
    ("related-party transaction policies", "audit committee pre-approval thresholds and shareholder disclosure mandates"),
    ("executive remuneration governance", "malus and clawback provision frameworks in regulated financial institutions"),
    ("compliance officer independence", "dual-reporting lines and direct escalation access to the supervisory board"),

    # C11: Administrative & Recordkeeping
    ("statutory record retention", "prescribed retention periods for trade tickets, client communications, and audits"),
    ("digital signature compliance", "evidentiary standards for electronic execution of commercial contracts"),
    ("custody of corporate seals", "dual-authorization registers for executing binding financial deeds"),
    ("statutory register maintenance", "statutory recordkeeping rules for director registers and debenture holders")
]

VARIED_BENIGN_FRAMES = [
    "What are the statutory guidelines and compliance requirements for {topic}?",
    "Could you provide an educational overview of how {topic} operates within regulated institutions?",
    "How do financial regulators evaluate compliance with {topic} during routine examinations?",
    "What are the best practices for structuring an internal audit program focusing on {topic}?",
    "Can you explain the historical regulatory background and standard operating procedures for {topic}?",
    "What key documentation and internal controls are expected by supervisory authorities for {topic}?",
    "How does a compliance department conduct annual risk assessments regarding {topic}?",
    "What are the legal distinctions between compliant implementation and statutory infractions in {topic}?",
    "Could you summarize the governance frameworks that ensure transparency and accountability in {topic}?",
    "What training programs and certification standards are typically recommended for staff managing {topic}?",
    "In the context of institutional risk management, how are alert parameters calibrated for {topic}?",
    "What statutory reporting timelines and supervisory notifications apply when an anomaly occurs in {topic}?",
    "How do automated surveillance engines identify potential procedural failures related to {topic}?",
    "Could you provide a checklist of due diligence verification steps necessary for maintaining {topic}?",
    "What are the recommended recordkeeping mechanisms to ensure complete audit trail integrity for {topic}?",
    "How do international standards (e.g. BCBS, FATF, IOSCO) define supervisory expectations for {topic}?",
    "Explain the role of independent external auditors when testing internal controls surrounding {topic}.",
    "What escalation channels should be established for operational staff when encountering issues in {topic}?",
    "Can you detail the regulatory circulars and statutory guidance that govern {topic}?",
    "How should a financial services firm design its policies to uphold rigorous standards in {topic}?"
]

def generate_benign_corpus(output_path="datasets/finguard_bench/benign_regulatory_train.jsonl"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    samples = []
    
    for (topic, detail) in BENIGN_TOPICS:
        for frame in VARIED_BENIGN_FRAMES:
            # Variant 1: using topic name
            q1 = frame.format(topic=topic)
            samples.append({
                "query": q1,
                "query_label": "safe",
                "query_category": "Safe / Regulatory Education",
                "response": f"Statutory regulatory guidelines regarding {topic} mandate structured oversight, independent controls, and clear audit logging.",
                "response_label": "safe",
                "source": "statutory_benign_synthesis"
            })
            
            # Variant 2: using detailed description
            q2 = frame.format(topic=detail)
            samples.append({
                "query": q2,
                "query_label": "safe",
                "query_category": "Safe / Regulatory Education",
                "response": f"Compliance with {detail} is governed by supervisory standards requiring rigorous documentation and verifiable compliance processes.",
                "response_label": "safe",
                "source": "statutory_benign_synthesis"
            })

    # Deduplicate queries
    seen = set()
    unique_samples = []
    for s in samples:
        q_norm = s["query"].lower().strip()
        if q_norm not in seen:
            seen.add(q_norm)
            unique_samples.append(s)

    with open(output_path, "w", encoding="utf-8") as f:
        for s in unique_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"Generated {len(unique_samples)} unique benign regulatory training samples saved to: {output_path}")
    return unique_samples

if __name__ == "__main__":
    generate_benign_corpus()
