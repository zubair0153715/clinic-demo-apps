"""PharmaAI Assistant — RAG study assistant over the user's pharma books.

NOT fine-tuning (no GPU anywhere in this stack): BM25 retrieval over
chunked book text + an open model via API for generation, with citations.
Study & research aid only — never medical advice.
"""
