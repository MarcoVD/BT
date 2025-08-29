# usuarios/models.py
from django.db import models
from django.contrib.auth.models import User, AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.humanize.templatetags.humanize import intcomma # Para formatear con comas
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import secrets
import uuid


class UserManager(BaseUserManager):
    """Define una clase gestora de usuario para crear usuarios con email."""

    def create_user(self, email, password=None, **extra_fields):
        """Crea y guarda un usuario con el email y contraseña dados."""
        if not email:
            raise ValueError('Los usuarios deben tener una dirección de email')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Crea y guarda un superusuario con el email y contraseña dados."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', 'administrador')
        extra_fields.setdefault('email_verified', True)  # Los superusuarios están verificados por defecto

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superusuario debe tener is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractUser):
    """Modelo de usuario personalizado que utiliza email como nombre de usuario."""

    ROLES = (
        ('interesado', 'Interesado'),
        ('reclutador', 'Reclutador'),
        ('administrador', 'Administrador'),
    )

    username = None
    email = models.EmailField(_('email'), unique=True)
    rol = models.CharField(max_length=15, choices=ROLES, default='interesado')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ultimo_acceso = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    # Campos para verificación de email
    email_verified = models.BooleanField(
        default=False,
        help_text='Indica si el email ha sido verificado'
    )
    verification_token = models.UUIDField(
        blank=True,
        null=True,
        help_text='Token para verificación de email'
    )
    verification_token_expires = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Fecha de expiración del token'
    )
    
    #Recuperación de contraseña
    password_reset_token = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Token para recuperación de contraseña'
    )
    password_reset_token_expires = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Fecha de expiración del token de recuperación'
    )
    password_reset_attempts = models.IntegerField(
        default=0,
        help_text='Número de intentos de recuperación en las últimas 24 horas'
    )
    last_password_reset_attempt = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Fecha del último intento de recuperación'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
#Verificación de email
    def generate_verification_token(self):
        """Genera un nuevo token de verificación con expiración en 24 horas."""
        self.verification_token = uuid.uuid4()
        self.verification_token_expires = timezone.now() + timedelta(hours=24)
        self.save(update_fields=['verification_token', 'verification_token_expires'])

    def is_verification_token_valid(self, token):
        """Verifica si el token es válido y no ha expirado."""
        if not self.verification_token or not self.verification_token_expires:
            return False

        if str(self.verification_token) != str(token):
            return False

        if timezone.now() > self.verification_token_expires:
            return False

        return True

    def verify_email(self):
        """Marca el email como verificado y limpia el token."""
        self.email_verified = True
        self.verification_token = None
        self.verification_token_expires = None
        self.save(update_fields=['email_verified', 'verification_token', 'verification_token_expires'])
    def can_request_password_reset(self):
        """
        Verifica si el usuario puede solicitar recuperación de contraseña.
        Limita a 3 intentos por 24 horas.
        """
        now = timezone.now()
        
        # Si nunca ha intentado, puede hacerlo
        if not self.last_password_reset_attempt:
            return True
            
        # Si han pasado más de 24 horas, reiniciar contador
        if now - self.last_password_reset_attempt > timedelta(hours=24):
            self.password_reset_attempts = 0
            self.save(update_fields=['password_reset_attempts'])
            return True
            
        # Verificar límite de intentos
        return self.password_reset_attempts < 3

    def generate_password_reset_token(self):
        """
        Genera un token seguro para recuperación de contraseña.
        El token expira en 30 minutos.
        """
        # Verificar si puede solicitar
        if not self.can_request_password_reset():
            raise ValueError("Has excedido el límite de intentos de recuperación. Intenta en 24 horas.")
        
        # Generar token seguro
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_token_expires = timezone.now() + timedelta(minutes=30)
        
        # Actualizar contador de intentos
        now = timezone.now()
        if (not self.last_password_reset_attempt or 
            now - self.last_password_reset_attempt > timedelta(hours=24)):
            self.password_reset_attempts = 1
        else:
            self.password_reset_attempts += 1
            
        self.last_password_reset_attempt = now
        
        self.save(update_fields=[
            'password_reset_token', 
            'password_reset_token_expires',
            'password_reset_attempts',
            'last_password_reset_attempt'
        ])

    def is_password_reset_token_valid(self, token):
        """
        Verifica si el token de recuperación es válido y no ha expirado.
        """
        if not self.password_reset_token or not self.password_reset_token_expires:
            return False

        if self.password_reset_token != token:
            return False

        if timezone.now() > self.password_reset_token_expires:
            return False

        return True

    def reset_password_with_token(self, token, new_password):
        """
        Restablece la contraseña usando el token.
        Invalida el token después del uso.
        """
        if not self.is_password_reset_token_valid(token):
            raise ValueError("Token de recuperación inválido o expirado.")
        
        # Cambiar la contraseña
        self.set_password(new_password)
        
        # Limpiar tokens de recuperación
        self.clear_password_reset_tokens()
        
        # Guardar cambios
        self.save()

    def clear_password_reset_tokens(self):
        """
        Limpia todos los tokens de recuperación de contraseña.
        Se llama después de un restablecimiento exitoso o por seguridad.
        """
        self.password_reset_token = None
        self.password_reset_token_expires = None
        self.save(update_fields=['password_reset_token', 'password_reset_token_expires'])

    def get_remaining_reset_attempts(self):
        """
        Retorna el número de intentos de recuperación restantes.
        """
        if not self.last_password_reset_attempt:
            return 3
            
        # Si han pasado más de 24 horas, reiniciar
        if timezone.now() - self.last_password_reset_attempt > timedelta(hours=24):
            return 3
            
        return max(0, 3 - self.password_reset_attempts)
    
    @property
    def can_login(self):
        """Determina si el usuario puede iniciar sesión."""
        # Los administradores pueden iniciar sesión sin verificación
        if self.rol == 'administrador' or self.is_superuser:
            return True

        # Los demás usuarios necesitan verificar su email
        return self.email_verified

