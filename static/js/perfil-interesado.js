// static/js/perfil-interesado.js - Simplificado ya que el cropper maneja el guardado automático
document.addEventListener('DOMContentLoaded', function() {
    const guardarBtn = document.getElementById('guardarPerfilBtn');
    const form = document.getElementById('editarPerfilForm');
    const modal = document.getElementById('editarPerfilModal');

    if (!guardarBtn || !form || !modal) return;

    guardarBtn.addEventListener('click', function() {
        // Validar campos requeridos
        const nombre = form.querySelector('#nombre').value.trim();
        const apellidoPaterno = form.querySelector('#apellido_paterno').value.trim();

        if (!nombre || !apellidoPaterno) {
            mostrarMensaje('Nombre y apellido paterno son obligatorios', 'error');
            return;
        }

        // Mostrar spinner
        const btnText = guardarBtn.querySelector('.btn-text');
        const spinner = guardarBtn.querySelector('.spinner-border');

        btnText.textContent = 'Guardando...';
        spinner.classList.remove('d-none');
        guardarBtn.disabled = true;

        // Crear FormData solo con datos del formulario (sin imagen, ya se guardó automáticamente)
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        formData.append('nombre', form.querySelector('#nombre').value);
        formData.append('apellido_paterno', form.querySelector('#apellido_paterno').value);
        formData.append('apellido_materno', form.querySelector('#apellido_materno').value);
        formData.append('telefono', form.querySelector('#telefono').value);
        formData.append('fecha_nacimiento', form.querySelector('#fecha_nacimiento').value);
        formData.append('municipio', form.querySelector('#municipio').value);
        formData.append('codigo_postal', form.querySelector('#codigo_postal').value);

        // Obtener URL
        const updateUrl = form.dataset.updateUrl || '/ajax/actualizar-perfil/';

        // Enviar petición AJAX
        fetch(updateUrl, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Actualizar información en la página
                actualizarInformacionPerfil(data.data);

                // Mostrar mensaje de éxito
                mostrarMensaje('Perfil actualizado exitosamente', 'success');

                // Cerrar modal
                bootstrap.Modal.getInstance(modal).hide();
            } else {
                mostrarMensaje('Error: ' + (data.error || 'No se pudo actualizar el perfil'), 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarMensaje('Error de conexión. Inténtalo nuevamente.', 'error');
        })
        .finally(() => {
            // Restaurar botón
            btnText.textContent = 'Guardar Cambios';
            spinner.classList.add('d-none');
            guardarBtn.disabled = false;
        });
    });
});

// static/js/perfil-interesado.js - Función actualizarInformacionPerfil corregida

