# usuarios/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re
from .fields import CurrencyField
from .widgets import CurrencyInput
from .models import Interesado, Reclutador, Secretaria, Vacante, RequisitoVacante, Curriculum, ExperienciaLaboral, Educacion, HabilidadInteresado, IdiomaInteresado, Categoria
Usuario = get_user_model()

class LoginForm(AuthenticationForm):
    """Formulario para inicio de sesión."""

    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su correo electrónico'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su contraseña'})
    )


class InteresadoRegistroForm(UserCreationForm):
    """Formulario para registro de interesados."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su correo electrónico'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su contraseña'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirme su contraseña'})
    )
    class Meta:
        model = Usuario
        fields = ('email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.rol = 'interesado'
        if commit:
            user.save()
            # Crear el perfil de interesado con campos básicos vacíos
            Interesado.objects.get_or_create(
                usuario=user,
                defaults={
                    'nombre': '',
                    'apellido_paterno': '',
                    'apellido_materno': ''
                }
            )
        return user
#Creacion de clases para recuperacion de contraseña de perfil interesado
class RecuperarContrasenaForm(forms.Form):
    """
    Formulario para solicitar recuperación de contraseña.
    """
    email = forms.EmailField(
        label='Correo Electrónico',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu@email.com',
            'autocomplete': 'email'
        }),
        help_text='Ingresa el correo electrónico asociado a tu cuenta.'
    )

    def clean_email(self):
        """
        Valida que el email exista en el sistema.
        """
        email = self.cleaned_data.get('email')
        
        if not email:
            return email
            
        # Normalizar email
        email = email.lower().strip()
        
        try:
            # Verificar que el usuario existe
            user = Usuario.objects.get(email=email)
            
            # Verificar que el email esté verificado
            if not user.email_verified:
                raise ValidationError(
                    'Tu correo electrónico no ha sido verificado. '
                    'Primero debes verificar tu cuenta antes de poder recuperar la contraseña.'
                )
                
            # Verificar que la cuenta esté activa
            if not user.is_active:
                raise ValidationError(
                    'Tu cuenta está desactivada. Contacta al administrador.'
                )
                
            # Verificar límite de intentos
            if not user.can_request_password_reset():
                attempts_remaining = user.get_remaining_reset_attempts()
                if attempts_remaining == 0:
                    raise ValidationError(
                        'Has excedido el límite de intentos de recuperación de contraseña. '
                        'Intenta nuevamente en 24 horas.'
                    )
                else:
                    raise ValidationError(
                        f'Has realizado demasiados intentos. '
                        f'Te quedan {attempts_remaining} intentos antes de ser bloqueado por 24 horas.'
                    )
                    
        except Usuario.DoesNotExist:
            # Por seguridad, no revelar si el email existe o no
            # Pero internamente lo manejamos
            pass
            
        return email

    def get_user(self):
        """
        Retorna el usuario asociado al email si existe.
        """
        email = self.cleaned_data.get('email')
        if email:
            try:
                return Usuario.objects.get(email=email.lower().strip())
            except Usuario.DoesNotExist:
                return None
        return None


class RestablecerContrasenaForm(SetPasswordForm):
    """
    Formulario para restablecer contraseña con validaciones mejoradas.
    Extiende el SetPasswordForm de Django pero con validaciones personalizadas.
    """
    
    # Lista de contraseñas comunes
    COMMON_PASSWORDS = [
        '123456', 'password', '123456789', '12345678', '12345', '1234567',
        '1234567890', 'qwerty', 'abc123', 'password123', 'admin', 'letmein',
        '123123', 'welcome', 'monkey', '1234', 'password1', '123', 'qwerty123',
        'football', 'iloveyou', 'princess', 'dragon', 'baseball', 'sunshine',
        'superman', 'trustno1', 'starwars', 'whatever', '1qaz2wsx', 'shadow'
    ]

    new_password1 = forms.CharField(
        label='Nueva Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu nueva contraseña',
            'autocomplete': 'new-password',
            'id': 'id_new_password1'
        }),
        help_text='Tu contraseña debe ser segura y cumplir todos los requisitos.'
    )
    
    new_password2 = forms.CharField(
        label='Confirmar Nueva Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirma tu nueva contraseña',
            'autocomplete': 'new-password',
            'id': 'id_new_password2'
        }),
        help_text='Ingresa la misma contraseña para confirmar.'
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.user = user

    def clean_new_password1(self):
        """
        Validaciones personalizadas para la nueva contraseña.
        """
        password = self.cleaned_data.get('new_password1')
        
        if not password:
            return password

        # Validación de longitud mínima
        if len(password) < 8:
            raise ValidationError(
                'La contraseña debe tener al menos 8 caracteres.'
            )

        # Validación de longitud máxima
        if len(password) > 128:
            raise ValidationError(
                'La contraseña no puede tener más de 128 caracteres.'
            )

        # ✅ NUEVA VALIDACIÓN: La contraseña debe ser diferente a la actual
        if self.user and self.user.check_password(password):
            raise ValidationError(
                'La nueva contraseña debe ser diferente a tu contraseña actual. '
                'Por seguridad, elige una contraseña completamente nueva.'
            )

        # Validación contra contraseñas comunes
        if password.lower() in self.COMMON_PASSWORDS:
            raise ValidationError(
                'Esta contraseña es demasiado común. Elige una contraseña más única.'
            )

        # Validación de contraseña completamente numérica
        if password.isdigit():
            raise ValidationError(
                'La contraseña no puede ser completamente numérica.'
            )

        # Validación de similitud con información personal
        if self.user:
            user_info = [
                self.user.email.split('@')[0].lower(),
                self.user.first_name.lower() if self.user.first_name else '',
                self.user.last_name.lower() if self.user.last_name else '',
            ]
            
            for info in user_info:
                if info and len(info) > 2 and info in password.lower():
                    raise ValidationError(
                        'La contraseña no puede contener información personal.'
                    )

        # Validación de complejidad básica (al menos 2 tipos de caracteres)
        char_types = 0
        if re.search(r'[a-z]', password):
            char_types += 1
        if re.search(r'[A-Z]', password):
            char_types += 1
        if re.search(r'\d', password):
            char_types += 1
        if re.search(r'[^A-Za-z0-9]', password):
            char_types += 1

        if char_types < 2:
            raise ValidationError(
                'La contraseña debe contener al menos dos tipos de caracteres diferentes '
                '(letras minúsculas, mayúsculas, números o símbolos).'
            )

        return password

    def clean_new_password2(self):
        """
        Valida que las contraseñas coincidan.
        """
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError('Las contraseñas no coinciden.')
        
        return password2

    def save(self, commit=True):
        """
        Guarda la nueva contraseña y limpia los tokens de recuperación.
        """
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        
        # Limpiar tokens de recuperación
        self.user.clear_password_reset_tokens()
        
        if commit:
            self.user.save()
        return self.user


class ReenviarRecuperacionForm(forms.Form):
    """
    Formulario para reenviar el correo de recuperación.
    """
    email = forms.EmailField(
        widget=forms.HiddenInput()
    )

    def clean_email(self):
        """
        Valida que el email sea válido para reenvío.
        """
        email = self.cleaned_data.get('email')
        
        if not email:
            raise ValidationError('Email requerido.')
            
        try:
            user = Usuario.objects.get(email=email.lower().strip())
            
            # Verificar que puede solicitar recuperación
            if not user.can_request_password_reset():
                raise ValidationError(
                    'Has excedido el límite de intentos. Espera 24 horas antes de intentar nuevamente.'
                )
                
        except Usuario.DoesNotExist:
            raise ValidationError('Email no encontrado.')
            
        return email

    def get_user(self):
        """
        Retorna el usuario asociado al email.
        """
        email = self.cleaned_data.get('email')
        if email:
            try:
                return Usuario.objects.get(email=email.lower().strip())
            except Usuario.DoesNotExist:
                return None
        return None
#FIN recuperacion de contraseña
class CurriculumForm(forms.ModelForm):
    """Formulario para la información básica del CV."""

    class Meta:
        model = Curriculum
        fields = ['resumen_profesional']
        widgets = {
            'resumen_profesional': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                # 'placeholder': 'Ej: Profesional con 5 años de experiencia en desarrollo web...'
            })
        }

# usuarios/forms.py - FORMULARIO ACTUALIZADO PARA INTERESADO
# usuarios/forms.py - InteresadoPerfilForm actualizado

class InteresadoPerfilForm(forms.ModelForm):
    """Formulario para editar la información personal del interesado."""

    class Meta:
        model = Interesado
        fields = [
            'nombre', 'apellido_paterno', 'apellido_materno', 'telefono',
            'fecha_nacimiento', 'municipio', 'codigo_postal'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese su nombre'
            }),
            'apellido_paterno': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese su apellido paterno'
            }),
            'apellido_materno': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese su apellido materno'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 55 1234 5678'
            }),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'municipio': forms.Select(attrs={
                'class': 'form-select'
            }),
            'codigo_postal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 50000'
            })
        }
        labels = {
            'nombre': 'Nombre(s)',
            'apellido_paterno': 'Apellido Paterno',
            'apellido_materno': 'Apellido Materno (opcional)',
            'telefono': 'Teléfono',
            'fecha_nacimiento': 'Fecha de Nacimiento',
            'municipio': 'Municipio del Estado de México',
            'codigo_postal': 'Código Postal'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar opción vacía al select de municipio
        municipio_choices = [('', 'Selecciona un municipio...')] + list(self.fields['municipio'].choices)
        self.fields['municipio'].choices = municipio_choices

class ExperienciaLaboralForm(forms.ModelForm):
    """Formulario para experiencias laborales."""

    class Meta:
        model = ExperienciaLaboral
        fields = ['empresa', 'puesto', 'descripcion', 'fecha_inicio', 'fecha_fin', 'actual']
        widgets = {
            'empresa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Tecnologías Acme S.A. de C.V.'
            }),
            'puesto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Desarrollador Web'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe tus actividades principales...'
            }),
            # CAMBIAR ESTOS DOS WIDGETS:
            'fecha_inicio': forms.DateInput(attrs={
                'class': 'form-control date-picker',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'fecha_fin': forms.DateInput(attrs={
                'class': 'form-control date-picker',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'actual': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'empresa': 'Empresa',
            'puesto': 'Puesto / Cargo',
            'descripcion': 'Funciones y Responsabilidades',
            'fecha_inicio': 'Fecha de Inicio',
            'fecha_fin': 'Fecha de Fin',
            'actual': 'Trabajo actual'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar formato de fecha para input
        self.fields['fecha_inicio'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_fin'].input_formats = ['%Y-%m-%d']


class EducacionForm(forms.ModelForm):
    """Formulario para educación."""

    class Meta:
        model = Educacion
        fields = ['titulo', 'institucion', 'fecha_inicio', 'fecha_fin', 'descripcion']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Ingeniería en Sistemas'
            }),
            'institucion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Universidad Nacional'
            }),
            # CAMBIAR ESTOS DOS WIDGETS:
            'fecha_inicio': forms.DateInput(attrs={
                'class': 'form-control date-picker',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'fecha_fin': forms.DateInput(attrs={
                'class': 'form-control date-picker',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción adicional (opcional)'
            })
        }
        labels = {
            'titulo': 'Título Obtenido / Nivel',
            'institucion': 'Institución Educativa',
            'fecha_inicio': 'Fecha de Inicio',
            'fecha_fin': 'Fecha de Fin',
            'descripcion': 'Descripción'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar formato de fecha para input
        self.fields['fecha_inicio'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_fin'].input_formats = ['%Y-%m-%d']

class HabilidadInteresadoForm(forms.ModelForm):
    """Formulario para habilidades del interesado."""

    nombre_habilidad = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: JavaScript, Liderazgo'
        }),
        label='Habilidad'
    )

    class Meta:
        model = HabilidadInteresado
        fields = ['nivel']
        widgets = {
            'nivel': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'nivel': 'Nivel de Dominio'
        }


class IdiomaInteresadoForm(forms.ModelForm):
    """Formulario para idiomas del interesado."""

    class Meta:
        model = IdiomaInteresado
        fields = ['idioma', 'nivel_lectura', 'nivel_escritura', 'nivel_conversacion']
        widgets = {
            'idioma': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Inglés'
            }),
            'nivel_lectura': forms.Select(attrs={
                'class': 'form-select'
            }),
            'nivel_escritura': forms.Select(attrs={
                'class': 'form-select'
            }),
            'nivel_conversacion': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'idioma': 'Idioma',
            'nivel_lectura': 'Nivel de Lectura',
            'nivel_escritura': 'Nivel de Escritura',
            'nivel_conversacion': 'Nivel de Conversación'
        }


class SecretariaRegistroForm(forms.ModelForm):
    """Formulario para registro de secretarías."""

    class Meta:
        model = Secretaria
        fields = ('rfc', 'descripcion', 'sitio_web', 'direccion')  # Removido 'nombre'
        widgets = {
            'rfc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese un RFC valido'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': ''}),
            'sitio_web': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.example.com'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Ej.  Av. Dr. Gustavo Baz 2160, La Loma, 54060 Tlalnepantla, Méx.'})
        }

    def save(self, commit=True):
        secretaria = super().save(commit=False)
        # Forzar el nombre de la secretaría
        secretaria.nombre = 'Secretaría de Movilidad'
        if commit:
            secretaria.save()
        return secretaria
# usuarios/forms.py - Formulario actualizado

class ReclutadorRegistroForm(UserCreationForm):
    """Formulario para registro de reclutadores - SIN gestión de secretaría."""

    nombre = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''})
    )
    apellido_paterno = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''})
    )
    apellido_materno = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''})
    )
    cargo = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''})
    )
    telefono = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': ''})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': ''})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': ''})
    )

    class Meta:
        model = Usuario
        fields = ('email', 'password1', 'password2')

    def save(self, commit=True):
        """Guarda el usuario - La secretaría se asigna en la vista."""
        user = super().save(commit=False)
        user.rol = 'reclutador'
        if commit:
            user.save()
        return user


# usuarios/forms.py - Formulario VacanteForm actualizado con validaciones de salario
# usuarios/forms.py - VacanteForm actualizado con manejo correcto de fechas

class VacanteForm(forms.ModelForm):
    """Formulario para crear/editar vacantes con validaciones de salario y fechas mejoradas."""

    def clean_salario_min(self):
        """Validar salario mínimo."""
        valor = self.cleaned_data.get('salario_min')

        if valor is not None:
            # Limpiar formato si viene como string
            if isinstance(valor, str):
                valor_str = str(valor).replace(',', '').replace('$', '').strip()
                try:
                    valor = float(valor_str)
                except ValueError:
                    raise forms.ValidationError('Ingresa un valor numérico válido.')

            # ✅ VALIDACIÓN: No puede ser cero o negativo
            if valor <= 0:
                raise forms.ValidationError('El salario mínimo debe ser mayor a $0.')

            # ✅ VALIDACIÓN: Límite máximo razonable (10 millones)
            if valor > 10000000:
                raise forms.ValidationError('El salario ingresado es demasiado alto (máximo $10,000,000).')

        return valor

    def clean_salario_max(self):
        """Validar salario máximo."""
        valor = self.cleaned_data.get('salario_max')

        if valor is not None:
            # Limpiar formato si viene como string
            if isinstance(valor, str):
                valor_str = str(valor).replace(',', '').replace('$', '').strip()
                try:
                    valor = float(valor_str)
                except ValueError:
                    raise forms.ValidationError('Ingresa un valor numérico válido.')

            # ✅ VALIDACIÓN: No puede ser cero o negativo
            if valor <= 0:
                raise forms.ValidationError('El salario máximo debe ser mayor a $0.')

            # ✅ VALIDACIÓN: Límite máximo razonable (10 millones)
            if valor > 10000000:
                raise forms.ValidationError('El salario ingresado es demasiado alto (máximo $10,000,000).')

        return valor

    # def clean_fecha_limite(self):
    #     """Validar fecha límite de postulación."""
    #     fecha_limite = self.cleaned_data.get('fecha_limite')
        
    #     if fecha_limite:
    #         from datetime import date
    #         if fecha_limite <= date.today():
    #             raise forms.ValidationError('La fecha límite debe ser posterior a la fecha actual.')
        
    #     return fecha_limite

    # def clean_fecha_inicio_estimada(self):
    #     """Validar fecha de inicio estimada."""
    #     fecha_inicio = self.cleaned_data.get('fecha_inicio_estimada')
        
    #     if fecha_inicio:
    #         from datetime import date
    #         if fecha_inicio <= date.today():
    #             raise forms.ValidationError('La fecha de inicio debe ser futura.')
        
    #     return fecha_inicio

    class Meta:
        model = Vacante
        fields = [
            'titulo', 'categoria', 'tipo_empleo', 'descripcion',
            'municipio', 'salario_min', 'salario_max', 'detalles_salario',
            'fecha_inicio_estimada', 'fecha_limite', 'max_postulantes', 'modalidad'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': ''
            }),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'tipo_empleo': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                # 'placeholder': 'Describe las funciones, responsabilidades, el equipo de trabajo, la cultura de la empresa, etc.'
            }),
            'municipio': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Selecciona un municipio...'
            }),
            # ✅ WIDGETS ACTUALIZADOS PARA SALARIOS
            'salario_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '25000.00',
                'min': '1',
                'step': '0.01'
            }),
            'salario_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '35000.00',
                'min': '1',
                'step': '0.01'
            }),
            'detalles_salario': forms.TextInput(attrs={
                'class': 'form-control',
                # 'placeholder': 'Ej: A tratar, Según aptitudes, Más bonos'
            }),
            # ✅ WIDGETS CORREGIDOS PARA FECHAS
            'fecha_inicio_estimada': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_limite': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'max_postulantes': forms.Select(attrs={'class': 'form-select'}),
            'modalidad': forms.Select(attrs={'class': 'form-select'}),
        }

        labels = {
            'titulo': 'Título de la Vacante',
            'categoria': 'Categoría de la Vacante',
            'tipo_empleo': 'Tipo de Empleo',
            'descripcion': 'Descripción Detallada de la Vacante',
            'municipio': 'Municipio',
            'salario_min': 'Salario Mínimo (MXN)',
            'salario_max': 'Salario Máximo (MXN)',
            # 'detalles_salario': 'Detalles Adicionales del Salario',
            'fecha_inicio_estimada': 'Fecha de Inicio de labores',
            'fecha_limite': 'Fecha Límite para Postularse',
            'max_postulantes': 'Núm Máx de Postulantes',
            'modalidad': 'Modalidad de Trabajo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Marcar campos obligatorios
        self.fields['titulo'].required = True
        self.fields['categoria'].required = True
        self.fields['tipo_empleo'].required = True
        self.fields['descripcion'].required = True
        self.fields['municipio'].required = True
        self.fields['fecha_limite'].required = True
        self.fields['max_postulantes'].required = True

        # ✅ HACER CAMPOS DE SALARIO OBLIGATORIOS
        self.fields['salario_min'].required = True
        self.fields['salario_max'].required = True

        # Configurar ayuda para campos de salario
        self.fields['salario_min'].help_text = 'Ingresa el salario mínimo. Debe ser mayor a $0. Ejemplo: 25000.00'
        self.fields['salario_max'].help_text = 'Ingresa el salario máximo. Debe ser mayor al mínimo. Ejemplo: 35000.00'

        # ✅ CONFIGURAR FORMATO DE FECHA CORRECTO
        # self.fields['fecha_limite'].help_text = 'Selecciona la fecha límite para recibir postulaciones'
        # self.fields['fecha_inicio_estimada'].help_text = 'Fecha estimada de inicio del trabajo (opcional)'
        
        # # Configurar input_formats para fechas
        # self.fields['fecha_limite'].input_formats = ['%Y-%m-%d']
        # self.fields['fecha_inicio_estimada'].input_formats = ['%Y-%m-%d']

        # Agregar opción vacía al select de municipio
        municipio_choices = [('', 'Selecciona un municipio...')] + list(self.fields['municipio'].choices)
        self.fields['municipio'].choices = municipio_choices

    def clean(self):
        """Validaciones adicionales que requieren comparar múltiples campos."""
        cleaned_data = super().clean()
        salario_min = cleaned_data.get('salario_min')
        salario_max = cleaned_data.get('salario_max')
        # fecha_limite = cleaned_data.get('fecha_limite')
        # fecha_inicio = cleaned_data.get('fecha_inicio_estimada')

        # ✅ VALIDACIÓN: El salario mínimo no puede ser mayor o igual al máximo
        if salario_min and salario_max:
            if salario_min >= salario_max:
                raise forms.ValidationError({
                    'salario_min': 'El salario mínimo debe ser menor al salario máximo.',
                    'salario_max': 'El salario máximo debe ser mayor al salario mínimo.'
                })

            # ✅ VALIDACIÓN ADICIONAL: Diferencia mínima razonable (al menos $1000)
            if (salario_max - salario_min) < 1000:
                raise forms.ValidationError({
                    'salario_max': 'La diferencia entre salario mínimo y máximo debe ser de al menos $1,000.'
                })

        # Validar que la fecha límite sea posterior a hoy
        fecha_limite = cleaned_data.get('fecha_limite')
        if fecha_limite:
            from datetime import date
            if fecha_limite <= date.today():
                raise forms.ValidationError({
                    'fecha_limite': 'La fecha límite debe ser posterior a la fecha actual.'
                })

        return cleaned_data


class RequisitoVacanteForm(forms.ModelForm):
    """Formulario para los requisitos de la vacante."""

    class Meta:
        model = RequisitoVacante
        fields = ['educacion_minima', 'experiencia_minima', 'descripcion_requisitos']
        widgets = {
            'educacion_minima': forms.TextInput(attrs={
                'class': 'form-control',
                # 'placeholder': 'Ej: Licenciatura en Informática (Titulado)'
            }),
            # WIDGET ACTUALIZADO: Ahora es un Select para elegir años
            'experiencia_minima': forms.Select(attrs={
                'class': 'form-select'
            }),
            'descripcion_requisitos': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                # 'placeholder': 'Ej: - Licenciatura en Informática (Titulado).\n- 3+ años de experiencia con Python/Django.\n- Conocimiento de bases de datos PostgreSQL.\n- Habilidades de comunicación efectiva.'
            }),
        }
        labels = {
            'educacion_minima': 'Educación Mínima (opcional)',
            'experiencia_minima': 'Años de Experiencia Mínima',
            'descripcion_requisitos': 'Requisitos (Educación, Experiencia, Habilidades)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descripcion_requisitos'].required = True

        # Agregar opción vacía al select de experiencia
        experiencia_choices = [('', 'Selecciona años de experiencia...')] + list(
            self.fields['experiencia_minima'].choices)
        self.fields['experiencia_minima'].choices = experiencia_choices

        # Configurar help_text personalizado
        self.fields[
            'experiencia_minima'].help_text = 'Selecciona los años mínimos de experiencia requeridos para el puesto.'