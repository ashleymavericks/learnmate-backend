import json
from app.dependencies.openai_client import openai_chat_completion
from app.dependencies.http import get
from uuid import UUID
from datetime import datetime
from app.db_adapter import insert_into_sqlite, get_all_records
from app.schema import UserQuestion, QuestionRefinement, ChatMessage, ChatMessageTypeEnum, ChatInteraction, UserAssessment, FinalEvaluationReport
from typing import List, Dict

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


async def initialize_chat_interaction(user_question: UserQuestion, chat_interaction: ChatInteraction) -> List[ChatMessage]:
    question_type = " ".join(user_question.questionType.value.split("_")).capitalize()
    question_complexity = " ".join(user_question.questionComplexity.value.split("_")).capitalize()
    
    system_prompt = """You are an AI tutor helping a student understand and answer a specific question. Provide guidance, explanations, and constructive feedback without revealing the correct answer until final evaluation. Only provide hints if explicitly asked. Do not evaluate the user's answer until they confirm it's their final answer. Keep the conversation strictly focused on the given question and its context. Do not allow the user to wander off-topic. Be strict about these rules."""
    
    user_prompt = f"""This is a {question_type} type question with {question_complexity} complexity: "{user_question.questionText}"   
    
    The correct answer is: {user_question.correctAnswer}
    The user's original answer was: {user_question.userAnswer}
    
    Initiate the conversation by introducing yourself as an AI tutor. Inform the user about the question's complexity level ({question_complexity}), question type ({question_type}), and mention that the average response time for this question is {user_question.questionDuration} seconds. Ask if they need any help understanding or approaching the question. Remember:
    1. Do not reveal the correct answer unless the user explicitly states it's their final answer.
    2. Only provide hints if the user explicitly asks for them.
    3. When the user provides their final answer, evaluate it against the correct answer.
    4. After evaluating the final answer, explain any shortcomings and provide the correct answer.
    5. Be encouraging and maintain a strict adherence to these rules throughout the interaction.
    6. Do not display the question text to the user.
    7. Keep the conversation strictly focused on this specific question and its context. If the user tries to change the topic or ask about unrelated matters, gently redirect them back to the question at hand."""
    
    initial_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    system_chat_message = ChatMessage(
        chatInteractionId=chat_interaction.id,
        message=system_prompt,
        messageType=ChatMessageTypeEnum.SYSTEM
    )
    await insert_into_sqlite(system_chat_message)
    
    user_chat_message = ChatMessage(
        chatInteractionId=chat_interaction.id,
        message=user_prompt,
        messageType=ChatMessageTypeEnum.USER
    )    
    await insert_into_sqlite(user_chat_message)
    
    assistant_response = await openai_chat_completion(
        payload={"messages": initial_messages}
    )
    assistant_chat_message = ChatMessage(
        chatInteractionId=chat_interaction.id,
        message=assistant_response,
        messageType=ChatMessageTypeEnum.ASSISTANT
    )
    await insert_into_sqlite(assistant_chat_message)
    return await get_all_records(ChatMessage, filter_by={"chatInteractionId": chat_interaction.id})


async def continue_chat_interaction(chat_messages: List[ChatMessage], chat_interaction: ChatInteraction) -> str:
    chat_history = []
    sorted_chat_messages = sorted(chat_messages, key=lambda x: x.createdAt)
    for message in sorted_chat_messages:
        chat_history.append({"role": message.messageType.value.lower(), "content": message.message})
    
    assistant_response = await openai_chat_completion(
        payload={"messages": chat_history}
    )
    
    assistant_message = ChatMessage(
        chatInteractionId=chat_interaction.id,
        message=assistant_response,
        messageType="ASSISTANT"
    )
    return await insert_into_sqlite(assistant_message)


async def generate_final_evaluation_report(user_assessment: UserAssessment, user_question_chat_interactions: Dict[UserQuestion, ChatInteraction]) -> FinalEvaluationReport:
    evaluation_prompts = []
    for user_chat_interaction in user_question_chat_interactions:
        chat_interaction = user_chat_interaction['chatInteraction']
        question = user_chat_interaction['question']
        chat_messages = await get_all_records(ChatMessage, filter_by={"chatInteractionId": chat_interaction.id})
        chat_messages = sorted(chat_messages, key=lambda x: x.createdAt)
        chat_history = [{"role": msg.messageType.value.lower(), "content": msg.message} for msg in chat_messages]
        
        prompt = f"""
        Question: {question.questionText}
        Complexity: {question.questionComplexity}
        Correct Answer: {question.correctAnswer}
        User's Original Answer: {question.userAnswer}
        Chat History: {json.dumps(chat_history)}
        
        Based on this interaction, evaluate the user's performance on the following metrics:
        1. Understanding: How well did the user understand the question?
        2. Approach: Did the user take an appropriate approach to solve the problem?
        3. Knowledge Application: How effectively did the user apply their knowledge?
        4. Learning Progress: Did the user show improvement during the interaction?
        5. Final Accuracy: Was the user's final answer correct?
        
        Provide a score from 1-5 for each metric and a brief explanation.
        """
        evaluation_prompts.append(prompt)
    
    evaluations = []
    for prompt in evaluation_prompts:
        evaluation = await openai_chat_completion(
            payload={
                "messages": [
                    {"role": "system", "content": "You are an AI evaluator assessing a student's performance based on their interaction with an AI tutor on a specific question. Analyze the chat history carefully. For each metric (Understanding, Approach, Knowledge Application, Learning Progress, Final Accuracy), provide a score from 1-5 and a concise, specific explanation referencing the student's responses."},
                    {"role": "user", "content": prompt}
                ]
            },
            output_schema=FinalEvaluationReport
        )
        evaluations.append(evaluation)

    final_prompt = f"""
    Based on the following individual question evaluations, provide an overall assessment of the user's performance across all questions:

    {json.dumps(evaluations)}

    Summarize the user's performance in these five areas:
    1. Overall Understanding
    2. Problem-Solving Approach
    3. Knowledge Application
    4. Learning Progress
    5. Final Accuracy

    For each area, provide a score from 1-5 and a brief final explanation in overallFeedback. Address the user directly in first person, providing personalized feedback and specific, actionable recommendations for improvement based on their performance.
    """
    
    final_evaluation = await openai_chat_completion(
        payload={
            "messages": [
                {"role": "system", "content": "You are an AI evaluator providing a comprehensive final assessment of a student's overall performance based on multiple question interactions. Analyze the individual evaluations carefully to identify patterns and trends. For each of the five areas (Understanding, Problem-Solving Approach, Knowledge Application, Learning Progress, Final Accuracy), provide a score from 1-5 and a concise, evidence-based explanation. In the overallFeedback, summarize the student's strengths and weaknesses, noting any significant improvements or consistent challenges across questions. Provide specific, actionable recommendations for improvement tailored to the student's performance."},
                {"role": "user", "content": final_prompt}
            ]
        },
        output_schema=FinalEvaluationReport
    )
    return json.loads(final_evaluation)
