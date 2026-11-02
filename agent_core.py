from dotenv import load_dotenv
from google import genai
from google.genai import types

from tools import (
    fetch_job_page, evaluate_answer, get_past_progress,
    get_session_result, build_application_kit,
)

load_dotenv()
client = genai.Client()
MODEL = "gemini-3.1-flash-lite"

fetch_tool = types.FunctionDeclaration(
    name="fetch_job_page",
    description="Downloads a job post page and returns its text.",
    parameters=types.Schema(
        type="OBJECT",
        properties={"url": types.Schema(type="STRING", description="The job post link")},
        required=["url"],
    ),
)

evaluate_tool = types.FunctionDeclaration(
    name="evaluate_answer",
    description="Scores the candidate's answer to an interview question from 0 to 10.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "question": types.Schema(type="STRING", description="The question that was asked"),
            "answer": types.Schema(type="STRING", description="The candidate's answer"),
        },
        required=["question", "answer"],
    ),
)

progress_tool = types.FunctionDeclaration(
    name="get_past_progress",
    description="Returns the candidate's past average score and weak topics from earlier interviews.",
)

result_tool = types.FunctionDeclaration(
    name="get_session_result",
    description="Returns the average score of this interview and whether the candidate passed.",
)

kit_tool = types.FunctionDeclaration(
    name="build_application_kit",
    description="Writes a cover letter and CV tips. Only call this if the candidate passed.",
    parameters=types.Schema(
        type="OBJECT",
        properties={"job_description": types.Schema(type="STRING", description="Short summary of the job")},
        required=["job_description"],
    ),
)

SYSTEM = """You are a mock interview agent.
1. When the user gives a job link, call fetch_job_page AND get_past_progress.
   If the page cannot be read, ask the user to paste the job description.
2. If there are past weak topics, include questions about them.
3. Ask ONE interview question at a time, based on the job.
4. When the user answers, call evaluate_answer with the question and answer.
5. Show the score and short feedback, then ask the next question.
6. After 5 questions, call get_session_result.
7. If passed is true: you MUST call build_application_kit (never write the cover letter yourself), then show its result.
   If the tool returns an error, explain it to the user.
8. If passed is false: do NOT call build_application_kit. Give a short study plan for the weak topics and invite the user to try again."""

config = types.GenerateContentConfig(
    system_instruction=SYSTEM,
    tools=[types.Tool(function_declarations=[
        fetch_tool, evaluate_tool, progress_tool, result_tool, kit_tool,
    ])],
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)


def call_tool(name, args, store, cv_text):
    """Runs the tool Gemini asked for, giving it this visitor's data."""
    args = args or {}
    if name == "fetch_job_page":
        return fetch_job_page(args["url"])
    if name == "evaluate_answer":
        return evaluate_answer(args["question"], args["answer"], store)
    if name == "get_past_progress":
        return get_past_progress(store)
    if name == "get_session_result":
        return get_session_result(store)
    if name == "build_application_kit":
        return build_application_kit(args["job_description"], cv_text)
    return {"error": f"Unknown tool: {name}"}


def run_agent(contents, user_message, store, cv_text):
    """Runs one full agent turn. Returns (reply_text, list_of_tools_used)."""
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))
    tools_used = []

    try:
        for turn in range(6):
            response = client.models.generate_content(model=MODEL, contents=contents, config=config)
            contents.append(response.candidates[0].content)

            if not response.function_calls:
                return response.text, tools_used

            results = []
            for call in response.function_calls:
                tools_used.append(call.name)
                result = call_tool(call.name, call.args, store, cv_text)
                results.append(types.Part.from_function_response(
                    name=call.name, response={"result": result}
                ))
            contents.append(types.Content(role="user", parts=results))
    except Exception as e:
        return f"⚠️ Something went wrong ({type(e).__name__}). The AI server may be busy or the free limit is reached. Please try again in a minute.", tools_used

    return "⚠️ The agent took too many steps. Please try again.", tools_used