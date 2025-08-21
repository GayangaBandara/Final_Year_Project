from fastapi import FastAPI
from pydantic import BaseModel
import os
from supabase import create_client

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL", "https://cpuhivcyhvqayzgdvdaw.supabase.co")
supabase_key = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNwdWhpdmN5aHZxYXl6Z2R2ZGF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMzNDc4NDgsImV4cCI6MjA2ODkyMzg0OH0.dO22JLQjE7UeQHvQn6mojILNuWi_02MiZ9quz5v8pNk")  # use service role for inserts
supabase = create_client(supabase_url, supabase_key)

app = FastAPI()

class UserRequest(BaseModel):
    user_id: str

def get_user_dominant_state(user_id):
    response = (
        supabase.table("mental_state_reports")
        .select("dominant_state")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return response.data[0]['dominant_state'] if response.data else None

def get_doctors_by_dominant_state(dominant_state):
    response = (
        supabase.table("doctors")
        .select("*")
        .eq("dominant_state", dominant_state)
        .execute()
    )
    return response.data if response.data else []

def is_doctor_already_assigned(doctor_id):
    response = (
        supabase.table("recommended_doctor")
        .select("doctor_id")
        .eq("doctor_id", doctor_id)
        .execute()
    )
    return len(response.data) > 0

def store_recommended_doctor(user_id, doctor_id):
    response = supabase.table("recommended_doctor").insert({
        "user_id": user_id,
        "doctor_id": doctor_id
    }).execute()
    return response.data

def assign_best_available_doctor(user_id, matching_doctors):
    for doctor in matching_doctors:
        if not is_doctor_already_assigned(doctor["id"]):
            store_recommended_doctor(user_id, doctor["id"])
            return doctor
    return None

@app.post("/recommend")
def recommend_doctor(req: UserRequest):
    user_id = req.user_id
    dominant_state = get_user_dominant_state(user_id)

    if not dominant_state:
        return {"error": "No mental state report found"}

    matching_doctors = get_doctors_by_dominant_state(dominant_state)

    if not matching_doctors:
        return {"error": f"No doctors found for {dominant_state}"}

    assigned_doctor = assign_best_available_doctor(user_id, matching_doctors)

    if not assigned_doctor:
        return {"error": "No available doctors left"}

    return {"assigned_doctor": assigned_doctor}
