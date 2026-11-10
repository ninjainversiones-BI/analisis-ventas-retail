"""
anonimizar_ventas.py
--------------------
Une los reportes anuales de "Detalle de ventas" y de "Formas de Pago" y genera
dos tablas anonimizadas, aptas para un portafolio público, que se relacionan
por la columna id_documento:
  - ventas_anonimizadas.csv : una fila por producto vendido
  - pagos_anonimizados.csv  : una fila por forma de pago usada en cada documento

Qué hace:
  1. Elimina datos personales de clientes (nombre, RUT, email, dirección).
  2. Crea un ID de cliente seudónimo (hash con "sal" secreta) a partir de RUT o email,
     para poder analizar recurrencia sin saber quién es quién.
  3. Reemplaza nombres de vendedores por códigos y quita el nombre de la tienda
     de todos los textos.
  4. Renumera los documentos (boletas/facturas) manteniendo qué líneas van juntas.
  5. Multiplica todos los montos por un factor secreto: los patrones y los % se
     mantienen, los niveles reales de venta quedan ocultos.
  6. Agrupa las listas de precio en un "canal" (Tienda, Uber/Rappi, Cornershop, ...).
  7. Lee los reportes de formas de pago (son HTML con extensión .xls) y los agrupa.

Uso:
  python anonimizar_ventas.py  carpeta_con_los_reportes  carpeta_de_salida

La primera vez crea "llaves_privadas.json" con la sal y el factor.
¡NUNCA subas ese archivo a GitHub! Agrégalo a tu .gitignore.
"""

import glob
import hashlib
import html
import json
import os
import re
import secrets
import sys

import numpy as np
import pandas as pd

ARCHIVO_LLAVES = "llaves_privadas.json"

COLUMNAS_PERSONALES = [
    "Nombre Cliente", "Cliente RUT", "Email Cliente", "Cliente Dirección",
    "Cliente Comuna", "Cliente Ciudad", "Tracking number",
]
COLUMNAS_VACIAS_O_CONSTANTES = [
    "Otros Atributos", "Detalle de Productos/Servicios Pack/Promo",
    "Sucursal", "Moneda", "Fecha de Emisión",
]
COLUMNAS_MONTO = [
    "Precio de Lista", "Precio Neto Unitario", "Precio Bruto Unitario",
    "Venta Total Neta", "Total Impuestos", "Venta Total Bruta",
    "Descuento Neto", "Descuento Bruto", "Costo neto unitario",
    "Costo Total Neto", "Margen",
]
PATRON_TIENDA = re.compile(r"rumbo\s*verde|\bRV\b", flags=re.IGNORECASE)


def cargar_llaves():
    """Lee la sal y el factor secretos, o los crea la primera vez."""
    if os.path.exists(ARCHIVO_LLAVES):
        with open(ARCHIVO_LLAVES) as f:
            return json.load(f)
    llaves = {
        "sal": secrets.token_hex(16),
        "factor_montos": round(0.6 + secrets.randbelow(8000) / 10000, 4),  # entre 0.6 y 1.4
    }
    with open(ARCHIVO_LLAVES, "w") as f:
        json.dump(llaves, f, indent=2)
    print(f"Llaves nuevas guardadas en {ARCHIVO_LLAVES} (no lo publiques).")
    return llaves


def limpiar_texto(s):
    """Quita saltos de línea, espacios dobles y el nombre de la tienda."""
    if pd.isna(s):
        return s
    s = re.sub(r"\s+", " ", str(s)).strip()
    return PATRON_TIENDA.sub("Marca Propia", s)


def hash_cliente(rut, email, sal):
    """ID seudónimo estable: mismo cliente -> mismo ID, pero irreversible sin la sal."""
    if pd.notna(rut):
        clave = re.sub(r"[^0-9kK]", "", str(rut)).upper()
    elif pd.notna(email):
        clave = str(email).strip().lower()
    else:
        return np.nan
    return "C_" + hashlib.sha256((sal + clave).encode()).hexdigest()[:10]


