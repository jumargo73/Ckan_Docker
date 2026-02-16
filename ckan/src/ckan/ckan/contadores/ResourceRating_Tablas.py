from ckan.model import meta,ResourceRating

#!/usr/bin/env python
import os
import sys

# 1️⃣ Ruta absoluta a tu .ini de CKAN
ini_path = '/etc/ckan/default/production.ini'    # ← ajústalo

# 2️⃣ Indica a CKAN dónde está el config
os.environ['CKAN_CONFIG'] = ini_path

# 3️⃣ Asegúrate de que el paquete 'ckan' esté en el PYTHONPATH
ckan_root = '/usr/lib/ckan/default/src/ckan'     # ← ajústalo
if ckan_root not in sys.path:
    sys.path.insert(0, ckan_root)

# 4️⃣ Levanta CKAN
from ckan.config.environment import load_environment
load_environment()    # ← sin parámetros

# 5️⃣ Importa tu modelo y meta
from ckan.model import meta, ResourceRating

# 6️⃣ Crea la tabla  
try:
    # metadata es un MetaData ya enlazado a meta.engine
    print("⏳ Iniciando creación de tabla…")

    ResourceRating.__table__.create(bind=meta.engine, checkfirst=True)
    print("✅ Tabla ‘resource_rating’ creada o ya existía.")

except Exception as e:
    print("❌ Error al crear tabla:", e)
