import streamlit as st
from database import SessionLocal, AdherenceLog
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

st.title("📈 Progress")
st.markdown("Track your adherence and progress over time.")

db = SessionLocal()

logs = db.query(AdherenceLog).filter(
    AdherenceLog.user_id == st.session_state.user_id
).order_by(AdherenceLog.date.desc()).all()

if not logs:
    st.info("No adherence logs yet. Start logging in the **Today** page!")
    db.close()
    st.stop()

st.subheader("📊 Overview")

total_days = len(logs)
workouts_completed = sum(1 for log in logs if log.workout_done)
adherence_rate = (workouts_completed / total_days * 100) if total_days > 0 else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Days Logged", total_days)
with col2:
    st.metric("Workouts Completed", workouts_completed)
with col3:
    st.metric("Adherence Rate", f"{adherence_rate:.1f}%")

st.markdown("---")
st.subheader("📅 Recent Logs")

df_logs = pd.DataFrame([
    {
        "Date": log.date,
        "Workout Done": "✅" if log.workout_done else "❌",
        "RPE": log.rpe or "N/A",
        "Soreness": log.soreness or "N/A",
        "Meals Done": log.meals_done,
        "Notes": log.notes or ""
    }
    for log in logs[:30]
])

st.dataframe(df_logs, use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("📈 Trends")

if len(logs) >= 2:
    df_chart = pd.DataFrame([
        {
            "Date": log.date,
            "RPE": log.rpe if log.rpe else None,
            "Soreness": log.soreness if log.soreness else None,
            "Workout Done": 1 if log.workout_done else 0
        }
        for log in reversed(logs)
    ])
    
    tab1, tab2, tab3 = st.tabs(["RPE Trend", "Soreness Trend", "Workout Adherence"])
    
    with tab1:
        if df_chart["RPE"].notna().any():
            fig_rpe = px.line(
                df_chart.dropna(subset=["RPE"]),
                x="Date",
                y="RPE",
                title="RPE Over Time",
                markers=True
            )
            fig_rpe.update_layout(yaxis_range=[0, 10])
            st.plotly_chart(fig_rpe, use_container_width=True)
        else:
            st.info("Not enough RPE data to display trend.")
    
    with tab2:
        if df_chart["Soreness"].notna().any():
            fig_soreness = px.line(
                df_chart.dropna(subset=["Soreness"]),
                x="Date",
                y="Soreness",
                title="Soreness Over Time",
                markers=True
            )
            fig_soreness.update_layout(yaxis_range=[0, 10])
            st.plotly_chart(fig_soreness, use_container_width=True)
        else:
            st.info("Not enough soreness data to display trend.")
    
    with tab3:
        fig_adherence = px.bar(
            df_chart,
            x="Date",
            y="Workout Done",
            title="Workout Completion",
            labels={"Workout Done": "Completed (1=Yes, 0=No)"}
        )
        fig_adherence.update_layout(yaxis_range=[0, 1.2])
        st.plotly_chart(fig_adherence, use_container_width=True)
        
        last_7_days = df_chart.tail(7)
        last_7_adherence = (last_7_days["Workout Done"].sum() / len(last_7_days) * 100) if len(last_7_days) > 0 else 0
        st.metric("Last 7 Days Adherence", f"{last_7_adherence:.1f}%")

else:
    st.info("Log at least 2 days to see trends.")

st.markdown("---")
st.subheader("💡 Insights")

recent_logs = logs[:7]
avg_rpe = sum(log.rpe for log in recent_logs if log.rpe) / len([log for log in recent_logs if log.rpe]) if any(log.rpe for log in recent_logs) else None
avg_soreness = sum(log.soreness for log in recent_logs if log.soreness) / len([log for log in recent_logs if log.soreness]) if any(log.soreness for log in recent_logs) else None

if avg_rpe and avg_rpe > 8:
    st.warning("⚠️ Your average RPE is high. Consider scheduling more recovery days.")

if avg_soreness and avg_soreness > 7:
    st.warning("⚠️ High soreness detected. Focus on recovery, hydration, and mobility work.")

if adherence_rate < 50:
    st.info("💪 Consistency is key! Try setting reminders or adjusting your schedule for better adherence.")
elif adherence_rate >= 80:
    st.success("🎉 Amazing adherence! Keep up the great work!")

db.close()
