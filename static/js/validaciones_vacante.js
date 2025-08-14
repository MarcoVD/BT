class ValidadorFechasVacante {
    constructor() {
        // Referencias a elementos del DOM
        this.elementosDOM = {};
        
        // Estado de validación
        this.estadoValidacion = {
            fechaInicioValida: false,
            fechaLimiteValida: false,
            relacionFechasValida: false,
            formularioListo: false
        };

        // Configuración de mensajes de error
        this.mensajesError = {
            fechaPasada: 'No se pueden seleccionar fechas pasadas. La fecha debe ser posterior a hoy.',
            fechasDuplicadas: 'La fecha de inicio y la fecha límite no pueden ser el mismo día.',
            fechaInicioAnterior: 'La fecha de inicio debe ser al menos un día después de la fecha límite.',
            fechaLimiteRequerida: 'La fecha límite de postulación es obligatoria.',
            fechaInvalida: 'Por favor, selecciona una fecha válida.',
            // domingoNoPermitido: 'No se pueden seleccionar domingos. Las postulaciones no están disponibles los domingos.'
        };

        // Inicializar cuando el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.inicializar());
        } else {
            this.inicializar();
        }
    }

    /**
     * Inicializa el validador de fechas
     */
    inicializar() {
        try {
            this.configurarElementosDOM();
            this.configurarEventos();
            this.establecerFechasMinimas();
            this.validarValoresIniciales();
            console.log('✅ ValidadorFechasVacante inicializado correctamente');
        } catch (error) {
            console.error('❌ Error al inicializar ValidadorFechasVacante:', error);
        }
    }

    /**
     * Configura las referencias a elementos del DOM
     */
    configurarElementosDOM() {
        // Campos de fecha principales
        this.elementosDOM.campoFechaInicio = document.getElementById('id_fecha_inicio_estimada');
        this.elementosDOM.campoFechaLimite = document.getElementById('id_fecha_limite');
        
        // Contenedores para mensajes de error
        this.elementosDOM.contenedorFechaInicio = this.elementosDOM.campoFechaInicio?.closest('.col-md-6') || 
                                                  this.elementosDOM.campoFechaInicio?.parentElement;
        this.elementosDOM.contenedorFechaLimite = this.elementosDOM.campoFechaLimite?.closest('.col-md-6') || 
                                                  this.elementosDOM.campoFechaLimite?.parentElement;
        
        // Elementos del formulario
        this.elementosDOM.botonPublicar = document.getElementById('btn-publicar');
        this.elementosDOM.botonBorrador = document.querySelector('button[name="accion"][value="guardar_borrador"]');
        this.elementosDOM.formulario = document.getElementById('vacanteForm');

        // Verificar elementos críticos
        if (!this.elementosDOM.campoFechaLimite) {
            throw new Error('No se encontró el campo de fecha límite (requerido)');
        }
    }

    /**
     * Configura los event listeners para validación en tiempo real
     */
    configurarEventos() {
        // Eventos para fecha de inicio (opcional)
        if (this.elementosDOM.campoFechaInicio) {
            this.elementosDOM.campoFechaInicio.addEventListener('change', () => this.validarFechaInicio());
            this.elementosDOM.campoFechaInicio.addEventListener('input', () => this.validarFechaInicio());
        }

        // Eventos para fecha límite (obligatoria)
        this.elementosDOM.campoFechaLimite.addEventListener('change', () => this.validarFechaLimite());
        this.elementosDOM.campoFechaLimite.addEventListener('input', () => this.validarFechaLimite());

        // Validación antes de enviar el formulario
        if (this.elementosDOM.formulario) {
            this.elementosDOM.formulario.addEventListener('submit', (evento) => this.manejarEnvioFormulario(evento));
        }
    }

    /**
     * Establece las fechas mínimas permitidas (mañana)
     */
    establecerFechasMinimas() {
        const fechaHoy = new Date();
        const fechaManana = new Date(fechaHoy.getTime() + 24 * 60 * 60 * 1000);
        const fechaMinimaFormateada = this.formatearFechaParaInput(fechaManana);

        // Establecer fecha mínima para ambos campos
        if (this.elementosDOM.campoFechaInicio) {
            this.elementosDOM.campoFechaInicio.setAttribute('min', fechaMinimaFormateada);
        }
        
        this.elementosDOM.campoFechaLimite.setAttribute('min', fechaMinimaFormateada);
    }

    /**
     * Valida los valores iniciales (útil para modo edición)
     */
    validarValoresIniciales() {
        if (this.elementosDOM.campoFechaInicio?.value) {
            this.validarFechaInicio();
        }
        if (this.elementosDOM.campoFechaLimite.value) {
            this.validarFechaLimite();
        }
    }

    /**
     * Valida la fecha de inicio estimada
     */
    validarFechaInicio() {
        const valorFechaInicio = this.elementosDOM.campoFechaInicio?.value;
        
        if (!valorFechaInicio) {
            // Campo opcional - si está vacío es válido
            this.estadoValidacion.fechaInicioValida = true;
            this.limpiarErroresCampo(this.elementosDOM.campoFechaInicio);
            this.validarRelacionEntreFechas();
            this.actualizarEstadoBotones();
            return;
        }

        const fechaInicioSeleccionada = new Date(valorFechaInicio + 'T00:00:00');
        let esFechaValida = true;
        let mensajeError = '';

        console.log(`Validando fecha inicio: ${valorFechaInicio} - Objeto Date: ${fechaInicioSeleccionada.toDateString()}`);

        // Validación I: Verificar formato y fecha válida
        if (isNaN(fechaInicioSeleccionada.getTime())) {
            esFechaValida = false;
            mensajeError = this.mensajesError.fechaInvalida;
        }
        // Validación III: No puede ser fecha pasada
        else if (this.esFechaPasada(fechaInicioSeleccionada)) {
            esFechaValida = false;
            mensajeError = this.mensajesError.fechaPasada;
        }
        // Validación adicional: No domingos
        // else if (this.esDomingo(fechaInicioSeleccionada)) {
        //     esFechaValida = false;
        //     mensajeError = this.mensajesError.domingoNoPermitido;
        // }

        this.estadoValidacion.fechaInicioValida = esFechaValida;

        if (esFechaValida) {
            this.limpiarErroresCampo(this.elementosDOM.campoFechaInicio);
        } else {
            this.mostrarErrorCampo(this.elementosDOM.campoFechaInicio, mensajeError);
        }

        // Validar relación entre fechas
        this.validarRelacionEntreFechas();
        this.actualizarEstadoBotones();
    }

    /**
     * Valida la fecha límite de postulación
     */
    validarFechaLimite() {
        const valorFechaLimite = this.elementosDOM.campoFechaLimite.value;
        
        if (!valorFechaLimite) {
            // Campo obligatorio
            this.estadoValidacion.fechaLimiteValida = false;
            this.mostrarErrorCampo(this.elementosDOM.campoFechaLimite, this.mensajesError.fechaLimiteRequerida);
            this.validarRelacionEntreFechas();
            this.actualizarEstadoBotones();
            return;
        }

        const fechaLimiteSeleccionada = new Date(valorFechaLimite + 'T00:00:00');
        let esFechaValida = true;
        let mensajeError = '';

        console.log(`Validando fecha límite: ${valorFechaLimite} - Objeto Date: ${fechaLimiteSeleccionada.toDateString()}`);

        // Validación I: Verificar formato y fecha válida
        if (isNaN(fechaLimiteSeleccionada.getTime())) {
            esFechaValida = false;
            mensajeError = this.mensajesError.fechaInvalida;
        }
        // Validación III: No puede ser fecha pasada
        else if (this.esFechaPasada(fechaLimiteSeleccionada)) {
            esFechaValida = false;
            mensajeError = this.mensajesError.fechaPasada;
        }
        // // Validación adicional: No domingos
        // else if (this.esDomingo(fechaLimiteSeleccionada)) {
        //     esFechaValida = false;
        //     mensajeError = this.mensajesError.domingoNoPermitido;
        // }

        this.estadoValidacion.fechaLimiteValida = esFechaValida;

        if (esFechaValida) {
            this.limpiarErroresCampo(this.elementosDOM.campoFechaLimite);
        } else {
            this.mostrarErrorCampo(this.elementosDOM.campoFechaLimite, mensajeError);
        }

        // Validar relación entre fechas
        this.validarRelacionEntreFechas();
        this.actualizarEstadoBotones();
    }

    /**
     * Valida la relación entre fechas según las restricciones
     */
    validarRelacionEntreFechas() {
        const valorFechaInicio = this.elementosDOM.campoFechaInicio?.value;
        const valorFechaLimite = this.elementosDOM.campoFechaLimite.value;

        // Si no hay fecha límite, no hay relación que validar
        if (!valorFechaLimite) {
            this.estadoValidacion.relacionFechasValida = false;
            return;
        }

        // Si no hay fecha de inicio, la relación es válida (campo opcional)
        if (!valorFechaInicio) {
            this.estadoValidacion.relacionFechasValida = true;
            return;
        }

        const fechaInicioObj = new Date(valorFechaInicio + 'T00:00:00');
        const fechaLimiteObj = new Date(valorFechaLimite + 'T00:00:00');
        
        console.log(`Comparando fechas - Inicio: ${fechaInicioObj.toDateString()} vs Límite: ${fechaLimiteObj.toDateString()}`);

        let relacionValida = true;
        let mensajeError = '';

        // Validación II: Las fechas no pueden ser el mismo día
        if (fechaInicioObj.getTime() === fechaLimiteObj.getTime()) {
            relacionValida = false;
            mensajeError = this.mensajesError.fechasDuplicadas;
            console.log('Error: Fechas son el mismo día');
        }
        // Validación IV: fecha inicio debe ser al menos un día después de fecha límite
        else if (fechaInicioObj.getTime() <= fechaLimiteObj.getTime()) {
            relacionValida = false;
            mensajeError = this.mensajesError.fechaInicioAnterior;
            console.log('Error: Fecha inicio no es posterior a fecha límite');
        }
        // Verificar que haya al menos un día de diferencia
        else {
            const diferenciaMilisegundos = fechaInicioObj.getTime() - fechaLimiteObj.getTime();
            const diferenciaDias = Math.ceil(diferenciaMilisegundos / (1000 * 60 * 60 * 24));
            
            console.log(`Diferencia en días: ${diferenciaDias}`);
            
            if (diferenciaDias < 1) {
                relacionValida = false;
                mensajeError = this.mensajesError.fechaInicioAnterior;
                console.log('Error: Diferencia menor a 1 día');
            } else {
                console.log('✅ Relación entre fechas válida');
            }
        }

        this.estadoValidacion.relacionFechasValida = relacionValida;

        if (relacionValida) {
            // Limpiar errores de relación en ambos campos
            this.limpiarErroresRelacion();
        } else {
            // Mostrar error en el campo de fecha inicio principalmente
            if (this.elementosDOM.campoFechaInicio) {
                this.mostrarErrorCampo(this.elementosDOM.campoFechaInicio, mensajeError);
            }
        }
    }

    /**
     * Verifica si una fecha es del pasado
     */
    esFechaPasada(fechaAComparar) {
        const fechaHoy = new Date();
        fechaHoy.setHours(0, 0, 0, 0);
        
        const fechaParaValidar = new Date(fechaAComparar);
        fechaParaValidar.setHours(0, 0, 0, 0);
        
        const esDelPasado = fechaParaValidar <= fechaHoy;
        console.log(`Verificando si es fecha pasada - Fecha: ${fechaParaValidar.toDateString()}, Hoy: ${fechaHoy.toDateString()}, ¿Es pasada?: ${esDelPasado}`);
        
        return esDelPasado;
    }

    /**
     * Verifica si una fecha es domingo
     * En JavaScript: 0=Domingo, 1=Lunes, 2=Martes, 3=Miércoles, 4=Jueves, 5=Viernes, 6=Sábado
     */
    esDomingo(fechaAValidar) {
        const diaDeLaSemana = fechaAValidar.getDay();
        console.log(`Verificando si es domingo - Fecha: ${fechaAValidar.toDateString()}, Día: ${diaDeLaSemana} (0=Dom, 1=Lun, 2=Mar, 3=Mié, 4=Jue, 5=Vie, 6=Sáb)`);
        return diaDeLaSemana === 0; // 0 = Domingo en JavaScript
    }

    /**
     * Formatea una fecha para input type="date" (YYYY-MM-DD)
     */
    formatearFechaParaInput(fecha) {
        return fecha.toISOString().split('T')[0];
    }

    /**
     * Muestra un error en un campo específico
     */
    mostrarErrorCampo(campo, mensaje) {
        // Limpiar errores anteriores
        this.limpiarErroresCampo(campo);

        // Agregar clase de error
        campo.classList.add('is-invalid');

        // Crear mensaje de error
        const elementoError = document.createElement('div');
        elementoError.className = 'invalid-feedback validacion-fecha-error';
        elementoError.style.display = 'block';
        elementoError.innerHTML = `<i class="bi bi-exclamation-circle me-1"></i>${mensaje}`;

        // Insertar después del campo
        campo.parentNode.insertBefore(elementoError, campo.nextSibling);
    }

    /**
     * Limpia los errores de un campo específico
     */
    limpiarErroresCampo(campo) {
        if (!campo) return;
        
        campo.classList.remove('is-invalid');
        
        // Remover mensajes de error existentes
        const mensajesError = campo.parentNode.querySelectorAll('.validacion-fecha-error');
        mensajesError.forEach(mensaje => mensaje.remove());
    }

    /**
     * Limpia errores de relación entre fechas
     */
    limpiarErroresRelacion() {
        if (this.elementosDOM.campoFechaInicio) {
            this.limpiarErroresCampo(this.elementosDOM.campoFechaInicio);
        }
        this.limpiarErroresCampo(this.elementosDOM.campoFechaLimite);
    }

    /**
     * Actualiza el estado de los botones del formulario
     */
    actualizarEstadoBotones() {
        const todasLasValidacionesCorrectas = this.estadoValidacion.fechaInicioValida && 
                                             this.estadoValidacion.fechaLimiteValida && 
                                             this.estadoValidacion.relacionFechasValida;

        this.estadoValidacion.formularioListo = todasLasValidacionesCorrectas;

        // Actualizar botón de publicar
        if (this.elementosDOM.botonPublicar) {
            this.elementosDOM.botonPublicar.disabled = !todasLasValidacionesCorrectas;
            
            if (todasLasValidacionesCorrectas) {
                this.elementosDOM.botonPublicar.classList.remove('btn-secondary');
                this.elementosDOM.botonPublicar.classList.add('btn-primary');
                this.elementosDOM.botonPublicar.innerHTML = '<i class="bi bi-send-check-fill"></i> Publicar Vacante';
                this.elementosDOM.botonPublicar.title = 'Listo para publicar';
            } else {
                this.elementosDOM.botonPublicar.classList.remove('btn-primary');
                this.elementosDOM.botonPublicar.classList.add('btn-secondary');
                this.elementosDOM.botonPublicar.innerHTML = '<i class="bi bi-exclamation-circle"></i> Revisar Fechas';
                this.elementosDOM.botonPublicar.title = 'Corrige las fechas antes de publicar';
            }
        }

        // El botón de borrador siempre está habilitado
        if (this.elementosDOM.botonBorrador) {
            this.elementosDOM.botonBorrador.disabled = false;
        }
    }

    /**
     * Maneja el envío del formulario
     */
    manejarEnvioFormulario(evento) {
        const accionFormulario = evento.submitter?.value || 'publicar';
        
        // Si es para guardar borrador, permitir el envío sin validar fechas
        if (accionFormulario === 'guardar_borrador') {
            console.log('💾 Guardando como borrador - validaciones de fecha omitidas');
            return true;
        }

        // Para publicar, validar todas las fechas
        if (accionFormulario === 'publicar') {
            // Re-validar todo antes de enviar
            this.validarFechaInicio();
            this.validarFechaLimite();

            if (!this.estadoValidacion.formularioListo) {
                evento.preventDefault();
                evento.stopPropagation();

                // Mostrar alerta general
                this.mostrarAlertaGeneral(
                    'No se puede publicar la vacante. Por favor, corrige los errores en las fechas.',
                    'error'
                );

                // Enfocar el primer campo con error
                const primerCampoConError = document.querySelector('.is-invalid');
                if (primerCampoConError) {
                    primerCampoConError.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'center' 
                    });
                    primerCampoConError.focus();
                }

                console.warn('❌ Publicación bloqueada - Errores en fechas');
                return false;
            }
        }

        console.log('✅ Validación de fechas completada - Permitiendo envío');
        return true;
    }

    /**
     * Muestra una alerta temporal
     */
    mostrarAlertaGeneral(mensaje, tipo) {
        // Eliminar alertas anteriores
        const alertasAnteriores = document.querySelectorAll('.alerta-validacion-fechas');
        alertasAnteriores.forEach(alerta => alerta.remove());

        // Crear nueva alerta
        const alerta = document.createElement('div');
        alerta.className = `alert alert-${tipo === 'error' ? 'danger' : 'success'} alert-dismissible fade show alerta-validacion-fechas`;
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
     * Método público para validar manualmente todo
     */
    validarTodoManualmente() {
        this.validarFechaInicio();
        this.validarFechaLimite();
        return this.estadoValidacion.formularioListo;
    }

    /**
     * Método público para obtener el estado de validación
     */
    obtenerEstadoValidacionCompleto() {
        return {
            ...this.estadoValidacion,
            puedePublicar: this.estadoValidacion.formularioListo,
            resumenValidaciones: {
                fechaInicio: this.estadoValidacion.fechaInicioValida ? 'Válida' : 'Inválida',
                fechaLimite: this.estadoValidacion.fechaLimiteValida ? 'Válida' : 'Inválida',
                relacionFechas: this.estadoValidacion.relacionFechasValida ? 'Válida' : 'Inválida'
            }
        };
    }

    /**
     * Método para limpiar todas las validaciones
     */
    limpiarTodasLasValidaciones() {
        this.limpiarErroresCampo(this.elementosDOM.campoFechaInicio);
        this.limpiarErroresCampo(this.elementosDOM.campoFechaLimite);
        
        // Resetear estado
        this.estadoValidacion = {
            fechaInicioValida: false,
            fechaLimiteValida: false,
            relacionFechasValida: false,
            formularioListo: false
        };
        
        this.actualizarEstadoBotones();
    }
}

