
import streamlit as st
import requests
import json
import pandas as pd

API_BASE = "http://127.0.0.1:8000/api"
st.set_page_config(page_title="OMR Evaluator", layout="wide")

# ----- SESSION STATE -----
if "college" not in st.session_state:
    st.session_state.college = None
if "batches" not in st.session_state:
    st.session_state.batches = []
if "batch_id" not in st.session_state:
    st.session_state.batch_id = None
if "official_set" not in st.session_state:
    st.session_state.official_set = False
if "current_batch_results" not in st.session_state:
    st.session_state.current_batch_results = []
if "students_list" not in st.session_state:
    st.session_state.students_list = [{"sid": "", "sname": "", "omr_file": None}]

# ----- SIDEBAR -----
if st.session_state.college:
    menu = st.sidebar.radio("Navigation", ["Dashboard", "Logout"])
else:
    menu = st.sidebar.radio("Navigation", ["Signup", "Login"])

# ----- AUTH -----
if menu == "Signup":
    st.title("College Signup")
    st.markdown("**Instructions:** Fill in your college name, email, and password to create a new account.")

    with st.form("signup_form"):
        cname = st.text_input("College Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Signup")
        if submitted:
            resp = requests.post(f"{API_BASE}/signup", data={"name": cname, "email": email, "password": password})
            if resp.status_code == 200:
                st.success("Signup successful. Please log in from the left sidebar.")
            else:
                st.error(resp.text)

elif menu == "Login":
    st.title("College Login")
    st.markdown("**Instructions:** Enter your registered email and password to log in.")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            resp = requests.post(f"{API_BASE}/login", data={"email": email, "password": password})
            if resp.status_code == 200:
                st.session_state.college = resp.json()
                st.rerun()
            else:
                st.error(resp.text)