class Interesado(models.Model):
    """Modelo para el perfil de un interesado/candidato."""

    # Municipios del Estado de México (misma lista que en Vacante)
    MUNICIPIOS_ESTADO_MEXICO = (
        ('acambay', 'Acambay'),
        ('acolman', 'Acolman'),
        ('aculco', 'Aculco'),
        ('almoloya_de_alquisiras', 'Almoloya de Alquisiras'),
        ('almoloya_de_juarez', 'Almoloya de Juárez'),
        ('almoloya_del_rio', 'Almoloya del Río'),
        ('amanalco', 'Amanalco'),
        ('amatepec', 'Amatepec'),
        ('amecameca', 'Amecameca'),
        ('apaxco', 'Apaxco'),
        ('atenco', 'Atenco'),
        ('atizapan', 'Atizapán'),
        ('atizapan_de_zaragoza', 'Atizapán de Zaragoza'),
        ('atlacomulco', 'Atlacomulco'),
        ('atlautla', 'Atlautla'),
        ('axapusco', 'Axapusco'),
        ('ayapango', 'Ayapango'),
        ('calimaya', 'Calimaya'),
        ('capulhuac', 'Capulhuac'),
        ('coacalco_de_berriozabal', 'Coacalco de Berriozábal'),
        ('coatepec_harinas', 'Coatepec Harinas'),
        ('cocotitlan', 'Cocotitlán'),
        ('coyotepec', 'Coyotepec'),
        ('cuautitlan', 'Cuautitlán'),
        ('cuautitlan_izcalli', 'Cuautitlán Izcalli'),
        ('donato_guerra', 'Donato Guerra'),
        ('ecatepec_de_morelos', 'Ecatepec de Morelos'),
        ('ecatzingo', 'Ecatzingo'),
        ('el_oro', 'El Oro'),
        ('huehuetoca', 'Huehuetoca'),
        ('hueypoxtla', 'Hueypoxtla'),
        ('huixquilucan', 'Huixquilucan'),
        ('isidro_fabela', 'Isidro Fabela'),
        ('ixtapaluca', 'Ixtapaluca'),
        ('ixtapan_de_la_sal', 'Ixtapan de la Sal'),
        ('ixtapan_del_oro', 'Ixtapan del Oro'),
        ('ixtlahuaca', 'Ixtlahuaca'),
        ('jaltenco', 'Jaltenco'),
        ('jilotepec', 'Jilotepec'),
        ('jilotzingo', 'Jilotzingo'),
        ('jiquipilco', 'Jiquipilco'),
        ('jocotitlan', 'Jocotitlán'),
        ('joquicingo', 'Joquicingo'),
        ('juchitepec', 'Juchitepec'),
        ('la_paz', 'La Paz'),
        ('lerma', 'Lerma'),
        ('luvianos', 'Luvianos'),
        ('malinalco', 'Malinalco'),
        ('melchor_ocampo', 'Melchor Ocampo'),
        ('metepec', 'Metepec'),
        ('mexicaltzingo', 'Mexicaltzingo'),
        ('morelos', 'Morelos'),
        ('naucalpan_de_juarez', 'Naucalpan de Juárez'),
        ('nezahualcoyotl', 'Nezahualcóyotl'),
        ('nextlalpan', 'Nextlalpan'),
        ('nicolas_romero', 'Nicolás Romero'),
        ('nopaltepec', 'Nopaltepec'),
        ('ocoyoacac', 'Ocoyoacac'),
        ('ocuilan', 'Ocuilan'),
        ('otumba', 'Otumba'),
        ('otzoloapan', 'Otzoloapan'),
        ('otzolotepec', 'Otzolotepec'),
        ('ozumba', 'Ozumba'),
        ('papalotla', 'Papalotla'),
        ('polotitlan', 'Polotitlán'),
        ('rayon', 'Rayón'),
        ('san_antonio_la_isla', 'San Antonio la Isla'),
        ('san_felipe_del_progreso', 'San Felipe del Progreso'),
        ('san_martin_de_las_piramides', 'San Martín de las Pirámides'),
        ('san_mateo_atenco', 'San Mateo Atenco'),
        ('san_simon_de_guerrero', 'San Simón de Guerrero'),
        ('santo_tomas', 'Santo Tomás'),
        ('soyaniquilpan_de_juarez', 'Soyaniquilpan de Juárez'),
        ('sultepec', 'Sultepec'),
        ('tecamac', 'Tecámac'),
        ('tejupilco', 'Tejupilco'),
        ('temamatla', 'Temamatla'),
        ('temascalapa', 'Temascalapa'),
        ('temascalcingo', 'Temascalcingo'),
        ('temascaltepec', 'Temascaltepec'),
        ('temoaya', 'Temoaya'),
        ('tenancingo', 'Tenancingo'),
        ('tenango_del_aire', 'Tenango del Aire'),
        ('tenango_del_valle', 'Tenango del Valle'),
        ('teoloyucan', 'Teoloyucan'),
        ('teotihuacan', 'Teotihuacán'),
        ('tepetlaoxtoc', 'Tepetlaoxtoc'),
        ('tepetlixpa', 'Tepetlixpa'),
        ('tepotzotlan', 'Tepotzotlán'),
        ('tequixquiac', 'Tequixquiac'),
        ('texcaltitlan', 'Texcaltitlán'),
        ('texcalyacac', 'Texcalyacac'),
        ('texcoco', 'Texcoco'),
        ('tezoyuca', 'Tezoyuca'),
        ('tianguistenco', 'Tianguistenco'),
        ('timilpan', 'Timilpan'),
        ('tlalmanalco', 'Tlalmanalco'),
        ('tlalnepantla_de_baz', 'Tlalnepantla de Baz'),
        ('tlatlaya', 'Tlatlaya'),
        ('toluca', 'Toluca'),
        ('tonanitla', 'Tonanitla'),
        ('tonatico', 'Tonatico'),
        ('tultepec', 'Tultepec'),
        ('tultitlan', 'Tultitlán'),
        ('valle_de_bravo', 'Valle de Bravo'),
        ('valle_de_chalco_solidaridad', 'Valle de Chalco Solidaridad'),
        ('villa_de_allende', 'Villa de Allende'),
        ('villa_del_carbon', 'Villa del Carbón'),
        ('villa_guerrero', 'Villa Guerrero'),
        ('villa_victoria', 'Villa Victoria'),
        ('xonacatlan', 'Xonacatlán'),
        ('zacazonapan', 'Zacazonapan'),
        ('zacualpan', 'Zacualpan'),
        ('zinacantepec', 'Zinacantepec'),
        ('zumpahuacan', 'Zumpahuacán'),
        ('zumpango', 'Zumpango'),
    )

    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='interesado')
    nombre = models.CharField(max_length=50, blank=True)
    apellido_paterno = models.CharField(max_length=50, blank=True)
    apellido_materno = models.CharField(max_length=50, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)

    # CAMPOS DE UBICACIÓN EXISTENTES
    municipio = models.CharField(
        max_length=50,
        choices=MUNICIPIOS_ESTADO_MEXICO,
        blank=True,
        null=True,
        verbose_name="Municipio"
    )
    codigo_postal = models.CharField(max_length=10, blank=True, null=True)

    # NUEVOS CAMPOS DE UBICACIÓN DETALLADA
    estado_id = models.IntegerField(blank=True, null=True, help_text="ID del estado desde catálogo")
    municipio_id = models.IntegerField(blank=True, null=True, help_text="ID del municipio desde catálogo")
    localidad_id = models.IntegerField(blank=True, null=True, help_text="ID de la localidad desde catálogo")
    calle_numero = models.CharField(max_length=200, blank=True, null=True, verbose_name="Calle y número")

    # CAMPOS PARA ALMACENAR NOMBRES LEGIBLES
    estado_nombre = models.CharField(max_length=100, blank=True, null=True)
    municipio_nombre = models.CharField(max_length=100, blank=True, null=True)
    localidad_nombre = models.CharField(max_length=100, blank=True, null=True)

    foto_perfil = models.ImageField(upload_to='interesados/', blank=True, null=True)

    def save(self, *args, **kwargs):
        try:
            # Obtener la instancia actual de la base de datos para comparar la foto
            old_instance = Interesado.objects.get(pk=self.pk)
            # Si la foto ha cambiado y la foto antigua existe
            if old_instance.foto_perfil and old_instance.foto_perfil != self.foto_perfil:
                # Eliminar el archivo de la foto anterior
                old_instance.foto_perfil.delete(save=False)
        except Interesado.DoesNotExist:
            pass
        super().save(*args, **kwargs)

    def __str__(self):
        if self.nombre and self.apellido_paterno:
            apellido_completo = f"{self.apellido_paterno} {self.apellido_materno}" if self.apellido_materno else self.apellido_paterno
            return f"{self.nombre} {apellido_completo}"
        return self.usuario.email

    @property
    def nombre_completo(self):
        """Retorna el nombre completo con apellidos."""
        if self.nombre and self.apellido_paterno:
            apellido_completo = f"{self.apellido_paterno} {self.apellido_materno}" if self.apellido_materno else self.apellido_paterno
            return f"{self.nombre} {apellido_completo}"
        return "Sin nombre registrado"

    @property
    def ubicacion_completa(self):
        """Retorna la ubicación completa formateada."""
        partes = []

        if self.calle_numero:
            partes.append(self.calle_numero)

        if self.localidad_nombre:
            partes.append(self.localidad_nombre)
        elif self.municipio_nombre:
            partes.append(self.municipio_nombre)
        elif self.municipio:
            partes.append(self.get_municipio_display())

        if self.codigo_postal:
            partes.append(f'C.P. {self.codigo_postal}')

        if self.estado_nombre:
            partes.append(self.estado_nombre)
        else:
            partes.append('Estado de México')

        return ', '.join(partes) if partes else ''

    @property
    def ubicacion_basica(self):
        """Ubicación básica para compatibilidad con código existente."""
        if self.codigo_postal and self.municipio:
            return f'C.P. {self.codigo_postal}, {self.get_municipio_display()}, Estado de México'
        elif self.municipio:
            return f'{self.get_municipio_display()}, Estado de México'
        else:
            return ''

    def actualizar_ubicacion_desde_catalogo(self, localidad_obj):
        """
        Actualiza los campos de ubicación basándose en un objeto Localidad.
        """
        if localidad_obj:
            self.localidad_id = localidad_obj.id
            self.localidad_nombre = localidad_obj.localidad

            if localidad_obj.catalogo_municipio:
                self.municipio_id = localidad_obj.catalogo_municipio.id
                self.municipio_nombre = localidad_obj.catalogo_municipio.municipio

            if localidad_obj.catalogo_estado:
                self.estado_id = localidad_obj.catalogo_estado.id
                self.estado_nombre = localidad_obj.catalogo_estado.estado

            if localidad_obj.catalogo_codigo_postal:
                self.codigo_postal = str(localidad_obj.catalogo_codigo_postal.codigo_postal)

    @property
    def tiene_cv_completo(self):
        """Verifica si el interesado tiene un CV completo."""
        return (
                hasattr(self, 'curriculum') and
                self.nombre and
                self.apellido_paterno and
                self.curriculum.resumen_profesional and
                self.codigo_postal  # Ahora también requiere código postal
        )

