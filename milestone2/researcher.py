import json
from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

class ResearcherAgent:

    def research(self, sub_questions, context=""):

        answers = []
        urls = []
        all_titles = []

        for question in sub_questions:

            try:
                response = client.search(
                    query=question,
                    search_depth="advanced",
                    max_results=6,
                    include_answer=True,
                    include_raw_content=False,
                )
            except Exception as e:
                if "api_key" in str(e).lower():
                    raise Exception("TAVILY_API_MISSING")
                elif "connection" in str(e).lower():
                    raise Exception("NO_INTERNET")
                else:
                    raise Exception(f"TAVILY_ERROR: {str(e)}")

            results = response.get("results", [][:2000])

            answer = ""
            url = ""
            titles = ""

            for r in results:
                answer += r.get("content", "") + "\n"

                title = r.get("title", "No Title")
                link = r.get("url", "")

                titles += title + "\n"
                url += link + "\n"

            answers.append(answer.strip())
            urls.append(url.strip())
            all_titles.append(titles.strip())

        return answers, urls, all_titles


    def save_answers_to_json(self, answers, urls, titles, file_path="research_data.json"):

        with open(file_path, "r") as f:
            data = json.load(f)

        sub_questions = data["sub_questions"]

        for i in range(len(sub_questions)):

            if i < len(answers):
                sub_questions[i]["answer"] = answers[i]
                sub_questions[i]["url"] = urls[i]
                sub_questions[i]["title"] = titles[i]

        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)