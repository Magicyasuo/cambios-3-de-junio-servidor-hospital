from django import forms
from .models import RegistroDeArchivo, SerieDocumental, SubserieDocumental
from django.utils.timezone import now
from django.forms import DateInput
from django import forms
from .models import FUID, RegistroDeArchivo
from django.utils.timezone import now, timedelta
from django.contrib.auth.models import User  # IMPORTAR User
# from .forms import FichaPacienteForm



from django import forms
from django.utils.timezone import now
from .models import RegistroDeArchivo, SubserieDocumental

from django import forms
from django.utils.timezone import now
from django.core.exceptions import ValidationError

# documentos/forms.py

from django import forms
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from .models import RegistroDeArchivo, SubserieDocumental
from .models import Documento  # si necesitas usarlo en este archivo
from django.conf import settings

# Tu validador de tamaño
def validate_file_size(value):
    max_size = 10 * 1024 * 1024  # 10 MB
    if value.size > max_size:
        raise ValidationError("El archivo no puede superar los 10 MB.")

class RegistroDeArchivoForm(forms.ModelForm):
    # Aplica el validador al campo archivo
    archivo = forms.FileField(
        required=False,
        help_text="Sube un documento (máx 10 MB).",
        validators=[validate_file_size]
    )

    fecha_archivo = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'type': 'date', 'class': 'form-control'}
        ),
        input_formats=['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']
    )

    fecha_inicial = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'type': 'date', 'class': 'form-control'}
        ),
        input_formats=['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']
    )

    fecha_final = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'type': 'date', 'class': 'form-control'}
        ),
        input_formats=['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']
    )

    class Meta:
        model = RegistroDeArchivo
        exclude = ['creado_por', 'numero_orden']
        widgets = {
            'Estado_archivo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tamano_documentos_electronicos': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Evitar que 'ubicacion' sea requerida
        self.fields['ubicacion'].required = False

        # Asignar fecha_archivo por defecto en el formulario
        if not self.instance.pk:
            self.fields['fecha_archivo'].initial = now().date()

        # Configuración dinámica de subseries
        if 'codigo_serie' in self.data:
            try:
                serie_id = int(self.data.get('codigo_serie'))
                self.fields['codigo_subserie'].queryset = SubserieDocumental.objects.filter(serie_id=serie_id)
            except (ValueError, TypeError):
                self.fields['codigo_subserie'].queryset = SubserieDocumental.objects.none()
        elif self.instance.pk and self.instance.codigo_serie:
            self.fields['codigo_subserie'].queryset = SubserieDocumental.objects.filter(serie_id=self.instance.codigo_serie.id)
        else:
            self.fields['codigo_subserie'].queryset = SubserieDocumental.objects.none()

    def clean(self):
        cleaned_data = super().clean()

        # Si fecha_archivo está vacío, asignar la fecha actual
        if not cleaned_data.get('fecha_archivo'):
            cleaned_data['fecha_archivo'] = now().date()

        # Soporte Físico
        if not cleaned_data.get('soporte_fisico'):
            cleaned_data['caja'] = 0
            cleaned_data['carpeta'] = 0
            cleaned_data['tomo_legajo_libro'] = "N/A"
            cleaned_data['numero_folios'] = 0
            cleaned_data['tipo'] = "N/A"
            cleaned_data['cantidad'] = 0

        # Soporte Electrónico
        if not cleaned_data.get('soporte_electronico'):
            cleaned_data['ubicacion'] = "N/A"
            cleaned_data['cantidad_documentos_electronicos'] = 0
            cleaned_data['tamano_documentos_electronicos'] = "N/A"

        return cleaned_data




class FUIDForm(forms.ModelForm):
    # Campos y configuración del formulario
    usuario = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label="Filtrar por Usuario",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    fecha_inicio = forms.DateField(
        required=False,
        label="Fecha Inicio",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    fecha_fin = forms.DateField(
        required=False,
        label="Fecha Fin",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    # registros = forms.ModelMultipleChoiceField(
    #     queryset=RegistroDeArchivo.objects.none(),  
    #     widget=forms.CheckboxSelectMultiple,
    #     required=False,
    #     label="Registros Asociados"
    # )

    elaborado_por_nombre = forms.CharField(
        required=False,
        max_length=255,
        label="Elaborado Por (Nombre)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    elaborado_por_cargo = forms.CharField(
        required=False,
        max_length=255,
        label="Elaborado Por (Cargo)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    elaborado_por_lugar = forms.CharField(
        required=False,
        max_length=255,
        label="Elaborado Por (Lugar)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    elaborado_por_fecha = forms.DateField(
        required=False,
        label="Elaborado Por (Fecha)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    entregado_por_nombre = forms.CharField(
        required=False,
        max_length=255,
        label="Entregado Por (Nombre)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    entregado_por_cargo = forms.CharField(
        required=False,
        max_length=255,
        label="Entregado Por (Cargo)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    entregado_por_lugar = forms.CharField(
        required=False,
        max_length=255,
        label="Entregado Por (Lugar)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    entregado_por_fecha = forms.DateField(
        required=False,
        label="Entregado Por (Fecha)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    recibido_por_nombre = forms.CharField(
        required=False,
        max_length=255,
        label="Recibido Por (Nombre)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    recibido_por_cargo = forms.CharField(
        required=False,
        max_length=255,
        label="Recibido Por (Cargo)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    recibido_por_lugar = forms.CharField(
        required=False,
        max_length=255,
        label="Recibido Por (Lugar)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    recibido_por_fecha = forms.DateField(
        required=False,
        label="Recibido Por (Fecha)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = FUID
        fields = [
            'entidad_productora', 'unidad_administrativa', 'oficina_productora', 'objeto', 'notas',
            'registros',
            'elaborado_por_nombre', 'elaborado_por_cargo', 'elaborado_por_lugar', 'elaborado_por_fecha',
            'entregado_por_nombre', 'entregado_por_cargo', 'entregado_por_lugar', 'entregado_por_fecha',
            'recibido_por_nombre', 'recibido_por_cargo', 'recibido_por_lugar', 'recibido_por_fecha'
        ]
        widgets = {
            'entidad_productora': forms.Select(attrs={'class': 'form-select'}),
            'unidad_administrativa': forms.Select(attrs={'class': 'form-select'}),
            'oficina_productora': forms.Select(attrs={'class': 'form-select'}),
            'objeto': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Usuario autenticado
        # No es necesario asignar self.instance aquí, ModelForm ya lo hace
        super().__init__(*args, **kwargs)

        # # Configura el queryset de registros
        # if self.instance and self.instance.pk:
        #     registros_actuales = self.instance.registros.all()
        #     registros_disponibles = RegistroDeArchivo.objects.filter(fuids__isnull=True)
        #     self.fields['registros'].queryset = registros_actuales | registros_disponibles
        # else:
        #     self.fields['registros'].queryset = RegistroDeArchivo.objects.filter(fuids__isnull=True)
  
from django import forms
from .models import FichaPaciente
from django import forms
from .models import FichaPaciente, TipoDocumento


from django import forms
from .models import FichaPaciente

# ---- Paso 0: Selección de Ubicación Física ------------------------------
class UbicacionFisicaForm(forms.Form):
    """Se rellena 1 vez por sesión; guarda los valores en `request.session`.
       Deje en blanco los campos que no desee prefijar."""
    gabeta   = forms.IntegerField(required=False, min_value=1, label="Gabeta")
    caja     = forms.CharField(required=False, max_length=20, label="Caja")
    carpeta  = forms.CharField(required=False, max_length=20, label="Carpeta")

# ---- Paso 1: Búsqueda Rápida --------------------------------------------
class BuscaFichaForm(forms.Form):
    """El funcionario introduce un ID o historia clínica para ver si ya existe."""
    num_identificacion = forms.CharField(max_length=50, required=False, label="Número de Identificación")
    numero_historia_clinica = forms.IntegerField(required=False, label="Número de Historia Clínica")

    def clean(self):
        cd = super().clean()
        if not cd.get("num_identificacion") and not cd.get("numero_historia_clinica"):
            raise forms.ValidationError("Ingresa un número de identificación o de historia clínica.")
        return cd

# ---- Paso 2: Alta / Edición de la Ficha ---------------------------------
from django import forms
from django.core.exceptions import ValidationError
from .models import FichaPaciente

from django import forms
from django.core.exceptions import ValidationError
from .models import FichaPaciente

from django.core.exceptions import ValidationError

class FichaPacienteForm(forms.ModelForm):
    class Meta:
        model = FichaPaciente
        fields = [
            'primer_apellido', 'segundo_apellido', 'primer_nombre', 'segundo_nombre', 
            'num_identificacion', 'tipo_identificacion', 'num_identificacion_secundario',
            'tipo_identificacion_secundario',
            'primer_apellido_padre', 'segundo_apellido_padre',
            'primer_nombre_padre', 'segundo_nombre_padre',          
            'Numero_historia_clinica', 'caja', 'carpeta', 'gabeta',
            'sexo', 'activo', 'estado_de_migracion', 'nacionalidad',
            'Fecha_de_visita_de_la_tarjeta', 'fecha_nacimiento', 
            # 'año_de_registro'
        ]
        widgets = {
            'Fecha_de_visita_de_la_tarjeta': forms.DateInput(attrs={'type': 'date', 'placeholder': 'Fecha del primer ingreso'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'año_de_visita_segun_Fuid': forms.DateInput(attrs={'type': 'date'}),
            'ultimo_registro_de_visita': forms.DateInput(attrs={'type': 'date'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'estado_de_migracion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'nacionalidad': forms.Select(attrs={'class': 'custom-select'}),
            'sexo': forms.Select(choices=[
                ('Masculino', 'Masculino'),
                ('Femenino', 'Femenino'),
                ('Otro', 'Otro'),
            ], attrs={'class': 'custom-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                css = 'form-control'
                if self.errors.get(field_name):
                    css += ' is-invalid'
                field.widget.attrs.update({'class': css})

    def clean(self):
        cleaned_data = super().clean()
        num_identificacion_secundario = cleaned_data.get('num_identificacion_secundario')
        tipo_identificacion_secundario = cleaned_data.get('tipo_identificacion_secundario')
        num_identificacion = cleaned_data.get('num_identificacion')
        tipo_identificacion = cleaned_data.get('tipo_identificacion')

        # Validación secundaria
        if num_identificacion_secundario and tipo_identificacion_secundario:
            existe = FichaPaciente.objects.filter(
                num_identificacion_secundario=num_identificacion_secundario,
                tipo_identificacion_secundario=tipo_identificacion_secundario
            )
            if self.instance.pk:
                existe = existe.exclude(pk=self.instance.pk)
            if existe.exists():
                raise ValidationError("Ya existe un registro con esta identificación secundaria.")

        # Validación primaria
        if num_identificacion and tipo_identificacion:
            existe = FichaPaciente.objects.filter(
                num_identificacion=num_identificacion,
                tipo_identificacion=tipo_identificacion
            )
            if self.instance.pk:
                existe = existe.exclude(pk=self.instance.pk)
            if existe.exists():
                raise ValidationError("Ya existe un registro con esta identificación principal.")

        return cleaned_data