class Secretaria(models.Model):
    """Modelo para las secretarías (organizaciones) que pueden publicar vacantes."""

    nombre = models.CharField(max_length=100)
    rfc = models.CharField(max_length=13, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='secretarias/', blank=True, null=True)
    sitio_web = models.URLField(blank=True, null=True)
    ciudad = models.CharField(max_length=50, blank=True, null=True)
    estado = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    TAMAÑOS = (
        ('pequeña', 'Pequeña (1-50 empleados)'),
        ('mediana', 'Mediana (51-250 empleados)'),
        ('grande', 'Grande (251+ empleados)'),
    )
    tamaño = models.CharField(max_length=10, choices=TAMAÑOS, blank=True, null=True)
    sector = models.CharField(max_length=100, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)
    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Secretaría"
        verbose_name_plural = "Secretarías"


class Reclutador(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='reclutador')
    secretaria = models.ForeignKey(Secretaria, on_delete=models.CASCADE, related_name='reclutadores')
    nombre = models.CharField(max_length=50)
    apellido_paterno = models.CharField(max_length=50)
    apellido_materno = models.CharField(max_length=50, blank=True, null=True)
    cargo = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    aprobado = models.BooleanField(default=False)

    def __str__(self):
        apellido_completo = f"{self.apellido_paterno} {self.apellido_materno}" if self.apellido_materno else self.apellido_paterno
        return f"{self.nombre} {apellido_completo} ({self.secretaria.nombre})"

    @property
    def nombre_completo(self):
        """Retorna el nombre completo con apellidos."""
        apellido_completo = f"{self.apellido_paterno} {self.apellido_materno}" if self.apellido_materno else self.apellido_paterno
        return f"{self.nombre} {apellido_completo}"


