// AGREGAR estas funciones en perfil-interesado.js o en el template

// =========================
// MODAL DE PERFIL PERSONAL
// =========================
// En perfil-interesado.js - REEMPLAZAR la función validarFormularioCompleto()
// EN perfil-interesado.js - AGREGAR verificación en las funciones AJAX existentes

// ✅ MODIFICAR la función guardarExperiencia()
window.guardarExperiencia = function() {
    const form = document.getElementById('experienciaForm');
    const formData = new FormData(form);

    let url = experienciaEditandoId ?
        `/ajax/experiencia/editar/${experienciaEditandoId}/` :
        '/ajax/experiencia/agregar/';

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            bootstrap.Modal.getInstance(document.getElementById('experienciaModal')).hide();
            location.reload();
            // ✅ VERIFICAR BOTÓN DESPUÉS DE AGREGAR/EDITAR EXPERIENCIA
            setTimeout(() => verificarEstadoBotonGuardarCV(), 300);
        } else {
            alert('Error: ' + JSON.stringify(data.errors || data.error));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al guardar la experiencia');
    });
}

// ✅ MODIFICAR la función guardarEducacion()
window.guardarEducacion = function() {
    const form = document.getElementById('educacionForm');
    const formData = new FormData(form);
    let url = educacionEditandoId ?
        `/ajax/educacion/editar/${educacionEditandoId}/` :
        '/ajax/educacion/agregar/';

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            bootstrap.Modal.getInstance(document.getElementById('educacionModal')).hide();
            location.reload();
            // ✅ VERIFICAR BOTÓN DESPUÉS DE AGREGAR/EDITAR EDUCACIÓN
            setTimeout(() => verificarEstadoBotonGuardarCV(), 300);
        } else {
            alert('Error: ' + JSON.stringify(data.errors || data.error));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al guardar la educación');
    });
}

// ✅ MODIFICAR la función guardarHabilidad()
window.guardarHabilidad = function() {
    const form = document.getElementById('habilidadForm');
    const formData = new FormData(form);

    fetch('/ajax/habilidad/agregar/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            bootstrap.Modal.getInstance(document.getElementById('habilidadModal')).hide();
            location.reload();
            // ✅ VERIFICAR BOTÓN DESPUÉS DE AGREGAR HABILIDAD
            setTimeout(() => verificarEstadoBotonGuardarCV(), 300);
        } else {
            alert('Error: ' + JSON.stringify(data.errors || data.error));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al guardar la habilidad');
    });
}

// ✅ MODIFICAR la función guardarIdioma()
window.guardarIdioma = function() {
    const form = document.getElementById('idiomaForm');
    const formData = new FormData(form);

    fetch('/ajax/idioma/agregar/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            bootstrap.Modal.getInstance(document.getElementById('idiomaModal')).hide();
            location.reload();
            // ✅ VERIFICAR BOTÓN DESPUÉS DE AGREGAR IDIOMA
            setTimeout(() => verificarEstadoBotonGuardarCV(), 300);
        } else {
            alert('Error: ' + JSON.stringify(data.errors || data.error));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al guardar el idioma');
    });
}

