import json
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"
)

class PlannerAgent:

    # 🔥 LLM HELPER (used for rewriting also)
    def llm(self, prompt):
        response = client.chat.completions.create(
            model="qwen2.5-vl-3b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()

    # 🔥 GENERATE SUBQUESTIONS (NOW CLEAN QUERY BASED)
    def generate_subquestions(self, question, context=""):

        SYSTEM_PROMPT = f"""
You are a research planner.

Conversation Context:
{context}

User Question:
{question}

IMPORTANT:
- If the question is related to previous conversation, use context to understand it.
- If not related, ignore context.

Break into 5 researchable sub-questions.

Return ONLY numbered list.
"""

        try:
            response = client.chat.completions.create(
                model="qwen2.5-vl-3b-instruct",
                messages=[{"role":"user","content":SYSTEM_PROMPT}],
                temperature=0.7,
                top_p=0.9,
                max_tokens=300
            )
        except Exception as e:
            if "connection" in str(e).lower() or "refused" in str(e).lower():
                raise Exception("LM_STUDIO_ERROR")
            raise e

        text = response.choices[0].message.content

        sub_questions = [
            q.split(".",1)[-1].strip()
            for q in text.split("\n") if q.strip()
        ]

        return sub_questions


    def save_to_json(self, main_question, sub_questions):

        data = {
            "main_question": main_question,
            "sub_questions": []
        }

        for q in sub_questions:
            data["sub_questions"].append({
                "question": q,
                "answer": "",
                "url": "",
                "title": ""
            })

        with open("research_data.json","w") as f:
            json.dump(data,f,indent=4)