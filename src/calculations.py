import numpy as np
import pandas as pd
from datetime import timedelta
import calendar

def load_and_preprocess(filepath):
    df = pd.read_excel(filepath)
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    return df

def get_pulse_metrics(df, selected_date):
    """Calcula KPIs principales, MTD, Proyección y Crecimiento YoY."""
    df_upto = df[df['Fecha'] <= selected_date]
    
    # --- MÉTRICAS DEL MES (MTD) ---
    inicio_mes = selected_date.replace(day=1)
    mtd_data = df_upto[(df_upto['Fecha'] >= inicio_mes)]
    
    ingreso_mtd = mtd_data['Ingreso Real'].sum()
    ppto_mtd = mtd_data['Presupuesto'].sum()
    ingreso_yoy_mtd = mtd_data['Ingreso Año Anterior'].sum() # Lo que se vendió el año pasado a esta fecha
    
    cumplimiento_mtd = ingreso_mtd / ppto_mtd if ppto_mtd > 0 else 0
    crecimiento_mtd = (ingreso_mtd / ingreso_yoy_mtd) - 1 if ingreso_yoy_mtd > 0 else 0

    # --- PROYECCIÓN ---
    dias_transcurridos = selected_date.day
    _, dias_del_mes = calendar.monthrange(selected_date.year, selected_date.month)
    mes_completo = df[(df['Fecha'].dt.year == selected_date.year) & (df['Fecha'].dt.month == selected_date.month)]
    ppto_total_mes = mes_completo['Presupuesto'].sum()

    proyeccion_mes = (ingreso_mtd / dias_transcurridos) * dias_del_mes if dias_transcurridos > 0 else 0
    cumplimiento_proyectado = proyeccion_mes / ppto_total_mes if ppto_total_mes > 0 else 0

    return {
        'ingreso_mtd': ingreso_mtd, 
        'ppto_mtd': ppto_mtd,
        'ingreso_yoy_mtd': ingreso_yoy_mtd,
        'cumplimiento_mtd': cumplimiento_mtd,
        'crecimiento_mtd': crecimiento_mtd,
        'proyeccion_mes': proyeccion_mes, 
        'ppto_total_mes': ppto_total_mes,
        'cumplimiento_proyectado': cumplimiento_proyectado
    }

def prepare_advanced_table(df, selected_date):
    """Prepara la tabla Multinivel sin totales por columna, añadiendo fila TOTAL."""
    # 1. Rango dinámico (D0, D-7, y D-1 a D-6)
    rango_historial = [selected_date - timedelta(days=i) for i in range(1, 7)]
    fechas_finales = [selected_date, selected_date - timedelta(days=7)] + rango_historial
    
    # Eliminar duplicados manteniendo orden
    fechas_unicas = []
    for f in fechas_finales:
        if f not in fechas_unicas: fechas_unicas.append(f)

    df_filtered = df[df['Fecha'].isin(fechas_unicas)].copy()
    grouped = df_filtered.groupby(['Fecha', 'Metodo Pago'])[['Ingreso Real', 'Presupuesto', 'Ingreso Año Anterior']].sum().reset_index()

    # 2. Pivotar datos
    piv_fact = grouped.pivot(index='Fecha', columns='Metodo Pago', values='Ingreso Real').fillna(0)
    piv_ppto = grouped.pivot(index='Fecha', columns='Metodo Pago', values='Presupuesto').fillna(0)
    piv_yoy = grouped.pivot(index='Fecha', columns='Metodo Pago', values='Ingreso Año Anterior').fillna(0)

    # Asegurar orden de columnas
    metodos = [m for m in ['ACH', 'Efectivo', 'Tarjeta de Crédito', 'Yappy'] if m in piv_fact.columns]
    
    piv_fact = piv_fact.reindex(index=fechas_unicas, columns=metodos).fillna(0)
    piv_ppto = piv_ppto.reindex(index=fechas_unicas, columns=metodos).fillna(0)
    piv_yoy = piv_yoy.reindex(index=fechas_unicas, columns=metodos).fillna(0)

    # 3. Calcular Fila TOTAL (Excluyendo índice 1 que es D-7)
    fechas_7dias = [fechas_unicas[0]] + fechas_unicas[2:]
    
    piv_fact.loc['TOTAL'] = piv_fact.loc[fechas_7dias].sum()
    piv_ppto.loc['TOTAL'] = piv_ppto.loc[fechas_7dias].sum()
    piv_yoy.loc['TOTAL'] = piv_yoy.loc[fechas_7dias].sum()

    # 4. Cálculos Proporcionales (Evita el promedio de porcentajes)
    cumpl = (piv_fact / piv_ppto).fillna(0)
    crec = (piv_fact / piv_yoy).fillna(0)

    # 5. Construir DataFrame MultiIndex
    resultado = pd.DataFrame(index=piv_fact.index)
    
    for col in metodos: resultado[('Facturación', col)] = piv_fact[col]
    for col in metodos: resultado[('Cumplimiento', col)] = cumpl[col]
    for col in metodos: resultado[('Crecimiento', col)] = crec[col]
        
    resultado = resultado.reset_index()
    
    # 6. Formato de Fechas y Textos (Adaptado para la Nube)
    dias_espanol = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
    
    dias_semana = []
    fechas_str = []
    for val in resultado['Fecha']:
        if val == 'TOTAL':
            dias_semana.append('')
            fechas_str.append('TOTAL')
        else:
            # Usamos weekday() que devuelve un número del 0 (Lunes) al 6 (Domingo)
            dias_semana.append(dias_espanol[val.weekday()])
            fechas_str.append(val.strftime('%d/%m'))
            
    resultado.insert(0, ('Datos', 'Fecha'), fechas_str)
    resultado.insert(1, ('Datos', 'Día Semana'), dias_semana)
    resultado = resultado.drop(columns=['Fecha'])
    
    resultado.columns = pd.MultiIndex.from_tuples(resultado.columns)
    return resultado

def prepare_chart_trend(df, selected_date):
    """Tendencia de los últimos 7 días con las 3 variables en dinero real."""
    fecha_inicio = selected_date - timedelta(days=6)
    df_trend = df[(df['Fecha'] >= fecha_inicio) & (df['Fecha'] <= selected_date)]
    trend_daily = df_trend.groupby('Fecha')[['Ingreso Real', 'Presupuesto', 'Ingreso Año Anterior']].sum().reset_index()
    return trend_daily