class Categoria(models.Model):
    """Modelo para las categorías de trabajo."""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
# usuarios/models.py - SECCIÓN ACTUALIZADA PARA VACANTES

class Vacante(models.Model):
    """Modelo para las vacantes de trabajo."""
    TIPOS_EMPLEO = (
        ('tiempo_completo', 'Tiempo Completo'),
        ('medio_tiempo', 'Medio Tiempo'),
        ('proyecto', 'Por Proyecto'),
        ('temporal', 'Temporal'),
        ('practicas', 'Prácticas Profesionales'),
    )

    MODALIDAD = (
        ('presencial', 'Presencial'),
        ('remoto', 'Remoto'),
        ('hibrido', 'Híbrido'),
    )

    ESTADOS_VACANTE = (
        ('borrador', 'Borrador'),
        ('publicada', 'Publicada'),
        ('cerrada', 'Cerrada'),
        ('eliminada', 'Eliminada'),
    )

    # Municipios del Estado de México
    MUNICIPIOS_ESTADO_MEXICO = (
        ('acambay', 'Acambay'),
        ('acolman', 'Acolman'),
        ('aculco', 'Aculco'),
        ('almoloya_de_alquisiras', 'Almoloya de Alquisiras'),
        ('almoloya_de_juarez', 'Almoloya de Juárez'),
        ('almoloya_del_rio', 'Almoloya del Río'),
        ('amanalco', 'Amanalco'),
        ('amatepec', 'Amatepec'),
        ('amecameca', 'Amecameca'),
        ('apaxco', 'Apaxco'),
        ('atenco', 'Atenco'),
        ('atizapan', 'Atizapán'),
        ('atizapan_de_zaragoza', 'Atizapán de Zaragoza'),
        ('atlacomulco', 'Atlacomulco'),
        ('atlautla', 'Atlautla'),
        ('axapusco', 'Axapusco'),
        ('ayapango', 'Ayapango'),
        ('calimaya', 'Calimaya'),
        ('capulhuac', 'Capulhuac'),
        ('coacalco_de_berriozabal', 'Coacalco de Berriozábal'),
        ('coatepec_harinas', 'Coatepec Harinas'),
        ('cocotitlan', 'Cocotitlán'),
        ('coyotepec', 'Coyotepec'),
        ('cuautitlan', 'Cuautitlán'),
        ('cuautitlan_izcalli', 'Cuautitlán Izcalli'),
        ('donato_guerra', 'Donato Guerra'),
        ('ecatepec_de_morelos', 'Ecatepec de Morelos'),
        ('ecatzingo', 'Ecatzingo'),
        ('el_oro', 'El Oro'),
        ('huehuetoca', 'Huehuetoca'),
        ('hueypoxtla', 'Hueypoxtla'),
        ('huixquilucan', 'Huixquilucan'),
        ('isidro_fabela', 'Isidro Fabela'),
        ('ixtapaluca', 'Ixtapaluca'),
        ('ixtapan_de_la_sal', 'Ixtapan de la Sal'),
        ('ixtapan_del_oro', 'Ixtapan del Oro'),
        ('ixtlahuaca', 'Ixtlahuaca'),
        ('jaltenco', 'Jaltenco'),
        ('jilotepec', 'Jilotepec'),
        ('jilotzingo', 'Jilotzingo'),
        ('jiquipilco', 'Jiquipilco'),
        ('jocotitlan', 'Jocotitlán'),
        ('joquicingo', 'Joquicingo'),
        ('juchitepec', 'Juchitepec'),
        ('la_paz', 'La Paz'),
        ('lerma', 'Lerma'),
        ('luvianos', 'Luvianos'),
        ('malinalco', 'Malinalco'),
        ('melchor_ocampo', 'Melchor Ocampo'),
        ('metepec', 'Metepec'),
        ('mexicaltzingo', 'Mexicaltzingo'),
        ('morelos', 'Morelos'),
        ('naucalpan_de_juarez', 'Naucalpan de Juárez'),
        ('nezahualcoyotl', 'Nezahualcóyotl'),
        ('nextlalpan', 'Nextlalpan'),
        ('nicolas_romero', 'Nicolás Romero'),
        ('nopaltepec', 'Nopaltepec'),
        ('ocoyoacac', 'Ocoyoacac'),
        ('ocuilan', 'Ocuilan'),
        ('otumba', 'Otumba'),
        ('otzoloapan', 'Otzoloapan'),
        ('otzolotepec', 'Otzolotepec'),
        ('ozumba', 'Ozumba'),
        ('papalotla', 'Papalotla'),
        ('polotitlan', 'Polotitlán'),
        ('rayon', 'Rayón'),
        ('san_antonio_la_isla', 'San Antonio la Isla'),
        ('san_felipe_del_progreso', 'San Felipe del Progreso'),
        ('san_martin_de_las_piramides', 'San Martín de las Pirámides'),
        ('san_mateo_atenco', 'San Mateo Atenco'),
        ('san_simon_de_guerrero', 'San Simón de Guerrero'),
        ('santo_tomas', 'Santo Tomás'),
        ('soyaniquilpan_de_juarez', 'Soyaniquilpan de Juárez'),
        ('sultepec', 'Sultepec'),
        ('tecamac', 'Tecámac'),
        ('tejupilco', 'Tejupilco'),
        ('temamatla', 'Temamatla'),
        ('temascalapa', 'Temascalapa'),
        ('temascalcingo', 'Temascalcingo'),
        ('temascaltepec', 'Temascaltepec'),
        ('temoaya', 'Temoaya'),
        ('tenancingo', 'Tenancingo'),
        ('tenango_del_aire', 'Tenango del Aire'),
        ('tenango_del_valle', 'Tenango del Valle'),
        ('teoloyucan', 'Teoloyucan'),
        ('teotihuacan', 'Teotihuacán'),
        ('tepetlaoxtoc', 'Tepetlaoxtoc'),
        ('tepetlixpa', 'Tepetlixpa'),
        ('tepotzotlan', 'Tepotzotlán'),
        ('tequixquiac', 'Tequixquiac'),
        ('texcaltitlan', 'Texcaltitlán'),
        ('texcalyacac', 'Texcalyacac'),
        ('texcoco', 'Texcoco'),
        ('tezoyuca', 'Tezoyuca'),
        ('tianguistenco', 'Tianguistenco'),
        ('timilpan', 'Timilpan'),
        ('tlalmanalco', 'Tlalmanalco'),
        ('tlalnepantla_de_baz', 'Tlalnepantla de Baz'),
        ('tlatlaya', 'Tlatlaya'),
        ('toluca', 'Toluca'),
        ('tonanitla', 'Tonanitla'),
        ('tonatico', 'Tonatico'),
        ('tultepec', 'Tultepec'),
        ('tultitlan', 'Tultitlán'),
        ('valle_de_bravo', 'Valle de Bravo'),
        ('valle_de_chalco_solidaridad', 'Valle de Chalco Solidaridad'),
        ('villa_de_allende', 'Villa de Allende'),
        ('villa_del_carbon', 'Villa del Carbón'),
        ('villa_guerrero', 'Villa Guerrero'),
        ('villa_victoria', 'Villa Victoria'),
        ('xonacatlan', 'Xonacatlán'),
        ('zacazonapan', 'Zacazonapan'),
        ('zacualpan', 'Zacualpan'),
        ('zinacantepec', 'Zinacantepec'),
        ('zumpahuacan', 'Zumpahuacán'),
        ('zumpango', 'Zumpango'),
    )

    # Información básica
    secretaria = models.ForeignKey(Secretaria, on_delete=models.CASCADE, related_name='vacantes')
    reclutador = models.ForeignKey(Reclutador, on_delete=models.CASCADE, related_name='vacantes')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='vacantes')

    # Condiciones de trabajo
    tipo_empleo = models.CharField(max_length=20, choices=TIPOS_EMPLEO)
    modalidad = models.CharField(max_length=15, choices=MODALIDAD, default='presencial')

    # Ubicación - SOLO ESTADO DE MÉXICO
    municipio = models.CharField(max_length=50, choices=MUNICIPIOS_ESTADO_MEXICO, verbose_name="Municipio")

    # Salario
    salario_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    salario_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    detalles_salario = models.CharField(max_length=200, blank=True, null=True,
                                        help_text="Ej: A tratar, Según aptitudes, Más bonos")

    # Fechas
    fecha_inicio_estimada = models.DateField(blank=True, null=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    fecha_limite = models.DateField(null=True, blank=True)
    # fecha_limite = models.DateField()
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    # Control de estado
    estado_vacante = models.CharField(max_length=15, choices=ESTADOS_VACANTE, default='borrador')
    aprobada = models.BooleanField(default=False)
    destacada = models.BooleanField(default=False)

    # Límites de postulación
    max_postulantes = models.IntegerField(choices=[(5, '5'), (10, '10'), (20, '20'), (50, '50')], default=20)
    max_postulaciones_por_interesado = models.IntegerField(default=1)
    max_postulaciones_por_consulta = models.IntegerField(default=5)

    def __str__(self):
        return f"{self.titulo} - {self.secretaria.nombre}"

    @property
    def es_borrador(self):
        return self.estado_vacante == 'borrador'

    @property
    def es_publicada(self):
        return self.estado_vacante == 'publicada'

    @property
    def salario_formateado(self):
        """Retorna el salario formateado para mostrar."""
        if self.salario_min and self.salario_max:
            return f"${self.salario_min:,.0f} - ${self.salario_max:,.0f} MXN"
        elif self.salario_min:
            return f"Desde ${self.salario_min:,.0f} MXN"
        elif self.salario_max:
            return f"Hasta ${self.salario_max:,.0f} MXN"
        elif self.detalles_salario:
            return self.detalles_salario
        else:
            return "No especificado"

    @property
    def estado_completo(self):
        """Retorna 'Estado de México' siempre"""
        return "Estado de México"

    def cerrar_por_vencimiento(self):
        """Cierra la vacante si ha llegado a su fecha límite."""
        if self.fecha_limite and timezone.now().date() >= self.fecha_limite:
            if self.estado_vacante == 'publicada':
                self.estado_vacante = 'cerrada'
                self.save(update_fields=['estado_vacante'])
                return True
        return False

    @classmethod
    def cerrar_vacantes_vencidas(cls):
        """Método de clase para cerrar todas las vacantes vencidas."""
        from django.utils import timezone
        hoy = timezone.now().date()
        
        vacantes_vencidas = cls.objects.filter(
            estado_vacante='publicada',
            fecha_limite__lt=hoy
        )
        
        contador = 0
        for vacante in vacantes_vencidas:
            vacante.estado_vacante = 'cerrada'
            contador += 1
        
        if contador > 0:
            cls.objects.bulk_update(vacantes_vencidas, ['estado_vacante'])
        
        return contador

    class Meta:
        verbose_name = "Vacante"
        verbose_name_plural = "Vacantes"
        ordering = ['-fecha_publicacion']



class RequisitoVacante(models.Model):
    """Modelo para los requisitos específicos de una vacante."""
    # Choices para años de experiencia
    EXPERIENCIA_CHOICES = (
        ('0', 'Sin experiencia requerida'),
        ('1', '1 año'),
        ('2', '2 años'),
        ('3', '3 años'),
        ('4', '4 años'),
        ('5', '5 años'),
        ('6', '6 años'),
        ('7', '7 años'),
        ('8', '8 años'),
        ('9', '9 años'),
        ('10', '10 años'),
        ('10+', 'Más de 10 años'),
    )

    vacante = models.OneToOneField(Vacante, on_delete=models.CASCADE, related_name='requisitos')
    educacion_minima = models.CharField(max_length=200, blank=True, null=True)

    # CAMPO ACTUALIZADO: Ahora es un campo de choices
    experiencia_minima = models.CharField(
        max_length=10,
        choices=EXPERIENCIA_CHOICES,
        blank=True,
        null=True,
        verbose_name="Años de experiencia mínima"
    )

    descripcion_requisitos = models.TextField(
        help_text="Detalla los requisitos específicos, habilidades técnicas, etc."
    )

    def __str__(self):
        return f"Requisitos - {self.vacante.titulo}"

    @property
    def experiencia_display(self):
        """Retorna el texto formateado de la experiencia."""
        if self.experiencia_minima:
            return dict(self.EXPERIENCIA_CHOICES).get(self.experiencia_minima, self.experiencia_minima)
        return "No especificada"

    class Meta:
        verbose_name = "Requisito de Vacante"
        verbose_name_plural = "Requisitos de Vacantes"

class Curriculum(models.Model):
    """Modelo para el currículum de un interesado."""

    interesado = models.OneToOneField(Interesado, on_delete=models.CASCADE, related_name='curriculum')
    resumen_profesional = models.TextField(
        blank=True, null=True,
        help_text="Describe brevemente tu perfil y objetivos profesionales"
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"CV de {self.interesado.nombre_completo}"

    class Meta:
        verbose_name = "Currículum"
        verbose_name_plural = "Currículums"

    @property
    def validation_errors(self):
        errors = []
        interesado = self.interesado
        # 1. Validar campos del perfil del interesado
        profile_fields = {
            'nombre': 'Nombre(s)',
            'apellido_paterno': 'Apellido Paterno',
            'apellido_materno': 'Apellido Materno',
            'telefono': 'Teléfono',
            'fecha_nacimiento': 'Fecha de Nacimiento',
            'municipio': 'Municipio',
            'codigo_postal': 'Código Postal',
            'foto_perfil': 'Foto de Perfil',
        }
        for field, label in profile_fields.items():
            if not getattr(interesado, field):
                errors.append(label)

        # 2. Validar resumen profesional
        if not self.resumen_profesional or not self.resumen_profesional.strip():
            errors.append('Resumen Profesional')

        # 3. Validar secciones con al menos una entrada
        if not self.experiencias.exists():
            errors.append('Al menos una Experiencia Laboral')
        if not self.educaciones.exists():
            errors.append('Al menos una entrada de Educación')
        if not self.idiomas.exists():
            errors.append('Al menos un Idioma')
        habilidades_count = self.habilidades.count()
        if habilidades_count < 5:
            errors.append(f'Al menos 5 habilidades (tienes {habilidades_count})')
        return errors

    @property
    def is_cv_complete(self):
        return not self.validation_errors

class ExperienciaLaboral(models.Model):
    """Modelo para las experiencias laborales del CV."""

    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='experiencias')
    empresa = models.CharField(max_length=200)
    puesto = models.CharField(max_length=200)
    descripcion = models.TextField(help_text="Funciones y responsabilidades principales")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)
    actual = models.BooleanField(default=False, help_text="Marca si es tu trabajo actual")

    def __str__(self):
        return f"{self.puesto} en {self.empresa}"

    @property
    def periodo_trabajo(self):
        """Retorna el periodo de trabajo formateado."""
        inicio = self.fecha_inicio.strftime("%m/%Y")
        if self.actual:
            return f"{inicio} - Presente"
        elif self.fecha_fin:
            fin = self.fecha_fin.strftime("%m/%Y")
            return f"{inicio} - {fin}"
        else:
            return f"Desde {inicio}"

    class Meta:
        verbose_name = "Experiencia Laboral"
        verbose_name_plural = "Experiencias Laborales"
        ordering = ['-fecha_inicio']


