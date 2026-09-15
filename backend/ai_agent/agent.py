"""
VidyaSetu AI Agent
Uses Gemini Function Calling to intelligently select and call backend analytics tools,
then summarizes verified data results naturally.
"""
import os
import json
import google.generativeai as genai
from .tools import (
    get_dashboard_summary,
    get_attendance_analysis,
    get_mdm_analysis,
    get_infrastructure_analysis,
    get_learning_analysis,
    get_risk_analysis,
    get_school_details,
    get_district_analysis,
    get_all_districts_ranked,
    compare_electricity_scores,
    compare_districts,
    AGENT_TOOLS,
)

# Dispatch map: maps function names Gemini may call to actual Python callables
TOOL_DISPATCH = {
    "get_dashboard_summary": get_dashboard_summary,
    "get_attendance_analysis": get_attendance_analysis,
    "get_mdm_analysis": get_mdm_analysis,
    "get_infrastructure_analysis": get_infrastructure_analysis,
    "get_learning_analysis": get_learning_analysis,
    "get_risk_analysis": get_risk_analysis,
    "get_school_details": get_school_details,
    "get_district_analysis": get_district_analysis,
    "get_all_districts_ranked": get_all_districts_ranked,
    "compare_electricity_scores": compare_electricity_scores,
    "compare_districts": compare_districts,
}

# System prompt that sets the agent's behaviour
SYSTEM_PROMPT = """You are VidyaSetu AI Assistant — a professional data analysis agent for the VidyaSetu school monitoring project.

Your role is to answer natural-language questions about school attendance, Mid-Day Meal (MDM) data, infrastructure, FLN/test scores, and retention risk — all based strictly on actual project data retrieved by calling the provided tools.

IMPORTANT RULES:
1. Always call a tool to retrieve verified data before answering any question that involves numbers or specific schools/districts.
2. Never invent, estimate, or hallucinate numbers. Only report values returned by the tools.
3. Use "Retention Risk Indicator" or "Early Warning Risk Score" — do NOT claim actual dropout probability prediction.
4. Avoid causal language; use "associated with", "in this dataset", or "based on available data".
5. If a question is not about VidyaSetu education data (attendance, MDM, infrastructure, learning, risk), politely say you are specialized for VidyaSetu data only.
6. Answer in a natural, professional, executive-friendly style.
7. When tool data is insufficient to answer, clearly say so.
"""

def run_agent(user_query: str):
    """
    Runs the VidyaSetu AI agent on a user query.
    Returns a dict with: answer (str), chart_type (str|None), chart_data (list|None)
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "answer": "AI Agent is unavailable. Please configure GEMINI_API_KEY in the backend.",
            "chart_type": None,
            "chart_data": None,
        }

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-flash-lite-latest",
        tools=AGENT_TOOLS,
        system_instruction=SYSTEM_PROMPT,
    )

    chart_type = None
    chart_data = None

    try:
        # Start the conversation
        chat = model.start_chat(enable_automatic_function_calling=False)
        response = chat.send_message(user_query)

        # Agentic loop: keep executing tool calls until the model gives a final text answer
        max_iterations = 5
        iteration = 0
        while iteration < max_iterations:
            iteration += 1

            # Check if there are function calls in the response
            fn_calls = []
            for part in response.parts:
                if hasattr(part, "function_call") and part.function_call.name:
                    fn_calls.append(part.function_call)

            if not fn_calls:
                # No more function calls — this is the final text answer
                break

            # Execute each function call and build the function response parts
            tool_response_parts = []
            for fn_call in fn_calls:
                fn_name = fn_call.name
                fn_args = dict(fn_call.args) if fn_call.args else {}

                if fn_name not in TOOL_DISPATCH:
                    result = {"error": f"Unknown tool: {fn_name}"}
                else:
                    try:
                        result = TOOL_DISPATCH[fn_name](**fn_args)
                    except Exception as e:
                        result = {"error": str(e)}

                # Extract chart data if the tool returned it (take the last chart result)
                if "chart_type" in result and result["chart_type"]:
                    chart_type = result["chart_type"]
                    chart_data = result.get("chart_data")

                # Build function response part to send back to the model
                tool_response_parts.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=fn_name,
                            response={"result": json.dumps(result, default=str)},
                        )
                    )
                )

            # Send tool results back to the model
            response = chat.send_message(tool_response_parts)

        # Extract the final text answer
        answer_text = ""
        for part in response.parts:
            if hasattr(part, "text") and part.text:
                answer_text += part.text

        if not answer_text:
            answer_text = "I was unable to generate a response. Please try rephrasing your question."

        return {
            "answer": answer_text,
            "chart_type": chart_type,
            "chart_data": chart_data,
        }

    except Exception as e:
        return {
            "answer": f"An error occurred while processing your request: {str(e)}",
            "chart_type": None,
            "chart_data": None,
        }
