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

# --- FUNCIÓN DEL TACÓMETRO ESTÁNDAR 0-100 ---
def create_gauge_chart(value, title, is_percent_growth=False):
    display_value = value * 100
    
    fig = go.Figure()

    # 1. El Tacómetro (Escala fija 0-100)
    fig.add_trace(go.Indicator(
        mode = "gauge",
        # Visualmente limitamos la aguja al rango 0-100
        value = max(0, min(display_value, 100)), 
        domain = {'x': [0, 1], 'y': [0.35, 1]},
        gauge = {
            'axis': {
                'range': [0, 100], 
                'tickwidth': 1, 
                'tickcolor': "#94a3b8",
                'tickmode': 'array',
                'tickvals': [0, 50, 100],
                'tickfont': {'size': 12, 'color': "#94a3b8"}
            },
            'bar': {'color': "#ffffff", 'thickness': 0.12}, # Aguja blanca ultra-delgada y elegante
            'bgcolor': "rgba(255,255,255,0.05)",
            'steps': [
                {'range': [0, 70], 'color': "#dc2626"},   # Rojo Corporativo
                {'range': [70, 90], 'color': "#f59e0b"}, # Ámbar/Amarillo Precaución
                {'range': [90, 100], 'color': "#16a34a"} # Verde Éxito
            ],
            'threshold': {
                'line': {'color': "#ffffff", 'width': 3},
                'thickness': 0.8,
                'value': 100 if not is_percent_growth else 0
            }
        }
    ))

    # 2. Número Central (Ubicado debajo del arco para máxima visibilidad)
    fig.add_annotation(
        text=f"{display_value:.1f}%",
        x=0.5, y=0.15,
        showarrow=False,
        font=dict(size=34, color="#ffffff", family="Arial Black"),
        xref="paper", yref="paper"
    )
    
    # 3. Etiqueta de Comparativa (Delta)
    ref = 100 if not is_percent_growth else 0
    diff = display_value - ref
    color = "#4ade80" if diff >= 0 else "#f87171"
    sign = "+" if diff > 0 else ""
    
    fig.add_annotation(
        text=f"{sign}{diff:.1f}% vs objetivo",
        x=0.5, y=0.42,
        showarrow=False,
        font=dict(size=13, color=color, family="Arial"),
        xref="paper", yref="paper"
    )

    fig.update_layout(
        title = {
            'text': title.upper(), 
            'y': 0.98, 'x': 0.5, 
            'xanchor': 'center', 
            'font': {'size': 14, 'color': '#94a3b8', 'letter_spacing': 2}
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=240, # Aumentamos un poco el alto para dar aire al número inferior
        margin=dict(l=25, r=25, t=50, b=10)
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