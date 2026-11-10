# Análisis de Ventas Retail · Tienda de productos naturales

Análisis de casi **7 años de ventas reales** (febrero 2020 – noviembre 2026) de una tienda chilena de productos naturales y saludables que vende por tienda física, tienda online, apps de delivery y Mercado Libre.

El proyecto cubre el ciclo completo de un análisis de negocio: anonimización de datos, limpieza documentada, construcción de variables a partir de reglas de negocio, análisis exploratorio y recomendaciones.

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-2.x-150458?logo=pandas&logoColor=white)
![matplotlib](https://img.shields.io/badge/matplotlib-seaborn-11557c)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?logo=jupyter&logoColor=white)

---

## Problema de negocio

En 2026 las ventas de la tienda cayeron. El objetivo fue entender **cuánto, dónde y por qué**, y responder seis preguntas:

1. ¿Cómo han evolucionado las ventas desde 2020?
2. ¿En qué meses, días y horas se concentran?
3. ¿Qué peso tiene cada canal y cómo ha cambiado?
4. ¿Qué productos generan más venta y cuáles dejan más margen?
5. ¿Qué categorías lideran el negocio?
6. ¿Cómo ha evolucionado el ticket promedio?

---

## Hallazgos principales

- **La caída de 2026 es real: −15%** comparando el mismo período que 2025 (enero a noviembre). Se explica por cerca de 10% menos compras y 5% menos de ticket promedio.
- **La caída se concentra en la tienda física (−30%)**, donde la cantidad de compras baja entre 25% y 30% desde septiembre de 2025, coincidiendo con una reducción de la inversión en anuncios de Meta.
- **Los canales se mueven en direcciones opuestas:** Mercado Libre crece 68% y las apps de delivery 24%, mientras la tienda física pasa de representar el 59% de la venta en 2023 al 41% en 2026.
- **Los suplementos sostienen el negocio:** son la mitad de la venta y se mantuvieron estables en 2026 (−1%), mientras alimentos, bebidas y hogar (compras de impulso que dependen del flujo en tienda) caen entre 26% y 30%.
- **Concentración 80/20:** el 24% de los productos genera el 80% de la venta.
- **Estacionalidad marcada:** febrero es el mes más bajo (vacaciones de verano) y julio–agosto los más altos (invierno). En tienda física hay dos peaks diarios: 13:00 y 18:00.

---

## Decisiones de calidad de datos destacadas

- **Facturas publicitarias:** 264 líneas de "glosa" eran acuerdos publicitarios, no ventas de productos. Representaban el 0,1% de las líneas pero el 2,6% de la venta, y sus notas de crédito explicaban el **85% del monto devuelto**. Sin esta revisión, la tasa de devolución habría parecido 6 veces mayor.
- **Canal de venta reconstruido:** la columna de canal del sistema clasificaba el 92% de las ventas como "Tienda". Se construyó un canal nuevo a partir de la forma de pago, con reglas definidas junto al negocio, que cubre el 99,9% de las ventas.
- **Categorías limitadas a 2024–2026:** el catálogo se reestructuró en 2026 y la cobertura de categorías en años anteriores era baja (34% de la venta en 2020), por lo que ese análisis se restringió al período confiable.

---

## Estructura del proyecto

```
analisis-ventas-retail/
├── data/
│   ├── raw/                      ← datos originales (no incluidos: contienen datos personales)
│   └── processed/
│       └── ventas_limpias.parquet  ← datos anonimizados y limpios
├── notebooks/
│   ├── 01_limpieza_y_eda.ipynb          ← calidad de datos, limpieza y canales
│   └── 02_analisis_exploratorio.ipynb   ← análisis y conclusiones
├── src/
│   └── anonimizar_ventas.py      ← anonimización de los reportes del sistema
└── README.md
```

---

## Privacidad de los datos

Los datos originales provienen del sistema de ventas de la tienda y se usan con autorización. Antes de cualquier análisis se anonimizaron con `src/anonimizar_ventas.py`:

- Se eliminaron nombres, RUT, correos y direcciones de clientes.
- Los clientes se identifican con un código seudónimo irreversible.
- Vendedores y documentos se codificaron.
- **Los montos se escalaron por un factor confidencial:** las tendencias y proporciones son reales, pero las cifras absolutas no corresponden a las ventas reales.

---

## Cómo reproducir

```bash
pip install pandas numpy matplotlib seaborn pyarrow
```

- `02_analisis_exploratorio.ipynb` se puede ejecutar directamente con `data/processed/ventas_limpias.parquet`.
- `01_limpieza_y_eda.ipynb` requiere los CSV anonimizados intermedios, que no se incluyen por su tamaño.

---

## Limitaciones

- La relación entre la reducción de anuncios y la caída de ventas es una coincidencia temporal, no una causalidad probada.
- Los montos no están ajustados por inflación.
- El margen de Mercado Libre y las apps de delivery no descuenta las comisiones de cada plataforma.

---

## Próximos pasos

- Dashboards interactivos en Tableau y Power BI.
- Clasificación ABC de inventario.
- Análisis de canasta (productos que se compran juntos).
- Pronóstico de demanda con series de tiempo.

---

## Autor

**Cristopher Escamilla** · Publicista y analista de datos (Data Science, Desafío Latam)
[LinkedIn](#) · [Tableau Public](#)
