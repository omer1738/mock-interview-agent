import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client()
MODEL = "gemini-3.1-flash-lite"
PASS_SCORE = 6   # average needed to pass


def fetch_job_page(url):
    if not url.startswith(("http://", "https://")):
        return {"error": "Invalid link. It must start with http:// or https://"}
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return {"error": "Could not open this page. Ask the user to paste the job description instead."}

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    return text[:8000]


def evaluate_answer(question, answer, store):
    prompt = f"""You are a strict interviewer. Score this answer from 0 to 10.
Question: {question}
Answer: {answer}
Reply ONLY with JSON: {{"score": number, "feedback": "one short sentence", "weak_topic": "short topic name or none"}}"""
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    result = json.loads(response.text)
    store["answers"].append({
        "interview": store["interview"],
        "question": question,
        "answer": answer,
        "score": result["score"],
        "weak_topic": result["weak_topic"],
    })
    return result


def get_past_progress(store):
    old = [a for a in store["answers"] if a["interview"] != store["interview"]]
    if not old:
        return {"message": "No past interviews yet."}
    weak = {a["weak_topic"] for a in old if a["weak_topic"] != "none"}
    avg = sum(a["score"] for a in old) / len(old)
    return {"answers_so_far": len(old), "average_score": round(avg, 1), "weak_topics": list(weak)[:5]}


def get_session_result(store):
    current = [a for a in store["answers"] if a["interview"] == store["interview"]]
    if not current:
        return {"message": "No answers yet in this interview."}
    avg = round(sum(a["score"] for a in current) / len(current), 1)
    passed = avg >= PASS_SCORE
    if passed:
        next_step = ("The candidate PASSED. You MUST now call build_application_kit "
                     "with a short job summary, then show its output. "
                     "Do NOT write the cover letter yourself.")
    else:
        next_step = ("The candidate FAILED. Do NOT call build_application_kit. "
                     "Give a short study plan.")
    return {"average_score": avg, "pass_score": PASS_SCORE, "passed": passed, "next_step": next_step}


def build_application_kit(job_description, cv_text):
    if not cv_text.strip():
        return {"error": "No CV provided. Tell the user to paste their CV in the sidebar, then ask again."}
    prompt = f"""Write a short professional cover letter (max 200 words) and 3 specific CV improvement tips.
Job: {job_description}
Candidate CV: {cv_text}
Only use facts from the CV. Do not invent experience."""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return {"kit": response.text}