// Auto-inicialización cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Solo inicializar si estamos en la página de publicar/editar vacante
    if (document.getElementById('vacanteForm')) {
        // Destruir instancia anterior si existe
        if (window.validadorFechasVacante) {
            window.validadorFechasVacante.limpiarTodasLasValidaciones();
        }
        
        // Crear nueva instancia
        window.validadorFechasVacante = new ValidadorFechasVacante();
        console.log('🚀 ValidadorFechasVacante iniciado con restricciones mejoradas');

        // Script de prueba para depuración (solo en desarrollo)
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.log('=== PRUEBA DE VALIDACIÓN DE DOMINGOS ===');
            const fechasPrueba = ['2025-08-03', '2025-08-04', '2025-08-05', '2025-08-06'];
            fechasPrueba.forEach(fechaStr => {
                const fechaObj = new Date(fechaStr + 'T00:00:00');
                const nombresDias = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
                console.log(`${fechaStr} (${nombresDias[fechaObj.getDay()]}) - getDay(): ${fechaObj.getDay()}`);
            });
        }

        // Agregar mensaje informativo para el usuario
        const mensajeInfo = document.createElement('div');
        mensajeInfo.className = 'alert alert-info mt-0';
        mensajeInfo.innerHTML = `
            <i class="bi bi-info-circle me-0"></i>
            <strong>Restricciones de fechas:</strong> 
            <ul class="mb-0 mt-2">
                <li>No se pueden seleccionar fechas pasadas (ayer, antier, etc.)</li>
                <li>No se pueden seleccionar domingos</li>
                <li>La fecha de inicio y límite no pueden ser el mismo día</li>
                <li>La fecha de inicio debe ser al menos un día después de la fecha límite</li>
                <li>La fecha límite es obligatoria para publicar</li>
            </ul>
        `;

        // Insertar el mensaje después de la sección de fechas
        const seccionFechas = document.querySelector('.card:has(#id_fecha_limite)');
        if (seccionFechas) {
            seccionFechas.after(mensajeInfo);
        }
    }
});

// Exportar para uso en módulos (si es necesario)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ValidadorFechasVacante };
}