import requests
url = "http://127.0.0.1:8000/api/engine/route"
data = {
    "task_type": "teach",
    "user_profile": {"user_id": "8b40ebcf-92aa-43a2-8def-bee49247cebc", "target_exam": "IIT JEE", "current_class": "12th", "language_pref": "English"},
    "learning_state": {"mastery_level": "beginner"},
    "learning_pattern": {"style": "visual"},
    "task_input": {"topic": "Newton"}
}
try:
    res = requests.post(url, json=data)
    print("STATUS:", res.status_code)
    print("BODY:", res.text)
except Exception as e:
    print("ERROR:", e)