// ✅ FUNCIÓN DE VALIDACIÓN MEJORADA
function validarFormularioCompleto() {
    const camposFaltantes = [];
    let esValido = true;


    // ✅ 1. VALIDAR INFORMACIÓN PERSONAL usando las variables JavaScript
    if (!window.datosInteresado.nombre.trim()) {
        camposFaltantes.push('- Nombre');
        esValido = false;
    }

    if (!window.datosInteresado.apellido_paterno.trim()) {
        camposFaltantes.push('- Apellido Paterno');
        esValido = false;
    }

    if (!window.datosInteresado.apellido_materno.trim()) {
        camposFaltantes.push('- Apellido Materno');
        esValido = false;
    }

    if (!window.datosInteresado.telefono.trim()) {
        camposFaltantes.push('- Teléfono');
        esValido = false;
    }

    if (!window.datosInteresado.fecha_nacimiento.trim()) {
        camposFaltantes.push('- Fecha de Nacimiento');
        esValido = false;
    }

    if (!window.datosInteresado.codigo_postal.trim()) {
        camposFaltantes.push('- Código Postal');
        esValido = false;
    }

    // ✅ VALIDAR UBICACIÓN COMPLETA MEJORADA
    if (!window.datosInteresado.ubicacion_completa.trim() ||
        window.datosInteresado.ubicacion_completa.toLowerCase().includes('no especificada') ||
        window.datosInteresado.ubicacion_completa.toLowerCase().includes('ubicación no especificada')) {
        camposFaltantes.push('- Ubicación completa (Estado, Municipio, Localidad)');
        esValido = false;
    }

    // ✅ 2. VALIDAR FOTO DE PERFIL
    if (!window.datosInteresado.tiene_foto) {
        camposFaltantes.push('- Foto de perfil');
        esValido = false;
    }

    // ✅ 3. VALIDAR RESUMEN PROFESIONAL
    // Verificar tanto desde la variable JavaScript como desde el DOM
    let tieneResumen = false;
    
    // Primero verificar la variable JavaScript
    if (window.datosInteresado.resumen_profesional && window.datosInteresado.resumen_profesional.trim()) {
        tieneResumen = true;
    }
    
    // Si no está en la variable, verificar el textarea directamente
    if (!tieneResumen) {
        const resumenTextarea = document.querySelector('#resumen_profesional');
        if (resumenTextarea && resumenTextarea.value.trim()) {
            tieneResumen = true;
        }
    }
    
    if (!tieneResumen) {
        camposFaltantes.push('- Resumen profesional');
        esValido = false;
    }

    // ✅ 4. VALIDAR EXPERIENCIAS LABORALES (mínimo 1)
    const cantidadExperiencias = document.querySelectorAll('#experienciaContainer .experiencia-item').length;
    if (cantidadExperiencias < 1) {
        camposFaltantes.push('- Al menos 1 experiencia laboral');
        esValido = false;
    }

    // ✅ 5. VALIDAR EDUCACIÓN/FORMACIÓN (mínimo 1)
    const cantidadEducacion = document.querySelectorAll('#educacionContainer .educacion-item').length;
    if (cantidadEducacion < 1) {
        camposFaltantes.push('- Al menos 1 formación educativa');
        esValido = false;
    }

    // ✅ 6. VALIDAR HABILIDADES TÉCNICAS (mínimo 5)
    const cantidadHabilidades = document.querySelectorAll('#habilidadesContainer .badge').length;
    if (cantidadHabilidades < 5) {
        camposFaltantes.push(`- Al menos 5 habilidades técnicas (tienes ${cantidadHabilidades})`);
        esValido = false;
    }

    // ✅ 7. VALIDAR IDIOMAS (mínimo 1)
    const cantidadIdiomas = document.querySelectorAll('#idiomasContainer .idioma-item').length;
    if (cantidadIdiomas < 1) {
        camposFaltantes.push('- Al menos 1 idioma');
        esValido = false;
    }


    return {
        esValido: esValido,
        camposFaltantes: camposFaltantes
    };
}

// ✅ FUNCIÓN MEJORADA PARA ACTUALIZAR EL BOTÓN
function verificarEstadoBotonGuardarCV() {

    const btnGuardarCV = document.getElementById('btnDescargarCV');
    if (!btnGuardarCV) {
        return;
    }

    // Verificar que las variables estén disponibles
    if (!window.datosInteresado) {
        return;
    }

    const validacionCompleta = validarFormularioCompleto();


    if (validacionCompleta.esValido) {
        // ✅ CV COMPLETO - HABILITAR BOTÓN
        btnGuardarCV.disabled = false;
        btnGuardarCV.title = 'Descargar CV - Todos los campos están completos';
        btnGuardarCV.innerHTML = '<i class="bi bi-download"></i> Descargar PDF';
        btnGuardarCV.classList.remove('btn-secondary');
        btnGuardarCV.classList.add('btn-primary', 'text-white');

    } else {
        // ❌ CV INCOMPLETO - DESHABILITAR BOTÓN
        btnGuardarCV.disabled = true;
        btnGuardarCV.title = 'Campos faltantes:\n' + validacionCompleta.camposFaltantes.join('\n');
        btnGuardarCV.innerHTML = '<i class="bi bi-exclamation-circle"></i> <span class="fw-bold">CV Incompleto</span>';
        btnGuardarCV.classList.remove('btn-primary', 'text-white');
        btnGuardarCV.classList.add('btn-secondary');

    }
}

