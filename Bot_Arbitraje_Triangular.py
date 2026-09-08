import streamlit as st
import asyncio
import ccxt.pro as ccxt
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Monitor de Arbitraje Triangular", layout="wide")

st.title("⚡ Monitor de Arbitraje Triangular en Tiempo Real")
st.caption("Conexión WebSocket vía CCXT - Modo Simulación")

COMISION = 0.0025  # 0.25% de Ripio

# Caché de memoria local
if "orderbooks" not in st.session_state:
    st.session_state.orderbooks = {
        'BTC/USDT': None,
        'ETH/BTC': None,
        'ETH/USDT': None
    }

if "historial" not in st.session_state:
    st.session_state.historial = []

# Métrica e interfaz visual
col1, col2, col3 = st.columns(3)
metrica_margen = col1.empty()
metrica_usdt = col2.empty()
estado_status = col3.empty()

tabla_oportunidades = st.empty()

async def escuchar_par(exchange, simbolo):
    while True:
        try:
            orderbook = await exchange.watch_order_book(simbolo)
            st.session_state.orderbooks[simbolo] = orderbook
        except Exception:
            await asyncio.sleep(1)

async def calcular_arbitraje():
    while True:
        cache = st.session_state.orderbooks
        if not all(cache.values()):
            estado_status.warning("Conectando WebSockets...")
            await asyncio.sleep(0.5)
            continue

        try:
            ob_btc_usdt = cache['BTC/USDT']
            ob_eth_btc = cache['ETH/BTC']
            ob_eth_usdt = cache['ETH/USDT']

            ask_btc_usdt = ob_btc_usdt['asks'][0][0] if ob_btc_usdt['asks'] else None
            ask_eth_btc = ob_eth_btc['asks'][0][0] if ob_eth_btc['asks'] else None
            bid_eth_usdt = ob_eth_usdt['bids'][0][0] if ob_eth_usdt['bids'] else None

            if ask_btc_usdt and ask_eth_btc and bid_eth_usdt:
                monto_inicial = 100.0

                btc = (monto_inicial / ask_btc_usdt) * (1 - COMISION)
                eth = (btc / ask_eth_btc) * (1 - COMISION)
                usdt_final = (eth * bid_eth_usdt) * (1 - COMISION)

                profit_pct = ((usdt_final - monto_inicial) / monto_inicial) * 100

                # Actualizar métricas visuales
                metrica_margen.metric("Margen Actual", f"{profit_pct:.3f}%")
                metrica_usdt.metric("Retorno Estimado", f"${usdt_final:.2f} USDT")

                if profit_pct > 0:
                    estado_status.success("🔥 ¡Oportunidad detectada!")
                    registro = {
                        "Fecha_Hora": datetime.now().strftime("%H:%M:%S"),
                        "Margen_%": round(profit_pct, 4),
                        "USDT_Final": round(usdt_final, 2),
                        "BTC/USDT": ask_btc_usdt,
                        "ETH/BTC": ask_eth_btc,
                        "ETH/USDT": bid_eth_usdt
                    }
                    st.session_state.historial.insert(0, registro)
                    
                    # Mostrar tabla con historial de oportunidades
                    df = pd.DataFrame(st.session_state.historial)
                    tabla_oportunidades.dataframe(df, use_container_width=True)
                else:
                    estado_status.info("Escaneando el mercado...")

        except Exception as e:
            pass

        await asyncio.sleep(0.1)

async def main():
    exchange = ccxt.binance({'enableRateLimit': True})
    await asyncio.gather(
        escuchar_par(exchange, 'BTC/USDT'),
        escuchar_par(exchange, 'ETH/BTC'),
        escuchar_par(exchange, 'ETH/USDT'),
        calcular_arbitraje()
    )

if st.button("Iniciar Monitor"):
    asyncio.run(main())
