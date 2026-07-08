from typing import List


class PromptBuilder:

    SYSTEM_PROMPT = """
You are an expert software engineer.

Answer ONLY using the provided repository context.

If the answer cannot be found in the repository,
reply exactly:

"I couldn't find that in the indexed repository."

Never invent functions or files.

Always cite file paths and line numbers.
""".strip()

    def build(
        self,
        query: str,
        retrieved_chunks: List[dict]
    ) -> str:

        sections = []

        for chunk in retrieved_chunks:

            meta = chunk["metadata"]

            section = f"""
======================================================
File: {meta['file_path']}

Lines: {meta['start_line']}-{meta['end_line']}

Chunk Type: {meta['chunk_type']}

Code:

{chunk['text']}
"""

            sections.append(section)

        context = "\n".join(sections)

        prompt = f"""
{self.SYSTEM_PROMPT}

======================================================
Repository Context
======================================================

{context}

======================================================
Question

{query}

======================================================

Answer:

""".strip()

        return prompt