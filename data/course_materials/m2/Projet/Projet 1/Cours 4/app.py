import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

class AppHandler:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url

    def get_departments(self):
        """Retourne la liste des départements depuis l'API"""
        url = f"{self.base_url}/departments"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def get_births_by_department(self, dep):
        """Retourne toutes les naissances pour un département"""
        url = f"{self.base_url}/births/{dep}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def get_births_by_department_and_period(self, dep, period):
        """Retourne les naissances pour un département et une période donnée"""
        url = f"{self.base_url}/births/{dep}/{period}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()


st.set_page_config(page_title="Naissances par département", layout="wide")
st.title("Évolution des naissances par département")

app_handler = AppHandler()

departments = app_handler.get_departments()
selected_dep = st.selectbox("Sélectionnez un département :", departments)

if selected_dep:
    births_data = app_handler.get_births_by_department(selected_dep)
    df = pd.DataFrame(births_data)
    df["births"] = pd.to_numeric(df["births"], errors="coerce")  
    df["period"] = pd.to_datetime(df["period"], errors="coerce") 
    df = df.sort_values(by="period").reset_index(drop=True)

    st.subheader(f"Naissances pour le département {selected_dep}")
    st.dataframe(df)

    st.bar_chart(df.set_index("period")["births"])

