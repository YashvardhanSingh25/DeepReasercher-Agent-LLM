from openai import OpenAI
import json

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"
)

class WriterAgent:

    def summarize(self, content, context=""):

        prompt = f"""
You are an expert research assistant.

Your task is to convert raw research content into a clean, structured answer.

Follow STRICT format for EVERY answer:

📌 Overview:
- Write 3-4 lines summarizing the topic.

📊 Key Points:
- Bullet points (4–6 important facts)

🧠 Explanation:
- Clear explanation in 4–6 lines
- Simple and easy to understand
- No repetition

✅ Conclusion:
- Final takeaway in 2-3 lines

RULES:
- Keep answer between 500 - 1000 words
- Remove duplicate or irrelevant info
- Use simple language
- DO NOT skip any section
- DO NOT change format
- DO NOT add extra headings

Content:
{content}
"""

        try:
            response = client.chat.completions.create(
                model="qwen2.5-vl-3b-instruct",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3,
                top_p=0.9
            )
        except Exception as e:
            if "connection" in str(e).lower() or "refused" in str(e).lower():
                raise Exception("LM_STUDIO_ERROR")
            raise e

        return response.choices[0].message.content.strip()


    def write_answers(self, context="", file_path="research_data.json"):

        with open(file_path, "r") as f:
            data = json.load(f)

        for i, item in enumerate(data["sub_questions"]):

            content = item["answer"]

            print(f"Summarizing Sub Question {i+1}...")

            summary = self.summarize(content, context=context)

            data["sub_questions"][i]["answer"] = summary

        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)