import streamlit as st
from supabase import create_client, Client
import pandas as pd
import time

st.set_page_config(page_title="Dashboard Arbitraje", layout="wide")

st.title("📊 Dashboard de Oportunidades en Tiempo Real")
st.caption("Conectado a la base de datos Supabase")

# Configuración de llaves de Supabase
SUPABASE_URL = "https://dmzseqotfotbycygwhzj.supabase.co"
SUPABASE_KEY = "sb_publishable_jxL6lYpaAC6Vl7Lrk4yfIA_yxq4Fjia" # Pegá acá tu clave de la foto anterior

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

col1, col2 = st.columns(2)
m_total = col1.empty()
m_max = col2.empty()

tabla_placeholder = st.empty()

st.sidebar.header("Estado")
st.sidebar.success("Conectado a Supabase")

while True:
    try:
        # Consulta los últimos 20 registros
        response = supabase.table("oportunidades").select("*").order("created_at", desc=True).limit(20).execute()
        datos = response.data

        if datos:
            df = pd.DataFrame(datos)
            
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%H:%M:%S')
            df_display = df[['created_at', 'margen_pct', 'usdt_final', 'btc_usdt', 'eth_btc', 'eth_usdt']]
            df_display.columns = ['Hora', 'Margen %', 'USDT Final', 'BTC/USDT', 'ETH/BTC', 'ETH/USDT']

            m_total.metric("Oportunidades Registradas", len(df))
            m_max.metric("Mejor Margen", f"{df['Margen %'].max():.3f}%")

            tabla_placeholder.dataframe(df_display, use_container_width=True)
        else:
            st.info("Esperando que el bot backend envíe oportunidades desde tu PC...")

    except Exception as e:
        st.error(f"Error al leer Supabase: {e}")

    time.sleep(3)
