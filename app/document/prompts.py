
def build_rag_prompt(context: str, question: str) -> str:
    return f"""Answer the question using ONLY the context below. If the context doesn't contain the answer, say you don't know.
        Context:
        {context}

        Question: {question}"""