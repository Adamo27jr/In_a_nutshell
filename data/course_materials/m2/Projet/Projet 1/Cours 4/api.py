from fastapi import FastAPI, HTTPException
from typing import List, Dict
import requests
import pandas as pd
import os
import csv

app = FastAPI(title="INSEE Births API")

class ApiHandler:
    def __init__(self):
        self.url = "https://api.insee.fr/melodi/data/DS_EC_NAIS"
        self.headers = {
            "Authorization": "Bearer VOTRE_CLE_API_ICI"  
        }
        self.params = {
            "FREQ": "M",
            "EC_MEASURE": "LVB",
            "GEO": "DEP"
        }

    def get_data_from_api_insee(self):
        """Récupère les données JSON depuis l'API INSEE"""
        response = requests.get(self.url, headers=self.headers, params=self.params)
        response.raise_for_status()
        return response.json()

    def create_df_from_api_insee(self, data=None):
        """Crée un DataFrame pandas à partir des données de l'API"""
        if data is None:
            data = self.get_data_from_api_insee()

        observations = data["observations"]
        df = pd.DataFrame({
            "departement": [obs["dimensions"]["GEO"].split("DEP-")[1] for obs in observations],
            "period": [obs["dimensions"]["TIME_PERIOD"] for obs in observations],
            "births": [obs["measures"]["OBS_VALUE_NIVEAU"]["value"] for obs in observations]
        })
        df["period"] = pd.to_datetime(df["period"], format="%Y-%m")  
        df = df.sort_values(by=["departement", "period"]).reset_index(drop=True)
        return df

    def get_departments(self, df=None):
        """Retourne la liste des départements"""
        if df is None:
            df = self.create_df_from_api_insee()
        return df["departement"].unique().tolist()

    def get_births_by_department(self, dep, df=None):
        """Retourne les naissances pour un département"""
        if df is None:
            df = self.create_df_from_api_insee()
        df_dep = df[df["departement"] == dep]
        result = df_dep.to_dict(orient="records")
        return result

    def get_births_by_department_and_month(self, dep, month, df=None):
        """Retourne les naissances pour un département et un mois donné"""
        if df is None:
            df = self.create_df_from_api_insee()
        df_filtered = df[(df["departement"] == dep) & (df["period"] == month)]
        if df_filtered.empty:
            raise HTTPException(status_code=404, detail="Données non trouvées")
        return df_filtered.iloc[0].to_dict()


api_handler = ApiHandler()


@app.get("/hello/{name}")
def hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/departments", response_model=List[str])
def departments():
    return api_handler.get_departments()


@app.get("/births/{dep}", response_model=List[Dict])
def births_by_department(dep: str):
    return api_handler.get_births_by_department(dep)


@app.get("/births/{dep}/{month}", response_model=Dict)
def births_by_department_and_month(dep: str, month: str):
    return api_handler.get_births_by_department_and_month(dep, month)


@app.post("/insert/{dep}")
def insert_department(dep: str):
    file_path = "data/departments.csv"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    rows = []
    if os.path.exists(file_path):
        with open(file_path, mode="r", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if any(row["department"] == dep for row in rows):
                return {"message": "Le département existe déjà"}

    rows.append({"department": dep, "checked": "0"})
    with open(file_path, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["department", "checked"])
        writer.writeheader()
        writer.writerows(rows)

    return {"message": f"Département {dep} inséré avec checked=0"}


@app.post("/update/{dep}")
def update_department(dep: str):
    file_path = "data/departments.csv"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=500, detail="Fichier CSV non trouvé")

    updated = False
    rows = []
    with open(file_path, mode="r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["department"] == dep:
                row["checked"] = "1"
                updated = True
            rows.append(row)

    if not updated:
        raise HTTPException(status_code=500, detail=f"Département {dep} non trouvé dans le fichier CSV")

    with open(file_path, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["department", "checked"])
        writer.writeheader()
        writer.writerows(rows)

    return {"message": f"Département {dep} mis à jour avec checked=1"}
