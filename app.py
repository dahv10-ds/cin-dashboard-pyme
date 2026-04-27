import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from src.calculations import load_and_preprocess, get_pulse_metrics, prepare_advanced_table, prepare_chart_trend

st.set_page_config(page_title="Control Estratégico Integral", layout="wide", initial_sidebar_state="collapsed")

# CSS Avanzado UI/UX
st.markdown("""
    <style>
    .stApp { background-color: #0b1120; }
    h1, h2, h3, p { text-align: center !important; color: #f8fafc !important; }
    div[data-testid="metric-container"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 15px 10px;
    }
    div[data-testid="stMetricValue"] { text-align: center !important; font-size: 1.8rem !important; color: #ffffff !important; }
    div[data-testid="stMetricLabel"] { text-align: center !important; font-size: 1rem !important; color: #94a3b8 !important; }
    button[data-baseweb="tab"] { font-size: 1.1rem !important; padding: 0.8rem 1.5rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- FUNCIÓN DEL TACÓMETRO MEJORADA (Línea delgada y colores vivos) ---
def create_gauge_chart(value, title, is_percent_growth=False):
    display_value = value * 100
    reference_val = 0 if is_percent_growth else 100
    
    # Ajustamos el rango del eje para que sea más proporcionado
    min_range = -30 if is_percent_growth else 0
    max_range = max(50, display_value + 10) if is_percent_growth else max(120, display_value + 10)
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = display_value,
        domain = {'x': [0, 1], 'y': [0, 0.75]},
        delta = {'reference': reference_val, 'position': "top", 'suffix': "%", 'font': {'size': 16}},
        number = {'suffix': "%", 'font': {'size': 22, 'color': '#ffffff'}},
        gauge = {
            'axis': {'range': [min_range, max_range], 'tickcolor': "#334155"},
            # Aquí hacemos la línea azul delgada (15% del grosor total)
            'bar': {'color': "#3b82f6", 'thickness': 0.15},
            'bgcolor': "rgba(0,0,0,0)",
            'steps': [
                # Subimos la opacidad a 0.7 para que los colores sean vivos y premium
                {'range': [min_range, 0 if is_percent_growth else 80], 'color': "rgba(239, 68, 68, 0.7)"},   # Rojo
                {'range': [0 if is_percent_growth else 80, 10 if is_percent_growth else 100], 'color': "rgba(245, 158, 11, 0.7)"}, # Amarillo
                {'range': [10 if is_percent_growth else 100, max_range], 'color': "rgba(16, 185, 129, 0.7)"} # Verde
            ],
            'threshold': {'line': {'color': "white", 'width': 2}, 'value': reference_val}
        }
    ))
    
    fig.update_layout(
        title = {'text': title, 'y': 0.9, 'x': 0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 14, 'color': '#94a3b8'}},
        paper_bgcolor="rgba(0,0,0,0)",
        height=200,
        margin=dict(l=15, r=15, t=50, b=10)
    )
    return fig

@st.cache_data
def get_data():
    return load_and_preprocess(os.path.join("data", "raw", "datos_retail_pyme.xlsx"))

df_base = get_data()

st.title("Control Integral de Negocios (CIN)")
st.markdown("<p style='color: #64748b; font-size: 1.1rem; margin-top:-15px;'>Consultoría DaaS - Dashboard Estratégico</p><br>", unsafe_allow_html=True)

col_sel1, col_sel2 = st.columns(2)
with col_sel1:
    ultima_fecha = df_base['Fecha'].max()
    fecha_analisis = pd.to_datetime(st.date_input("🗓️ Fecha de análisis:", ultima_fecha))
with col_sel2:
    perspectiva = st.selectbox("🏬 Perspectiva:", ["General del Negocio"] + sorted(list(df_base['Categoria'].unique())))

df_working = df_base if perspectiva == "General del Negocio" else df_base[df_base['Categoria'] == perspectiva]
metrics = get_pulse_metrics(df_working, fecha_analisis)

if metrics:
    tab1, tab2, tab3 = st.tabs(["🎛️ Centro de Mando", "📈 Análisis Visual", "📋 Auditoría"])

    with tab1:
        # BLOQUE 1: CUMPLIMIENTO
        st.subheader("Cumplimiento del Presupuesto (MTD)")
        c1, c2, c3 = st.columns([1, 1, 1.2])
        c1.metric("Venta Acumulada", f"${metrics['ingreso_mtd']:,.0f}")
        c2.metric("Ppto. a la Fecha", f"${metrics['ppto_mtd']:,.0f}")
        with c3:
            st.plotly_chart(create_gauge_chart(metrics['cumplimiento_mtd'], "Cumplimiento Meta"), use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")
        
        # BLOQUE 2: CRECIMIENTO YoY (Nueva sección solicitada)
        st.subheader("Crecimiento vs Año Anterior (YoY)")
        st.markdown("<p style='color: #94a3b8; font-size: 0.85rem; margin-top:-15px;'>Comparativa acumulada contra los mismos días del año pasado</p>", unsafe_allow_html=True)
        g1, g2, g3 = st.columns([1, 1, 1.2])
        g1.metric("Venta Actual", f"${metrics['ingreso_mtd']:,.0f}")
        g2.metric("Venta Año Pasado", f"${metrics['ingreso_yoy_mtd']:,.0f}")
        with g3:
            # Usamos lógica de crecimiento (referencia 0%)
            st.plotly_chart(create_gauge_chart(metrics['crecimiento_mtd'], "Crecimiento Real", is_percent_growth=True), use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")
        
        # BLOQUE 3: PROYECCIÓN
        st.subheader("Proyección a Cierre de Mes")
        p1, p2, p3 = st.columns([1, 1, 1.2])
        p1.metric("Proyección Final", f"${metrics['proyeccion_mes']:,.0f}")
        p2.metric("Meta Total Mes", f"${metrics['ppto_total_mes']:,.0f}")
        with p3:
            st.plotly_chart(create_gauge_chart(metrics['cumplimiento_proyectado'], "Éxito Proyectado"), use_container_width=True, config={'displayModeBar': False})

    with tab2:
        st.subheader("Tendencia de Facturación (7 Días)")
        df_trend = prepare_chart_trend(df_working, fecha_analisis)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_trend['Fecha'].dt.strftime('%d/%m'), y=df_trend['Ingreso Real'], name='Real', marker_color='#3b82f6'))
        fig.add_trace(go.Scatter(x=df_trend['Fecha'].dt.strftime('%d/%m'), y=df_trend['Presupuesto'], name='Ppto', line=dict(color='#10b981', width=3)))
        fig.add_trace(go.Scatter(x=df_trend['Fecha'].dt.strftime('%d/%m'), y=df_trend['Ingreso Año Anterior'], name='Año Pasado', line=dict(color='#f59e0b', dash='dot')))
        fig.update_layout(template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Auditoría de Datos")
        df_table = prepare_advanced_table(df_working, fecha_analisis)
        html_table = df_table.to_html(index=False)
        st.markdown(f'<div style="overflow-x:auto;">{html_table}</div>', unsafe_allow_html=True)