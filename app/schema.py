from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel, field_validator
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime
from typing import List


class QuestionTypeEnum(str, Enum):
    SINGLE_ANSWER = "SINGLE_ANSWER"
    SHORT_ANSWER = "SHORT_ANSWER"
    NUMERIC_ANSWER = "NUMERIC_ANSWER"


class QuestionComplexityEnum(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    

class ChatMessageTypeEnum(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class QuestionEvaluation(BaseModel):
    questionText: str = Field(description="The text of the question")
    questionComplexity: QuestionComplexityEnum = Field(description="The complexity level of the question")
    

class QuestionRefinement(BaseModel):
    questions: List[QuestionEvaluation] = Field(description="List of evaluated and refined questions")
    

class FinalEvaluationReport(BaseModel):
    understanding: int = Field(description="Score for the user's understanding of the questions between 1 and 5")
    approach: int = Field(description="Score for the user's approach to solving the problems between 1 and 5")
    knowledgeApplication: int = Field(description="Score for how effectively the user applied their knowledge between 1 and 5")
    learningProgress: int = Field(description="Score for the user's learning progress during the interactions between 1 and 5")
    finalAccuracy: int = Field(description="Score for the accuracy of the user's final answers between 1 and 5")
    overallFeedback: str = Field(description="Overall feedback and summary of the user's performance")


class ChatInteractionCreateModel(SQLModel):
    userQuestionId: UUID = Field(foreign_key="user_question.id")
    id: UUID = Field(default_factory=uuid4, primary_key=True)


class ChatInteraction(ChatInteractionCreateModel, table=True):
    __tablename__ = "chat_interaction"
    userId: UUID | None = None
    courseId: UUID | None = None
    activityId: UUID | None = None
    question: "UserQuestion" = Relationship(back_populates="chatInteraction")
    chatMessages: List["ChatMessage"] = Relationship(back_populates="chatInteraction")


class ChatMessageCreateModel(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    message: str
    messageType: ChatMessageTypeEnum

    
class ChatMessage(ChatMessageCreateModel, table=True):
    __tablename__ = "chat_message"
    chatInteractionId: UUID = Field(foreign_key="chat_interaction.id")
    chatInteraction: ChatInteraction = Relationship(back_populates="chatMessages")
    createdAt: datetime = Field(default_factory=datetime.utcnow)


class UserQuestion(SQLModel, table=True):
    __tablename__ = "user_question"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    userId: UUID
    courseId: UUID
    activityId: UUID
    questionText: str
    questionComplexity: QuestionComplexityEnum | None = None
    questionDuration: int
    questionType: QuestionTypeEnum
    correctAnswer: str
    userAnswer: str
    externalQuestionId: str
    externalQuestionImage: str
    isStudyComplete: bool
    isCorrect: bool
    userAssessmentId: UUID | None = Field(default=None, foreign_key="user_assessment.id")
    userAssessment: "UserAssessment" = Relationship(back_populates="questions")
    chatInteraction: List["ChatInteraction"] = Relationship(back_populates="question")


class UserAssessmentUpdateModel(SQLModel):
    questionCountToPractice: int | None = 1
    
    
class UserAssessmentCreateModel(UserAssessmentUpdateModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    userId: UUID
    courseId: UUID
    activityId: UUID | None = None

    @field_validator("activityId", mode="before")
    def validate_activity_id(cls, v):
        if v == "":
            return None
        return v


class UserAssessment(UserAssessmentCreateModel, table=True):
    __tablename__ = "user_assessment"
    userId: UUID
    courseId: UUID
    activityId: UUID | None = None
    questionCountToPractice: int | None = None
    questions: List[UserQuestion] = Relationship(back_populates="userAssessment")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    totalQuestions: int | None = None
    totalQuestionsAnsweredCorrectly: int | None = None
    totalQuestionsAnsweredWrong: int | None = None