function actualizarInformacionPerfil(data) {
    // Actualizar nombre en el perfil
    const nombreElement = document.querySelector('.card-body h4');
    if (nombreElement && data.nombre_completo) {
        nombreElement.textContent = data.nombre_completo;
    }

    // Actualizar información de contacto
    const contactInfo = document.querySelector('.contact-info');
    if (contactInfo) {
        // Actualizar teléfono
        const telefonoItem = contactInfo.querySelector('.contact-item:nth-child(2)');
        if (telefonoItem && data.telefono) {
            const telefonoSpan = telefonoItem.querySelector('span:last-child');
            if (telefonoSpan) {
                telefonoSpan.textContent = data.telefono;
            }
        }

        // Actualizar ubicación - CORREGIDO PARA EVITAR DUPLICACIÓN
        const ubicacionItem = contactInfo.querySelector('.contact-item:nth-child(3)');
        if (ubicacionItem && data.ubicacion) {
            const ubicacionContainer = ubicacionItem.querySelector('div.flex-grow-1');

            if (ubicacionContainer) {
                // Limpiar todo el contenido de ubicación para evitar duplicados
                ubicacionContainer.innerHTML = '';

                // Crear el contenido de ubicación completo
                const strongElement = document.createElement('strong');
                strongElement.className = 'd-block d-sm-inline small';
                strongElement.textContent = 'Ubicación:';

                const ubicacionSpan = document.createElement('span');

                // Manejar diferentes formatos de ubicación
                if (data.ubicacion.startsWith('C.P.')) {
                    // Formato: "C.P. 56616, Valle de Chalco Solidaridad, Estado de México"
                    ubicacionSpan.textContent = ` ${data.ubicacion}`;
                    ubicacionContainer.appendChild(strongElement);
                    ubicacionContainer.appendChild(ubicacionSpan);
                } else if (data.ubicacion.includes(' C.P. ')) {
                    // Formato: "Valle de Chalco Solidaridad, Estado de México C.P. 56616"
                    const parts = data.ubicacion.split(' C.P. ');
                    const ubicacionSinCP = parts[0];
                    const codigoPostal = parts[1];

                    if (codigoPostal && codigoPostal !== 'undefined') {
                        ubicacionSpan.textContent = ` ${ubicacionSinCP}`;

                        // Crear elemento del código postal
                        const cpElement = document.createElement('small');
                        cpElement.className = 'd-block text-muted';
                        cpElement.textContent = `C.P. ${codigoPostal}`;

                        // Añadir elementos al contenedor
                        ubicacionContainer.appendChild(strongElement);
                        ubicacionContainer.appendChild(ubicacionSpan);
                        ubicacionContainer.appendChild(cpElement);
                    } else {
                        // Si el código postal está undefined, solo mostrar la ubicación
                        ubicacionSpan.textContent = ` ${ubicacionSinCP}`;
                        ubicacionContainer.appendChild(strongElement);
                        ubicacionContainer.appendChild(ubicacionSpan);
                    }
                } else {
                    // Solo ubicación sin código postal
                    ubicacionSpan.textContent = ` ${data.ubicacion}`;
                    ubicacionContainer.appendChild(strongElement);
                    ubicacionContainer.appendChild(ubicacionSpan);
                }
            }
        }
    }

    // Actualizar foto de perfil principal y en información móvil
    if (data.foto_url) {
        const fotoElements = document.querySelectorAll('.profile-photo');
        const placeholderElements = document.querySelectorAll('.profile-photo-placeholder');

        fotoElements.forEach(el => el.src = data.foto_url);

        placeholderElements.forEach(placeholder => {
            const imgElement = document.createElement('img');
            imgElement.src = data.foto_url;
            imgElement.alt = 'Foto de perfil';
            imgElement.className = 'profile-photo';
            placeholder.parentNode.replaceChild(imgElement, placeholder);
        });
    }
}


function mostrarMensaje(mensaje, tipo) {
    // Crear contenedor de toasts si no existe
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 start-0 p-3';
        toastContainer.style.zIndex = '1055';
        document.body.appendChild(toastContainer);
    }

    // Crear toast
    const toastId = 'toast-' + Date.now();
    const toastDiv = document.createElement('div');
    toastDiv.id = toastId;
    toastDiv.className = `toast align-items-center text-bg-${tipo === 'success' ? 'success' : 'danger'} border-0`;
    toastDiv.setAttribute('role', 'alert');
    toastDiv.setAttribute('aria-live', 'assertive');
    toastDiv.setAttribute('aria-atomic', 'true');

    toastDiv.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-${tipo === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
                ${mensaje}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toastDiv);

    // Mostrar toast
    const toast = new bootstrap.Toast(toastDiv, {
        autohide: true,
        delay: 4000
    });
    toast.show();

    // Remover del DOM después de que se oculte
    toastDiv.addEventListener('hidden.bs.toast', function() {
        toastDiv.remove();
    });
}

// ===================================================================
// VALIDACIONES MEJORADAS PARA EL FORMULARIO CV
// ===================================================================

document.getElementById('cvForm').addEventListener('submit', function(e) {
    // Realizar validación completa antes del envío
    const validacionCompleta = validarFormularioCompleto();

    if (!validacionCompleta.esValido) {
        e.preventDefault();
        e.stopPropagation();

        // Mostrar mensaje detallado de campos faltantes
        const mensajeError = 'Por favor, completa todos los campos obligatorios:\n\n' +
                           validacionCompleta.camposFaltantes.join('\n');
        alert(mensajeError);

        this.classList.add('was-validated');
        return false;
    }

    // Validación adicional para inputs/textarea/select nativos
    if (!this.checkValidity()) {
        e.preventDefault();
        e.stopPropagation();
        alert('Por favor, revisa que todos los campos estén correctamente completados.');
        this.classList.add('was-validated');
        return false;
    }
});
// ===================================================================
// VALIDACIÓN ESPECÍFICA PARA EL BOTÓN DE DESCARGA DE CV
// ===================================================================

