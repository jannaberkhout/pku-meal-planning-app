import streamlit as st
import pandas as pd
from io import BytesIO

st.title("PKU meal planning app")

# Initialiseer session state voor dagplanning
if "dagplanning" not in st.session_state:
    st.session_state["dagplanning"] = []


# Upload bestand
bron = st.radio("Kies gegevensbron:", ["Upload bestand", "Gebruik voorbeeldbestand"])

if bron == "Upload bestand":
    uploaded_file = st.file_uploader("Upload je bestand (CSV of Excel)", type=["csv", "xlsx"])
    if uploaded_file:
    # Lees bestand
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, sep=';')
        else:
            df = pd.read_excel(uploaded_file)
else:
    df = pd.read_csv("data/product_list.csv", sep=';') 


# ✅ Alleen verder als df bestaat
if 'df' in locals():

# Conversie naar float
    for col in ["Eiwit (g) per 100 gram", "Energie (kcal) per 100 gram"]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", ".")
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors="raise").fillna(0)

    # Waarschuwing bij veel nullen (hier: waarden die 0 zijn)
    null_ratio_eiwit = (df["Eiwit (g) per 100 gram"] == 0).mean()
    null_ratio_energie = (df["Energie (kcal) per 100 gram"] == 0).mean()

    if null_ratio_eiwit > 0.2 or null_ratio_energie > 0.2:
        st.warning(f"⚠️ Let op: Meer dan 20% van de waarden in eiwit of energie zijn 0. Controleer je bestand!")

    st.write("📊 Gegevens ingeladen:")
    st.dataframe(df)



    # Filter op Productgroep en Maaltijd type
    maaltijd_type = st.selectbox("Kies maaltijd:", ["Ontbijt", "Tussendoor", "Lunch", "Snack", "Avondeten"])
    productgroepen = df["Productgroep"].unique()
    gekozen_groep = st.selectbox("Kies een productgroep:", productgroepen)

    # Filter producten binnen gekozen groep
    gefilterde_df = df[df["Productgroep"] == gekozen_groep]
    product = st.selectbox("Kies een product:", gefilterde_df["Naam"].unique())

    # Invoer hoeveelheid
    hoeveelheid = st.number_input("Voer hoeveelheid in (gram):", min_value=1.0, step=1.0)
    
    # Instelbare drempel
    drempel_eiwit = st.slider("Stel eiwit-drempel in (gram):", min_value=1.0, max_value=20.0, value=5.0, step=0.1)
 

    # Haal waarden op
    eiwit_per_100g = gefilterde_df.loc[gefilterde_df["Naam"] == product, "Eiwit (g) per 100 gram"].values[0]
    energie_per_100g = gefilterde_df.loc[gefilterde_df["Naam"] == product, "Energie (kcal) per 100 gram"].values[0]

    # Converteer Hoeveelheid gram/ml naar integer
    hoeveelheid_str = gefilterde_df.loc[gefilterde_df["Naam"] == product, "Hoeveelheid gram/ml"].values[0]
    hoeveelheid_per_vse = int(''.join(filter(str.isdigit, hoeveelheid_str))) if hoeveelheid_str else 0

    # Berekeningen
    totaal_eiwit = (eiwit_per_100g * hoeveelheid) / 100
    totaal_energie = (energie_per_100g * hoeveelheid) / 100
    aantal_vse = hoeveelheid / hoeveelheid_per_vse if hoeveelheid_per_vse > 0 else 0
    
    # Output
    st.subheader(f"✅ Resultaten voor {product}:")
    st.write(f"- **Totaal eiwit:** {totaal_eiwit:.2f} g")
    st.write(f"- **Totaal energie:** {totaal_energie:.2f} kcal")
    st.write(f"- **Aantal VSE:** {aantal_vse:.2f} (1 VSE = {hoeveelheid_per_vse} gram)")


    if st.button("➕ Voeg toe aan dagplanning"):
        st.session_state["dagplanning"].append({
            "Maaltijd": maaltijd_type,
            "Product": product,
            "Hoeveelheid (g)": hoeveelheid,
            "Eiwit (g)": round(totaal_eiwit, 2),
            "Energie (kcal)": round(totaal_energie, 2),
            "Aantal VSE": round(aantal_vse, 2)
        })

# Toon dagplanning
if st.session_state["dagplanning"]:
    st.subheader("📅 Dagplanning")
    dag_df = pd.DataFrame(st.session_state["dagplanning"])
    st.table(dag_df)


    # Resetknop
    if st.button("🔄 Reset dagplanning"):
        st.session_state["dagplanning"] = []
        st.rerun()


    # Bereken totaal
    totaal_eiwit_dag = dag_df["Eiwit (g)"].sum()
    totaal_energie_dag = dag_df["Energie (kcal)"].sum()

    st.write(f"**Totaal eiwit vandaag:** {totaal_eiwit_dag:.2f} g")
    st.write(f"**Totaal energie vandaag:** {totaal_energie_dag:.2f} kcal")


    # Hoeveel eiwit nog over
    eiwit_over = max(drempel_eiwit - totaal_eiwit_dag, 0)
    st.write(f"**Nog beschikbaar tot limiet:** {eiwit_over:.2f} g eiwit")

    # ✅ Voortgangsbalk
    progress = min(totaal_eiwit_dag / drempel_eiwit, 1.0)  # max 100%
    st.progress(progress)


    # Waarschuwing bij overschrijding drempel
    if totaal_eiwit_dag > drempel_eiwit:
        st.error(f"🚨 Waarschuwing: Het totaal eiwit ({totaal_eiwit_dag:.2f} g) is hoger dan de ingestelde drempel van {drempel_eiwit} g!")


    # ✅ Exportknop naar Excel met openpyxl
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dag_df.to_excel(writer, index=False, sheet_name="Dagplanning")
    st.download_button(
        label="📥 Download dagplanning als Excel",
        data=buffer.getvalue(),
        file_name="dagplanning.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


    # Toon tabel met verwijderknoppen
    for i, item in enumerate(st.session_state["dagplanning"]):
        st.write(f"{i+1}. {item['Maaltijd']} - {item['Product']} ({item['Hoeveelheid (g)']} g) | "
                 f"Eiwit: {item['Eiwit (g)']} g | Energie: {item['Energie (kcal)']} kcal | VSE: {item['Aantal VSE']}")
        if st.button(f"❌ Verwijder item {i+1}", key=f"remove_{i}"):
            st.session_state["dagplanning"].pop(i)
            st.rerun()  # herlaad de app om lijst te upd