class Educacion(models.Model):
    """Modelo para la educación y formación del CV."""

    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='educaciones')
    titulo = models.CharField(max_length=200, help_text="Título obtenido o nivel educativo")
    institucion = models.CharField(max_length=200)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True, help_text="Descripción adicional")

    def __str__(self):
        return f"{self.titulo} - {self.institucion}"

    @property
    def periodo_estudio(self):
        """Retorna el periodo de estudio formateado."""
        inicio = self.fecha_inicio.strftime("%m/%Y")
        if self.fecha_fin:
            fin = self.fecha_fin.strftime("%m/%Y")
            return f"{inicio} - {fin}"
        else:
            return f"Desde {inicio}"

    class Meta:
        verbose_name = "Educación"
        verbose_name_plural = "Educación y Formación"
        ordering = ['-fecha_inicio']


class Habilidad(models.Model):
    """Catálogo de habilidades disponibles."""

    nombre = models.CharField(max_length=100, unique=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='habilidades', null=True,
                                  blank=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Habilidad"
        verbose_name_plural = "Habilidades"
        ordering = ['nombre']


class HabilidadInteresado(models.Model):
    """Relación many-to-many entre interesados y habilidades con nivel."""

    NIVELES = (
        ('basico', 'Básico'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
        ('experto', 'Experto'),
    )

    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='habilidades')
    habilidad = models.ForeignKey(Habilidad, on_delete=models.CASCADE)
    nivel = models.CharField(max_length=15, choices=NIVELES)

    def __str__(self):
        return f"{self.habilidad.nombre} - {self.get_nivel_display()}"

    class Meta:
        verbose_name = "Habilidad del Interesado"
        verbose_name_plural = "Habilidades del Interesado"
        unique_together = ['curriculum', 'habilidad']


class IdiomaInteresado(models.Model):
    """Modelo para los idiomas que maneja un interesado."""

    NIVELES_IDIOMA = (
        ('A1', 'A1 - Principiante'),
        ('A2', 'A2 - Elemental'),
        ('B1', 'B1 - Intermedio'),
        ('B2', 'B2 - Intermedio Alto'),
        ('C1', 'C1 - Avanzado'),
        ('C2', 'C2 - Maestría'),
        ('nativo', 'Nativo'),
    )

    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='idiomas')
    idioma = models.CharField(max_length=50)
    nivel_lectura = models.CharField(max_length=10, choices=NIVELES_IDIOMA)
    nivel_escritura = models.CharField(max_length=10, choices=NIVELES_IDIOMA)
    nivel_conversacion = models.CharField(max_length=10, choices=NIVELES_IDIOMA)

    def __str__(self):
        return f"{self.idioma} - {self.get_nivel_lectura_display()}"

    @property
    def nivel_general(self):
        """Retorna el nivel general basado en el promedio de habilidades."""
        niveles = {
            'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6, 'nativo': 7
        }

        total = (
                        niveles.get(self.nivel_lectura, 1) +
                        niveles.get(self.nivel_escritura, 1) +
                        niveles.get(self.nivel_conversacion, 1)
                ) / 3

        # Retornar el nivel más cercano
        for nivel_code, nivel_num in sorted(niveles.items(), key=lambda x: x[1]):
            if total <= nivel_num:
                return dict(self.NIVELES_IDIOMA)[nivel_code]
        return "Nativo"

    class Meta:
        verbose_name = "Idioma del Interesado"
        verbose_name_plural = "Idiomas del Interesado"
        unique_together = ['curriculum', 'idioma']


