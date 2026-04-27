import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from src.calculations import load_and_preprocess, get_pulse_metrics, prepare_advanced_table, prepare_chart_trend

st.set_page_config(page_title="Control Estratégico Integral", layout="wide", initial_sidebar_state="collapsed")

# CSS Avanzado UI/UX (Tarjetas Corporativas y Optimización Móvil)
st.markdown("""
    <style>
    .stApp { background-color: #0b1120; }
    h1, h2, h3, p { text-align: center !important; color: #f8fafc !important; }
    
    /* Diseño de las Tarjetas (Cards) para las Métricas */
    div[data-testid="metric-container"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 15px 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    
    div[data-testid="stMetricValue"] { text-align: center !important; font-size: 1.8rem !important; color: #ffffff !important; }
    div[data-testid="stMetricLabel"] { text-align: center !important; font-size: 1rem !important; color: #94a3b8 !important; }
    div[data-testid="stMetricDelta"] { justify-content: center !important; font-size: 0.9rem !important;}
    
    /* Pestañas optimizadas para toque en móvil */
    button[data-baseweb="tab"] { font-size: 1.1rem !important; padding: 0.8rem 1.5rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- FUNCIÓN DEL TACÓMETRO ---
def create_gauge_chart(value, title):
    pct_value = value * 100 
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = pct_value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 14, 'color': '#94a3b8'}},
        delta = {'reference': 100, 'position': "top", 'suffix': "%"},
        number = {'suffix': "%", 'font': {'size': 24, 'color': '#ffffff'}},
        gauge = {
            'axis': {'range': [0, max(120, pct_value + 10)], 'tickwidth': 1, 'tickcolor': "#334155"},
            'bar': {'color': "#3b82f6"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "#1e293b",
            'steps': [
                {'range': [0, 80], 'color': "rgba(239, 68, 68, 0.3)"},   # Rojo
                {'range': [80, 100], 'color': "rgba(245, 158, 11, 0.3)"}, # Amarillo
                {'range': [100, max(120, pct_value + 10)], 'color': "rgba(16, 185, 129, 0.3)"} # Verde
            ],
            'threshold': {
                'line': {'color': "white", 'width': 3},
                'thickness': 0.75,
                'value': 100
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': "#f8fafc", 'family': "Arial"},
        height=180, # Altura compacta para móviles
        margin=dict(l=10, r=10, t=30, b=10)
    )
    return fig
# -----------------------------

@st.cache_data
def get_data():
    return load_and_preprocess(os.path.join("data", "raw", "datos_retail_pyme.xlsx"))

df_base = get_data()

st.title("Control Integral de Negocios (CIN)")
st.markdown("<p style='color: #64748b; font-size: 1.1rem; margin-top:-15px;'>Visibilidad Estratégica en Tiempo Real</p><br>", unsafe_allow_html=True)

# Eliminamos las columnas espaciadoras para maximizar el ancho en móviles
col_sel1, col_sel2 = st.columns(2)
with col_sel1:
    ultima_fecha = df_base['Fecha'].max()
    fecha_analisis = pd.to_datetime(st.date_input("🗓️ Fecha de análisis:", ultima_fecha, min_value=df_base['Fecha'].min(), max_value=ultima_fecha))
with col_sel2:
    perspectiva = st.selectbox("🏬 Perspectiva Comercial:", ["General del Negocio"] + sorted(list(df_base['Categoria'].unique())))

df_working = df_base if perspectiva == "General del Negocio" else df_base[df_base['Categoria'] == perspectiva]
st.markdown("---")

metrics = get_pulse_metrics(df_working, fecha_analisis)

if metrics:
    tab1, tab2, tab3 = st.tabs(["🎛️ Centro de Mando", "📈 Análisis Visual", "📋 Auditoría y Detalles"])

    with tab1:
        st.subheader("Rendimiento del Mes a la Fecha (MTD)")
        st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-top:-15px;'>¿Cómo vamos desde el día 1 hasta hoy?</p>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Acumulado a la Fecha", f"${metrics['ingreso_mtd']:,.0f}")
        c2.metric("Presupuesto a la Fecha", f"${metrics['ppto_mtd']:,.0f}")
        with c3:
            st.plotly_chart(create_gauge_chart(metrics['cumplimiento_mtd'], "Cumplimiento MTD"), use_container_width=True, config={'displayModeBar': False})

        st.markdown("<br>", unsafe_allow_html=True)
        
        st.subheader("Proyección a Cierre de Mes (Run-Rate)")
        st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-top:-15px;'>Si mantenemos el ritmo, ¿alcanzaremos la meta del mes?</p>", unsafe_allow_html=True)
        
        c4, c5, c6 = st.columns(3)
        c4.metric("Proyección Final MTD", f"${metrics['proyeccion_mes']:,.0f}")
        c5.metric("Presupuesto Total del Mes", f"${metrics['ppto_total_mes']:,.0f}")
        with c6:
            st.plotly_chart(create_gauge_chart(metrics['cumplimiento_proyectado'], "Proyección Final"), use_container_width=True, config={'displayModeBar': False})

    with tab2:
        st.subheader(f"Tendencia de Facturación (Últimos 7 Días)")
        df_trend = prepare_chart_trend(df_working, fecha_analisis)
        if not df_trend.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_trend['Fecha'].dt.strftime('%d/%m'), y=df_trend['Ingreso Real'], name='Venta Real', marker_color='#3b82f6', text=df_trend['Ingreso Real'].map('${:,.0f}'.format), textposition='auto'))
            fig.add_trace(go.Scatter(x=df_trend['Fecha'].dt.strftime('%d/%m'), y=df_trend['Presupuesto'], mode='lines+markers', name='Presupuesto', line=dict(color='#10b981', width=3)))
            fig.add_trace(go.Scatter(x=df_trend['Fecha'].dt.strftime('%d/%m'), y=df_trend['Ingreso Año Anterior'], mode='lines+markers', name='Año Anterior', line=dict(color='#f59e0b', width=3, dash='dot')))
            
            fig.update_layout(template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Historial Estratégico")
        df_table = prepare_advanced_table(df_working, fecha_analisis)
        
        def style_dataframe(df):
            format_dict = {col: '${:,.2f}' if col[0] == 'Facturación' else '{:.0%}' for col in df.columns if col[0] in ['Facturación', 'Cumplimiento', 'Crecimiento']}
            st_df = df.style.hide(axis='index').format(format_dict)
            
            def highlight_rows(x):
                df_colors = pd.DataFrame('', index=x.index, columns=x.columns)
                if len(df_colors) > 1: 
                    df_colors.iloc[1, :] = 'background-color: #1e3a8a; color: white;'
                    df_colors.iloc[-1, :] = 'background-color: #334155; color: white; font-weight: bold;'
                return df_colors

            st_df = st_df.apply(highlight_rows, axis=None)
            st_df = st_df.set_table_styles([
                {'selector': 'th', 'props': [('text-align', 'center !important'), ('border-bottom', '1px solid #334155')]},
                {'selector': 'td', 'props': [('text-align', 'center !important'), ('border-bottom', '1px solid #1e293b')]}
            ])
            return st_df
            
        html_table = style_dataframe(df_table).to_html()
        
        custom_html = f"""
        <div style="width:100%; overflow-x: auto;">
            <style>
                table.dataframe {{ width: 100%; border-collapse: collapse; color: #f8fafc; font-size: 13px; }}
                table.dataframe th {{ background-color: #0f172a; padding: 10px; font-weight: 600; white-space: nowrap; }}
                table.dataframe td {{ padding: 8px; white-space: nowrap; }}
                table.dataframe tr:hover {{ background-color: #1e293b; }}
            </style>
            {html_table}
        </div>
        """
        st.markdown(custom_html, unsafe_allow_html=True)
else:
    st.warning("No hay datos disponibles para esta fecha.")