from fastapi import APIRouter, HTTPException, Request
from app.schema import UserAssessment, UserQuestion, ChatInteraction, ChatMessage, UserAssessmentCreateModel, \
    UserAssessmentUpdateModel
from app.usecase import evaluate_question_complexity, extract_data_from_course
from app.db_adapter import insert_into_sqlite, get_record, get_all_records, update_record
import random
from typing import List
from uuid import UUID

router = APIRouter()


@router.put("/userAssessments", response_model=UserAssessment)
async def process_data(request: Request, payload: UserAssessmentCreateModel):
    token = request.headers.get("Authorization")

    user_id = payload.userId
    course_id = payload.courseId
    activity_id = payload.activityId

    # Insert User Questions
    extracted_question_data = await extract_data_from_course(str(course_id), str(activity_id), token)
    enhanced_extracted_question_data = await evaluate_question_complexity(extracted_question_data)
    user_questions = [UserQuestion(**question) for question in enhanced_extracted_question_data]

    total_questions_answered_correctly = 0
    total_questions_answered_wrong = 0
    total_questions = len(user_questions)
    for user_question in user_questions:
        if user_question.isCorrect:
            total_questions_answered_correctly += 1
        else:
            total_questions_answered_wrong += 1

    check_existing_user_questions = await get_all_records(UserQuestion,
                                                          filter_by={"userId": user_id, "courseId": course_id})
    if check_existing_user_questions:
        return check_existing_user_questions[0]

    await insert_into_sqlite(user_questions)

    # Insert User Assessment
    user_assessment = UserAssessment(
        userId=user_id,
        courseId=course_id,
        activityId=activity_id,
        totalQuestions=total_questions,
        totalQuestionsAnsweredCorrectly=total_questions_answered_correctly,
        totalQuestionsAnsweredWrong=total_questions_answered_wrong
    )

    inserted_assessment = await insert_into_sqlite(user_assessment)

    if inserted_assessment:
        return inserted_assessment
    else:
        raise HTTPException(status_code=404, detail="UserAssessment not found after insertion")


@router.patch("/userAssessments/{userAssessmentId}", response_model=UserAssessment)
async def update_user_assessment(userAssessmentId: UUID, payload: UserAssessmentUpdateModel):
    user_assessment = await get_record(UserAssessment, userAssessmentId)
    if not user_assessment:
        raise HTTPException(status_code=404, detail="User assessment not found")

    if user_assessment.activityId:
        user_question_without_assessment_filter = {"userAssessmentId": None, "courseId": user_assessment.courseId,
                                                   "activityId": user_assessment.activityId,
                                                   "userId": user_assessment.userId}
    else:
        user_question_without_assessment_filter = {"userAssessmentId": None, "courseId": user_assessment.courseId,
                                                   "userId": user_assessment.userId}
    user_question_without_assessment = await get_all_records(UserQuestion,
                                                             filter_by=user_question_without_assessment_filter)
    user_question_paylod = {"userAssessmentId": userAssessmentId}

    for user_question in user_question_without_assessment:
        await update_record(UserQuestion, user_question.id, **user_question_paylod)
    return await update_record(UserAssessment, userAssessmentId, **payload.model_dump(exclude_unset=True))


@router.get("/userAssessments/{userAssessmentId}/userQuestions", response_model=List[UserQuestion])
async def get_user_assessment(userAssessmentId: UUID, request: Request):
    user_assessment = await get_record(UserAssessment, userAssessmentId)
    if not user_assessment:
        raise HTTPException(status_code=404, detail="User assessment not found")

    question_details = await get_all_records(UserQuestion,
                                             filter_by={"userAssessmentId": userAssessmentId, "isStudyComplete": False})
    total_questions = len(question_details)

    question_count_to_practice = user_assessment.questionCountToPractice
    selected_indices = random.sample(range(total_questions), question_count_to_practice)
    selected_questions = [question_details[i] for i in selected_indices]
    return selected_questions


@router.put("/chatInteractions", response_model=ChatInteraction)
async def create_chat_interaction(payload: ChatInteraction, request: Request):
    payload_dict = payload.model_dump()
    payload = ChatInteraction.model_validate(payload_dict)

    user_question = await get_record(UserQuestion, payload.userQuestionId)
    if not user_question:
        raise HTTPException(status_code=404, detail="User Question not found")

    if user_question.isStudyComplete:
        raise HTTPException(status_code=400, detail="Question study is already completed")

    chat_interaction = ChatInteraction(
        userId=user_question.userId,
        courseId=user_question.courseId,
        activityId=user_question.activityId,
        userQuestionId=user_question.id
    )
    # TODO: When to update the isStudyComplete to True
    existing_chat_interaction = await get_all_records(ChatInteraction, filter_by={"userQuestionId": user_question.id})
    if existing_chat_interaction:
        return existing_chat_interaction[0]

    inserted_chat_interaction = await insert_into_sqlite(chat_interaction)
    if inserted_chat_interaction:
        return inserted_chat_interaction
    else:
        raise HTTPException(status_code=500, detail="Failed to create chat interaction")

# @router.get("/chatInteractions/{chatInteractionId}/messages", response_model=ChatInteraction)
# async def get_chat_interaction_messages(chatInteractionId: UUID, request: Request):
#     token = request.headers.get("Authorization")
#     chat_interaction = await get_record(ChatInteraction, chatInteractionId)
#     if chat_interaction:
#         return chat_interaction
#     else:
#         raise HTTPException(status_code=404, detail="Chat interaction not found"        
# @router.post("/chatEvalaution", response_model=ChatInteraction)
