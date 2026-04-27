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
def create_gauge_chart(value, title):
    display_value = value * 100
    
    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode = "gauge",
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
            'bar': {'color': "#ffffff", 'thickness': 0.12},
            'bgcolor': "rgba(255,255,255,0.05)",
            'steps': [
                {'range': [0, 70], 'color': "#dc2626"},
                {'range': [70, 90], 'color': "#f59e0b"},
                {'range': [90, 100], 'color': "#16a34a"}
            ],
            'threshold': {
                'line': {'color': "#ffffff", 'width': 3},
                'thickness': 0.8,
                'value': 100
            }
        }
    ))

    fig.add_annotation(
        text=f"{display_value:.1f}%",
        x=0.5, y=0.15,
        showarrow=False,
        font=dict(size=34, color="#ffffff", family="Arial Black"),
        xref="paper", yref="paper"
    )
    
    diff = display_value - 100
    color = "#4ade80" if diff >= 0 else "#f87171"
    sign = "+" if diff > 0 else ""
    
    fig.add_annotation(
        text=f"{sign}{diff:.1f}% vs base",
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
            'font': {'size': 14, 'color': '#94a3b8'}
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=240,
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
        st.subheader("📊 Desempeño Acumulado vs. Presupuesto")
        st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-top:-15px;'>¿Cómo vamos desde el día 1 hasta hoy en comparación con la meta?</p>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 1, 1.2])
        c1.metric("Venta Acumulada", f"${metrics['ingreso_mtd']:,.0f}")
        c2.metric("Ppto. a la Fecha", f"${metrics['ppto_mtd']:,.0f}")
        with c3:
            st.plotly_chart(create_gauge_chart(metrics['cumplimiento_mtd'], "Cumplimiento Meta"), use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")
        
        # BLOQUE 2: CRECIMIENTO YoY
        st.subheader("📈 Variación de Crecimiento (YoY)")
        st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-top:-15px;'>Comparativa de ventas contra los mismos días del año pasado.</p>", unsafe_allow_html=True)
        
        g1, g2, g3 = st.columns([1, 1, 1.2])
        g1.metric("Venta Actual", f"${metrics['ingreso_mtd']:,.0f}")
        g2.metric("Venta Año Pasado", f"${metrics['ingreso_yoy_mtd']:,.0f}")
        with g3:
            st.plotly_chart(create_gauge_chart(metrics['crecimiento_mtd'] + 1, "Rendimiento YoY"), use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")
        
        # BLOQUE 3: PROYECCIÓN
        st.subheader("🎯 Escenario Proyectado y Meta de Cierre")
        st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-top:-15px;'>Si mantenemos el ritmo actual, ¿alcanzaremos la meta del mes?</p>", unsafe_allow_html=True)
        
        p1, p2, p3 = st.columns([1, 1, 1.2])
        p1.metric("Proyección Final", f"${metrics['proyeccion_mes']:,.0f}")
        p2.metric("Meta Total Mes", f"${metrics['ppto_total_mes']:,.0f}")
        with p3:
            st.plotly_chart(create_gauge_chart(metrics['cumplimiento_proyectado'], "Éxito Proyectado"), use_container_width=True, config={'displayModeBar': False})

    # (El tab2 queda igual)
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
        st.subheader("📋 Auditoría de Datos")
        st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-top:-15px;'>Desglose detallado del histórico reciente.</p>", unsafe_allow_html=True)
        
        df_table = prepare_advanced_table(df_working, fecha_analisis)
        
        def style_dataframe(df):
            format_dict = {}
            for col in df.columns:
                col_name = str(col).lower()
                # 1. Si la columna es de tipo porcentaje, fijamos 2 decimales y símbolo %
                if 'cumplimiento' in col_name or 'crecimiento' in col_name or '%' in col_name:
                    format_dict[col] = '{:.2%}'
                # 2. Si es cualquier otro número, fijamos formato moneda con 2 decimales
                elif pd.api.types.is_numeric_dtype(df[col]):
                    format_dict[col] = '${:,.2f}'
                    
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
                table.dataframe td {{ padding: 8px; white-space: nowrap; text-align: center; }}
                table.dataframe tr:hover {{ background-color: #1e293b; }}
            </style>
            {html_table}
        </div>
        """
        st.markdown(custom_html, unsafe_allow_html=True)