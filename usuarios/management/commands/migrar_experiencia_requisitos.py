# usuarios/management/commands/migrar_experiencia_requisitos.py
from django.core.management.base import BaseCommand
from usuarios.models import RequisitoVacante
import re


class Command(BaseCommand):
    help = 'Migra los datos existentes de experiencia_minima de texto libre a choices predefinidos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué cambios se harían sin ejecutarlos',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING('🔄 MIGRANDO DATOS DE EXPERIENCIA A CHOICES')
        )
        self.stdout.write('=' * 50)

        # Obtener todos los requisitos con experiencia_minima no vacía
        requisitos = RequisitoVacante.objects.exclude(
            experiencia_minima__isnull=True
        ).exclude(experiencia_minima='')

        if not requisitos.exists():
            self.stdout.write(
                self.style.SUCCESS('✅ No hay datos de experiencia para migrar.')
            )
            return

        migrados = 0
        no_migrados = 0
        errores = []

        for requisito in requisitos:
            texto_original = requisito.experiencia_minima
            nuevo_valor = self.convertir_experiencia(texto_original)

            if nuevo_valor:
                if options['dry_run']:
                    self.stdout.write(
                        f'  🔄 "{texto_original}" → "{nuevo_valor}"'
                    )
                else:
                    requisito.experiencia_minima = nuevo_valor
                    requisito.save()
                    self.stdout.write(
                        f'  ✅ Migrado: "{texto_original}" → "{nuevo_valor}"'
                    )
                migrados += 1
            else:
                mensaje_error = f'❌ No se pudo migrar: "{texto_original}" (Vacante: {requisito.vacante.titulo})'
                errores.append(mensaje_error)
                self.stdout.write(mensaje_error)
                no_migrados += 1

        # Resumen
        self.stdout.write('\n' + '=' * 50)
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Se migrarían {migrados} registros')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Migrados exitosamente: {migrados} registros')
            )

        if no_migrados > 0:
            self.stdout.write(
                self.style.ERROR(f'❌ No migrados: {no_migrados} registros')
            )
            self.stdout.write('\nRECOMENDADO: Revisar manualmente los casos no migrados.')

    def convertir_experiencia(self, texto):
        """
        Convierte texto libre de experiencia a una de las opciones predefinidas.

        Ejemplos:
        - "3+ años" → "3"
        - "Sin experiencia" → "0"
        - "Más de 5 años" → "5"
        - "10 años o más" → "10+"
        """
        if not texto:
            return None

        texto = texto.lower().strip()

        # Casos especiales primero
        if any(palabra in texto for palabra in ['sin experiencia', 'no requiere', 'principiante', 'junior']):
            return '0'

        if any(palabra in texto for palabra in ['más de 10', 'superior a 10', '10+']):
            return '10+'

        # Buscar números en el texto
        numeros = re.findall(r'\d+', texto)

        if not numeros:
            # Si no hay números, pero menciona años, asumir que es experiencia requerida
            if 'año' in texto or 'experiencia' in texto:
                return '1'  # Valor por defecto
            return None

        # Tomar el primer número encontrado
        primer_numero = int(numeros[0])

        # Mapear a nuestras opciones
        if primer_numero == 0:
            return '0'
        elif primer_numero <= 10:
            return str(primer_numero)
        else:
            return '10+'

    def mostrar_estadisticas(self):
        """Muestra estadísticas de los datos actuales."""
        self.stdout.write('\n📊 ESTADÍSTICAS ACTUALES:')

        total = RequisitoVacante.objects.count()
        con_experiencia = RequisitoVacante.objects.exclude(
            experiencia_minima__isnull=True
        ).exclude(experiencia_minima='').count()

        self.stdout.write(f'  Total de requisitos: {total}')
        self.stdout.write(f'  Con experiencia definida: {con_experiencia}')
        self.stdout.write(f'  Sin experiencia definida: {total - con_experiencia}')

        # Mostrar algunos ejemplos
        ejemplos = RequisitoVacante.objects.exclude(
            experiencia_minima__isnull=True
        ).exclude(experiencia_minima='')[:5]

        if ejemplos.exists():
            self.stdout.write('\n🔍 EJEMPLOS DE DATOS ACTUALES:')
            for req in ejemplos:
                self.stdout.write(f'  - "{req.experiencia_minima}"')

        self.stdout.write('\n' + '-' * 50)