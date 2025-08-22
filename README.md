# SafeSpace 🛡️

SafeSpace is a Flutter-based mobile application focused on **mental health, counseling, and safe community interactions**.  
The app provides users with a supportive platform to connect with counselors, access resources, and engage in anonymous group discussions.  

---

## ✨ Features

- 🔐 **Authentication** – Secure sign-up and sign-in with Supabase
- 🎧 **Entertainment & Relaxation** – Meditation, music, and interactive exercises  
- 🤖 **AI Chatbot** – Mental health assistant to guide users with suggestions   
- 👨‍⚕️ **Counselor Channeling** – Book appointments and connect via Google Meet (Future devlopment) 
- 📝 **Forum / Blog** – Share thoughts, stories, and mental health tips  (Future devlopment) 
- 💬 **Anonymous Group Chat** – Engage in peer-to-peer conversations safely  (Future devlopment) 


---

## 🛠️ Tech Stack

- **Frontend:** Flutter (Dart)  
- **Backend:** Supabase (Postgres Database, API, Auth, Storage)  
- **Authentication:** Supabase Auth  
- **Database:** Supabase PostgreSQL  
- **Storage:** Supabase Storage  
- **Integrations:** Google Meet API  

---

## 🚀 Getting Started

### Prerequisites
- Install [Flutter](https://docs.flutter.dev/get-started/install) (>=3.27.3)  
- Install [Dart](https://dart.dev/get-dart)  
- Setup [Supabase Project](https://supabase.com/)  
- Configure your **API Keys** and **Environment Variables**  

### Installation
```bash
# Clone the repository
git clone https://github.com/DhanukaRathnayaka/Final_Year_Project.git

# Navigate to project
cd safespace

# Get dependencies
flutter pub get

# Run the app
flutter run
```

## 🤖 Running the Mental Health Chatbot

The chatbot is located inside the `lib/Mental_Health_Chatbot` directory.  
Follow these steps to set it up and run:

```bash
# Navigate to chatbot directory
cd lib
cd Mental_Health_Chatbot      

# Install dependencies
pip install -r requirements.txt

# Run chatbot with Uvicorn (FastAPI server)
python -m uvicorn MentalHealthChatbot:app --host 0.0.0.0 --port 8000 --reload

```
Once running, the chatbot API will be available at:
👉 http://192.168.1.6:8000

Interactive API docs will be available at:
👉 http://192.168.1.6:8000/docs

## 🧑‍💻 Contributors
- **Kavindu Dedunupitiya** – Project Lead and UX UI Designer ( 22UG1-0812 )
- **Dhanuka Rathnayaka** – Fullstack Developer  ( 22UG1-0828 )
- **Gayanga Bandara** – Fullstack Developer  (22UG1-0285)


  