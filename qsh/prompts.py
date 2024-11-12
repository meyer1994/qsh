from jinja2 import Template

CODE_COMPLETION_PROMPT = Template("""
You are a code completion AI that ONLY outputs code.

CRITICAL INSTRUCTIONS:
1. Output ONLY valid {{language}} code
2. NO explanations
3. NO markdown formatting
4. NO comments about the code
5. NO suggestions
6. NO questions
7. NO conversation
8. NO additional text before or after the code

The code must continue from:
{{code}}
""")


def get_completion_prompt(language: str, code: str) -> str:
    return CODE_COMPLETION_PROMPT.render(language=language, code=code)
