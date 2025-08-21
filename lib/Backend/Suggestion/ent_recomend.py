from supabase import create_client
import uuid
from datetime import datetime

# Initialize Supabase client
supabase = create_client(
    "https://cpuhivcyhvqayzgdvdaw.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNwdWhpdmN5aHZxYXl6Z2R2ZGF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMzNDc4NDgsImV4cCI6MjA2ODkyMzg0OH0.dO22JLQjE7UeQHvQn6mojILNuWi_02MiZ9quz5v8pNk"
)

# Get user input
user_id = input("Enter the user ID: ").strip()

if not user_id:
    print("Please provide a user ID")
    exit()

try:
    # Fetch user's dominant state
    response = supabase.table('mental_state_reports') \
        .select('dominant_state, created_at') \
        .eq('user_id', user_id) \
        .order('created_at', desc=True) \
        .limit(1) \
        .execute()
    
    if response.data:
        report = response.data[0]
        user_dominant_state = report['dominant_state']
        
        print(f"\n✅ Latest mental state report found:")
        print(f"👤 User ID: {user_id}")
        print(f"🧠 Dominant State: {user_dominant_state}")
        print(f"📅 Report Date: {report['created_at']}")
        
        # Fetch entertainments with matching dominant state
        print(f"\n🔍 Searching for entertainments matching '{user_dominant_state}' state...")
        
        entertainment_response = supabase.table('entertainments') \
            .select('id, title, type, dominant_state') \
            .eq('dominant_state', user_dominant_state) \
            .execute()
        
        if entertainment_response.data:
            print(f"\n🎉 Found {len(entertainment_response.data)} entertainment(s) matching your dominant state:")
            
            # Store recommendations in the new table
            recommendations_stored = 0
            
            for entertainment in entertainment_response.data:
                print(f"   - {entertainment['title']} ({entertainment['type']})")
                
                # Insert into recommended_entertainments table
                try:
                    recommendation_data = {
                        'id': str(uuid.uuid4()),  # Generate unique ID for each recommendation
                        'user_id': user_id,
                        'entertainment_id': entertainment['id'],
                        'recommended_at': datetime.now().isoformat(),
                        'matched_state': user_dominant_state
                    }
                    
                    # Insert into the recommended_entertainments table
                    insert_response = supabase.table('recommended_entertainments') \
                        .insert(recommendation_data) \
                        .execute()
                    
                    recommendations_stored += 1
                    print(f"     ✅ Stored recommendation in database")
                    
                except Exception as insert_error:
                    print(f"     ❌ Failed to store recommendation: {insert_error}")
            
            print(f"\n📊 Successfully stored {recommendations_stored} recommendation(s) in 'recommended_entertainments' table!")
            
            # Optional: Read back and display stored recommendations
            print(f"\n📋 Stored Recommendations:")
            stored_response = supabase.table('recommended_entertainments') \
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
            
            if stored_response.data:
                for i, rec in enumerate(stored_response.data, 1):
                    print(f"{i}. Entertainment: {rec['entertainments']['title']}")
                    print(f"   Type: {rec['entertainments']['type']}")
                    print(f"   Recommended at: {rec['recommended_at']}")
                    print(f"   Matched State: {rec['matched_state']}")
                    print()
            
        else:
            print(f"\n❌ No entertainments found matching the '{user_dominant_state}' state.")
            
    else:
        print(f"\n❌ No mental state reports found for user: {user_id}")
        
except Exception as e:
    print(f"❌ Error occurred: {e}")