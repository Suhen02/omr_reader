


# 📝 OMR Evaluation System

A complete **OMR (Optical Mark Recognition) evaluation system** built with **FastAPI** (backend) and **Streamlit** (frontend).  
It allows colleges/institutions to upload an official answer key, process **multiple students' OMR sheets at once**, and view results — all in a simple, web-based interface.

---
---

## 📌 Problem Statement

Evaluating OMR sheets manually is time-consuming, error-prone, and not scalable for large batches of students.  
Our solution automates this process.


Solution:

### 1️⃣ Signup / Login Page
This is the page where a new college registers or logs in to the system.
![Signup Screenshot](https://github.com/Suhen02/omr_reader/blob/main/Screenshot%202025-09-21%20222256.png)

---

### 2️⃣ Upload Answer Key Page
Once logged in, you can upload the **official answer key** (XLSX/JSON).  
The system normalizes it to show **questions 1–100**, even if some are blank.
![Answer Key Screenshot](https://github.com/Suhen02/omr_reader/blob/main/Screenshot%202025-09-21%20222334.png)

---

### 3️⃣ Multi-Student Evaluation & Results Page
You can add **3 or more students** at once, upload their OMR sheets, and see their scores in one click.  
Results are displayed in a clean table and can be **downloaded as CSV**.
![Upload 3 or more students](https://github.com/Suhen02/omr_reader/blob/main/Screenshot%202025-09-21%20222521.png)
![Results Screenshot](https://github.com/Suhen02/omr_reader/blob/main/Screenshot%202025-09-21%20222533.png)


---

## ⚙️ Installation & Setup

```bash
git clone https://github.com/your-username/omr-evaluation-system.git
cd omr-evaluation-system
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
````

Start backend:

```bash
cd backend
uvicorn api.main:app --reload
```

Start frontend:

```bash
cd frontend
streamlit run app.py
```



---

## 🚀 Features

* ✅ Upload **official answer key** in XLSX/JSON
* ✅ **Multi-student OMR upload** (more students at once)
* ✅ Automatic evaluation with correct/incorrect marking
* ✅ **Batch-wise result storage** & CSV download
* ✅ Easy to run locally or deploy

---

## 🛠 Tech Stack


Backend: FastAPI, Sqllite

Frontend: Streamlit

Image Processing: OpenCV, NumPy

Data Handling: Pandas, JSON

---


## 📄 License

MIT © 2025 \[suhen02]



Would you like me to create placeholder `assets/` folder structure and dummy image links for now, so you can just drop your screenshots there and commit?
```

