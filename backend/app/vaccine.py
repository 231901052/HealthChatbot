import json
from datetime import datetime, timedelta
from .twilio_client import send_whatsapp
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

USERS_FILE = "./app/users_vaccine.json"
VACCINE_SCHEDULE_FILE = "./app/vaccine_data.json"

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_vaccine_schedule():
    try:
        with open(VACCINE_SCHEDULE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    print("Saving data:", users)  # Debug
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)
        f.close()
    print("Saved successfully to", USERS_FILE)

def register_child(phone: str, child_name: str, dob: str):
    users = load_users()

    if phone not in users:
        users[phone] = {"children": []}

    users[phone]["children"].append({
        "name": child_name,
        "dob": dob,
        "registered_on": datetime.now().strftime("%Y-%m-%d"),
        "completed_vaccines": [] 
    })
    logging.info(f"USERRR {users}")
    save_users(users)
    return True


def calculate_age(dob_str: str):
    dob = datetime.strptime(dob_str, "%Y-%m-%d")
    today = datetime.now()
    delta = today - dob
    weeks = delta.days // 7
    months = delta.days // 30
    years = delta.days // 365
    return {"days": delta.days, "weeks": weeks, "months": months, "years": years}


def get_due_vaccines(phone: str, child_name: str, vaccine_schedule: dict):
    users = load_users()
    due = []
    
    # Find the child
    children = users.get(phone, {}).get("children", [])
    child = next((c for c in children if c["name"] == child_name), None)
    if not child:
        return []

    age = calculate_age(child["dob"])
    print(age)
    completed = child.get("completed_vaccines", [])  # Track completed vaccines here

    # Infant vaccines
    
    for v in vaccine_schedule.get("infant_vaccines", []):
        
        if v["vaccine"] in completed:
            print(v)
            continue
        if "At birth" in v["when"] and age["weeks"] < 2:
            due.append(v)
        elif "6 weeks" in v["when"] and 6 <= age["weeks"] < 8:
            due.append(v)
        elif "10 weeks" in v["when"] and 10 <= age["weeks"] < 12:
            due.append(v)
        elif "14 weeks" in v["when"] and 14 <= age["weeks"] < 16:
            due.append(v)
        elif "9 completed months" in v["when"] and 9 <= age["months"] <= 12:
            due.append(v)

    # Children vaccines
    for v in vaccine_schedule.get("children_vaccines", []):
        if v["vaccine"] in completed:
            continue
        if "16-24 months" in v["when"] and 16 <= age["months"] <= 24:
            due.append(v)
        elif "5-6 years" in v["when"] and 5 <= age["years"] <= 6:
            due.append(v)
        elif "10 years" in v["when"] and age["years"] == 10:
            due.append(v)
        elif "16 years" in v["when"] and age["years"] == 16:
            due.append(v)

    print(due)
    return due



def check_and_notify_vaccines():
    users = load_users()
    vaccine_schedule = load_vaccine_schedule()
    for phone, data in users.items():
        for child in data.get("children", []):
            due_vaccines = get_due_vaccines(phone,child["name"], vaccine_schedule)
            logging.info(f"SINNNNNN {due_vaccines} {child}")
            if due_vaccines:
                msg = f"💉 Vaccination Reminder for {child['name']}:\n"
                for i,v in enumerate(due_vaccines):
                    msg += f"{i+1}. {v['vaccine']} ({v['when']})\n"
                send_whatsapp(phone, msg)
                logging.info(f"Sent reminder to {phone}: {msg}")


def mark_vaccine_done(phone: str, child_name: str, vaccine_name: str):
    users = load_users()
    if phone not in users:
        return False
    
    for child in users[phone]["children"]:
        if child["name"].lower() == child_name.lower():
            if "completed_vaccines" not in child:
                child["completed_vaccines"] = []
            if vaccine_name not in child["completed_vaccines"]:
                child["completed_vaccines"].append(vaccine_name)
                save_users(users)
                return True
    return False


