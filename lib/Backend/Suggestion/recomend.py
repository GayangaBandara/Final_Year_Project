import os
from supabase import create_client, Client

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL", "https://cpuhivcyhvqayzgdvdaw.supabase.co")
supabase_key = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNwdWhpdmN5aHZxYXl6Z2R2ZGF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMzNDc4NDgsImV4cCI6MjA2ODkyMzg0OH0.dO22JLQjE7UeQHvQn6mojILNuWi_02MiZ9quz5v8pNk")
supabase = create_client(supabase_url, supabase_key)

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

def main():
    """Main function to run the doctor recommendation system"""
    print("=== Doctor Matching System ===")
    
    # Get user input
    user_id = input("Please enter the user ID: ").strip()
    
    if not user_id:
        print("User ID cannot be empty.")
        return
    
    # Get user's dominant state
    dominant_state = get_user_dominant_state(user_id)
    
    if dominant_state:
        print(f"\n✅ User's dominant mental state: {dominant_state.upper()}")
        
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

# Run the program
if __name__ == "__main__":
    main()