// Agregar validación específica al botón de descarga
document.addEventListener('DOMContentLoaded', function() {
    const btnDescargarCV = document.getElementById('btnDescargarCV');

    if (btnDescargarCV) {
        // Interceptar el clic del botón para validar antes de proceder
        btnDescargarCV.addEventListener('click', function(e) {
            const validacionCompleta = validarFormularioCompleto();

            if (!validacionCompleta.esValido) {
                e.preventDefault();
                e.stopPropagation();

                // Mostrar mensaje detallado de lo que falta
                const mensajeError = 'No se puede descargar el CV. Faltan los siguientes campos:\n\n' +
                                   validacionCompleta.camposFaltantes.join('\n') +
                                   '\n\nPor favor, completa toda la información antes de continuar.';
                alert(mensajeError);
                return false;
            }
        });
    }
});

// Validación mejorada para el botón de guardar perfil
document.getElementById('guardarPerfilBtn').addEventListener('click', function() {
    var fotoInput = document.getElementById('foto_perfil');
    var preview = document.querySelector('#photoPreview');

    // Valida si hay una imagen ya cargada o seleccionada
    if ((!fotoInput.value || fotoInput.files.length === 0) && !preview) {
        alert('Debes cargar una foto de perfil antes de guardar.');
        return false;
    }

    // Si pasa la validación, aquí sigue con tu AJAX normal
    document.getElementById('editarPerfilForm').submit();
});

// ===================================================================
// FUNCIÓN PARA VERIFICAR ESTADO DEL BOTÓN DE GUARDAR CV
// ===================================================================

function verificarEstadoBotonGuardarCV() {
    const btnGuardarCV = document.getElementById('btnDescargarCV');
    if (!btnGuardarCV) return;

    // Validar todos los campos del formulario y secciones
    const validacionCompleta = validarFormularioCompleto();

    // Habilitar o deshabilitar el botón según la validación completa
    if (validacionCompleta.esValido) {
        btnGuardarCV.disabled = false;
        btnGuardarCV.title = 'Descargar CV - Todos los campos están completos';
        btnGuardarCV.innerHTML = '<i class="bi bi-save"></i> Descargar CV';
        btnGuardarCV.classList.remove('btn-secondary');
        btnGuardarCV.classList.add('btn-primary');
        btnGuardarCV.classList.add('text-white');
    } else {
        btnGuardarCV.disabled = true;
        btnGuardarCV.title = 'Campos faltantes:\n' + validacionCompleta.camposFaltantes.join('\n');
        btnGuardarCV.innerHTML = '<i class="bi bi-exclamation-circle"></i> <span class="fw-bold">CV Incompleto</span>';
        btnGuardarCV.classList.remove('btn-primary');
        btnGuardarCV.classList.add('btn-secondary');
    }
}
// ===================================================================
// FUNCIÓN PARA VALIDAR FORMULARIO COMPLETO
// ===================================================================

