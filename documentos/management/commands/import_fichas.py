# app/management/commands/import_fichas.py
import re, unicodedata, pandas as pd
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from documentos.models import FichaPaciente, TipoDocumento, Nacionalidad
from django.core.management.base import BaseCommand
# documentos/management/commands/import_fichas.py
import re, unicodedata, pandas as pd
from datetime import date
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Max
from documentos.models import (
    FichaPaciente, TipoDocumento, Nacionalidad
)
    
# ------------  CONFIGURACIÓN  -------------------------------------------------
COL_MAP = {
    "Nombres y apellidos del paciente": "nombre_completo",
    "Fecha_de_visita_de_la_tarjeta":    "fecha_visita",
    "ultimo_registro_de_visita_en_la_base_de_datos": "fecha_ultimo",
    "CAJA":      "caja",
    "CARPETA":   "carpeta",
    "num_identificacion": "num_identificacion",
}

# Ids fijos que ya tienes en la BD
ID_NAC = {          # prefijo  →  id nacionalidad
    "VEN": 1,
    "ECU": 3,
    "": 2,
}
ID_DOC = {          # tipo     →  id tipo documento
    "CEDULA": 3,
    "PASAPORTE": 4,
}

FEMALE_SUFFIX = ("A",)
MALE_EXCEPTIONS = {"JOSE", "LUISA", "JONATHAN"}  # amplía si quieres
# -----------------------------------------------------------------------------

def infer_sexo(primer_nombre: str):
    if not primer_nombre:
        return "Masculino"
    n = unicodedata.normalize("NFD", primer_nombre).encode("ascii", "ignore").decode().upper()
    if n in MALE_EXCEPTIONS:
        return "Masculino"
    return "Femenino" if n.endswith(FEMALE_SUFFIX) else "Masculino"

def split_nombre(full: str):
    """Devuelve primer_nombre, segundo_nombre, primer_apellido, segundo_apellido"""
    if not isinstance(full, str):
        return (None, None, None, None)
    partes = full.strip().split()
    if len(partes) >= 4:
        a1, a2, n1, n2 = partes[0], partes[1], partes[2], " ".join(partes[3:])
    elif len(partes) == 3:
        a1, a2, n1, n2 = partes[0], partes[1], partes[2], None
    elif len(partes) == 2:
        a1, a2, n1, n2 = partes[0], None, partes[1], None
    else:
        a1, a2, n1, n2 = None, None, partes[0], None
    return n1, n2, a1, a2

def clean_num(num):
    """Devuelve (prefijo, numeros)"""
    if pd.isna(num):
        return "", None
    num = str(num).strip().upper()
    m = re.match(r"([A-Z]+)(\d+)", num)
    if m:
        return m.group(1), m.group(2)
    return "", num  # solo dígitos

def safe_date(val):
    try:
        return pd.to_datetime(val, errors="coerce").date()
    except Exception:
        return None

class Command(BaseCommand):
    help = "Importa fichas de pacientes desde un archivo Excel"

    def add_arguments(self, parser):
        parser.add_argument("excel_path", type=str, help="Ruta al .xlsx")
        parser.add_argument("--sheet", default="FUID 2021 ", help="Nombre o índice de la hoja")

    @transaction.atomic
    def handle(self, *args, **opts):
        path = opts["excel_path"]
        hoja = opts["sheet"]

        # ---------- leer y renombrar columnas ----------
        try:
            df = pd.read_excel(path, sheet_name=hoja, header=0)
        except Exception as e:
            raise CommandError(f"No se pudo leer el archivo: {e}")

        df = df.rename(columns=lambda c: COL_MAP.get(c, c))
        if "nombre_completo" not in df.columns:
            raise CommandError("Cabeceras inesperadas: verifica el Excel.")

        df = df[df["nombre_completo"].notna()]  # elimina filas vacías

        # ids existentes para auto-incrementar historia clínica
        siguiente_hist = (FichaPaciente.objects
                          .aggregate(m=Max("Numero_historia_clinica"))
                          .get("m") or 0) + 1

        # objetos fijos
        doc_cedula = TipoDocumento.objects.get(pk=ID_DOC["CEDULA"])
        doc_pasaporte = TipoDocumento.objects.get(pk=ID_DOC["PASAPORTE"])
        nac_col = Nacionalidad.objects.get(pk=1)
        nac_ven = Nacionalidad.objects.get(pk=2)
        nac_ecu = Nacionalidad.objects.get(pk=3)

        resumen = {"creados": 0, "actualizados": 0, "errores": 0}

        for _, row in df.iterrows():
            try:
                # --- nombre y sexo ---
                n1, n2, a1, a2 = split_nombre(row["nombre_completo"])
                sexo = infer_sexo(n1)

                # --- documento, nacionalidad, tipo doc ---
                pref, numeros = clean_num(row.get("num_identificacion"))
                if pref.startswith("VEN"):
                    nacionalidad = nac_ven
                    tipo_doc = doc_pasaporte
                elif pref.startswith("ECU"):
                    nacionalidad = nac_ecu
                    tipo_doc = doc_pasaporte
                else:
                    nacionalidad = nac_col
                    tipo_doc = doc_cedula

                num_id = numeros or None

                # --- fechas ---
                f_visita = safe_date(row.get("fecha_visita"))
                f_ultimo = safe_date(row.get("fecha_ultimo"))
                ano_reg = f_visita.year if f_visita else None

                # --- historia clínica única ---
                nhc = siguiente_hist
                siguiente_hist += 1

                obj, created = FichaPaciente.objects.update_or_create(
                    num_identificacion=num_id,
                    defaults=dict(
                        primer_nombre=n1,
                        segundo_nombre=n2,
                        primer_apellido=a1,
                        segundo_apellido=a2,
                        tipo_identificacion=tipo_doc,
                        Numero_historia_clinica=nhc,
                        caja=row.get("caja") or "",
                        carpeta=row.get("carpeta") or "",
                        sexo=sexo,
                        activo=True,
                        estado_de_migracion=False,
                        Fecha_de_visita_de_la_tarjeta=f_visita,
                        ultimo_registro_de_visita_en_la_base_de_datos=f_ultimo,
                        año_de_registro=ano_reg,
                        nacionalidad=nacionalidad,
                    )
                )
                resumen["creados" if created else "actualizados"] += 1
            except Exception as e:
                resumen["errores"] += 1
                self.stderr.write(f"Fila {_+2}: {e}")  # +2 por índice base-0 + cabecera

        self.stdout.write(self.style.SUCCESS(f"Importación terminada: {resumen}"))
