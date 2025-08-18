// static/js/gestion-vacantes.js
// Sistema avanzado de gestión de vacantes para reclutadores

class GestionVacantes {
    constructor() {
        this.csrfToken = this.obtenerCSRFToken();
        this.init();
    }

    init() {
        this.configurarEventListeners();
        this.verificarEstadosVacantes();
    }

    /**
     * Configura los event listeners globales
     */
    configurarEventListeners() {
        // Escuchar clics en botones de acción
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-accion-vacante]')) {
                e.preventDefault();
                const accion = e.target.dataset.accionVacante;
                const vacanteId = e.target.dataset.vacanteId;
                const titulo = e.target.dataset.vacanteTitulo;
                this.ejecutarAccion(accion, vacanteId, titulo);
            }
        });

        // Verificar estado periódicamente para vacantes activas
        setInterval(() => {
            this.verificarEstadosVacantes();
        }, 30000); // Cada 30 segundos
    }

    /**
     * Verifica el estado actual de todas las vacantes visibles
     */
    async verificarEstadosVacantes() {
        const tarjetas = document.querySelectorAll('[id^="vacante-card-"]');

        for (const tarjeta of tarjetas) {
            const vacanteId = tarjeta.id.replace('vacante-card-', '');
            try {
                await this.actualizarEstadoVacante(vacanteId);
            } catch (error) {
            }
        }
    }

    /**
     * Actualiza el estado de una vacante específica
     */
    async actualizarEstadoVacante(vacanteId) {
        try {
            const response = await fetch(`/ajax/estado-vacante/${vacanteId}/`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            });

            if (response.ok) {
                const resultado = await response.json();
                if (resultado.success) {
                    this.sincronizarInterfaz(vacanteId, resultado);
                }
            }
        } catch (error) {
            // Silenciar errores de verificación para no molestar al usuario
        }
    }

    /**
     * Sincroniza la interfaz con el estado real de la vacante
     */
    sincronizarInterfaz(vacanteId, datos) {
        // Actualizar badge de estado
        const badge = document.getElementById(`estado-badge-${vacanteId}`);
        if (badge && badge.dataset.estado !== datos.estado) {
            badge.dataset.estado = datos.estado;
            // Trigger actualización visual sutil
            badge.style.transform = 'scale(1.05)';
            setTimeout(() => {
                badge.style.transform = 'scale(1)';
            }, 200);
        }

        // Actualizar información de postulaciones
        const infoPostulaciones = document.getElementById(`postulaciones-info-${vacanteId}`);
        if (infoPostulaciones) {
            const postulacionesActuales = parseInt(
                infoPostulaciones.querySelector('.fw-bold')?.textContent || '0'
            );

            if (postulacionesActuales !== datos.postulaciones_actuales) {
                // Hay cambios en las postulaciones
                this.actualizarContadorPostulaciones(vacanteId, datos);
                this.mostrarNotificacionSutil(`Nueva postulación en "${datos.titulo}"`);
            }
        }
    }

    /**
     * Actualiza el contador de postulaciones con animación
     */
    actualizarContadorPostulaciones(vacanteId, datos) {
        const infoPostulaciones = document.getElementById(`postulaciones-info-${vacanteId}`);
        if (!infoPostulaciones) return;

        let html = `<i class="bi bi-people-fill"></i>
                   Postulantes: <span class="fw-bold">${datos.postulaciones_actuales}</span> / ${datos.limite_postulaciones}`;

        if (datos.postulaciones_actuales >= datos.limite_postulaciones) {
            html += ' <span class="badge bg-warning text-dark ms-1">LLENA</span>';
        } else if (datos.estado === 'cerrada') {
            html += ' <span class="badge bg-danger ms-1">CERRADA</span>';
        }

        infoPostulaciones.innerHTML = html;

        // Animación de destaque
        infoPostulaciones.style.backgroundColor = 'rgba(25, 135, 84, 0.1)';
        setTimeout(() => {
            infoPostulaciones.style.backgroundColor = 'transparent';
        }, 1000);
    }

    /**
     * Muestra una notificación sutil no intrusiva
     */
    mostrarNotificacionSutil(mensaje) {
        // Verificar si ya hay una notificación
        if (document.querySelector('.notificacion-sutil')) return;

        const notificacion = document.createElement('div');
        notificacion.className = 'notificacion-sutil';
        notificacion.innerHTML = `
            <i class="bi bi-bell-fill me-2"></i>
            ${mensaje}
        `;

        notificacion.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            padding: 12px 20px;
            border-radius: 25px;
            font-size: 0.875rem;
            z-index: 1050;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
            max-width: 300px;
        `;

        document.body.appendChild(notificacion);

        // Animación de entrada
        setTimeout(() => {
            notificacion.style.opacity = '1';
            notificacion.style.transform = 'translateX(0)';
        }, 100);

        // Auto-remover
        setTimeout(() => {
            notificacion.style.opacity = '0';
            notificacion.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notificacion.parentNode) {
                    notificacion.remove();
                }
            }, 300);
        }, 4000);
    }

    /**
     * Obtiene el token CSRF de diferentes fuentes
     */
    obtenerCSRFToken() {
        // Buscar en meta tag
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }

        // Buscar en input hidden
        const inputTag = document.querySelector('[name=csrfmiddlewaretoken]');
        if (inputTag) {
            return inputTag.value;
        }

        // Buscar en cookies
        return this.getCookie('csrftoken');
    }

    /**
     * Función auxiliar para obtener cookies
     */
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Método para refrescar manualmente el estado de todas las vacantes
     */
    async refrescarEstados() {
        const botonRefresh = document.getElementById('refresh-estados');
        if (botonRefresh) {
            botonRefresh.disabled = true;
            botonRefresh.innerHTML = '<i class="bi bi-arrow-clockwise spin"></i> Actualizando...';
        }

        await this.verificarEstadosVacantes();

        if (botonRefresh) {
            botonRefresh.disabled = false;
            botonRefresh.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refrescar';
        }

        this.mostrarNotificacionSutil('Estados actualizados');
    }

    /**
     * Método para exportar estadísticas de vacantes
     */
    exportarEstadisticas() {
        const tarjetas = document.querySelectorAll('[id^="vacante-card-"]');
        const estadisticas = [];

        tarjetas.forEach(tarjeta => {
            const vacanteId = tarjeta.id.replace('vacante-card-', '');
            const titulo = tarjeta.querySelector('.card-title')?.textContent?.trim();
            const estado = tarjeta.querySelector('.estado-badge')?.dataset?.estado;
            const postulaciones = tarjeta.querySelector('#postulaciones-info-' + vacanteId)?.textContent;

            estadisticas.push({
                id: vacanteId,
                titulo,
                estado,
                postulaciones
            });
        });

        // Crear y descargar archivo CSV
        const csv = this.convertirACSV(estadisticas);
        this.descargarArchivo(csv, 'estadisticas_vacantes.csv', 'text/csv');
    }

    /**
     * Convierte datos a formato CSV
     */
    convertirACSV(datos) {
        const headers = ['ID', 'Título', 'Estado', 'Postulaciones'];
        const filas = datos.map(row => [
            row.id,
            `"${row.titulo || ''}"`,
            row.estado || '',
            row.postulaciones || ''
        ]);

        return [headers, ...filas].map(row => row.join(',')).join('\n');
    }

    /**
     * Descarga un archivo
     */
    descargarArchivo(contenido, nombreArchivo, tipoMime) {
        const blob = new Blob([contenido], { type: tipoMime });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = nombreArchivo;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
}

// Estilos CSS adicionales para las animaciones
const estilosAdicionales = `
<style>
.spin {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.notificacion-sutil {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    backdrop-filter: blur(10px);
}

.estado-badge {
    transition: transform 0.2s ease;
}

.vacancy-card {
    transition: all 0.3s ease;
}

.vacancy-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}

@media (prefers-reduced-motion: reduce) {
    .spin, .vacancy-card {
        animation: none !important;
        transition: none !important;
    }
}
</style>
`;

// Inyectar estilos
document.head.insertAdjacentHTML('beforeend', estilosAdicionales);

// Auto-inicialización
document.addEventListener('DOMContentLoaded', function() {
    window.gestionVacantes = new GestionVacantes();
});

// Exportar para uso global
window.GestionVacantes = GestionVacantes;