// ✅ FUNCIÓN PARA ACTUALIZAR VARIABLES JAVASCRIPT
function actualizarDatosInteresado(nuevosDatos) {

    if (!window.datosInteresado) {
        window.datosInteresado = {};
    }

    // Actualizar solo los campos que vienen en nuevosDatos
    Object.keys(nuevosDatos).forEach(key => {
        if (nuevosDatos[key] !== undefined && nuevosDatos[key] !== null) {
            window.datosInteresado[key] = nuevosDatos[key];
        }
    });


    // Re-verificar estado del botón
    verificarEstadoBotonGuardarCV();
}

// ✅ AGREGAR AL FINAL DE LA FUNCIÓN guardarPerfil() EN EL MODAL
// Modificar la función guardarPerfil existente para que llame a la validación después de guardar:
window.guardarPerfil = function() {
    const form = document.getElementById('perfilForm');
    const formData = new FormData(form);

    // Mostrar loading en el botón
    const guardarBtn = document.querySelector('#perfilModal .btn-primary');
    const textoOriginal = guardarBtn.innerHTML;
    guardarBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Guardando...';
    guardarBtn.disabled = true;

    fetch('/ajax/actualizar-perfil-completo/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // ✅ ACTUALIZAR LAS VARIABLES JAVASCRIPT CON LOS NUEVOS DATOS
            actualizarDatosInteresado({
                nombre: formData.get('nombre') || '',
                apellido_paterno: formData.get('apellido_paterno') || '',
                apellido_materno: formData.get('apellido_materno') || '',
                telefono: formData.get('telefono') || '',
                fecha_nacimiento: formData.get('fecha_nacimiento') || '',
                codigo_postal: formData.get('codigo_postal') || '',
                ubicacion_completa: data.datos.ubicacion_completa || '',
                // Mantener estado de foto actual
                tiene_foto: window.datosInteresado ? window.datosInteresado.tiene_foto : false
            });


            // Cerrar modal
            bootstrap.Modal.getInstance(document.getElementById('perfilModal')).hide();

            // Actualizar la información en la card
            actualizarCardPerfil(data.datos);

            // ✅ IMPORTANTE: Re-verificar el estado del botón inmediatamente
            setTimeout(() => {
                verificarEstadoBotonGuardarCV();
            }, 300);

            // Mostrar mensaje de éxito
            mostrarToast('Perfil actualizado exitosamente', 'success');

        } else {
            mostrarToast('Error: ' + (data.error || 'Error desconocido'), 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarToast('Error al actualizar el perfil', 'error');
    })
    .finally(() => {
        // Restaurar botón
        guardarBtn.innerHTML = textoOriginal;
        guardarBtn.disabled = false;
    });
}

// ✅ FUNCIÓN PARA AUTOGUARDADO DE RESUMEN PROFESIONAL CON VERIFICACIÓN
window.autoguardarResumenConVerificacion = function() {
    const resumenTextarea = document.getElementById('resumen_profesional');
    if (!resumenTextarea) return;

    let timeoutResumen = null;

    resumenTextarea.addEventListener('input', function() {
        // Limpiar timeout anterior
        clearTimeout(timeoutResumen);

        // Configurar nuevo timeout
        timeoutResumen = setTimeout(() => {
            // Aquí puedes agregar lógica de autoguardado si la necesitas

            // Re-verificar estado del botón después de cambio
            verificarEstadoBotonGuardarCV();
        }, 1500); // 1.5 segundos después de dejar de escribir
    });
}

// ✅ INICIALIZACIÓN AL CARGAR LA PÁGINA
document.addEventListener('DOMContentLoaded', function() {

    // Verificar que las variables estén disponibles
    if (window.datosInteresado) {

        // ✅ EJECUTAR VERIFICACIÓN INICIAL DEL BOTÓN
        setTimeout(() => {
            verificarEstadoBotonGuardarCV();
        }, 1000); // Esperar 1 segundo para que todo se cargue

        // Configurar autoguardado de resumen
        autoguardarResumenConVerificacion();

    } else {
        console.error('❌ Variables del interesado no están disponibles');
    }

    // ✅ VERIFICAR ELEMENTOS EN LA PÁGINA PARA DEBUG
    const elementos = {
        btnDescarga: document.getElementById('btnDescargarCV'),
        resumen: document.querySelector('#resumen_profesional'),
        experiencias: document.querySelectorAll('#experienciaContainer .experiencia-item').length,
        educaciones: document.querySelectorAll('#educacionContainer .educacion-item').length,
        habilidades: document.querySelectorAll('#habilidadesContainer .badge').length,
        idiomas: document.querySelectorAll('#idiomasContainer .idioma-item').length
    };

});