elif menu == "Dashboard":
    st.title("Dashboard")
    college_id = st.session_state.college["id"]

    # ----- BATCH MANAGEMENT -----
    st.subheader("Batch Management")
    st.markdown("**Instructions:** Select an existing batch from the dropdown below, or create a new batch if none exist.")

    batch_resp = requests.get(f"{API_BASE}/batches/{college_id}")
    if batch_resp.status_code == 200:
        st.session_state.batches = batch_resp.json()

    batch_names = [b["name"] for b in st.session_state.batches]
    selected_batch = st.selectbox("Select Batch", batch_names)

    if selected_batch:
        st.session_state.batch_id = next(b["id"] for b in st.session_state.batches if b["name"] == selected_batch)

    with st.expander("Create New Batch"):
        st.markdown("Fill the batch name below and click **Create Batch** to add a new batch for this college.")
        with st.form("create_batch_form"):
            batch_name = st.text_input("Batch Name")
            submit_batch = st.form_submit_button("Create Batch")
            if submit_batch:
                resp = requests.post(f"{API_BASE}/batches", data={"college_id": college_id, "name": batch_name})
                if resp.status_code == 200:
                    st.success("Batch created successfully. It will now appear in the dropdown above.")
                    st.rerun()
                else:
                    st.error(resp.text)

    # ----- OFFICIAL ANSWER KEY -----
    st.subheader("Upload Official Answer Key")
    st.markdown("**Instructions:** Upload the official answer key for this batch in either XLSX or JSON format. "
                "The system will automatically normalize and display all 100 questions, filling blanks if missing.")

    official_file = st.file_uploader("Choose Answer Key File", type=["xlsx", "json"])
    if st.button("Upload Official Key"):
        if st.session_state.batch_id and official_file:
            resp = requests.post(
                f"{API_BASE}/batches/{st.session_state.batch_id}/official_result",
                files={"file": (official_file.name, official_file.getvalue(), official_file.type)},
            )
            if resp.status_code == 200:
                st.session_state.official_set = True
                st.success("Official answer key uploaded successfully.")
                key_dict = resp.json()["answer_key"]

                key_dict = {int(k): v for k, v in key_dict.items()}
                df_key = pd.DataFrame({
                    "Question": range(1, 101),
                    "Answer": [key_dict.get(q, "") for q in range(1, 101)]
                })

                st.dataframe(df_key, use_container_width=True)
            else:
                st.error(resp.text)
        else:
            st.warning("Please select a batch before uploading an answer key.")

    # ----- STUDENT EVALUATION -----
    st.subheader("Student OMR Evaluation")
    st.markdown("**Instructions:** Add student details and upload their OMR sheet image. "
                "You can add multiple students at once and evaluate them together.")

    def add_student_row():
        st.session_state.students_list.append({"sid": "", "sname": "", "omr_file": None})

    def reset_students():
        st.session_state.students_list = [{"sid": "", "sname": "", "omr_file": None}]

    with st.form("multi_student_form", clear_on_submit=False):
        for i, student in enumerate(st.session_state.students_list):
            st.markdown(f"#### Student {i+1}")
            st.session_state.students_list[i]["sid"] = st.text_input(f"Student ID {i+1}", value=student["sid"], key=f"sid_{i}")
            st.session_state.students_list[i]["sname"] = st.text_input(f"Student Name {i+1}", value=student["sname"], key=f"sname_{i}")
            st.session_state.students_list[i]["omr_file"] = st.file_uploader(
                f"Upload OMR Sheet for Student {i+1}", type=["jpg", "jpeg", "png"], key=f"omr_{i}"
            )

        st.form_submit_button("Add Another Student", on_click=add_student_row)
        evaluate_all = st.form_submit_button("Evaluate All Students")
        st.form_submit_button("Reset Form", on_click=reset_students)

    if evaluate_all:
        if not st.session_state.batch_id:
            st.warning("Please select a batch before evaluation.")
        else:
            results_list = []
            for student in st.session_state.students_list:
                if not student["sid"] or not student["omr_file"]:
                    st.warning(f"Skipping student with missing ID or OMR file.")
                    continue
                meta = {
                    "student_id": student["sid"],
                    "name": student["sname"],
                    "college_id": st.session_state.college["id"],
                    "batch_id": st.session_state.batch_id
                }
                files = {"file": (student["omr_file"].name, student["omr_file"].getvalue(), student["omr_file"].type)}
                data = {"student_meta": json.dumps(meta)}

                resp = requests.post(f"{API_BASE}/evaluate_student", files=files, data=data)

                if resp.status_code == 200:
                    result = resp.json()["evaluated_result"]
                    st.success(f"Result stored for {student['sname'] or student['sid']}")
                    results_list.append(result)
                else:
                    st.error(f"Failed to evaluate student {student['sid']}: {resp.text}")

            if results_list:
                df_all = pd.DataFrame([
                    {"Student ID": r["student_id"], "Name": r["name"], "Score": r["score"], "Total": r["total"]}
                    for r in results_list
                ])
                st.subheader("Evaluation Summary")
                st.markdown("The table below shows the scores of all students evaluated in this batch.")
                st.dataframe(df_all, use_container_width=True)

                batch_resp = requests.get(f"{API_BASE}/batches/{st.session_state.batch_id}/final_results")
                if batch_resp.status_code == 200:
                    st.session_state.current_batch_results = batch_resp.json()
                    st.success("Batch results updated successfully.")

    # ----- VIEW BATCH RESULTS -----
    st.subheader("Batch Results")
    st.markdown("**Instructions:** View or download the evaluation results for this batch.")

    if st.session_state.batch_id:
        if st.session_state.current_batch_results:
            results_df = pd.DataFrame(st.session_state.current_batch_results)
            results_df = results_df.drop(columns=["answers"])
            st.dataframe(results_df, use_container_width=True)

            csv = results_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Results as CSV", data=csv, file_name="batch_results.csv", mime="text/csv")

elif menu == "Logout":
    st.session_state.clear()
    st.rerun()