def asignar_canal(lista):
    l = str(lista).lower()
    if "uber" in l or "rappi" in l:
        return "Delivery Uber/Rappi"
    if "corner" in l:
        return "Delivery Cornershop"
    if "cafeter" in l:
        return "Cafetería"
    if "mayorista" in l:
        return "Mayorista"
    if "ml full" in l:
        return "Mercado Libre"
    if "base" in l:
        return "Tienda"
    return "Otro"


GRUPOS_PAGO = {
    "TARJETA DEBITO": "Tarjeta presencial", "TARJETA CREDITO": "Tarjeta presencial",
    "WEBPAY DEBITO": "Webpay", "WEBPAY CREDITO": "Webpay",
    "MERCADOPAGO": "MercadoPago", "PAYPAL": "Paypal",
    "EFECTIVO": "Efectivo", "VUELTO EFECTIVO": "Efectivo",
    "TRANSFERENCIA BANCARIA": "Transferencia",
    "CORNERSHOP": "App delivery", "UBER EATS": "App delivery", "RAPPI": "App delivery",
    "GOODMEAL": "App delivery", "CUPÓN PEDIDOS YA": "App delivery",
    "MERCADOLIBRE": "Mercado Libre", "ML FULL - NO USAR": "Mercado Libre",
    "CREDITO TRABAJADORES": "Crédito trabajadores", "CHEQUE": "Otros",
}
CELDA = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S)


def leer_formas_de_pago(archivo):
    """Los reportes 'Formas de Pago' son HTML mal formado: se recorren a mano.
    Cada sección parte con el nombre de la forma de pago en negrita."""
    texto = open(archivo, encoding="utf-8").read()
    texto = texto[texto.find("<body"):]
    filas, forma = [], None
    for bloque in texto.split("</tr>"):
        celdas = [html.unescape(re.sub("<[^>]+>", "", c)).strip() for c in CELDA.findall(bloque)]
        if not celdas:
            continue
        if "font-weight: 700" in bloque and len(celdas) == 1:
            forma = celdas[0]
        elif len(celdas) >= 7 and celdas[0] != "Tipo de Documento":
            filas.append([forma] + celdas[:6])  # se descartan sucursal y atributos de comprobante
    return pd.DataFrame(filas, columns=["forma_pago", "tipo_de_documento", "numero",
                                        "fecha", "total_documento", "monto_forma_pago", "usuario"])


