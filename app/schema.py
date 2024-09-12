from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel
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
    
class MessageTypeEnum(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class QuestionEvaluation(BaseModel):
    questionText: str = Field(description="The text of the question")
    questionComplexity: QuestionComplexityEnum = Field(description="The complexity level of the question")
    

class QuestionRefinement(BaseModel):
    questions: List[QuestionEvaluation] = Field(description="List of evaluated and refined questions")


class ChatInteraction(SQLModel, table=True):
    __tablename__ = "chat_interaction"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    userId: UUID | None = None
    courseId: UUID | None = None
    activityId: UUID | None = None
    userQuestionId: UUID = Field(foreign_key="user_question.id")
    question: "UserQuestion" = Relationship(back_populates="chatInteraction")
    chatMessages: List["ChatMessage"] = Relationship(back_populates="chatInteraction")

    
class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_message"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    chatInteractionId: UUID = Field(foreign_key="chat_interaction.id")
    chatInteraction: ChatInteraction = Relationship(back_populates="chatMessages")
    message: str
    messageType: str
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
    
    
class UserAssessment(SQLModel, table=True):
    __tablename__ = "user_assessment"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    userId: UUID
    courseId: UUID
    activityId: UUID | None = None
    questionCountToPractice: int | None = None
    questions: List[UserQuestion] = Relationship(back_populates="userAssessment")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    totalQuestions: int | None = None
    totalQuestionsAnsweredCorrectly: int | None = None
    totalQuestionsAnsweredWrong: int | None = None