// ✅ OTRAS FUNCIONES EXISTENTES SE MANTIENEN IGUAL...
// [El resto de las funciones como mostrarModalPerfil, configurarValidadorModalPerfil, etc. se mantienen iguales]

window.mostrarModalPerfil = function() {
    // El modal ya tiene los valores pre-cargados desde el template
    // Solo necesitamos configurar el validador de CP para el modal
    configurarValidadorModalPerfil();

    new bootstrap.Modal(document.getElementById('perfilModal')).show();
}

function configurarValidadorModalPerfil() {
    const modalCP = document.getElementById('modal_codigo_postal');

    if (!modalCP) return;

    // Remover listeners existentes para evitar duplicados
    modalCP.replaceWith(modalCP.cloneNode(true));
    const nuevoModalCP = document.getElementById('modal_codigo_postal');

    let timeoutCP = null;

    // Event listener para el CP en el modal
    nuevoModalCP.addEventListener('input', function(e) {
        const valor = e.target.value.trim();

        clearTimeout(timeoutCP);
        limpiarSelectsModal();

        if (valor.length === 5 && /^\d{5}$/.test(valor)) {
            timeoutCP = setTimeout(() => {
                consultarCPParaModal(valor);
            }, 1000);
        }
    });

    // También validar al perder foco
    nuevoModalCP.addEventListener('blur', function(e) {
        const valor = e.target.value.trim();

        if (valor.length === 5 && /^\d{5}$/.test(valor)) {
            clearTimeout(timeoutCP);
            consultarCPParaModal(valor);
        }
    });
}

