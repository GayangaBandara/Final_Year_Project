import os
import uuid
from datetime import datetime
from supabase import create_client, Client

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL", "https://cpuhivcyhvqayzgdvdaw.supabase.co")
supabase_key = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNwdWhpdmN5aHZxYXl6Z2R2ZGF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMzNDc4NDgsImV4cCI6MjA2ODkyMzg0OH0.dO22JLQjE7UeQHvQn6mojILNuWi_02MiZ9quz5v8pNk")
supabase = create_client(supabase_url, supabase_key)

# Common utility functions
def get_user_dominant_state(user_id):
    """Fetch the most recent dominant_state for a user"""
    try:
        response = (
            supabase.table("mental_state_reports")
            .select("dominant_state")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0]['dominant_state'] if response.data else None
    except Exception as e:
        print(f"Error fetching user state: {e}")
        return None

# Doctor recommendation functions
def get_all_doctors():
    """Fetch all doctors from the database"""
    try:
        response = supabase.table("doctors").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching doctors: {e}")
        return []

def get_doctors_by_dominant_state(dominant_state):
    """Fetch doctors who have the same dominant_state"""
    try:
        # First try to find doctors specializing in this state
        response = (
            supabase.table("doctors")
            .select("*")
            .eq("dominant_state", dominant_state)
            .execute()
        )
        
        if response.data:
            return response.data
            
        # If no specialists found, get doctors who handle general cases
        response = (
            supabase.table("doctors")
            .select("*")
            .eq("dominant_state", "General")
            .execute()
        )
        
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching doctors by dominant state: {e}")
        return []

def is_doctor_already_assigned(doctor_id):
    """Check if the doctor is already assigned to another user"""
    try:
        response = (
            supabase.table("recommended_doctor")
            .select("doctor_id")
            .eq("doctor_id", doctor_id)
            .execute()
        )
        return len(response.data) > 0
    except Exception as e:
        print(f"Error checking doctor assignment: {e}")
        return False

def store_recommended_doctor(user_id, doctor_id):
    """Store the recommended doctor for a user"""
    try:
        response = supabase.table("recommended_doctor").insert({
            "user_id": user_id,
            "doctor_id": doctor_id
        }).execute()
        print(f"\n💾 Recommended doctor stored successfully for user {user_id}")
        return response.data
    except Exception as e:
        print(f"Error storing recommended doctor: {e}")
        return None

def assign_best_available_doctor(user_id, matching_doctors):
    """
    Assign the best available doctor based on specialization and availability.
    """
    try:
        # Check if user already has an assigned doctor
        existing = (
            supabase.table("recommended_doctor")
            .select("doctor_id")
            .eq("user_id", user_id)
            .execute()
        )
        
        if existing.data:
            doctor_id = existing.data[0]["doctor_id"]
            doctor = next((d for d in matching_doctors if d["id"] == doctor_id), None)
            if doctor:
                return doctor
        
        # Sort doctors by specialization (specialists first, then general practitioners)
        sorted_doctors = sorted(
            matching_doctors,
            key=lambda x: 0 if x.get("dominant_state") != "General" else 1
        )
        
        # Try to find an available doctor
        for doctor in sorted_doctors:
            if not is_doctor_already_assigned(doctor["id"]):
                result = store_recommended_doctor(user_id, doctor["id"])
                if result:
                    print(f"\n✅ Assigned Dr. {doctor['name']} to user {user_id}")
                    return doctor
        
        print(f"\n❌ No available doctors found for user {user_id}")
        return None
        
    except Exception as e:
        print(f"Error assigning doctor: {e}")
        return None

def display_doctors(doctors, title="ALL DOCTORS"):
    """Display doctors in a formatted way using the actual table columns"""
    print(f"\n{title}")
    print("=" * 70)
    
    if not doctors:
        print("No doctors found.")
        return
    
    for i, doctor in enumerate(doctors, 1):
        print(f"\n{i}. Dr. {doctor.get('name', 'N/A')}")
        print(f"   Email: {doctor.get('email', 'N/A')}")
        print(f"   Phone: {doctor.get('phone', 'N/A')}")
        print(f"   Category: {doctor.get('category', 'N/A')}")
        print(f"   Specializes in: {doctor.get('dominant_state', 'General')}")
        print("-" * 50)

# Entertainment recommendation functions
def get_entertainments_by_dominant_state(dominant_state):
    """Fetch entertainments that match the dominant state"""
    try:
        response = supabase.table('entertainments') \
            .select('id, title, type, dominant_state') \
            .eq('dominant_state', dominant_state) \
            .execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching entertainments: {e}")
        return []

def store_recommended_entertainments(user_id, entertainments, dominant_state):
    """Store entertainment recommendations for a user"""
    recommendations_stored = 0
    
    for entertainment in entertainments:
        try:
            recommendation_data = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'entertainment_id': entertainment['id'],
                'recommended_at': datetime.now().isoformat(),
                'matched_state': dominant_state
            }
            
            # Insert into the recommended_entertainments table
            supabase.table('recommended_entertainments') \
                .insert(recommendation_data) \
                .execute()
            
            recommendations_stored += 1
            print(f"     ✅ Stored {entertainment['title']} recommendation")
            
        except Exception as insert_error:
            print(f"     ❌ Failed to store {entertainment['title']} recommendation: {insert_error}")
    
    return recommendations_stored