class Postulacion(models.Model):
    """Modelo para las postulaciones de interesados a vacantes."""

    ESTADOS_POSTULACION = (
        ('enviada', 'Enviada'),
        ('en_revision', 'En Revisión'),
        ('preseleccionado', 'Preseleccionado'),
        ('entrevista', 'En Entrevista'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    )
    interesado = models.ForeignKey(Interesado, on_delete=models.CASCADE, related_name='postulaciones')
    vacante = models.ForeignKey(Vacante, on_delete=models.CASCADE, related_name='postulaciones')
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='postulaciones')
    fecha_postulacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_POSTULACION, default='enviada')
    mensaje_motivacion = models.TextField(blank=True, null=True, help_text="Mensaje opcional del candidato")
    notas_reclutador = models.TextField(blank=True, null=True, help_text="Notas del reclutador")
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.interesado.nombre_completo} - {self.vacante.titulo}"

    @property
    def tiempo_desde_postulacion(self):
        """Retorna el tiempo transcurrido desde la postulación."""
        from django.utils import timezone
        delta = timezone.now() - self.fecha_postulacion

        if delta.days > 0:
            return f"Hace {delta.days} día{'s' if delta.days > 1 else ''}"
        elif delta.seconds > 3600:
            horas = delta.seconds // 3600
            return f"Hace {horas} hora{'s' if horas > 1 else ''}"
        else:
            minutos = delta.seconds // 60
            return f"Hace {minutos} minuto{'s' if minutos > 1 else ''}"

    class Meta:
        verbose_name = "Postulación"
        verbose_name_plural = "Postulaciones"
        unique_together = ['interesado', 'vacante']  # Un interesado solo puede postularse una vez por vacante
        ordering = ['-fecha_postulacion']


