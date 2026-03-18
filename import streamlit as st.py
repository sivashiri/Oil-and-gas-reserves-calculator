import streamlit as st
import pandas as pd
df = pd.read_excel(r'C:\Users\sivas\Desktop\datasheet.xlsx')
st.title("Preventive Maintenance Dashboard")
st.sidebar.title("Equipments")
equipment_list = df["Equipment"].unique()
selected_equipment = st.sidebar.selectbox("Select Equipment", equipment_list)
# Filter data
filtered_df = df[df["Equipment"] == selected_equipment]
st.header(f"🔧 {selected_equipment} Details")
# Components
st.subheader("Components")
st.write(filtered_df["Component"].unique())
# PM Activities
st.subheader("PM Activities")
st.write(filtered_df[["Component", "PM_Activity", "Last_PM_Date"]])
# Breakdown History
st.subheader("Breakdown History")
st.write(filtered_df[["Component", "Breakdown_Date", "Issue"]])