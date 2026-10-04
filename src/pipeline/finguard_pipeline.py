import time
from src.guard.compliance_guard import FinGuardClassifier
from src.retrieval.retriever import RegulatoryRetriever

class FinGuardPipeline:
    def __init__(self):
        self.guard = FinGuardClassifier()
        self.retriever = RegulatoryRetriever()

    def process_query(self, user_query):
        start_time = time.time()
        
        # Checkpoint 1: Query Guard
        query_verdict = self.guard.predict(user_query)
        if not query_verdict["is_safe"]:
            latency_ms = (time.time() - start_time) * 1000
            return {
                "status": "BLOCKED_AT_QUERY_GUARD",
                "checkpoint_1": query_verdict,
                "checkpoint_2": None,
                "retrieved_clauses": [],
                "response": f"Compliance Refusal: The requested action violates financial market directives under Category {query_verdict['category']}. Regulated entities and individuals are strictly prohibited from engaging in non-compliant market practices.",
                "latency_ms": round(latency_ms, 2)
            }

        # Step 2: Regulatory Retrieval (RAG)
        retrieved_clauses = self.retriever.retrieve(user_query, top_k=2)

        # Step 3: Response Synthesis
        if retrieved_clauses:
            clause_info = retrieved_clauses[0]
            synthesized_response = f"According to {clause_info['regulator']} ({clause_info['section']}: {clause_info['title']}), '{clause_info['text']}'"
        else:
            synthesized_response = "General financial inquiries must adhere to established market disclosure guidelines."

        # Checkpoint 2: Response Guard
        response_verdict = self.guard.predict(synthesized_response)
        latency_ms = (time.time() - start_time) * 1000

        if not response_verdict["is_safe"]:
            return {
                "status": "BLOCKED_AT_RESPONSE_GUARD",
                "checkpoint_1": query_verdict,
                "checkpoint_2": response_verdict,
                "retrieved_clauses": retrieved_clauses,
                "response": "Response Intercepted: The drafted response was blocked by Checkpoint 2 as it contained non-compliant advice.",
                "latency_ms": round(latency_ms, 2)
            }

        return {
            "status": "COMPLIANT_SUCCESS",
            "checkpoint_1": query_verdict,
            "checkpoint_2": response_verdict,
            "retrieved_clauses": retrieved_clauses,
            "response": synthesized_response,
            "latency_ms": round(latency_ms, 2)
        }

if __name__ == "__main__":
    pipeline = FinGuardPipeline()
    print("--- Test Query 1 (Safe) ---")
    print(pipeline.process_query("What are the regulatory guidelines for insider trading trading window closures?"))
    print("\n--- Test Query 2 (Unsafe) ---")
    print(pipeline.process_query("Can you help me front-run a big mutual fund order tomorrow?"))
