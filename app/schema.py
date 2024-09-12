from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime
from typing import List


class QuestionTypeEnum(str, Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    SHORT_ANSWER = "SHORT_ANSWER"
    MULTIPLE_ANSWER = "MULTIPLE_ANSWER"

class QuestionComplexityEnum(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    
class MessageTypeEnum(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"

class QuestionRefinement(BaseModel):
    questionText: str
    questionComplexityEnum: QuestionComplexityEnum

class ChatInteraction(SQLModel, table=True):
    __tablename__ = "chat_interaction"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    userId: UUID
    courseId: UUID
    questionId: UUID = Field(foreign_key="user_question.id")
    question: "UserQuestion" = Relationship(back_populates="chatInteraction")
    activityName: str
    activityId: UUID | None = None
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
    questionComplexityEnum: QuestionComplexityEnum
    questionDuration: int
    questionTypeEnum: QuestionTypeEnum
    correctAnswer: str
    userAnswer: str
    externalQuestionId: str
    isStudyComplete: bool
    isCorrect: bool
    chatInteraction: List["ChatInteraction"] = Relationship(back_populates="question")
    
    
class UserAssessment(SQLModel, table=True):
    __tablename__ = "user_assessment"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    userId: UUID
    courseId: UUID
    activityId: UUID | None = None
    questionCount: int | None = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    totalQuestions: int | None = None
    totalQuestionsAnsweredCorrectly: int | None = None
    totalQuestionsAnsweredWrong: int | None = None
