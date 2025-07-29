/**
 * validador_codigo_postal.js
 * JavaScript para validación automática de código postal usando API DIPOMEX
 * Ubicación: BT/static/js/validador_codigo_postal.js
 */

class ValidadorCodigoPostal {
    constructor() {
        this.timeout = null;
        this.tiempoEspera = 1000; // 1 segundo después de dejar de escribir
        this.consultandoAPI = false;
        
        this.inicializar();
    }
    
    inicializar() {
        console.log('🚀 ValidadorCodigoPostal inicializado');
        
        // Buscar el campo de código postal
        this.campoCodigoPostal = document.getElementById('codigo_postal');
        
        if (!this.campoCodigoPostal) {
            console.warn('Campo de código postal no encontrado');
            return;
        }
        
        this.configurarEventos();
        this.crearElementosUI();
    }
    
    configurarEventos() {
        // Evento de entrada de texto con debounce
        this.campoCodigoPostal.addEventListener('input', (evento) => {
            this.manejarEntradaTexto(evento);
        });
        
        // Evento al perder el foco
        this.campoCodigoPostal.addEventListener('blur', (evento) => {
            this.manejarPerdidaFoco(evento);
        });
        
        // Prevenir entrada de caracteres no numéricos
        this.campoCodigoPostal.addEventListener('keypress', (evento) => {
            this.validarEntradaNumerica(evento);
        });
        
        // Limitar a 5 dígitos
        this.campoCodigoPostal.addEventListener('keyup', (evento) => {
            this.limitarLongitud(evento);
        });
    }
    
    crearElementosUI() {
        // Crear contenedor para mensajes
        this.contenedorMensajes = document.createElement('div');
        this.contenedorMensajes.id = 'cp-mensaje';
        this.contenedorMensajes.className = 'mt-2';
        this.contenedorMensajes.style.display = 'none';
        
        // Insertar después del campo de código postal
        this.campoCodigoPostal.parentNode.insertBefore(
            this.contenedorMensajes, 
            this.campoCodigoPostal.nextSibling
        );
        
        // Crear indicador de carga
        this.indicadorCarga = document.createElement('div');
        this.indicadorCarga.id = 'cp-carga';
        this.indicadorCarga.className = 'mt-2 text-info';
        this.indicadorCarga.style.display = 'none';
        this.indicadorCarga.innerHTML = `
            <i class="bi bi-arrow-clockwise spin"></i> 
            <small>Validando código postal...</small>
        `;
        
        // Insertar indicador de carga
        this.campoCodigoPostal.parentNode.insertBefore(
            this.indicadorCarga, 
            this.contenedorMensajes
        );
    }
    
    manejarEntradaTexto(evento) {
        const valor = evento.target.value.trim();
        
        // Limpiar timeout anterior
        if (this.timeout) {
            clearTimeout(this.timeout);
        }
        
        // Limpiar mensajes anteriores
        this.limpiarMensajes();
        
        // Si está vacío, no hacer nada
        if (!valor) {
            return;
        }
        
        // Si tiene 5 dígitos, programar validación
        if (valor.length === 5) {
            this.timeout = setTimeout(() => {
                this.validarCodigoPostal(valor);
            }, this.tiempoEspera);
        } else if (valor.length > 5) {
            this.mostrarError('El código postal debe tener exactamente 5 dígitos');
        }
    }
    
    manejarPerdidaFoco(evento) {
        const valor = evento.target.value.trim();
        
        if (valor && valor.length === 5 && !this.consultandoAPI) {
            // Cancelar timeout y validar inmediatamente
            if (this.timeout) {
                clearTimeout(this.timeout);
            }
            this.validarCodigoPostal(valor);
        } else if (valor && valor.length !== 5) {
            this.mostrarError('El código postal debe tener exactamente 5 dígitos');
        }
    }
    
    validarEntradaNumerica(evento) {
        // Solo permitir números
        const codigoTecla = evento.which || evento.keyCode;
        
        // Permitir teclas especiales (backspace, delete, tab, etc.)
        if (codigoTecla === 8 || codigoTecla === 9 || codigoTecla === 46) {
            return true;
        }
        
        // Solo permitir números (0-9)
        if (codigoTecla < 48 || codigoTecla > 57) {
            evento.preventDefault();
            return false;
        }
        
        return true;
    }
    
    limitarLongitud(evento) {
        let valor = evento.target.value;
        
        // Remover caracteres no numéricos
        valor = valor.replace(/\D/g, '');
        
        // Limitar a 5 dígitos
        if (valor.length > 5) {
            valor = valor.substring(0, 5);
        }
        
        // Actualizar el valor del campo
        evento.target.value = valor;
    }
    
