from app.dependencies.openai_client import openai_chat_completion
from app.dependencies.http import get
from uuid import UUID
from datetime import datetime
from app.schema import UserQuestion,  QuestionRefinement
import json
from typing import List

async def evaluate_question_complexity(extracted_question_data: List[UserQuestion]):
    question_list = []
    
    for question in extracted_question_data:
        question_list.append(question['questionText'])
    
    prompt = f"""
    Clean up and improve the structure of the following questions while retaining their core logic. Remove redundant characters, extra whitespace, fix any obvious grammatical issues. If the question text includes multiple option texts, retain and format them as part of the question text. Then, evaluate the complexity of each question and categorize it as EASY, MEDIUM, or HARD.

    Original questions:
    {json.dumps(question_list)}

    Respond with a list of cleaned questions and respective complexities as per the provided schema.
    """
    
    response = await openai_chat_completion(
        payload={
            "messages": [
                {"role": "system", "content": "You are an AI assistant specialized in educational content analysis. Your task is to refine and evaluate questions. For each question: 1) Clean up the text by removing redundant characters, extra whitespace, and fixing obvious grammatical issues while preserving the core meaning. 2) If the question includes multiple choice options, retain them and format them clearly as part of the question text. 3) Assess the complexity of the question and categorize it as EASY, MEDIUM, or HARD based on cognitive demand, subject matter depth, and required problem-solving skills. Provide your output in the specified schema format."},
                {"role": "user", "content": prompt}
            ]
        },
        output_schema=QuestionRefinement
    )
    response_data = json.loads(response)
    
    for i in range(min(len(extracted_question_data), len(response_data["questions"]))):
        extracted_question_data[i]['questionText'] = response_data["questions"][i]['questionText']
        extracted_question_data[i]['questionComplexity'] = response_data["questions"][i]['questionComplexity']
    
    return extracted_question_data


async def extract_data_from_course(course_id: str, activity_id: str, token: str) -> List[UserQuestion]:
    url = f"https://api-beta.iclicker.com/v2/courses/{course_id}/class-sections?recordsPerPage=10&pageNumber=1&excludeEmptySessions=1&expandChild=activities&expandChild=questions&expandChild=userQuestions&expandChild=results"
    headers = {
        "authorization": token,
        "content-type": "application/json",
        "accept": "application/json"
    }
    response_data = await get(url=url, headers=headers)
    
    user_questions = []
    
    for class_section in response_data:
        for activity in class_section['activities']:
            if activity['_id'] == activity_id:
                activity_data = activity
                break
        else:
            activity_data = class_section['activities'][0]
        
        for question in activity_data['questions']:
            user_question = UserQuestion(
                userId=UUID(class_section['userId']),
                courseId=UUID(class_section['courseId']),
                activityId=UUID(activity_data['_id']),
                questionText=' '.join(question['textRecognition']['extractedText']),
                questionDuration=int((datetime.fromisoformat(question['ended'].replace('Z', '+00:00')) - datetime.fromisoformat(question['created'].replace('Z', '+00:00'))).total_seconds()),
                questionType=question['answerType'],
                correctAnswer= question['results'][0]['answer'],
                userAnswer= question['userQuestions'][0]['answer'],
                isStudyComplete= True if question['userQuestions'][0]['correct'] else False,
                isCorrect=question['userQuestions'][0]['correct'],
                externalQuestionId=question['_id'],
                externalQuestionImage=question['ImageURL']
            )
            user_questions.append(user_question.model_dump())
    
    return user_questions
