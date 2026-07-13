import requests
import json

WEBHOOK_URL = "http://localhost:5678/webhook/create-event"

headers = {
    "Content-Type": "application/json"
}

payload = {
    "start": "2026-07-13T11:00:00+05:30",
    "end": "2026-07-13T11:30:00+05:30",
    "summary": "Interview Appointment"
}

response = requests.post(WEBHOOK_URL, headers=headers, data=json.dumps(payload))

print("Status Code:", response.status_code)
print("Response Body:", response.text)