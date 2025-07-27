/**
 * validaciones_vacante.js
 * Script de validaciones para formulario de publicar/editar vacantes
 * Ubicación: BT/static/js/validaciones_vacante.js
 *
 * Funcionalidades:
 * - Validación de fechas (inicio estimada y límite)
 * - Prevención de selección de domingos
 * - Validación de fechas futuras
 * - Validación de diferencia entre fechas
 * - Control de estado del formulario
 */

class ValidadorVacante {
    constructor() {
        // Elementos del DOM
        this.elements = {};
        
        // Estado de validación
        this.validationState = {
            fechaInicio: false,
            fechaLimite: false,
            fechasValidas: false
        };

        // Inicializar cuando el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    /**
     * Inicializa el validador
     */
    init() {
        try {
            this.setupElements();
            this.setupEventListeners();
            this.setMinDates();
            this.validateInitialValues();
            console.log('✅ ValidadorVacante inicializado correctamente');
        } catch (error) {
            console.error('❌ Error al inicializar ValidadorVacante:', error);
        }
    }

    /**
     * Configura las referencias a elementos del DOM
     */
    setupElements() {
        // Campos de fecha
        this.elements.fechaInicio = document.getElementById('id_fecha_inicio_estimada');
        this.elements.fechaLimite = document.getElementById('id_fecha_limite');
        
        // Contenedores para mensajes de error
        this.elements.fechaInicioContainer = this.elements.fechaInicio?.closest('.col-md-6') || this.elements.fechaInicio?.parentElement;
        this.elements.fechaLimiteContainer = this.elements.fechaLimite?.closest('.col-md-6') || this.elements.fechaLimite?.parentElement;
        
        // Botones del formulario
        this.elements.btnPublicar = document.getElementById('btn-publicar');
        this.elements.btnBorrador = document.querySelector('button[name="accion"][value="guardar_borrador"]');
        this.elements.form = document.getElementById('vacanteForm');

        // Verificar que los elementos necesarios existen
        if (!this.elements.fechaInicio || !this.elements.fechaLimite) {
            throw new Error('No se encontraron los campos de fecha requeridos');
        }
    }

    /**
     * Configura los event listeners
     */
    setupEventListeners() {
        // Validación de fecha de inicio
        if (this.elements.fechaInicio) {
            this.elements.fechaInicio.addEventListener('change', () => this.validateFechaInicio());
            this.elements.fechaInicio.addEventListener('input', () => this.validateFechaInicio());
        }

        // Validación de fecha límite
        if (this.elements.fechaLimite) {
            this.elements.fechaLimite.addEventListener('change', () => this.validateFechaLimite());
            this.elements.fechaLimite.addEventListener('input', () => this.validateFechaLimite());
        }

        // Validación antes de enviar el formulario
        if (this.elements.form) {
            this.elements.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }
    }

    /**
     * Establece las fechas mínimas permitidas
     */
    setMinDates() {
        const hoy = new Date();
        const manana = new Date(hoy.getTime() + 24 * 60 * 60 * 1000);
        const fechaMinima = this.formatDateForInput(manana);

        // Establecer fecha mínima para ambos campos
        if (this.elements.fechaInicio) {
            this.elements.fechaInicio.setAttribute('min', fechaMinima);
        }
        
        if (this.elements.fechaLimite) {
            this.elements.fechaLimite.setAttribute('min', fechaMinima);
        }
    }

    /**
     * Valida los valores iniciales (útil para modo edición)
     */
    validateInitialValues() {
        if (this.elements.fechaInicio.value) {
            this.validateFechaInicio();
        }
        if (this.elements.fechaLimite.value) {
            this.validateFechaLimite();
        }
    }

    /**
     * Valida la fecha de inicio estimada
     */
    validateFechaInicio() {
        const fechaInicio = this.elements.fechaInicio.value;
        
        if (!fechaInicio) {
            this.validationState.fechaInicio = true; // Campo opcional
            this.clearFieldError(this.elements.fechaInicio);
            this.validateRelacionFechas();
            return;
        }

        const fecha = new Date(fechaInicio);
        const hoy = new Date();
        
        // Resetear horas para comparación precisa
        hoy.setHours(0, 0, 0, 0);
        fecha.setHours(0, 0, 0, 0);

        let esValida = true;
        let mensaje = '';

        // 1. No puede ser fecha pasada
        if (fecha <= hoy) {
            esValida = false;
            mensaje = 'La fecha de inicio no puede ser hoy o una fecha anterior.';
        }
        // 2. No puede ser domingo
        else if (this.esDomingo(fecha)) {
            esValida = false;
            mensaje = 'No se puede seleccionar domingo como fecha de inicio.';
        }

        this.validationState.fechaInicio = esValida;

        if (esValida) {
            this.clearFieldError(this.elements.fechaInicio);
        } else {
            this.showFieldError(this.elements.fechaInicio, mensaje);
        }

        // Validar relación entre fechas
        this.validateRelacionFechas();
        this.updateSubmitButtons();
    }

    /**
     * Valida la fecha límite
     */
    validateFechaLimite() {
        const fechaLimite = this.elements.fechaLimite.value;
        
        if (!fechaLimite) {
            this.validationState.fechaLimite = false;
            this.showFieldError(this.elements.fechaLimite, 'La fecha límite es obligatoria.');
            this.validateRelacionFechas();
            this.updateSubmitButtons();
            return;
        }

        const fecha = new Date(fechaLimite);
        const hoy = new Date();
        
        // Resetear horas para comparación precisa
        hoy.setHours(0, 0, 0, 0);
        fecha.setHours(0, 0, 0, 0);

        let esValida = true;
        let mensaje = '';

        // 1. No puede ser fecha pasada
        if (fecha <= hoy) {
            esValida = false;
            mensaje = 'La fecha límite no puede ser hoy o una fecha anterior.';
        }
        // 2. No puede ser domingo
        else if (this.esDomingo(fecha)) {
            esValida = false;
            mensaje = 'No se puede seleccionar domingo como fecha límite.';
        }

        this.validationState.fechaLimite = esValida;

        if (esValida) {
            this.clearFieldError(this.elements.fechaLimite);
        } else {
            this.showFieldError(this.elements.fechaLimite, mensaje);
        }

        // Validar relación entre fechas
        this.validateRelacionFechas();
        this.updateSubmitButtons();
    }

    /**
     * Valida la relación entre las fechas de inicio y límite
     */
    validateRelacionFechas() {
        const fechaInicio = this.elements.fechaInicio.value;
        const fechaLimite = this.elements.fechaLimite.value;

        // Si no hay ambas fechas, no hay relación que validar
        if (!fechaInicio || !fechaLimite) {
            this.validationState.fechasValidas = !fechaLimite ? false : true; // fechaLimite es obligatoria
            return;
        }

        const inicio = new Date(fechaInicio);
        const limite = new Date(fechaLimite);
        
        // Resetear horas para comparación precisa
        inicio.setHours(0, 0, 0, 0);
        limite.setHours(0, 0, 0, 0);

        let relacionValida = true;
        let mensaje = '';

        // 1. Las fechas no pueden ser el mismo día
        if (inicio.getTime() === limite.getTime()) {
            relacionValida = false;
            mensaje = 'La fecha de inicio y la fecha límite no pueden ser el mismo día.';
            this.showFieldError(this.elements.fechaLimite, mensaje);
        }
        // 2. La fecha límite no puede ser posterior a la fecha de inicio
        else if (limite >= inicio) {
            relacionValida = false;
            mensaje = 'La fecha límite debe ser anterior a la fecha de inicio estimada.';
            this.showFieldError(this.elements.fechaLimite, mensaje);
        }
        // 3. Debe haber al menos un día de diferencia
        else {
            const diferenciaDias = Math.ceil((inicio.getTime() - limite.getTime()) / (1000 * 60 * 60 * 24));
            if (diferenciaDias < 1) {
                relacionValida = false;
                mensaje = 'Debe haber al menos un día de diferencia entre la fecha límite y la fecha de inicio.';
                this.showFieldError(this.elements.fechaLimite, mensaje);
            }
        }

        this.validationState.fechasValidas = relacionValida;

        if (relacionValida && fechaLimite) {
            this.clearFieldError(this.elements.fechaLimite);
        }
    }

    /**
     * Verifica si una fecha es domingo
     */
    esDomingo(fecha) {
        return fecha.getDay() === 0; // 0 = Domingo
    }

    /**
     * Formatea una fecha para input type="date"
     */
    formatDateForInput(fecha) {
        return fecha.toISOString().split('T')[0];
    }

    /**
     * Muestra un error en un campo específico
     */
    showFieldError(field, mensaje) {
        // Limpiar errores anteriores
        this.clearFieldError(field);

        // Agregar clase de error al campo
        field.classList.add('is-invalid');

        // Crear mensaje de error
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback fecha-validation-error';
        errorDiv.style.display = 'block';
        errorDiv.innerHTML = `<i class="bi bi-exclamation-circle me-1"></i>${mensaje}`;

        // Insertar después del campo
        field.parentNode.insertBefore(errorDiv, field.nextSibling);
    }

    /**
     * Limpia los errores de un campo específico
     */
    clearFieldError(field) {
        field.classList.remove('is-invalid');
        
        // Remover mensajes de error existentes
        const errorMessages = field.parentNode.querySelectorAll('.fecha-validation-error');
        errorMessages.forEach(msg => msg.remove());
    }

    /**
     * Actualiza el estado de los botones del formulario
     */
    updateSubmitButtons() {
        const todasLasValidacionesOk = this.validationState.fechaInicio && 
                                      this.validationState.fechaLimite && 
                                      this.validationState.fechasValidas;

        // Actualizar botón de publicar
        if (this.elements.btnPublicar) {
            this.elements.btnPublicar.disabled = !todasLasValidacionesOk;
            
            if (todasLasValidacionesOk) {
                this.elements.btnPublicar.classList.remove('btn-secondary');
                this.elements.btnPublicar.classList.add('btn-primary');
                this.elements.btnPublicar.innerHTML = '<i class="bi bi-send-check-fill"></i> Publicar Vacante';
                this.elements.btnPublicar.title = 'Listo para publicar';
            } else {
                this.elements.btnPublicar.classList.remove('btn-primary');
                this.elements.btnPublicar.classList.add('btn-secondary');
                this.elements.btnPublicar.innerHTML = '<i class="bi bi-exclamation-circle"></i> Revisar Fechas';
                this.elements.btnPublicar.title = 'Corrige las fechas antes de publicar';
            }
        }

        // El botón de borrador siempre está habilitado (permite guardar borradores con fechas pendientes)
        if (this.elements.btnBorrador) {
            this.elements.btnBorrador.disabled = false;
        }
    }

    /**
     * Maneja el envío del formulario
     */
    handleSubmit(event) {
        const accion = event.submitter?.value || '';
        
        // Si es para guardar borrador, permitir el envío sin validar fechas
        if (accion === 'guardar_borrador') {
            console.log('💾 Guardando como borrador - validaciones de fecha omitidas');
            return true;
        }

        // Para publicar, validar todas las fechas
        if (accion === 'publicar') {
            this.validateFechaInicio();
            this.validateFechaLimite();

            const todasValidasParaPublicar = this.validationState.fechaInicio && 
                                           this.validationState.fechaLimite && 
                                           this.validationState.fechasValidas;

            if (!todasValidasParaPublicar) {
                event.preventDefault();
                event.stopPropagation();

                // Mostrar alerta general
                this.showAlert(
                    'No se puede publicar la vacante. Por favor, corrige los errores en las fechas.',
                    'error'
                );

                // Enfocar el primer campo con error
                const primerCampoConError = document.querySelector('.is-invalid');
                if (primerCampoConError) {
                    primerCampoConError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    primerCampoConError.focus();
                }

                console.warn('❌ Publicación bloqueada - Errores en fechas');
                return false;
            }
        }

        console.log('✅ Formulario válido - Permitiendo envío');
        return true;
    }

    /**
     * Muestra una alerta temporal
     */
    showAlert(mensaje, tipo) {
        // Eliminar alertas anteriores
        const alertasAnteriores = document.querySelectorAll('.fecha-validation-alert');
        alertasAnteriores.forEach(alerta => alerta.remove());

        // Crear nueva alerta
        const alerta = document.createElement('div');
        alerta.className = `alert alert-${tipo === 'error' ? 'danger' : 'success'} alert-dismissible fade show fecha-validation-alert`;
        alerta.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px; max-width: 500px;';

        alerta.innerHTML = `
            <i class="bi bi-${tipo === 'error' ? 'exclamation-triangle' : 'check-circle'} me-2"></i>
            ${mensaje}
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;

        document.body.appendChild(alerta);

        // Auto-remover después de 7 segundos
        setTimeout(() => {
            if (alerta.parentNode) {
                alerta.remove();
            }
        }, 7000);
    }

    /**
     * Método público para validar manualmente
     */
    validarTodo() {
        this.validateFechaInicio();
        this.validateFechaLimite();
        return this.validationState.fechaInicio && 
               this.validationState.fechaLimite && 
               this.validationState.fechasValidas;
    }

    /**
     * Método público para obtener el estado de validación
     */
    obtenerEstadoValidacion() {
        return {
            ...this.validationState,
            puedePublicar: this.validationState.fechaInicio && 
                          this.validationState.fechaLimite && 
                          this.validationState.fechasValidas
        };
    }
}

// Auto-inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Solo inicializar si estamos en la página de publicar/editar vacante
    if (document.getElementById('vacanteForm')) {
        window.validadorVacante = new ValidadorVacante();
        console.log('🚀 Validador de vacantes iniciado');

        // Mensaje informativo para el usuario
        const mensaje = document.createElement('div');
        mensaje.className = 'alert alert-info mt-3';
        mensaje.innerHTML = `
            <i class="bi bi-info-circle me-2"></i>
            <strong>Recordatorio:</strong> 
            <ul class="mb-0 mt-2">
                <li>No se pueden seleccionar fechas pasadas o domingos</li>
                <li>La fecha límite debe ser anterior a la fecha de inicio</li>
                <li>Debe haber al menos un día de diferencia entre ambas fechas</li>
                <li>La vacante se cerrará automáticamente al llegar a la fecha límite o al máximo de postulantes</li>
            </ul>
        `;

        // Insertar el mensaje después de la sección de fechas
        const fechasSection = document.querySelector('.card:has(#id_fecha_limite)');
        if (fechasSection) {
            fechasSection.after(mensaje);
        }
    }
});

// Exportar para uso en módulos (si es necesario)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ValidadorVacante };
}