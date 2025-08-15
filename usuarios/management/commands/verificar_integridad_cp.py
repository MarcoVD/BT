# usuarios/management/commands/verificar_integridad_cp.py

from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from usuarios.models import (
    Codigos_Postales, Estados, Municipios, Localidades,
    Tipos_Asentamientos, Zonas, Zonas_Regionales, Delegaciones
)


class Command(BaseCommand):
    help = 'Verifica la integridad de los datos de códigos postales y ubicación'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Mostrar detalles específicos de los problemas encontrados'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Intentar corregir automáticamente algunos problemas'
        )

    def handle(self, *args, **options):
        detailed = options['detailed']
        auto_fix = options['fix']

        self.stdout.write('🔍 VERIFICACIÓN DE INTEGRIDAD DE DATOS')
        self.stdout.write('=' * 50)

        # Contadores de problemas
        total_problemas = 0

        # 1. Verificar existencia de datos básicos
        total_problemas += self._verificar_datos_basicos()

        # 2. Verificar relaciones entre tablas
        total_problemas += self._verificar_relaciones(detailed)

        # 3. Verificar integridad referencial
        total_problemas += self._verificar_integridad_referencial(detailed, auto_fix)

        # 4. Verificar códigos postales específicos para pruebas
        total_problemas += self._verificar_codigos_prueba(detailed)

        # 5. Verificar Estado de México
        total_problemas += self._verificar_estado_mexico(detailed, auto_fix)

        # Resumen final
        self.stdout.write('\n' + '=' * 50)
        if total_problemas == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ VERIFICACIÓN COMPLETADA: No se encontraron problemas')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  VERIFICACIÓN COMPLETADA: {total_problemas} problemas encontrados')
            )

        if auto_fix:
            self.stdout.write('\n🔧 Se intentaron aplicar correcciones automáticas')

    def _verificar_datos_basicos(self):
        """Verificar que existan datos en las tablas principales."""
        self.stdout.write('\n📊 Verificando datos básicos...')

        problemas = 0
        tablas = {
            'Estados': Estados,
            'Códigos Postales': Codigos_Postales,
            'Municipios': Municipios,
            'Localidades': Localidades,
            'Tipos de Asentamiento': Tipos_Asentamientos,
        }

        for nombre, modelo in tablas.items():
            count = modelo.objects.count()
            if count == 0:
                self.stdout.write(f'   ❌ {nombre}: 0 registros (CRÍTICO)')
                problemas += 1
            else:
                self.stdout.write(f'   ✅ {nombre}: {count:,} registros')

        return problemas

    def _verificar_relaciones(self, detailed=False):
        """Verificar relaciones entre tablas."""
        self.stdout.write('\n🔗 Verificando relaciones...')

        problemas = 0

        # Localidades sin código postal
        sin_cp = Localidades.objects.filter(catalogo_codigo_postal__isnull=True).count()
        if sin_cp > 0:
            self.stdout.write(f'   ❌ {sin_cp} localidades sin código postal')
            problemas += 1
            if detailed:
                ejemplos = Localidades.objects.filter(catalogo_codigo_postal__isnull=True)[:5]
                for loc in ejemplos:
                    self.stdout.write(f'      - ID {loc.id}: {loc.localidad}')

        # Localidades sin municipio
        sin_municipio = Localidades.objects.filter(catalogo_municipio__isnull=True).count()
        if sin_municipio > 0:
            self.stdout.write(f'   ❌ {sin_municipio} localidades sin municipio')
            problemas += 1

        # Localidades sin estado
        sin_estado = Localidades.objects.filter(catalogo_estado__isnull=True).count()
        if sin_estado > 0:
            self.stdout.write(f'   ❌ {sin_estado} localidades sin estado')
            problemas += 1

        # Municipios sin delegación
        municipios_sin_delegacion = Municipios.objects.filter(catalogo_delegacion__isnull=True).count()
        if municipios_sin_delegacion > 0:
            self.stdout.write(f'   ⚠️  {municipios_sin_delegacion} municipios sin delegación')

        if problemas == 0:
            self.stdout.write('   ✅ Todas las relaciones están correctas')

        return problemas

    def _verificar_integridad_referencial(self, detailed=False, auto_fix=False):
        """Verificar integridad referencial."""
        self.stdout.write('\n🔍 Verificando integridad referencial...')

        problemas = 0

        # Códigos postales huérfanos (sin localidades)
        cps_huerfanos = Codigos_Postales.objects.annotate(
            num_localidades=Count('localidades')
        ).filter(num_localidades=0)

        count_huerfanos = cps_huerfanos.count()
        if count_huerfanos > 0:
            self.stdout.write(f'   ⚠️  {count_huerfanos} códigos postales sin localidades asociadas')
            if detailed:
                ejemplos = cps_huerfanos[:10]
                for cp in ejemplos:
                    self.stdout.write(f'      - CP {cp.codigo_postal} (ID: {cp.id})')
            problemas += 1

        # Tipos de asentamiento no utilizados
        tipos_no_usados = Tipos_Asentamientos.objects.annotate(
            num_localidades=Count('localidades')
        ).filter(num_localidades=0)

        count_tipos_no_usados = tipos_no_usados.count()
        if count_tipos_no_usados > 0:
            self.stdout.write(f'   ℹ️  {count_tipos_no_usados} tipos de asentamiento no utilizados')
            if auto_fix:
                tipos_no_usados.delete()
                self.stdout.write('      🔧 Tipos no utilizados eliminados')

        return problemas

    def _verificar_codigos_prueba(self, detailed=False):
        """Verificar códigos postales específicos para pruebas."""
        self.stdout.write('\n🧪 Verificando códigos de prueba...')

        problemas = 0
        codigos_prueba = [50000, 52140, 54000, 53000, 55000]

        for cp in codigos_prueba:
            try:
                cp_obj = Codigos_Postales.objects.get(codigo_postal=cp, estatus=1)
                localidades = Localidades.objects.filter(
                    catalogo_codigo_postal=cp_obj,
                    estatus=1
                ).count()

                if localidades > 0:
                    self.stdout.write(f'   ✅ CP {cp}: {localidades} localidades')
                else:
                    self.stdout.write(f'   ❌ CP {cp}: Sin localidades')
                    problemas += 1

            except Codigos_Postales.DoesNotExist:
                self.stdout.write(f'   ❌ CP {cp}: No encontrado en BD')
                problemas += 1

        return problemas

    def _verificar_estado_mexico(self, detailed=False, auto_fix=False):
        """Verificar que existe el Estado de México y tiene datos."""
        self.stdout.write('\n🏛️  Verificando Estado de México...')

        problemas = 0

        # Buscar Estado de México
        edomex = Estados.objects.filter(
            Q(estado__icontains='méxico') | Q(estado__icontains='mexico')
        ).first()

        if not edomex:
            self.stdout.write('   ❌ Estado de México no encontrado')
            if auto_fix:
                edomex = Estados.objects.create(
                    estado='Estado de México',
                    estatus=1
                )
                self.stdout.write('      🔧 Estado de México creado automáticamente')
            else:
                problemas += 1
        else:
            self.stdout.write(f'   ✅ Estado encontrado: {edomex.estado}')

            # Verificar que tenga localidades asociadas
            localidades_edomex = Localidades.objects.filter(
                catalogo_estado=edomex,
                estatus=1
            ).count()

            if localidades_edomex == 0:
                self.stdout.write('   ❌ Estado de México sin localidades asociadas')
                problemas += 1
            else:
                self.stdout.write(f'   ✅ {localidades_edomex:,} localidades en Estado de México')

        # Verificar municipios del Estado de México
        if edomex:
            municipios_edomex = Localidades.objects.filter(
                catalogo_estado=edomex,
                estatus=1
            ).values('catalogo_municipio__municipio').distinct().count()

            if municipios_edomex > 0:
                self.stdout.write(f'   ✅ {municipios_edomex} municipios diferentes en Estado de México')
            else:
                self.stdout.write('   ⚠️  No se encontraron municipios para Estado de México')

        return problemas

    def _mostrar_estadisticas_detalladas(self):
        """Mostrar estadísticas detalladas de la base de datos."""
        self.stdout.write('\n📈 ESTADÍSTICAS DETALLADAS:')
        self.stdout.write('-' * 30)

        # Top 5 municipios con más localidades
        top_municipios = Municipios.objects.annotate(
            num_localidades=Count('localidades')
        ).order_by('-num_localidades')[:5]

        self.stdout.write('\n🏘️  Top 5 municipios con más localidades:')
        for municipio in top_municipios:
            self.stdout.write(f'   {municipio.municipio}: {municipio.num_localidades} localidades')

        # Top 5 tipos de asentamiento más comunes
        top_tipos = Tipos_Asentamientos.objects.annotate(
            num_localidades=Count('localidades')
        ).order_by('-num_localidades')[:5]

        self.stdout.write('\n🏠 Top 5 tipos de asentamiento:')
        for tipo in top_tipos:
            self.stdout.write(f'   {tipo.tipo_asentamiento}: {tipo.num_localidades} localidades')

        # Rango de códigos postales
        cp_min = Codigos_Postales.objects.filter(estatus=1).order_by('codigo_postal').first()
        cp_max = Codigos_Postales.objects.filter(estatus=1).order_by('-codigo_postal').first()

        if cp_min and cp_max:
            self.stdout.write(f'\n📮 Rango de códigos postales: {cp_min.codigo_postal} - {cp_max.codigo_postal}')