# ====================================
# MODELOS DE CATÁLOGOS GEOGRÁFICOS
# ====================================

class Codigos_Postales(models.Model):
    """Catálogo de códigos postales."""
    codigo_postal = models.IntegerField(unique=True)
    estatus = models.SmallIntegerField(default=1)
    alta_fecha = models.DateField(auto_now_add=True)
    alta_hora = models.TimeField(auto_now_add=True)
    modificacion_fecha = models.DateField(auto_now=True)
    modificacion_hora = models.TimeField(auto_now=True)
    id_capturo = models.SmallIntegerField(default=1)
    id_modifico = models.SmallIntegerField(default=1)

    def __str__(self):
        return f"{self.codigo_postal}"

    class Meta:
        verbose_name = "Código Postal"
        verbose_name_plural = "Códigos Postales"
        db_table = 'codigos_postales'


class Estados(models.Model):
    """Catálogo de estados."""
    estado = models.CharField(max_length=100)
    estatus = models.SmallIntegerField(default=1)
    alta_fecha = models.DateField(auto_now_add=True)
    alta_hora = models.TimeField(auto_now_add=True)
    modificacion_fecha = models.DateField(auto_now=True)
    modificacion_hora = models.TimeField(auto_now=True)
    id_capturo = models.SmallIntegerField(default=1)
    id_modifico = models.SmallIntegerField(default=1)

    def __str__(self):
        return self.estado

    class Meta:
        verbose_name = "Estado"
        verbose_name_plural = "Estados"
        db_table = 'estados'