function validarFormularioCompleto() {
    const camposFaltantes = [];
    let esValido = true;

    // 1. Validar información personal
    const camposPersonales = [
        { selector: '#nombre', nombre: 'Nombre' },
        { selector: '#apellido_paterno', nombre: 'Apellido Paterno' },
        { selector: '#apellido_materno', nombre: 'Apellido Materno' },
        { selector: '#telefono', nombre: 'Teléfono' },
        { selector: '#fecha_nacimiento', nombre: 'Fecha de Nacimiento' },
        { selector: '#municipio', nombre: 'Municipio' },
        { selector: '#codigo_postal', nombre: 'Código Postal' }
    ];

    camposPersonales.forEach(campo => {
        const elemento = document.querySelector(campo.selector);
        if (!elemento || !elemento.value.trim()) {
            camposFaltantes.push(`- ${campo.nombre}`);
            esValido = false;
        }
    });

    // 2. Validar foto de perfil
    const fotoPreview = document.querySelector('#photoPreview');
    const fotoInput = document.getElementById('foto_perfil');
    if (!fotoPreview && (!fotoInput || !fotoInput.files.length)) {
        camposFaltantes.push('- Foto de perfil');
        esValido = false;
    }

    // 3. Validar resumen profesional
    const resumenProfesional = document.querySelector('#resumen_profesional');
    if (!resumenProfesional || !resumenProfesional.value.trim()) {
        camposFaltantes.push('- Resumen profesional');
        esValido = false;
    }

    // 4. Validar experiencias laborales (mínimo 1)
    const cantidadExperiencias = document.querySelectorAll('#experienciaContainer .experiencia-item').length;
    if (cantidadExperiencias < 1) {
        camposFaltantes.push('- Al menos 1 experiencia laboral');
        esValido = false;
    }

    // 5. Validar educación/formación (mínimo 1)
    const cantidadEducacion = document.querySelectorAll('#educacionContainer .educacion-item').length;
    if (cantidadEducacion < 1) {
        camposFaltantes.push('- Al menos 1 formación educativa');
        esValido = false;
    }

    // 6. Validar habilidades técnicas (mínimo 5)
    const cantidadHabilidades = document.querySelectorAll('#habilidadesContainer .badge').length;
    if (cantidadHabilidades < 5) {
        camposFaltantes.push(`- Al menos 5 habilidades técnicas (tienes ${cantidadHabilidades})`);
        esValido = false;
    }

    // 7. Validar idiomas (mínimo 1)
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

// Llamar a la verificación cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    verificarEstadoBotonGuardarCV();
});

// ===================================================================
// OBSERVADOR PARA DETECTAR CAMBIOS EN LAS SECCIONES DEL CV
// ===================================================================

// Crear un observador de mutaciones para detectar cambios en los contenedores
const observerConfig = { childList: true, subtree: true };

// Función que se ejecutará cuando se detecten cambios
const observerCallback = function(mutationsList) {
    // Verificar el estado del botón cuando hay cambios
    verificarEstadoBotonGuardarCV();
};

// Crear el observador
const observer = new MutationObserver(observerCallback);

// Observar cambios en los contenedores de CV y campos del formulario
document.addEventListener('DOMContentLoaded', function() {
    const contenedoresObservar = [
        '#experienciaContainer',
        '#educacionContainer',
        '#habilidadesContainer',
        '#idiomasContainer'
    ];

    contenedoresObservar.forEach(selector => {
        const elemento = document.querySelector(selector);
        if (elemento) {
            observer.observe(elemento, observerConfig);
        }
    });

    // También observar cambios en los inputs del formulario
    const camposFormulario = [
        '#nombre', '#apellido_paterno', '#apellido_materno',
        '#telefono', '#fecha_nacimiento', '#municipio',
        '#codigo_postal', '#resumen_profesional'
    ];

    camposFormulario.forEach(selector => {
        const campo = document.querySelector(selector);
        if (campo) {
            // Agregar eventos para detectar cambios en tiempo real
            campo.addEventListener('input', verificarEstadoBotonGuardarCV);
            campo.addEventListener('change', verificarEstadoBotonGuardarCV);
            campo.addEventListener('blur', verificarEstadoBotonGuardarCV);
        }
    });

    // Verificación inicial al cargar la página
    verificarEstadoBotonGuardarCV();
});

document.addEventListener('DOMContentLoaded', function() {
    var btnGuardar = document.querySelector('button[type="submit"].btn-primary'); // O ponle un id y usa getElementById
    var btnDescargar = document.getElementById('btnDescargarCV');

    // Función que sincroniza los estados
    function syncDescargarBtn() {
        // Si el botón guardar está habilitado, habilita "Descargar PDF"
        if (!btnGuardar.disabled) {
            btnDescargar.removeAttribute('disabled');
        } else {
            btnDescargar.setAttribute('disabled', true);
        }
    }

    // Observa cambios en el atributo 'disabled' del botón de guardar
    const observer = new MutationObserver(syncDescargarBtn);
    observer.observe(btnGuardar, { attributes: true, attributeFilter: ['disabled'] });

    // Valida el estado inicial al cargar
    syncDescargarBtn();
});