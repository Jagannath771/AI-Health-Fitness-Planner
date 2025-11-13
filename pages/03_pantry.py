import streamlit as st
from database import SessionLocal, Pantry
from datetime import date, timedelta
from adaptive_logic import auto_replan_after_pantry_update
from openai_service import analyze_grocery_receipt
import json

st.title("🥗 Pantry")
st.markdown("Track your groceries and shopping schedule for pantry-driven meal planning. Upload your grocery receipt to automatically add items!")

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
st.subheader("Upload Receipt")
st.info("📸 Note: The receipt scanning feature provides a quick start by detecting items, but may not be 100% accurate. Please review and adjust the detected items as needed!")
uploaded_file = st.file_uploader("Upload a photo of your grocery receipt to automatically add items", type=['png', 'jpg', 'jpeg'])

if uploaded_file is not None:
    # Display the uploaded image
    st.image(uploaded_file, caption="Uploaded Receipt", use_column_width=True)
    
    # Analyze the image when user clicks the button
    if st.button("🔍 Scan Receipt"):
        with st.spinner("Analyzing receipt..."):
            try:
                # Read the file
                bytes_data = uploaded_file.getvalue()
                # Analyze the receipt
                detected_items = analyze_grocery_receipt(bytes_data)
                
                if detected_items:
                    st.success(f"✅ Detected {len(detected_items)} items from receipt!")
                    for item in detected_items:
                        # Check if item already exists
                        exists = any(existing['name'].lower() == item['name'].lower() 
                                   for existing in st.session_state.pantry_items)
                        if not exists:
                            st.session_state.pantry_items.append(item)
                    st.rerun()
                else:
                    st.warning("No items detected in the receipt. Try uploading a clearer photo or add items manually.")
            except Exception as e:
                st.error(f"Error analyzing receipt: {str(e)}")

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
    if st.button("➕ Add Item", width="stretch"):
        # Use selected_common if it's not empty, otherwise use the custom input
        final_item_name = selected_common if selected_common else item_name
        if final_item_name.strip() and qty_unit.strip():
            new_item = {"name": final_item_name.strip(), "qty_unit": qty_unit.strip()}
            st.session_state.pantry_items.append(new_item)
            st.rerun()
        else:
            st.error("Please enter both item name and quantity/unit")

st.markdown("---")

col1, col2, col3 = st.columns([2, 1, 2])

with col1:
    if st.button("💾 Save Pantry", type="primary", width="stretch"):
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
        st.session_state.pantry_saved = True
        st.success("✅ Pantry saved successfully!")

# Continue button in the middle column
with col2:
    if st.button("Continue to Schedule →", type="primary", width="stretch", key="continue_schedule"):
        st.switch_page("pages/04_schedule.py")

# Restock button in the right column
with col3:
    if st.button("🔄 Mid-Week Restock & Replan", width="stretch"):
        if st.session_state.pantry_items:
            items_json = {"items": st.session_state.pantry_items}
            
            if existing:
                existing.items_json = items_json
                existing.last_shopping_date = date.today()
            else:
                new_pantry = Pantry(
                    user_id=st.session_state.user_id,
                    items_json=items_json,
                    last_shopping_date=date.today(),
                    next_shopping_date=next_shopping
                )
                db.add(new_pantry)
            
            db.commit()
            st.success("✅ Pantry updated!")
            
            with st.spinner("🔄 Replanning meals for remaining days..."):
                adapted, message = auto_replan_after_pantry_update(st.session_state.user_id)
                if adapted and "days_patch" in adapted:
                    st.success(f"✅ {message}")
                    st.info(f"🍽️ Meal plan updated: {adapted.get('reason', 'Using updated pantry items')}")
                elif adapted and "status" in adapted:
                    st.warning(f"⚠️ {adapted.get('message', message)}")
                else:
                    st.info(f"ℹ️ {message}")
        else:
            st.warning("⚠️ Add pantry items first!")

# Add navigation section with proper spacing
st.write("")  # Add some space
st.markdown("""
<div style='background: rgba(255,255,255,0.05); padding: 1.5rem; border-radius: 10px; text-align: center; margin: 1rem 0;'>
    <h3 style='margin-bottom: 1rem;'>🎯 Next Step: Schedule Setup</h3>
    <p style='color: #b8c0cc; margin-bottom: 1rem;'>Set your meal and workout schedule</p>
</div>
""", unsafe_allow_html=True)

db.close()