def anonimizar(carpeta, carpeta_salida):
    llaves = cargar_llaves()
    sal, factor = llaves["sal"], llaves["factor_montos"]

    # 1. Leer y unir todos los años
    archivos = sorted(glob.glob(os.path.join(carpeta, "Detalle_de_ventas*.xlsx")))
    df = pd.concat(
        [pd.read_excel(a, dtype={"SKU": str}) for a in archivos], ignore_index=True
    )
    df = df.dropna(subset=["Tipo Movimiento"])  # filas vacías al final de cada archivo
    print(f"{len(archivos)} archivos, {len(df):,} líneas")

    # 2. ID seudónimo de cliente, luego borrar datos personales
    df["id_cliente"] = [
        hash_cliente(r, e, sal) for r, e in zip(df["Cliente RUT"], df["Email Cliente"])
    ]
    df = df.drop(columns=COLUMNAS_PERSONALES + COLUMNAS_VACIAS_O_CONSTANTES)

    # 3. Vendedores: cajas genéricas se mantienen, personas pasan a código
    cajas = {"Tienda Rumbo Verde": "Caja Tienda", "Emporio Rumbo Verde": "Caja Emporio",
             "Plantas Rumbo Verde": "Caja Plantas"}
    personas = sorted(set(df["Vendedor"].dropna()) - set(cajas),
                      key=lambda n: hashlib.sha256((sal + n).encode()).hexdigest())
    codigos = {n: f"Vendedor_{i + 1:02d}" for i, n in enumerate(personas)}
    df["Vendedor"] = df["Vendedor"].map({**cajas, **codigos})

    # 4. Renumerar documentos (misma boleta -> mismo id)
    clave_doc = df["Tipo de Documento"].astype(str) + "|" + df["Numero del documento"].astype(int).astype(str)
    codigos_doc, claves_unicas = pd.factorize(clave_doc)
    df["id_documento"] = codigos_doc + 1
    mapa_docs = {k: i + 1 for i, k in enumerate(claves_unicas)}
    df = df.drop(columns=["Numero del documento"])

    # 5. Canal de venta y textos libres
    df["canal"] = df["Lista de Precio"].map(asignar_canal)
    df = df.drop(columns=["Lista de Precio"])
    df.loc[df["Producto / Servicio"] == "Glosa", "Variante"] = np.nan  # glosas de facturas: texto libre
    for c in ["Producto / Servicio", "Variante", "Marca", "Nombre de dcto",
              "Tipo de producto / Servicio", "SKU"]:
        df[c] = df[c].map(limpiar_texto)

    # 6. Montos escalados por el factor secreto (los % no cambian)
    for c in COLUMNAS_MONTO:
        df[c] = (pd.to_numeric(df[c], errors="coerce") * factor).round(0)

    # 7. Fecha y hora en formatos estándar
    df["fecha"] = pd.to_datetime(df["Fecha Venta"], format="%d/%m/%Y")
    df = df.drop(columns=["Fecha Venta"]).rename(columns={"Hora Venta": "hora"})

    # 8. Nombres de columna en snake_case
    df.columns = [
        re.sub(r"[^a-z0-9]+", "_",
               c.lower().replace("%", "pct ").translate(str.maketrans("áéíóúñ", "aeioun"))).strip("_")
        for c in df.columns
    ]

    os.makedirs(carpeta_salida, exist_ok=True)
    salida = os.path.join(carpeta_salida, "ventas_anonimizadas.csv")
    df.to_csv(salida, index=False, encoding="utf-8")
    print(f"Ventas: {salida} ({len(df):,} filas, {df.shape[1]} columnas)")

    # ---------------- Formas de pago ----------------
    archivos_pago = sorted(glob.glob(os.path.join(carpeta, "Formas_de_Pago*.xls")))
    if not archivos_pago:
        return df, None
    pg = pd.concat([leer_formas_de_pago(a) for a in archivos_pago], ignore_index=True)

    # mismo id_documento que en ventas (documentos sin venta reciben ids nuevos)
    clave = pg["tipo_de_documento"] + "|" + pg["numero"].str.lstrip("0")
    for k in clave[~clave.isin(mapa_docs)].unique():
        mapa_docs[k] = len(mapa_docs) + 1
    pg["id_documento"] = clave.map(mapa_docs)

    pg["vendedor"] = pg["usuario"].map({**cajas, **codigos})
    pg["forma_pago"] = pg["forma_pago"].str.upper().str.strip()
    pg["grupo_pago"] = pg["forma_pago"].map(GRUPOS_PAGO).fillna("Devoluciones y ajustes")
    for c in ["total_documento", "monto_forma_pago"]:
        pg[c] = (pd.to_numeric(pg[c], errors="coerce") * factor).round(0)
    pg["fecha"] = pd.to_datetime(pg["fecha"], format="%d/%m/%Y")
    pg = pg[["id_documento", "tipo_de_documento", "fecha", "forma_pago", "grupo_pago",
             "monto_forma_pago", "total_documento", "vendedor"]]

    salida_pg = os.path.join(carpeta_salida, "pagos_anonimizados.csv")
    pg.to_csv(salida_pg, index=False, encoding="utf-8")
    print(f"Pagos: {salida_pg} ({len(pg):,} filas)")
    return df, pg


if __name__ == "__main__":
    carpeta = sys.argv[1] if len(sys.argv) > 1 else "."
    carpeta_salida = sys.argv[2] if len(sys.argv) > 2 else "."
    anonimizar(carpeta, carpeta_salida)
