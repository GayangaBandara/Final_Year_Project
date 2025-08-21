from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from Mental_Health_Chatbot.MentalHealthChatbot import router as chatbot_router
from pydantic import BaseModel
import logging
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional, List
from datetime import datetime
import uuid

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create FastAPI app
app = FastAPI(title="SafeSpace API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the chatbot router with prefix
app.include_router(chatbot_router, prefix="/api", tags=["chatbot"])

@app.get("/")
async def root():
    return {
        "message": "SafeSpace API is running",
        "endpoints": {
            "chatbot": "/api/chat",
            "status": "/",
            "entertainment": "/recommend_entertainment"
        }
    }

class UserRequest(BaseModel):
    user_id: str

def get_user_dominant_state(user_id: str) -> Optional[str]:
    """Get the user's most recent dominant mental state"""
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
        logger.error(f"Error getting user state: {str(e)}")
        return None

def get_doctors_by_dominant_state(dominant_state: str) -> list:
    """Get doctors that can handle a specific mental state"""
    try:
        response = (
            supabase.table("doctors")
            .select("*")
            .or_(f"dominant_state.eq.{dominant_state},dominant_state.is.null")
            .execute()
        )
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error getting doctors: {str(e)}")
        return []

def is_doctor_already_assigned(doctor_id: str) -> bool:
    """Check if a doctor is already assigned to someone"""
    try:
        response = (
            supabase.table("recommended_doctor")
            .select("doctor_id")
            .eq("doctor_id", doctor_id)
            .execute()
        )
        return len(response.data) > 0
    except Exception as e:
        logger.error(f"Error checking doctor assignment: {str(e)}")
        return True  # Assume assigned in case of error

def store_recommended_doctor(user_id: str, doctor_id: str) -> Optional[dict]:
    """Store a doctor recommendation for a user"""

@app.post("/recommend_entertainment")
async def recommend_entertainment(request: UserRequest) -> dict:
    """Get entertainment recommendations for a user based on their mental state"""
    try:
        # Fetch user's dominant state
        response = (
            supabase.table('mental_state_reports')
            .select('dominant_state, created_at')
            .eq('user_id', request.user_id)
            .order('created_at', desc=True)
            .limit(1)
            .execute()
        )
        
        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="No mental state report found for this user"
            )

        report = response.data[0]
        user_dominant_state = report['dominant_state']
        
        # Fetch entertainments with matching dominant state
        entertainment_response = (
            supabase.table('entertainments')
            .select('id, title, type, dominant_state, cover_img_url, description, media_file_url')
            .eq('dominant_state', user_dominant_state)
            .execute()
        )
        
        if not entertainment_response.data:
            return {
                "success": True,
                "recommendations": [],
                "message": f"No entertainments found matching the '{user_dominant_state}' state."
            }
            
        # Store recommendations and prepare response
        recommendations = []
        for entertainment in entertainment_response.data:
            try:
                recommendation_data = {
                    'id': str(uuid.uuid4()),
                    'user_id': request.user_id,
                    'entertainment_id': entertainment['id'],
                    'recommended_at': datetime.now().isoformat(),
                    'matched_state': user_dominant_state
                }
                
                # Store the recommendation
                supabase.table('recommended_entertainments').insert(recommendation_data).execute()
                
                # Add to return list with additional details
                recommendations.append({
                    **entertainment,
                    'recommended_at': recommendation_data['recommended_at'],
                    'matched_state': user_dominant_state
                })
                
            except Exception as insert_error:
                logger.error(f"Failed to store recommendation: {insert_error}")
                continue
        
        return {
            "success": True,
            "recommendations": recommendations,
            "dominant_state": user_dominant_state
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in recommend_entertainment endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    try:
        response = supabase.table("recommended_doctor").insert({
            "user_id": user_id,
            "doctor_id": doctor_id
        }).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error storing recommendation: {str(e)}")
        return None

def assign_best_available_doctor(user_id: str, matching_doctors: list) -> Optional[dict]:
    """Find and assign the best available doctor from a list"""
    for doctor in matching_doctors:
        if not is_doctor_already_assigned(doctor["id"]):
            if store_recommended_doctor(user_id, doctor["id"]):
                return doctor
    return None

@app.post("/recommend")
async def recommend_doctor(req: UserRequest):
    """Recommend a doctor for a user based on their mental state"""
    try:
        logger.info("====== New Doctor Recommendation Request ======")
        logger.info(f"User ID: {req.user_id}")
        logger.info(f"Supabase URL: {SUPABASE_URL}")
        logger.info("Attempting to connect to Supabase...")
        
        # Check if user already has an assigned doctor
        try:
            existing = (
                supabase.table("recommended_doctor")
                .select("doctor_id")
                .eq("user_id", req.user_id)
                .execute()
            )
            
            if existing.data:
                doctor_id = existing.data[0]["doctor_id"]
                doctor = (
                    supabase.table("doctors")
                    .select("*")
                    .eq("id", doctor_id)
                    .execute()
                )
                if doctor.data:
                    logger.info(f"Found existing doctor assignment for user {req.user_id}")
                    return {"assigned_doctor": doctor.data[0]}
        except Exception as e:
            logger.error(f"Error checking existing doctor: {str(e)}")
            # Continue to new assignment if checking existing fails
        
        # Get user's dominant mental state
        dominant_state = get_user_dominant_state(req.user_id)
        if not dominant_state:
            logger.warning(f"No mental state found for user {req.user_id}")
            raise HTTPException(
                status_code=404,
                detail="No mental state report found. Please complete your mental state assessment first."
            )
        
        logger.info(f"User {req.user_id} dominant state: {dominant_state}")
        
        # Get matching doctors
        matching_doctors = get_doctors_by_dominant_state(dominant_state)
        if not matching_doctors:
            logger.warning(f"No doctors found for state: {dominant_state}")
            # Fallback to any available doctor if no specific match
            try:
                matching_doctors = supabase.table("doctors").select("*").execute().data
            except Exception as e:
                logger.error(f"Error getting all doctors: {str(e)}")
                matching_doctors = []
                
            if not matching_doctors:
                raise HTTPException(
                    status_code=404,
                    detail="No doctors available in the system"
                )
        
        # Assign best available doctor
        assigned_doctor = assign_best_available_doctor(req.user_id, matching_doctors)
        if not assigned_doctor:
            raise HTTPException(
                status_code=503,
                detail="All doctors are currently assigned. Please try again later."
            )
        
        logger.info(f"Successfully assigned doctor {assigned_doctor['id']} to user {req.user_id}")
        return {"assigned_doctor": assigned_doctor}
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in doctor recommendation: {error_msg}")
        logger.error(f"Type of error: {type(e)}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        
        # Return a more detailed error message
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {error_msg}"
        )
