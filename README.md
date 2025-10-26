# FitLife Planner 💪

A comprehensive fitness and lifestyle management application built with Streamlit that helps users plan their workouts, track nutrition, and monitor progress.

## 🌟 Features

- **User Authentication**: Secure login system to protect user data
- **Personalized Onboarding**: Customized fitness journey setup
- **Equipment Management**: Track available workout equipment
- **Pantry Management**: Monitor food inventory and nutritional info
- **Schedule Planning**: Organize workout routines
- **Weekly Planning**: Set and track weekly fitness goals
- **Daily Overview**: Track daily progress and tasks
- **Progress Tracking**: Monitor fitness achievements
- **Settings Management**: Customize app preferences

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Custom secure authentication system
- **Data Visualization**: Plotly
- **AI Integration**: Google Generative AI for adaptive planning

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL database
- Environment variables properly configured

## 🚀 Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd FitnessLife
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```env
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key
GOOGLE_API_KEY=your_google_api_key
```

4. Initialize the database:
```bash
python -c "from database import init_db; init_db()"
```

## 🏃‍♂️ Running the Application

1. Start the Streamlit server:
```bash
streamlit run app.py
```

2. Open your browser and navigate to `http://localhost:8501`

## 📁 Project Structure

```
FitnessLife/
├── app.py                 # Main application entry point
├── database.py           # Database configuration and models
├── adaptive_logic.py     # AI-powered adaptive planning
├── openai_service.py     # AI service integration
├── pages/               # Streamlit pages
│   ├── 00_login.py     # Authentication
│   ├── 01_onboarding.py # User onboarding
│   ├── 02_equipment.py  # Equipment management
│   ├── 03_pantry.py    # Food inventory
│   ├── 04_schedule.py  # Schedule planning
│   ├── 05_weekly_plan.py # Weekly planning
│   ├── 06_today.py     # Daily overview
│   ├── 07_progress.py  # Progress tracking
│   └── 08_settings.py  # User settings
└── requirements.txt     # Project dependencies
```

## 🔒 Security

- Environment variables for sensitive information
- Database Row Level Security (RLS)
- Secure authentication system
- Protected API endpoints

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Contact

For any questions or feedback, please reach out to the project maintainers.

---
Built with ❤️ for fitness enthusiasts