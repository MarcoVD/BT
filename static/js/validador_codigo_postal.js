class ValidadorCodigoPostal {
    constructor() {
        this.timeout = null;
        this.tiempoEspera = 1000; // 1 segundo después de dejar de escribir
        this.consultandoAPI = false;

        this.inicializar();
        this.verificarYPrecargarDatos();
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

            // Realizar petición AJAX con URL absoluta
            const response = await fetch(`${window.location.origin}/ajax/consultar-codigo-postal/?codigo_postal=${codigoPostal}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.obtenerCSRFToken()
                }
            });

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
    verificarYPrecargarDatos() {
        // Esperar un momento para que el DOM esté completamente cargado
        setTimeout(() => {
            const cpExistente = this.campoCodigoPostal.value.trim();

            console.log('🔍 Verificando CP existente:', cpExistente);

            // Si hay un CP de 5 dígitos, validarlo automáticamente
            if (cpExistente && cpExistente.length === 5 && /^\d{5}$/.test(cpExistente)) {
                console.log('✅ CP existente válido encontrado, precargando datos...');

                // Verificar si los selects ya tienen datos cargados
                const estadoSelect = document.getElementById('estado');
                const municipioSelect = document.getElementById('municipio');
                const localidadSelect = document.getElementById('localidad');

                // Si los selects están vacíos o en estado inicial, cargar datos
                const necesitaCargar = (
                    !estadoSelect ||
                    estadoSelect.options.length <= 1 ||
                    estadoSelect.options[0].text.includes('Ingresa tu código postal')
                );

                if (necesitaCargar) {
                    console.log('📡 Consultando datos para CP:', cpExistente);
                    this.validarCodigoPostal(cpExistente);
                } else {
                    console.log('✅ Datos ya están cargados, no es necesario consultar');
                }
            } else {
                console.log('❌ No hay CP válido para precargar');
            }
        }, 500); // Dar 500ms para que todo se inicialice
    }

    procesarRespuestaExitosa(datos) {
        console.log('✅ Procesando respuesta exitosa:', datos);

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

        // ✅ NUEVO: Autoguardar automáticamente cuando se cargan los datos
        this.autoguardarDatosUbicacion(datos);

        console.log('✅ Código postal validado exitosamente');
    }
// EN validador_codigo_postal.js - AGREGAR AL FINAL DE LA FUNCIÓN autoguardarDatosUbicacion()

autoguardarDatosUbicacion(datos) {
    try {
        const datosUbicacion = {
            codigo_postal: this.campoCodigoPostal.value.trim(),
            estado_id: datos.estados[0]?.id || null,
            municipio_id: datos.municipios[0]?.id || null,
            localidad_id: datos.localidades[0]?.id || null,
            estado_nombre: datos.estados[0]?.nombre || null,
            municipio_nombre: datos.municipios[0]?.nombre || null,
            localidad_nombre: datos.localidades[0]?.nombre || null,
            calle_numero: document.getElementById('calle_numero')?.value.trim() || null
        };

        console.log('💾 Autoguardando datos de ubicación:', datosUbicacion);

        // Hacer petición AJAX para guardar
        fetch('/ajax/autoguardar-ubicacion/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.obtenerCSRFToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datosUbicacion)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                console.log('✅ Datos de ubicación autoguardados exitosamente');

                // ✅ ACTUALIZAR VARIABLES JAVASCRIPT Y VERIFICAR BOTÓN
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

                    console.log('📍 Variables de ubicación actualizadas:', {
                        codigo_postal: window.datosInteresado.codigo_postal,
                        ubicacion_completa: window.datosInteresado.ubicacion_completa
                    });

                    // ✅ VERIFICAR ESTADO DEL BOTÓN DESPUÉS DE ACTUALIZAR UBICACIÓN
                    setTimeout(() => {
                        if (typeof verificarEstadoBotonGuardarCV === 'function') {
                            console.log('🔄 Verificando botón después de autoguardado de ubicación...');
                            verificarEstadoBotonGuardarCV();
                        }
                    }, 300);
                }

            } else {
                console.warn('⚠️ Error autoguardando ubicación:', result.error);
            }
        })
        .catch(error => {
            console.error('❌ Error en autoguardado de ubicación:', error);
        });

    } catch (error) {
        console.error('❌ Error preparando autoguardado:', error);
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
            document.getElementById('estado_id').value = estados[0].id;
            document.getElementById('estado_nombre').value = estados[0].nombre;
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
            document.getElementById('municipio_id').value = municipios[0].id;
            document.getElementById('municipio_nombre').value = municipios[0].nombre;
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
            document.getElementById('localidad_id').value = localidades[0].id;
            document.getElementById('localidad_nombre').value = localidades[0].nombre;
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

    obtenerCSRFToken() {
        const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        return tokenElement ? tokenElement.value : '';
    }
}

// EN validador_codigo_postal.js - AGREGAR AL FINAL DE LA FUNCIÓN autoguardarDatosUbicacion()



// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.ConsultaCP = new ValidadorCodigoPostal();
});