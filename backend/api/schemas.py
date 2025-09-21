from pydantic import BaseModel
from typing import List, Dict, Optional

class CollegeSignup(BaseModel):
    name: str
    email: str
    password: str

class CollegeLogin(BaseModel):
    email: str
    password: str

class QuestionBreakdown(BaseModel):
    question_no: int
    selected_option: Optional[str] = None
    is_correct: bool = False

class StudentMeta(BaseModel):
    student_id: str
    name: Optional[str] = None
    college_id: int
    batch_id: int

class OMRResult(BaseModel):
    student_meta: StudentMeta
    per_subject_scores: Dict[str, int]
    total_score: int
    question_breakdown: List[QuestionBreakdown]
    audit: Optional[Dict] = None
