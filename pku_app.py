from helper import prepare_df, solve_plan_pulp
import streamlit as st
import pandas as pd
from io import BytesIO

st.title("PKU meal planning app")

# Initialiseer session state voor dagplanning
if "dagplanning" not in st.session_state:
    st.session_state["dagplanning"] = []


# Upload bestand
bron = st.radio("Kies gegevensbron:", ["Gebruik voorbeeldbestand", "Upload bestand"])

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
    df = prepare_df(df)

    # Waarschuwing bij veel nullen (hier: waarden die 0 zijn)
    null_ratio_eiwit = (df["protein_100g"] == 0).mean()
    null_ratio_energie = (df["kcal_100g"] == 0).mean()

    if null_ratio_eiwit > 0.2 or null_ratio_energie > 0.2:
        st.warning(f"⚠️ Let op: Meer dan 20% van de waarden in eiwit of energie zijn 0. Controleer je bestand!")

    st.write("📊 Gegevens ingeladen:")
    st.dataframe(df)

    methode = st.radio("Kies methode:", ["Maak een eigen dagplanning", "Doe een voorstel"])
    
    if methode == "Doe een voorstel":
        
        st.markdown("### 💡 Plan-voorstel")

        df_solver = df

        drempel_eiwit = st.slider("Stel eiwit-drempel in (gram):", min_value=1.0, max_value=50.0, value=10.0, step=0.1)
        min_serv_vse   = st.number_input("Minimale portiegrootte (VSE)", value=0.5, min_value=0.1, step=0.1)
        max_serv_vse   = st.number_input("Maximale portiegrootte (VSE)", value=2.0, min_value=min_serv_vse, step=0.1)
        uniek_product  = st.checkbox("Voorkom hetzelfde product in meerdere maaltijden", value=True)

        if st.button("🔎 Maak voorstel"):
            try:
                plan_df, totals = solve_plan_pulp(
                    df_solver,
                    protein_limit= drempel_eiwit,
                    min_serv=min_serv_vse,
                    max_serv=max_serv_vse,
                    unique_product=uniek_product
                )
            except ModuleNotFoundError:
                st.error("PuLP is niet geïnstalleerd. Installeer met `pip install pulp`.")
                plan_df, totals = None, None

            if plan_df is None:
                st.warning(f"Geen optimaal plan (status: {totals.get('status','n/a')}). "
                        "Verhoog de daglimiet of verlaag min. VSE")
            else:
                st.subheader("✨ Voorgestelde dagindeling (meerdere producten)")
                st.dataframe(plan_df, use_container_width=True)
                st.write(totals)

    if methode == "Maak een eigen dagplanning":
    
        st.markdown("### Maak een eigen dagplanning")

        #Filter op maaltijd type
        maaltijd_type = st.selectbox("Kies maaltijd:", ["Ontbijt", "Tussendoor", "Lunch", "Snack", "Avondeten"])

        # multi-select op kleur

        # --- Kleurhulpjes ---
        kleur_emojis = {"groen": "🟢", "oranje": "🟠", "rood": "🔴"}

        # Normaliseer eventueel spaties/hoofdletters
        alle_kleuren = ["groen", "oranje", "rood"]
        default=alle_kleuren  # start met alles aan
        format_func=lambda k: f"{kleur_emojis.get(k,'')} {k.capitalize()}"
        gekozen_kleuren = st.multiselect(
            "Filter op kleurgroep:",alle_kleuren, default, format_func=format_func)


        # --- Extra filters:  Productgroep + Kleurgroep ---
        productgroepen = sorted(df["productgroep"].dropna().unique())
        gekozen_groep = st.selectbox("Kies een productgroep:", productgroepen)

        # Filter op groep én kleur
        mask = (df["productgroep"] == gekozen_groep) & (df["kleurgroep"].isin(gekozen_kleuren))
        gefilterde_df = df.loc[mask].copy()

        if gefilterde_df.empty:
            st.info("Geen producten voor deze combinatie van filters.")
            st.stop()

        product = st.selectbox("Kies een product:", gefilterde_df["naam"].unique(), format_func= format_func)
        product_kleur = df.loc[df["naam"] == product]["kleurgroep"].values[0]

        # Invoer hoeveelheid

        # Converteer Hoeveelheid gram/ml naar integer
        hoeveelheid_str = gefilterde_df.loc[gefilterde_df["naam"] == product, "hoeveelheid"].values[0]
        hoeveelheid_per_vse = int(''.join(filter(str.isdigit, hoeveelheid_str))) if hoeveelheid_str else 0

        hoeveelheid = st.number_input("Voer hoeveelheid in (gram):", min_value=1, step=1, value=hoeveelheid_per_vse)
        
        # Instelbare drempel
        drempel_eiwit = st.slider("Stel eiwit-drempel in (gram):", min_value=1.0, max_value=50.0, value=10.0, step=0.1)
    
        # Haal waarden op
        eiwit_per_100g = gefilterde_df.loc[gefilterde_df["naam"] == product, "protein_100g"].values[0]
        energie_per_100g = gefilterde_df.loc[gefilterde_df["naam"] == product, "kcal_100g"].values[0]

        # Berekeningen
        totaal_eiwit = (eiwit_per_100g * hoeveelheid) / 100
        totaal_energie = (energie_per_100g * hoeveelheid) / 100
        aantal_vse = hoeveelheid / hoeveelheid_per_vse if hoeveelheid_per_vse > 0 else 0
        
        # Output
        st.subheader(f"✅ Resultaten voor {product}:")
        st.write(f"- **Totaal eiwit:** {totaal_eiwit:.2f} g")
        st.write(f"- **Totaal energie:** {totaal_energie:.2f} kcal")
        st.write(f"- **Aantal VSE:** {aantal_vse:.2f} (1 VSE = {hoeveelheid_per_vse} gram)")
        st.write(f"- **Kleurgroep:** {kleur_emojis.get(product_kleur,'')} {product_kleur.capitalize()}")

        if st.button("➕ Voeg toe aan dagplanning"):
            st.session_state["dagplanning"].append({
                "Maaltijd": maaltijd_type,
                "Product": product,
                "Hoeveelheid (g)": hoeveelheid,
                "Eiwit (g)": round(totaal_eiwit, 2),
                "Energie (kcal)": round(totaal_energie, 2),
                "Aantal VSE": round(aantal_vse, 2),
                "Kleurgroep": f"{product_kleur}"
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
                        f"Eiwit: {item['Eiwit (g)']} g | Energie: {item['Energie (kcal)']} kcal | VSE: {item['Aantal VSE']} {kleur_emojis.get(item["Kleurgroep"],'')}")
                if st.button(f"❌ Verwijder item {i+1}", key=f"remove_{i}"):
                    st.session_state["dagplanning"].pop(i)
                    st.rerun()  # herlaad de app om lijst te updaten



 