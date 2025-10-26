import streamlit as st
from database import SessionLocal, Pantry
from datetime import date, timedelta
import json

st.title("🥗 Pantry")
st.markdown("Track your groceries and shopping schedule for pantry-driven meal planning.")

db = SessionLocal()

existing = db.query(Pantry).filter(
    Pantry.user_id == st.session_state.user_id
).first()

if "pantry_items" not in st.session_state:
    if existing:
        st.session_state.pantry_items = existing.items_json.get("items", [])
        st.session_state.last_shopping = existing.last_shopping_date
        st.session_state.next_shopping = existing.next_shopping_date
    else:
        st.session_state.pantry_items = []
        st.session_state.last_shopping = None
        st.session_state.next_shopping = None

st.subheader("Shopping Schedule")
col1, col2 = st.columns(2)
with col1:
    last_shopping = st.date_input(
        "Last Shopping Date",
        value=st.session_state.last_shopping or date.today()
    )
    st.session_state.last_shopping = last_shopping

with col2:
    next_shopping = st.date_input(
        "Next Shopping Date",
        value=st.session_state.next_shopping or (date.today() + timedelta(days=7))
    )
    st.session_state.next_shopping = next_shopping

days_until_shopping = (next_shopping - date.today()).days
if days_until_shopping < 0:
    st.warning(f"⚠️ Your next shopping date has passed! Update it to get accurate meal plans.")
elif days_until_shopping == 0:
    st.info(f"🛒 Shopping day is today!")
else:
    st.info(f"📅 {days_until_shopping} days until next shopping trip")

st.markdown("---")
st.subheader("Current Pantry Items")

if st.session_state.pantry_items:
    for idx, item in enumerate(st.session_state.pantry_items):
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.text(f"• {item['name']}")
        with col2:
            st.caption(f"Qty: {item['qty_unit']}")
        with col3:
            if st.button("🗑️", key=f"delete_{idx}"):
                st.session_state.pantry_items.pop(idx)
                st.rerun()
else:
    st.info("No pantry items added yet. Add your first item below!")

st.markdown("---")
st.subheader("Add Pantry Item")

common_items = [
    "Rice", "Pasta", "Bread", "Eggs", "Milk", "Chicken Breast", "Ground Beef",
    "Salmon", "Tofu", "Beans (canned)", "Lentils", "Oats", "Quinoa",
    "Olive Oil", "Butter", "Yogurt", "Cheese", "Tomatoes", "Onions",
    "Garlic", "Potatoes", "Sweet Potatoes", "Broccoli", "Spinach", "Carrots",
    "Bell Peppers", "Bananas", "Apples", "Berries", "Nuts", "Peanut Butter",
    "Honey", "Salt", "Pepper", "Spices"
]

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    selected_common = st.selectbox(
        "Select common item",
        [""] + sorted(common_items),
        key="common_select"
    )
    item_name = st.text_input("Or enter custom item", key="custom_name", value=selected_common)

with col2:
    qty_unit = st.text_input("Quantity/Unit (e.g., 500g, 1L, 12 eggs)", key="qty_input", value="1 unit")

with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Add Item", use_container_width=True):
        if item_name and qty_unit:
            new_item = {"name": item_name, "qty_unit": qty_unit}
            st.session_state.pantry_items.append(new_item)
            st.rerun()

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    if st.button("💾 Save Pantry", type="primary", use_container_width=True):
        items_json = {"items": st.session_state.pantry_items}
        
        if existing:
            existing.items_json = items_json
            existing.last_shopping_date = last_shopping
            existing.next_shopping_date = next_shopping
        else:
            new_pantry = Pantry(
                user_id=st.session_state.user_id,
                items_json=items_json,
                last_shopping_date=last_shopping,
                next_shopping_date=next_shopping
            )
            db.add(new_pantry)
        
        db.commit()
        st.success("✅ Pantry saved successfully!")
        st.info("👉 Next: Set your schedule in the **Schedule** page")

with col2:
    if st.button("🔄 Mid-Week Restock", use_container_width=True):
        st.session_state.last_shopping = date.today()
        st.info("🛒 Mark your new items above and save. The meal plan will adapt for remaining days!")

db.close()
