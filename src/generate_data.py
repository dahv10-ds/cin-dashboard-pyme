import pandas as pd
import numpy as np
from datetime import datetime
import os

# Asegurar reproducibilidad para el demo
np.random.seed(42)

def generate_improved_data(output_path):
    # Generamos datos hasta finales de abril de 2026
    fecha_inicio = datetime(2025, 1, 1)
    fecha_fin = datetime(2026, 4, 30)
    fechas = pd.date_range(start=fecha_inicio, end=fecha_fin, freq='D')

    categorias = ['Smartphones', 'Laptops', 'TVs', 'Audio']
    
    # 1. Separación de métodos de pago
    metodos_pago = ['Tarjeta de Crédito', 'Efectivo', 'ACH', 'Yappy']

    datos = []

    for fecha in fechas:
        # Lógica de estacionalidad
        es_fin_semana = fecha.weekday() >= 5
        es_quincena = fecha.day in [1, 2, 14, 15, 16, 30, 31]
        
        multiplicador_base = 1.0
        if es_fin_semana: multiplicador_base *= 1.3
        if es_quincena: multiplicador_base *= 1.5

        presupuesto_base = 2800 + (fecha.month * 20) + (100 if fecha.year == 2026 else 0)

        for cat in categorias:
            # Pesos de venta por categoría
            peso_cat = {'Smartphones': 0.4, 'Laptops': 0.35, 'TVs': 0.15, 'Audio': 0.1}[cat]
            
            for pago in metodos_pago:
                # Pesos de comportamiento transaccional realista
                peso_pago = {'Tarjeta de Crédito': 0.45, 'Efectivo': 0.20, 'Yappy': 0.25, 'ACH': 0.10}[pago]

                # Generación de Venta Base
                venta_base = presupuesto_base * peso_cat * peso_pago * multiplicador_base
                
                # 2. Venta Real (con ruido estadístico)
                venta_real = np.random.lognormal(mean=np.log(venta_base), sigma=0.15)
                
                # 3. Presupuesto en dinero (Ligeramente retador, un 5% por encima de la base)
                ppto_linea = venta_base * 1.05

                # 4. Dato Pasado en dinero real (Simulando que el año pasado vendían entre 5% y 15% menos)
                factor_crecimiento_yoy = np.random.uniform(1.05, 1.15)
                venta_ano_anterior = venta_real / factor_crecimiento_yoy

                datos.append({
                    'Fecha': fecha,
                    'Día Semana': fecha.day_name(locale='es_ES'),
                    'Categoria': cat,
                    'Metodo Pago': pago,
                    'Ingreso Real': round(venta_real, 2),
                    'Presupuesto': round(ppto_linea, 2),
                    'Ingreso Año Anterior': round(venta_ano_anterior, 2)
                })

    df = pd.DataFrame(datos)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_excel(output_path, index=False)
    print(f"✅ Datos corporativos generados exitosamente en: {output_path}")

if __name__ == "__main__":
    path = os.path.join("data", "raw", "datos_retail_pyme.xlsx")
    generate_improved_data(path)