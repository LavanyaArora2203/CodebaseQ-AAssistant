# backend/llm/prompts.py


# -----------------------------
# BASE PROMPT BUILDER
# -----------------------------
def get_prompt(query: str, context: str, query_type: str) -> str:
    """
    Select prompt based on query type
    """

    if query_type == "debugging":
        return debugging_prompt(query, context)

    elif query_type == "code_search":
        return code_search_prompt(query, context)

    elif query_type == "usage":
        return usage_prompt(query, context)

    elif query_type == "explanation":
        return explanation_prompt(query, context)

    else:
        return general_prompt(query, context)


# -----------------------------
# DEBUGGING PROMPT
# -----------------------------
def debugging_prompt(query: str, context: str) -> str:
    return f"""
You are an expert software debugger.

User Query:
{query}

Relevant Code:
{context}

Instructions:
- Identify the root cause of the issue
- Explain clearly what is wrong
- Suggest a fix
- Provide corrected code if possible
"""


# -----------------------------
# CODE SEARCH PROMPT
# -----------------------------
def code_search_prompt(query: str, context: str) -> str:
    return f"""
You are a codebase navigation assistant.

User Query:
{query}

Relevant Code:
{context}

Instructions:
- Identify exact file, function, or class
- Explain where it is located
- Provide a short description of what it does
"""


# -----------------------------
# USAGE PROMPT
# -----------------------------
def usage_prompt(query: str, context: str) -> str:
    return f"""
You are a software engineer helping with code usage.

User Query:
{query}

Relevant Code:
{context}

Instructions:
- Explain how to use the code
- Provide step-by-step usage
- Include examples if possible
"""


# -----------------------------
# EXPLANATION PROMPT
# -----------------------------
def explanation_prompt(query: str, context: str) -> str:
    return f"""
You are a senior developer explaining code.

User Query:
{query}

Relevant Code:
{context}

Instructions:
- Explain what the code does
- Break down logic step-by-step
- Keep explanation clear and simple
"""


# -----------------------------
# GENERAL PROMPT
# -----------------------------
def general_prompt(query: str, context: str) -> str:
    return f"""
You are an AI assistant for a GitHub repository.

User Query:
{query}

Relevant Code:
{context}

Instructions:
- Answer clearly and concisely
- Use the provided code as reference
"""