function consultarCPParaModal(codigoPostal) {

    fetch(`/ajax/consultar-codigo-postal/?codigo_postal=${codigoPostal}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            poblarSelectsModal(data);
            mostrarMensajeModal('Código postal válido', 'success');
        } else {
            mostrarMensajeModal(data.message || 'Código postal no encontrado', 'error');
        }
    })
    .catch(error => {
        console.error('Error consultando CP:', error);
        mostrarMensajeModal('Error de conexión', 'error');
    });
}

function poblarSelectsModal(datos) {
    // Poblar Estados
    const selectEstado = document.getElementById('modal_estado');
    if (selectEstado && datos.estados) {
        selectEstado.innerHTML = '<option value="">Selecciona un estado</option>';
        selectEstado.disabled = false;

        datos.estados.forEach(estado => {
            const option = document.createElement('option');
            option.value = estado.id;
            option.textContent = estado.nombre;
            selectEstado.appendChild(option);
        });

        if (datos.estados.length === 1) {
            selectEstado.value = datos.estados[0].id;
            document.getElementById('modal_estado_id').value = datos.estados[0].id;
            document.getElementById('modal_estado_nombre').value = datos.estados[0].nombre;
        }
    }

    // Poblar Municipios
    const selectMunicipio = document.getElementById('modal_municipio');
    if (selectMunicipio && datos.municipios) {
        selectMunicipio.innerHTML = '<option value="">Selecciona un municipio</option>';
        selectMunicipio.disabled = false;

        datos.municipios.forEach(municipio => {
            const option = document.createElement('option');
            option.value = municipio.id;
            option.textContent = municipio.nombre;
            selectMunicipio.appendChild(option);
        });

        if (datos.municipios.length === 1) {
            selectMunicipio.value = datos.municipios[0].id;
            document.getElementById('modal_municipio_id').value = datos.municipios[0].id;
            document.getElementById('modal_municipio_nombre').value = datos.municipios[0].nombre;
        }
    }

    // Poblar Localidades
    const selectLocalidad = document.getElementById('modal_localidad');
    if (selectLocalidad && datos.localidades) {
        selectLocalidad.innerHTML = '<option value="">Selecciona una localidad</option>';
        selectLocalidad.disabled = false;

        datos.localidades.forEach(localidad => {
            const option = document.createElement('option');
            option.value = localidad.id;
            const nombreCompleto = localidad.tipo_asentamiento ?
                `${localidad.nombre} (${localidad.tipo_asentamiento})` :
                localidad.nombre;
            option.textContent = nombreCompleto;
            selectLocalidad.appendChild(option);
        });
    }
}

function limpiarSelectsModal() {
    const selects = ['modal_estado', 'modal_municipio', 'modal_localidad'];

    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            select.innerHTML = '<option value="">Ingresa tu código postal primero</option>';
            select.disabled = true;
        }
    });
}

function mostrarMensajeModal(mensaje, tipo) {
    // Crear mensaje temporal en el modal
    const modalBody = document.querySelector('#perfilModal .modal-body');
    let alertExistente = modalBody.querySelector('.alert-temp');

    if (alertExistente) {
        alertExistente.remove();
    }

    const alertClass = tipo === 'success' ? 'alert-success' : 'alert-danger';
    const icono = tipo === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle';

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show alert-temp`;
    alertDiv.innerHTML = `
        <i class="bi ${icono} me-2"></i>${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    modalBody.insertBefore(alertDiv, modalBody.firstChild);

    // Auto-remover después de 3 segundos
    setTimeout(() => {
        if (alertDiv && alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}

function actualizarCardPerfil(datos) {
    // Actualizar nombre completo
    const nombreElemento = document.querySelector('.card h4, .card .h5');
    if (nombreElemento && datos.nombre_completo) {
        nombreElemento.textContent = datos.nombre_completo;
    }

    // Actualizar teléfono
    const telefonoSpan = document.querySelector('.bi-telephone').nextElementSibling;
    if (telefonoSpan) {
        telefonoSpan.textContent = datos.telefono || 'No especificado';
        telefonoSpan.className = datos.telefono ? '' : 'text-muted';
    }

    // Actualizar ubicación
    const ubicacionSpan = document.querySelector('.bi-geo-alt').nextElementSibling;
    if (ubicacionSpan) {
        ubicacionSpan.textContent = datos.ubicacion_completa || 'Ubicación no especificada';
        ubicacionSpan.className = datos.ubicacion_completa ? '' : 'text-muted';
    }
}

function mostrarToast(mensaje, tipo) {
    // Crear contenedor de toasts si no existe
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 start-0 p-3';
        toastContainer.style.zIndex = '1055';
        document.body.appendChild(toastContainer);
    }

    const toastId = 'toast-' + Date.now();
    const toastDiv = document.createElement('div');
    toastDiv.id = toastId;

    let bgClass = 'success';
    let icon = 'check-circle';

    if (tipo === 'error') {
        bgClass = 'danger';
        icon = 'exclamation-circle';
    }

    toastDiv.className = `toast align-items-center text-bg-${bgClass} border-0`;
    toastDiv.setAttribute('role', 'alert');
    toastDiv.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-${icon} me-2"></i>${mensaje}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toastDiv);

    const toast = new bootstrap.Toast(toastDiv, { autohide: true, delay: 4000 });
    toast.show();

    toastDiv.addEventListener('hidden.bs.toast', function() {
        toastDiv.remove();
    });
}

// =========================
// EVENT LISTENERS DEL MODAL
// =========================

// Event listeners del modal ya existentes...
document.addEventListener('DOMContentLoaded', function() {
    // Configurar event listeners para los selects del modal
    ['modal_estado', 'modal_municipio', 'modal_localidad'].forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            select.addEventListener('change', function() {
                const selectedOption = this.options[this.selectedIndex];
                const baseId = selectId.replace('modal_', '');
                const idField = document.getElementById(`modal_${baseId}_id`);
                const nameField = document.getElementById(`modal_${baseId}_nombre`);

                if (selectedOption && selectedOption.value && idField && nameField) {
                    idField.value = selectedOption.value;
                    nameField.value = selectedOption.text;
                }
            });
        }
    });

    // Limpiar modal al cerrar
    document.getElementById('perfilModal')?.addEventListener('hidden.bs.modal', function() {
        // Limpiar alertas temporales
        const alertsTemp = this.querySelectorAll('.alert-temp');
        alertsTemp.forEach(alert => alert.remove());
    });
});