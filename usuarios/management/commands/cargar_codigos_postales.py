import os
import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from usuarios.models import (
    Codigos_Postales, Estados, Municipios, Localidades,
    Tipos_Asentamientos, Zonas, Zonas_Regionales, Delegaciones
)


class Command(BaseCommand):
    help = 'Carga datos de códigos postales, estados, municipios y localidades desde archivos CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            default='/home/prodbt/Documentos/cp',
            help='Ruta donde están ubicados los archivos CSV'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la recarga eliminando datos existentes'
        )

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        force_reload = options['force']

        # Verificar que los archivos CSV existan
        csv_files = {
            'estados': 'ct_estados.csv',
            'codigos_postales': 'ct_codigopostal.csv',
            'municipios': 'ct_municipios.csv',
            'localidades': 'ct_localidades.csv'
        }

        for key, filename in csv_files.items():
            file_path = os.path.join(csv_path, filename)
            if not os.path.exists(file_path):
                raise CommandError(f'No se encontró el archivo: {file_path}')

        # Si force está activado, limpiar datos existentes
        if force_reload:
            self.stdout.write('🗑️  Limpiando datos existentes...')
            with transaction.atomic():
                Localidades.objects.all().delete()
                Municipios.objects.all().delete()
                Codigos_Postales.objects.all().delete()
                Tipos_Asentamientos.objects.all().delete()
                Estados.objects.all().delete()
                # Limpiar también los catálogos auxiliares
                Delegaciones.objects.all().delete()
                Zonas.objects.all().delete()
                Zonas_Regionales.objects.all().delete()

        try:
            with transaction.atomic():
                # 1. Crear catálogos auxiliares básicos
                self._crear_catalogos_auxiliares()

                # 2. Cargar Estados
                self._cargar_estados(os.path.join(csv_path, csv_files['estados']))

                # 3. Cargar Códigos Postales
                self._cargar_codigos_postales(os.path.join(csv_path, csv_files['codigos_postales']))

                # 4. Cargar Municipios
                self._cargar_municipios(os.path.join(csv_path, csv_files['municipios']))

                # 5. Cargar Localidades
                self._cargar_localidades(os.path.join(csv_path, csv_files['localidades']))

            self.stdout.write(
                self.style.SUCCESS('✅ Datos cargados exitosamente!')
            )

            # Mostrar estadísticas finales
            self._mostrar_estadisticas()

        except Exception as e:
            raise CommandError(f'Error al cargar datos: {str(e)}')

    def _crear_catalogos_auxiliares(self):
        """Crear catálogos auxiliares necesarios para las relaciones."""
        self.stdout.write('📁 Creando catálogos auxiliares...')

        # Crear Zona Regional por defecto para Estado de México
        zona_regional, created = Zonas_Regionales.objects.get_or_create(
            id=1,
            defaults={
                'zona_regional': 'Zona Centro',
                'estatus': 1
            }
        )
        if created:
            self.stdout.write('   ✅ Zona Regional creada')

        # Crear Zona por defecto
        zona, created = Zonas.objects.get_or_create(
            id=1,
            defaults={
                'zona': 'Zona Metropolitana',
                'estatus': 1
            }
        )
        if created:
            self.stdout.write('   ✅ Zona creada')

        # Crear Delegación por defecto
        delegacion, created = Delegaciones.objects.get_or_create(
            id=1,
            defaults={
                'catalogo_zona': zona,
                'delegacion': 'Delegación Central',
                'estatus': 1
            }
        )
        if created:
            self.stdout.write('   ✅ Delegación creada')

    def _cargar_estados(self, file_path):
        """Cargar datos de estados desde CSV."""
        self.stdout.write('🏛️  Cargando Estados...')

        contador = 0
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                estado, created = Estados.objects.get_or_create(
                    id=int(row['id']),
                    defaults={
                        'estado': row['estado'].strip(),
                        'estatus': int(row['iestado']),
                    }
                )
                if created:
                    contador += 1

        self.stdout.write(f'   ✅ {contador} estados cargados')

    def _cargar_codigos_postales(self, file_path):
        """Cargar códigos postales desde CSV."""
        self.stdout.write('📮 Cargando Códigos Postales...')

        contador = 0
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                cp, created = Codigos_Postales.objects.get_or_create(
                    id=int(row['id']),
                    defaults={
                        'codigo_postal': int(row['codigo_postal']),
                        'estatus': int(row['iestado']),
                    }
                )
                if created:
                    contador += 1

        self.stdout.write(f'   ✅ {contador} códigos postales cargados')

    def _cargar_municipios(self, file_path):
        """Cargar municipios desde CSV LEYENDO EL id_estado REAL."""
        self.stdout.write('🏘️  Cargando Municipios...')

        contador = 0
        errores = 0

        # Obtener la delegación por defecto
        delegacion_default = Delegaciones.objects.get(id=1)

        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # LEER EL id_estado REAL del CSV
                    id_estado_csv = row.get('id_estado')
                    estado = None

                    if id_estado_csv:
                        try:
                            estado = Estados.objects.get(id=int(id_estado_csv))
                        except Estados.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'   ⚠️  Estado ID {id_estado_csv} no encontrado para municipio {row["municipio"]}')
                            )
                            # Continuar sin estado por ahora
                            pass

                    municipio, created = Municipios.objects.get_or_create(
                        id=int(row['id']),
                        defaults={
                            'municipio': row['municipio'].strip(),
                            'catalogo_delegacion': delegacion_default,
                            'estatus': int(row['iestado']),
                        }
                    )

                    # Guardar temporalmente el id_estado en un campo personalizado si el modelo lo permite
                    # o crear una relación temporal
                    if hasattr(municipio, '_estado_id_temporal'):
                        municipio._estado_id_temporal = id_estado_csv

                    if created:
                        contador += 1

                except Exception as e:
                    errores += 1
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  Error en municipio {row.get("id", "?")}: {str(e)}')
                    )

        self.stdout.write(f'   ✅ {contador} municipios cargados')
        if errores > 0:
            self.stdout.write(f'   ⚠️  {errores} errores encontrados')

    def _cargar_localidades(self, file_path):
        """Cargar localidades usando el estado REAL del municipio."""
        self.stdout.write('🏠 Cargando Localidades...')

        contador = 0
        errores = 0
        tipos_asentamiento_cache = {}
        zona_regional_default = Zonas_Regionales.objects.get(id=1)

        # Crear cache de municipio -> estado
        self.stdout.write('   📋 Creando cache municipio -> estado...')
        municipio_estado_cache = {}

        # Releer el CSV de municipios para obtener las relaciones estado
        municipios_csv_path = file_path.replace('ct_localidades.csv', 'ct_municipios.csv')
        with open(municipios_csv_path, 'r', encoding='utf-8') as municipios_file:
            municipios_reader = csv.DictReader(municipios_file)
            for municipio_row in municipios_reader:
                municipio_id = int(municipio_row['id'])
                estado_id = municipio_row.get('id_estado')
                if estado_id:
                    try:
                        estado = Estados.objects.get(id=int(estado_id))
                        municipio_estado_cache[municipio_id] = estado
                    except Estados.DoesNotExist:
                        pass

        self.stdout.write(f'   ✅ Cache creado con {len(municipio_estado_cache)} relaciones')

        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # Obtener o crear tipo de asentamiento
                    tipo_asentamiento_nombre = row.get('tipo_asentamiento', '').strip()
                    if tipo_asentamiento_nombre:
                        if tipo_asentamiento_nombre not in tipos_asentamiento_cache:
                            tipo_asentamiento, created = Tipos_Asentamientos.objects.get_or_create(
                                tipo_asentamiento=tipo_asentamiento_nombre,
                                defaults={'estatus': 1}
                            )
                            tipos_asentamiento_cache[tipo_asentamiento_nombre] = tipo_asentamiento
                        else:
                            tipo_asentamiento = tipos_asentamiento_cache[tipo_asentamiento_nombre]
                    else:
                        tipo_asentamiento, _ = Tipos_Asentamientos.objects.get_or_create(
                            tipo_asentamiento='Sin especificar',
                            defaults={'estatus': 1}
                        )

                    # Obtener relaciones
                    try:
                        codigo_postal = Codigos_Postales.objects.get(id=int(row['id_codigo_postal']))
                    except Codigos_Postales.DoesNotExist:
                        continue

                    try:
                        municipio = Municipios.objects.get(id=int(row['id_municipio']))
                    except Municipios.DoesNotExist:
                        continue

                    # OBTENER EL ESTADO REAL DESDE EL CACHE
                    municipio_id = int(row['id_municipio'])
                    estado = municipio_estado_cache.get(municipio_id)

                    if not estado:
                        # Si no hay estado en cache, usar fallback
                        estado = Estados.objects.first()
                        if errores < 5:  # Solo mostrar primeros errores
                            self.stdout.write(
                                self.style.WARNING(
                                    f'   ⚠️  Sin estado para municipio ID {municipio_id}, usando fallback')
                            )

                    # Crear la localidad
                    localidad, created = Localidades.objects.get_or_create(
                        id=int(row['id']),
                        defaults={
                            'localidad': row['localidad'].strip(),
                            'catalogo_municipio': municipio,
                            'catalogo_codigo_postal': codigo_postal,
                            'catalogo_tipo_asentamiento': tipo_asentamiento,
                            'catalogo_zona_regional': zona_regional_default,
                            'catalogo_estado': estado,  # ESTADO REAL
                            'estatus': int(row['iestado']),
                        }
                    )

                    if created:
                        contador += 1

                    # Progress indicator cada 1000 registros
                    if contador % 1000 == 0:
                        self.stdout.write(f'   📍 {contador} localidades procesadas...')

                except Exception as e:
                    errores += 1
                    if errores <= 10:
                        self.stdout.write(
                            self.style.WARNING(f'   ⚠️  Error en localidad {row.get("id", "?")}: {str(e)}')
                        )

        self.stdout.write(f'   ✅ {contador} localidades cargadas')
        if errores > 0:
            self.stdout.write(f'   ⚠️  {errores} errores encontrados')

    def _mostrar_estadisticas(self):
        """Mostrar estadísticas finales de la carga."""
        self.stdout.write('\n📊 ESTADÍSTICAS FINALES:')
        self.stdout.write('=' * 40)

        stats = {
            'Estados': Estados.objects.count(),
            'Códigos Postales': Codigos_Postales.objects.count(),
            'Municipios': Municipios.objects.count(),
            'Tipos de Asentamiento': Tipos_Asentamientos.objects.count(),
            'Localidades': Localidades.objects.count(),
        }

        for categoria, cantidad in stats.items():
            self.stdout.write(f'   {categoria}: {cantidad:,}')

        self.stdout.write('=' * 40)

        # Verificar integridad básica
        self.stdout.write('\n🔍 VERIFICACIÓN DE INTEGRIDAD:')

        # Localidades sin relaciones válidas
        localidades_sin_cp = Localidades.objects.filter(catalogo_codigo_postal__isnull=True).count()
        localidades_sin_municipio = Localidades.objects.filter(catalogo_municipio__isnull=True).count()
        localidades_sin_estado = Localidades.objects.filter(catalogo_estado__isnull=True).count()

        if localidades_sin_cp == 0 and localidades_sin_municipio == 0 and localidades_sin_estado == 0:
            self.stdout.write('   ✅ Todas las localidades tienen relaciones válidas')
        else:
            if localidades_sin_cp > 0:
                self.stdout.write(f'   ⚠️  {localidades_sin_cp} localidades sin código postal')
            if localidades_sin_municipio > 0:
                self.stdout.write(f'   ⚠️  {localidades_sin_municipio} localidades sin municipio')
            if localidades_sin_estado > 0:
                self.stdout.write(f'   ⚠️  {localidades_sin_estado} localidades sin estado')