def display_entertainments(entertainments, title="RECOMMENDED ENTERTAINMENTS"):
    """Display entertainments in a formatted way"""
    print(f"\n{title}")
    print("=" * 70)
    
    if not entertainments:
        print("No entertainments found.")
        return
    
    for i, entertainment in enumerate(entertainments, 1):
        print(f"\n{i}. {entertainment.get('title', 'N/A')}")
        print(f"   Type: {entertainment.get('type', 'N/A')}")
        print(f"   Matches state: {entertainment.get('dominant_state', 'N/A')}")
        print("-" * 50)

def display_stored_recommendations(user_id):
    """Display stored entertainment recommendations for a user"""
    try:
        response = supabase.table('recommended_entertainments') \
            .select('''
                id,
                user_id,
                entertainment_id,
                recommended_at,
                matched_state,
                entertainments!inner(title, type)
            ''') \
            .eq('user_id', user_id) \
            .order('recommended_at', desc=True) \
            .execute()
        
        if response.data:
            print(f"\n📋 Stored Entertainment Recommendations for User {user_id}:")
            print("=" * 70)
            
            for i, rec in enumerate(response.data, 1):
                print(f"{i}. Entertainment: {rec['entertainments']['title']}")
                print(f"   Type: {rec['entertainments']['type']}")
                print(f"   Recommended at: {rec['recommended_at']}")
                print(f"   Matched State: {rec['matched_state']}")
                print()
        else:
            print(f"\nNo stored entertainment recommendations found for user {user_id}")
            
    except Exception as e:
        print(f"Error fetching stored recommendations: {e}")

# Main recommendation system
def recommend_doctors(user_id, dominant_state):
    """Doctor recommendation logic"""
    print(f"\n=== DOCTOR RECOMMENDATION ===")
    
    if dominant_state:
        print(f"🧠 User's dominant mental state: {dominant_state.upper()}")
        
        # Get doctors with matching dominant_state
        matching_doctors = get_doctors_by_dominant_state(dominant_state)
        
        if matching_doctors:
            # Assign best available doctor
            assigned_doctor = assign_best_available_doctor(user_id, matching_doctors)
            
            if assigned_doctor:
                display_doctors([assigned_doctor], f"ASSIGNED DOCTOR FOR {dominant_state.upper()}")
            else:
                print(f"\n⚠️ No available doctors specialize in '{dominant_state}' (all assigned).")
                # Show all doctors as fallback
                all_doctors = get_all_doctors()
                display_doctors(all_doctors, "ALL AVAILABLE DOCTORS")
        else:
            print(f"\n⚠️ No doctors specialize in '{dominant_state}'")
            all_doctors = get_all_doctors()
            display_doctors(all_doctors, "ALL AVAILABLE DOCTORS")
    else:
        print(f"\n❌ No mental state reports found for user {user_id}.")
        all_doctors = get_all_doctors()
        display_doctors(all_doctors, "ALL AVAILABLE DOCTORS")

def recommend_entertainments(user_id, dominant_state):
    """Entertainment recommendation logic"""
    print(f"\n=== ENTERTAINMENT RECOMMENDATION ===")
    
    if dominant_state:
        print(f"🧠 User's dominant mental state: {dominant_state.upper()}")
        
        # Fetch entertainments with matching dominant state
        print(f"\n🔍 Searching for entertainments matching '{dominant_state}' state...")
        
        matching_entertainments = get_entertainments_by_dominant_state(dominant_state)
        
        if matching_entertainments:
            print(f"\n🎉 Found {len(matching_entertainments)} entertainment(s) matching your dominant state:")
            display_entertainments(matching_entertainments)
            
            # Store recommendations
            stored_count = store_recommended_entertainments(user_id, matching_entertainments, dominant_state)
            print(f"\n📊 Successfully stored {stored_count} recommendation(s) in 'recommended_entertainments' table!")
            
            # Display stored recommendations
            display_stored_recommendations(user_id)
        else:
            print(f"\n❌ No entertainments found matching the '{dominant_state}' state.")
    else:
        print(f"\n❌ No mental state reports found for user: {user_id}")

def main():
    """Main function to run the combined recommendation system"""
    print("=== COMBINED RECOMMENDATION SYSTEM ===")
    
    # Get user input
    user_id = input("Please enter the user ID: ").strip()
    
    if not user_id:
        print("User ID cannot be empty.")
        return
    
    # Get user's dominant state
    dominant_state = get_user_dominant_state(user_id)
    
    # Automatically provide both recommendations
    recommend_doctors(user_id, dominant_state)
    recommend_entertainments(user_id, dominant_state)

# Run the program
if __name__ == "__main__":
    main()