class Zonas_Regionales(models.Model):
    """Catálogo de zonas regionales."""
    zona_regional = models.CharField(max_length=50)
    estatus = models.SmallIntegerField(default=1)
    alta_fecha = models.DateField(auto_now_add=True)
    alta_hora = models.TimeField(auto_now_add=True)
    modificacion_fecha = models.DateField(auto_now=True)
    modificacion_hora = models.TimeField(auto_now=True)
    id_capturo = models.SmallIntegerField(default=1)
    id_modifico = models.SmallIntegerField(default=1)

    def __str__(self):
        return self.zona_regional

    class Meta:
        verbose_name = "Zona Regional"
        verbose_name_plural = "Zonas Regionales"
        db_table = 'zonas_regionales'


class Tipos_Asentamientos(models.Model):
    """Catálogo de tipos de asentamientos."""
    tipo_asentamiento = models.CharField(max_length=50)
    estatus = models.SmallIntegerField(default=1)
    alta_fecha = models.DateField(auto_now_add=True)
    alta_hora = models.TimeField(auto_now_add=True)
    modificacion_fecha = models.DateField(auto_now=True)
    modificacion_hora = models.TimeField(auto_now=True)
    id_capturo = models.SmallIntegerField(default=1)
    id_modifico = models.SmallIntegerField(default=1)

    def __str__(self):
        return self.tipo_asentamiento

    class Meta:
        verbose_name = "Tipo de Asentamiento"
        verbose_name_plural = "Tipos de Asentamientos"
        db_table = 'tipos_asentamientos'


class Zonas(models.Model):
    """Catálogo de zonas."""
    zona = models.CharField(max_length=50)
    estatus = models.SmallIntegerField(default=1)
    alta_fecha = models.DateField(auto_now_add=True)
    alta_hora = models.TimeField(auto_now_add=True)
    modificacion_fecha = models.DateField(auto_now=True)
    modificacion_hora = models.TimeField(auto_now=True)
    id_capturo = models.SmallIntegerField(default=1)
    id_modifico = models.SmallIntegerField(default=1)

    def __str__(self):
        return self.zona

    class Meta:
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"
        db_table = 'zonas'


class Delegaciones(models.Model):
    """Catálogo de delegaciones."""
    catalogo_zona = models.ForeignKey('Zonas', on_delete=models.PROTECT)
    delegacion = models.CharField(max_length=100)
    estatus = models.SmallIntegerField(default=1)
    alta_fecha = models.DateField(auto_now_add=True)
    alta_hora = models.TimeField(auto_now_add=True)
    modificacion_fecha = models.DateField(auto_now=True)
    modificacion_hora = models.TimeField(auto_now=True)
    id_capturo = models.SmallIntegerField(default=1)
    id_modifico = models.SmallIntegerField(default=1)

    def __str__(self):
        return self.delegacion

    class Meta:
        verbose_name = "Delegación"
        verbose_name_plural = "Delegaciones"
        db_table = 'delegaciones'


class Municipios(models.Model):
    """Catálogo de municipios."""
    catalogo_delegacion = models.ForeignKey('Delegaciones', on_delete=models.SET_NULL, null=True, blank=True)
    municipio = models.CharField(max_length=100)
    estatus = models.SmallIntegerField(default=1)
    alta_fecha = models.DateField(auto_now_add=True)
    alta_hora = models.TimeField(auto_now_add=True)
    modificacion_fecha = models.DateField(auto_now=True)
    modificacion_hora = models.TimeField(auto_now=True)
    id_capturo = models.SmallIntegerField(default=1)
    id_modifico = models.SmallIntegerField(default=1)

    def __str__(self):
        return self.municipio

    class Meta:
        verbose_name = "Municipio"
        verbose_name_plural = "Municipios"
        db_table = 'municipios'


class Localidades(models.Model):
    """Catálogo de localidades con todas sus relaciones."""
    catalogo_municipio = models.ForeignKey('Municipios', on_delete=models.PROTECT)
    catalogo_codigo_postal = models.ForeignKey('Codigos_Postales', on_delete=models.PROTECT)
    catalogo_tipo_asentamiento = models.ForeignKey('Tipos_Asentamientos', on_delete=models.PROTECT)
    catalogo_zona_regional = models.ForeignKey('Zonas_Regionales', on_delete=models.PROTECT)
    catalogo_estado = models.ForeignKey('Estados', on_delete=models.PROTECT)
    localidad = models.CharField(max_length=100)
    estatus = models.SmallIntegerField(default=1)
    alta_fecha = models.DateField(auto_now_add=True)
    alta_hora = models.TimeField(auto_now_add=True)
    modificacion_fecha = models.DateField(auto_now=True)
    modificacion_hora = models.TimeField(auto_now=True)
    id_capturo = models.SmallIntegerField(default=1)
    id_modifico = models.SmallIntegerField(default=1)

    def __str__(self):
        return f"{self.localidad} - {self.catalogo_codigo_postal.codigo_postal}"

    @property
    def nombre_completo(self):
        """Nombre completo con tipo de asentamiento."""
        if self.catalogo_tipo_asentamiento:
            return f"{self.localidad} ({self.catalogo_tipo_asentamiento.tipo_asentamiento})"
        return self.localidad

    class Meta:
        verbose_name = "Localidad"
        verbose_name_plural = "Localidades"
        db_table = 'localidades'
        # Índices para optimizar consultas
        indexes = [
            models.Index(fields=['catalogo_codigo_postal', 'estatus']),
            models.Index(fields=['catalogo_municipio', 'estatus']),
            models.Index(fields=['catalogo_estado', 'estatus']),
        ]