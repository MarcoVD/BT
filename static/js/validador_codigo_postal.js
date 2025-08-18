class ValidadorCodigoPostal {
    constructor() {
        this.timeout = null;
        this.tiempoEspera = 1000; // 1 segundo después de dejar de escribir
        this.consultandoAPI = false;

        this.inicializar();
        this.verificarYPrecargarDatos();
    }

    inicializar() {

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

    // ✅ FUNCIÓN CORREGIDA - verificarYPrecargarDatos
    verificarYPrecargarDatos() {
        // Esperar un momento para que el DOM esté completamente cargado
        setTimeout(() => {
            const cpExistente = this.campoCodigoPostal?.value?.trim();

            // Si hay un CP de 5 dígitos, validarlo automáticamente
            if (cpExistente && cpExistente.length === 5 && /^\d{5}$/.test(cpExistente)) {

                // Verificar si los selects ya tienen datos cargados
                const estadoSelect = document.getElementById('estado');
                const municipioSelect = document.getElementById('municipio');
                const localidadSelect = document.getElementById('localidad');

                // Si los selects están vacíos o en estado inicial, cargar datos
                const necesitaCargar = (
                    !estadoSelect ||
                    estadoSelect.options.length <= 1 ||
                    (estadoSelect.options[0] && estadoSelect.options[0].text.includes('Ingresa tu código postal'))
                );

                if (necesitaCargar) {
                    this.validarCodigoPostal(cpExistente);
                } else {
                }
            } else {
            }
        }, 500); // Dar 500ms para que todo se inicialice
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

    // ✅ FUNCIÓN CORREGIDA - validarCodigoPostal
    async validarCodigoPostal(codigoPostal) {
        if (this.consultandoAPI) {
            return;
        }

        try {
            this.consultandoAPI = true;
            this.mostrarCarga(true);
            this.limpiarMensajes();


            // ✅ CORREGIR URL - usar la URL correcta de Django
            const url = `/ajax/obtener-datos-por-cp/?codigo_postal=${codigoPostal}`;
            
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                    // ✅ NO necesita CSRF token para peticiones GET
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const datos = await response.json();

            if (datos.success) {
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

        // Poblar selects como antes
        this.poblarSelectEstados(datos.estados);
        this.poblarSelectMunicipios(datos.municipios);
        this.poblarSelectLocalidades(datos.localidades);

        // Mostrar mensaje de éxito
        let mensaje = `
            <div class="alert alert-success py-2">
                <i class="bi bi-check-circle me-2"></i>
                <strong>Código postal válido</strong><br>
                <small>📍 ${datos.municipios[0]?.nombre || ''}, ${datos.estados[0]?.nombre || ''}</small>
            </div>
        `;

        this.mostrarMensaje(mensaje, 'exito');

        // Actualizar estilos del campo
        this.campoCodigoPostal.classList.remove('is-invalid');
        this.campoCodigoPostal.classList.add('is-valid');

        // ✅ AUTOGUARDAR SOLO SI EL USUARIO ESTÁ AUTENTICADO
        if (this.usuarioAutenticado()) {
            this.autoguardarDatosUbicacion(datos);
        }

    }

    // ✅ FUNCIÓN CORREGIDA - autoguardarDatosUbicacion
    autoguardarDatosUbicacion(datos) {
        // ✅ VERIFICAR QUE EL USUARIO ESTÉ AUTENTICADO
        if (!this.usuarioAutenticado()) {
            return;
        }

        try {
            const datosUbicacion = {
                codigo_postal: this.campoCodigoPostal.value.trim(),
                estado_id: datos.estados[0]?.id || null,
                municipio_id: datos.municipios[0]?.id || null,
                localidad_id: datos.localidades[0]?.id || null,
                estado_nombre: datos.estados[0]?.nombre || null,
                municipio_nombre: datos.municipios[0]?.nombre || null,
                localidad_nombre: datos.localidades[0]?.nombre || null,
                calle_numero: document.getElementById('calle_numero')?.value?.trim() || null
            };


            // ✅ USAR TOKEN CSRF CORRECTO
            const csrfToken = this.obtenerCSRFToken();
            if (!csrfToken) {
                        return;
            }

            // Hacer petición AJAX para guardar
            fetch('/ajax/autoguardar-ubicacion/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(datosUbicacion),
                credentials: 'same-origin'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(result => {
                if (result.success) {

                    // ✅ ACTUALIZAR VARIABLES JAVASCRIPT Y VERIFICAR BOTÓN
                    this.actualizarDatosInteresado(datosUbicacion, result);

                } else {
                }
            })
            .catch(error => {
                console.error('❌ Error en autoguardado de ubicación:', error);
                // ✅ NO mostrar error al usuario, es un autoguardado en segundo plano
            });

        } catch (error) {
            console.error('❌ Error preparando autoguardado:', error);
        }
    }

    // ✅ NUEVA FUNCIÓN - verificar si usuario está autenticado
    usuarioAutenticado() {
        // Verificar si hay indicadores de autenticación
        const authIndicator = document.querySelector('[data-user-authenticated="true"]');
        const csrfToken = this.obtenerCSRFToken();
        
        return !!(authIndicator && csrfToken);
    }

    // ✅ NUEVA FUNCIÓN - actualizar datos del interesado
    actualizarDatosInteresado(datosUbicacion, result) {
        if (window.datosInteresado) {
            // Actualizar código postal
            window.datosInteresado.codigo_postal = datosUbicacion.codigo_postal || '';

            // Actualizar ubicación completa si está disponible
            if (result.ubicacion_completa) {
                window.datosInteresado.ubicacion_completa = result.ubicacion_completa;
            } else {
                // Construir ubicación completa básica
                const partes = [];
                if (datosUbicacion.localidad_nombre) partes.push(datosUbicacion.localidad_nombre);
                if (datosUbicacion.municipio_nombre) partes.push(datosUbicacion.municipio_nombre);
                if (datosUbicacion.estado_nombre) partes.push(datosUbicacion.estado_nombre);
                if (datosUbicacion.codigo_postal) partes.push(`C.P. ${datosUbicacion.codigo_postal}`);

                window.datosInteresado.ubicacion_completa = partes.join(', ');
            }


            // ✅ VERIFICAR ESTADO DEL BOTÓN DESPUÉS DE ACTUALIZAR UBICACIÓN
            setTimeout(() => {
                if (typeof verificarEstadoBotonGuardarCV === 'function') {
                    verificarEstadoBotonGuardarCV();
                }
            }, 300);
        }
    }

    // ✅ MÉTODOS MEJORADOS: Poblar selects con auto-selección
    poblarSelectEstados(estados) {
        const selectEstado = document.getElementById('estado');
        if (!selectEstado) return;

        selectEstado.innerHTML = '<option value="">Selecciona un estado</option>';
        selectEstado.disabled = false;

        estados.forEach(estado => {
            const option = document.createElement('option');
            option.value = estado.id;
            option.textContent = estado.nombre;
            selectEstado.appendChild(option);
        });

        // Auto-seleccionar y actualizar campos ocultos
        if (estados.length === 1) {
            selectEstado.value = estados[0].id;
            
            // ✅ VERIFICAR QUE EXISTAN LOS CAMPOS ANTES DE ACTUALIZARLOS
            const estadoIdField = document.getElementById('estado_id');
            const estadoNombreField = document.getElementById('estado_nombre');
            
            if (estadoIdField) estadoIdField.value = estados[0].id;
            if (estadoNombreField) estadoNombreField.value = estados[0].nombre;
            
            selectEstado.dispatchEvent(new Event('change'));
        }
    }

    poblarSelectMunicipios(municipios) {
        const selectMunicipio = document.getElementById('municipio');
        if (!selectMunicipio) return;

        selectMunicipio.innerHTML = '<option value="">Selecciona un municipio</option>';
        selectMunicipio.disabled = false;

        municipios.forEach(municipio => {
            const option = document.createElement('option');
            option.value = municipio.id;
            option.textContent = municipio.nombre;
            selectMunicipio.appendChild(option);
        });

        // Auto-seleccionar y actualizar campos ocultos
        if (municipios.length === 1) {
            selectMunicipio.value = municipios[0].id;
            
            // ✅ VERIFICAR QUE EXISTAN LOS CAMPOS ANTES DE ACTUALIZARLOS
            const municipioIdField = document.getElementById('municipio_id');
            const municipioNombreField = document.getElementById('municipio_nombre');
            
            if (municipioIdField) municipioIdField.value = municipios[0].id;
            if (municipioNombreField) municipioNombreField.value = municipios[0].nombre;
            
            selectMunicipio.dispatchEvent(new Event('change'));
        }
    }

    poblarSelectLocalidades(localidades) {
        const selectLocalidad = document.getElementById('localidad');
        if (!selectLocalidad) return;

        selectLocalidad.innerHTML = '<option value="">Selecciona una localidad</option>';
        selectLocalidad.disabled = false;

        localidades.forEach(localidad => {
            const option = document.createElement('option');
            option.value = localidad.id;
            const nombreCompleto = localidad.tipo_asentamiento ?
                `${localidad.nombre} (${localidad.tipo_asentamiento})` :
                localidad.nombre;
            option.textContent = nombreCompleto;
            selectLocalidad.appendChild(option);
        });

        // ✅ IMPORTANTE: NO auto-seleccionar localidad para que el usuario pueda elegir
        // Pero sí actualizar si solo hay una opción
        if (localidades.length === 1) {
            selectLocalidad.value = localidades[0].id;
            
            // ✅ VERIFICAR QUE EXISTAN LOS CAMPOS ANTES DE ACTUALIZARLOS
            const localidadIdField = document.getElementById('localidad_id');
            const localidadNombreField = document.getElementById('localidad_nombre');
            
            if (localidadIdField) localidadIdField.value = localidades[0].id;
            if (localidadNombreField) localidadNombreField.value = localidades[0].nombre;
            
            selectLocalidad.dispatchEvent(new Event('change'));
        }
    }

    procesarRespuestaError(datos) {
        let mensajeError;

        // Primero decidir mensaje según código de error
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
            default:
                // Si no hay código_error válido, usar el mensaje del backend o mensaje por defecto
                mensajeError = datos.message || 'Error desconocido al validar código postal';
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
            </div>
        `;
        this.mostrarMensaje(html, 'error');
    }

    limpiarMensajes() {
        this.contenedorMensajes.style.display = 'none';
        this.contenedorMensajes.innerHTML = '';
    }

    mostrarCarga(mostrar) {
        this.indicadorCarga.style.display = mostrar ? 'block' : 'none';
    }

    // ✅ FUNCIÓN CORREGIDA - obtenerCSRFToken
    obtenerCSRFToken() {
        // Método 1: Desde cookie
        let token = this.getCookie('csrftoken');
        
        if (token) {
            return token;
        }
        
        // Método 2: Desde meta tag
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        // Método 3: Desde input hidden
        const hiddenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (hiddenInput) {
            return hiddenInput.value;
        }
        
        return null;
    }

    // ✅ NUEVA FUNCIÓN - getCookie
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
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.ConsultaCP = new ValidadorCodigoPostal();
});