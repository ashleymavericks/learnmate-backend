from app.dependencies.openai_client import openai_chat_completion
from app.schema import QuestionModel

async def evaluate_question_complexity(question_text: str):
    
    prompt = f"""
    First, clean up the following question by removing redundant characters, extra whitespace, and fixing any obvious grammatical issues. Then, evaluate its complexity and categorize it as EASY, MEDIUM, or HARD.

    Original question: {question_text}

    Respond in the following format:
    Cleaned question: [Cleaned version of the question]
    Complexity: [EASY/MEDIUM/HARD]
    """
    
    response = await openai_chat_completion(
        payload={
            "messages": [
                {"role": "system", "content": "You are an AI that cleans up text and evaluates question complexity."},
                {"role": "user", "content": prompt}
            ]
        },
        output_schema=QuestionModel
    )
    
    return response.choices[0].message.content
