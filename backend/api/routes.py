from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from .db import get_db
from . import models, schemas
from backend.api.omr_processor import OMRDetector
import json, hashlib, pandas as pd, io
import cv2
import numpy as np

router = APIRouter()

# -------- AUTH --------
@router.post("/signup")
def signup(name: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(models.College).filter(models.College.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    new_college = models.College(name=name, email=email, password_hash=hashed_pw)
    db.add(new_college)
    db.commit()
    db.refresh(new_college)
    return {"id": new_college.id, "name": new_college.name, "email": new_college.email}

@router.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    college = db.query(models.College).filter(models.College.email == email).first()
    if not college:
        raise HTTPException(status_code=404, detail="College not found")
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    if hashed_pw != college.password_hash:
        raise HTTPException(status_code=401, detail="Invalid password")
    return {"id": college.id, "name": college.name, "email": college.email}

# -------- BATCH --------
@router.post("/batches")
def create_batch(college_id: int = Form(...), name: str = Form(...), db: Session = Depends(get_db)):
    batch = models.Batch(name=name, college_id=college_id)
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return {"id": batch.id, "name": batch.name, "created_at": batch.created_at.isoformat()}

@router.get("/batches/{college_id}")
def list_batches(college_id: int, db: Session = Depends(get_db)):
    batches = db.query(models.Batch).filter(models.Batch.college_id == college_id).all()
    return [{"id": b.id, "name": b.name} for b in batches]

# -------- OFFICIAL RESULT --------
@router.post("/batches/{batch_id}/official_result")
async def upload_official_result(batch_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    filename = file.filename.lower()

    try:
        if filename.endswith(".json"):
            answer_key = json.loads(content.decode("utf-8"))
        elif filename.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(content), header=None)
            answer_key = {}

            # ✅ Row-wise iteration to handle multiple columns & empty cells
            for _, row in df.iterrows():
                for cell in row.dropna():
                    try:
                        cell_str = str(cell).replace(":", "-").replace(".", "-").replace(" ", "")
                        parts = cell_str.split("-")
                        if len(parts) >= 2:
                            q = int(parts[0])
                            ans = parts[1].lower()
                            answer_key[q] = ans
                    except:
                        continue
        else:
            answer_key = {}

        # ✅ Ensure all 1–100 questions are present
        for q in range(1, 101):
            if q not in answer_key:
                answer_key[q] = ""

        # ✅ Sort dictionary by question number before saving
        answer_key = {k: answer_key[k] for k in sorted(answer_key.keys())}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse official result: {str(e)}")

    existing = db.query(models.Result).filter(models.Result.batch_id == batch_id).first()
    if existing:
        existing.raw_json = json.dumps(answer_key, sort_keys=True)
    else:
        db.add(models.Result(batch_id=batch_id, college_id=1, raw_json=json.dumps(answer_key, sort_keys=True)))
    db.commit()
    return {"message": "Official answers stored", "answer_key": answer_key}


@router.post("/evaluate_student")
async def evaluate_student(file: UploadFile = File(...), student_meta: str = Form(...), db: Session = Depends(get_db)):
    try:
        meta = json.loads(student_meta)
        student_meta_obj = schemas.StudentMeta(**meta)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid student_meta")

    # Ensure student exists
    student = db.query(models.Student).filter(
        models.Student.student_id == student_meta_obj.student_id,
        models.Student.batch_id == student_meta_obj.batch_id
    ).first()

    if not student:
        student = models.Student(
            student_id=student_meta_obj.student_id,
            name=student_meta_obj.name or "",
            college_id=student_meta_obj.college_id,
            batch_id=student_meta_obj.batch_id,
            meta=json.dumps({"source": "OMR Evaluation"})
        )
        db.add(student)
    else:
        if student.name != student_meta_obj.name:
            student.name = student_meta_obj.name

    db.commit()

    # Fetch official key
    official = db.query(models.Result).filter(models.Result.batch_id == student_meta_obj.batch_id).first()
    if not official:
        raise HTTPException(status_code=400, detail="Upload official result first.")
    answer_key = json.loads(official.raw_json)

    # --- Start of Major Changes ---
    
    # 1. Read the uploaded file content.
    content = await file.read()
    
    # 2. Convert file content to an OpenCV image.
    # We use numpy to create a byte array and then decode it with cv2.imdecode.
    np_array = np.frombuffer(content, np.uint8)
    image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

    # Check if the image was decoded correctly
    if image is None:
        raise HTTPException(status_code=400, detail="Could not decode image file.")

    # 3. Instantiate and process the image with OMRProcessor.
    # Since OMRProcessor requires the image as a numpy array (or path),
    # we can pass the decoded 'image' variable directly.
    omr=OMRDetector()
    omr_result = omr.process_image(image, answer_key=answer_key)

    # --- End of Major Changes ---

    # Extract student's answers from the OMR result
    student_answers = omr_result["extracted_answers"]

    evaluated = []
    score = 0
    # The provided answer_key uses string keys, so we sort by int to keep order
    for q in sorted(answer_key.keys(), key=int):
        correct_answer = answer_key.get(str(q))
        student_ans = student_answers.get(int(q))
        
        is_correct = False
        if student_ans is not None:
            if isinstance(correct_answer, list):
                if student_ans in correct_answer:
                    is_correct = True
            elif student_ans == correct_answer:
                is_correct = True
        
        evaluated.append({
            "question": int(q),
            "correct_answer": correct_answer if not isinstance(correct_answer, list) else ",".join(correct_answer),
            "student_answer": student_ans if student_ans is not None else "Not Attempted",
            "is_correct": bool(is_correct)
        })
        
        if is_correct:
            score += 1

    # Sort answers list before saving
    evaluated = sorted(evaluated, key=lambda x: x["question"])

    result_data = {
        "student_id": student_meta_obj.student_id,
        "name": student_meta_obj.name or "",
        "batch_id": student_meta_obj.batch_id,
        "score": score,
        "total": 100,
        "answers": evaluated
    }

    db.add(models.FinalResult(
        college_id=student_meta_obj.college_id,
        batch_id=student_meta_obj.batch_id,
        aggregated_json=json.dumps(result_data)
    ))
    db.commit()

    return {"evaluated_result": result_data}




@router.get("/batches/{batch_id}/final_results")
def get_final_results(batch_id: int, db: Session = Depends(get_db)):
    results = db.query(models.FinalResult).filter(models.FinalResult.batch_id == batch_id).all()
    return [json.loads(r.aggregated_json) for r in results]