    async validarCodigoPostal(codigoPostal) {
        if (this.consultandoAPI) {
            console.log('Ya hay una consulta en progreso');
            return;
        }
        
        try {
            this.consultandoAPI = true;
            this.mostrarCarga(true);
            this.limpiarMensajes();
            
            console.log(`Validando código postal: ${codigoPostal}`);
            
            // Realizar petición AJAX
            const response = await fetch(`/ajax/consultar-codigo-postal/?codigo_postal=${codigoPostal}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.obtenerCSRFToken()
                }
            });
            
            const datos = await response.json();
            
            if (datos.exito) {
                this.procesarRespuestaExitosa(datos);
            } else {
                this.procesarRespuestaError(datos);
            }
            
        } catch (error) {
            console.error('Error al validar código postal:', error);
            this.mostrarError('Error de conexión al validar el código postal');
        } finally {
            this.consultandoAPI = false;
            this.mostrarCarga(false);
        }
    }
    
    procesarRespuestaExitosa(datos) {
        const info = datos.datos;
        
        // Actualizar campo de municipio si existe
        this.actualizarCampoMunicipio(info.municipio);
        
        // Mostrar mensaje de éxito
        let mensaje = `
            <div class="alert alert-success py-2">
                <i class="bi bi-check-circle me-2"></i>
                <strong>Código postal válido</strong><br>
                <small>
                    📍 ${info.municipio}, ${info.estado}<br>
                    ${info.ciudad ? `🏙️ ${info.ciudad}<br>` : ''}
                    ${info.total_colonias > 0 ? `🏘️ ${info.total_colonias} colonia(s) disponible(s)` : ''}
                </small>
            </div>
        `;
        
        if (info.colonias && info.colonias.length > 0 && info.colonias.length <= 5) {
            mensaje += `
                <div class="mt-2">
                    <small class="text-muted">Colonias principales:</small><br>
                    <small>${info.colonias.join(', ')}</small>
                </div>
            `;
        }
        
        this.mostrarMensaje(mensaje, 'exito');
        
        // Actualizar estilos del campo
        this.campoCodigoPostal.classList.remove('is-invalid');
        this.campoCodigoPostal.classList.add('is-valid');
        
        console.log('✅ Código postal validado exitosamente');
    }
    
    procesarRespuestaError(datos) {
        let mensajeError = datos.error || 'Error desconocido';
        
        // Personalizar mensajes según el tipo de error
        switch (datos.codigo_error) {
            case 'CP_NO_ENCONTRADO':
                mensajeError = `El código postal ${this.campoCodigoPostal.value} no existe en México`;
                break;
            case 'ESTADO_NO_VALIDO':
                mensajeError = `Este código postal no pertenece al Estado de México`;
                break;
            case 'FORMATO_INVALIDO':
                mensajeError = 'El código postal debe tener exactamente 5 dígitos';
                break;
            case 'TIMEOUT':
                mensajeError = 'Tiempo de espera agotado. Inténtalo nuevamente';
                break;
            case 'CONNECTION_ERROR':
                mensajeError = 'Error de conexión. Verifica tu internet';
                break;
        }
        
        this.mostrarError(mensajeError);
        
        // Actualizar estilos del campo
        this.campoCodigoPostal.classList.remove('is-valid');
        this.campoCodigoPostal.classList.add('is-invalid');
        
        console.warn('❌ Error en validación de código postal:', mensajeError);
    }
    
    actualizarCampoMunicipio(municipioAPI) {
        const campoMunicipio = document.getElementById('municipio');
        
        if (!campoMunicipio) {
            console.warn('Campo de municipio no encontrado');
            return;
        }
        
        // Buscar coincidencia en las opciones del select
        const opciones = campoMunicipio.options;
        
        for (let i = 0; i < opciones.length; i++) {
            const opcion = opciones[i];
            const textoOpcion = opcion.text.toLowerCase();
            const municipioLower = municipioAPI.toLowerCase();
            
            // Buscar coincidencia exacta o parcial
            if (textoOpcion.includes(municipioLower) || municipioLower.includes(textoOpcion)) {
                campoMunicipio.value = opcion.value;
                
                // Agregar efecto visual
                campoMunicipio.classList.add('is-valid');
                
                console.log(`✅ Municipio actualizado: ${opcion.text}`);
                break;
            }
        }
    }
    
    mostrarMensaje(mensaje, tipo = 'info') {
        this.contenedorMensajes.innerHTML = mensaje;
        this.contenedorMensajes.style.display = 'block';
        
        // Auto-ocultar mensajes de éxito después de 10 segundos
        if (tipo === 'exito') {
            setTimeout(() => {
                this.limpiarMensajes();
            }, 10000);
        }
    }
    
    mostrarError(mensaje) {
        const html = `
            <div class="alert alert-danger py-2">
                <i class="bi bi-exclamation-triangle me-2"></i>
                <strong>Error:</strong> ${mensaje}