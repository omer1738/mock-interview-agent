# 🎤 Mock Interview Agent

An AI agent that interviews you for a real job. Paste a job link, answer 5 questions, get scored, and if you pass, get a tailored cover letter and CV tips.

**Live demo:** [add your Streamlit link here]

## How it works (the agent loop)
The LLM decides which tool to call and when, then loops until the task is done:

1. `fetch_job_page`: reads the job post from a URL
2. `get_past_progress`: recalls weak topics from earlier interviews
3. `evaluate_answer`: scores each answer from 0 to 10
4. `get_session_result`: Python calculates the average and decides pass or fail
5. `build_application_kit`: writes a cover letter from your CV (only if you pass)

## Tech stack
Python, Google Gemini API (function calling), Streamlit, BeautifulSoup, requests

## What I learned
- Building an agent loop from scratch (no LangChain)
- Function calling and tool design
- Keeping decisions deterministic: pass/fail is calculated in code, not by the AI
- Per-user memory and a rate limit for a public demo

## Run locally
    pip install -r requirements.txt
    # create a .env file with: GEMINI_API_KEY=your-key
    streamlit run app.py

## Limitations
LinkedIn and Indeed block scrapers, so some job links fail. The agent then asks you to paste the job description.