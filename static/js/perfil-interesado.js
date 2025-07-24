// static/js/perfil-interesado.js - VERSIÓN SIMPLIFICADA SIN MODAL DE DATOS

document.addEventListener('DOMContentLoaded', function() {
    // ===================================================================
    // FUNCIONES PARA CV (mantener las existentes)
    // ===================================================================
    
    // Variables globales para controlar edición
    let experienciaEditandoId = null;
    let educacionEditandoId = null;

    // =========================
    // EXPERIENCIA LABORAL (mantener igual)
    // =========================
    window.mostrarModalExperiencia = function() {
        experienciaEditandoId = null;
        document.querySelector('#experienciaModal .modal-title').textContent = 'Agregar Experiencia Laboral';
        document.getElementById('experienciaForm').reset();
        document.querySelector('#experienciaForm input[name="fecha_fin"]').disabled = false;
        new bootstrap.Modal(document.getElementById('experienciaModal')).show();
    }

    window.editarExperiencia = function(id, puesto, empresa, fechaInicio, fechaFin, actual, descripcion) {
        experienciaEditandoId = id;

        document.querySelector('#experienciaForm input[name="puesto"]').value = puesto;
        document.querySelector('#experienciaForm input[name="empresa"]').value = empresa;
        document.querySelector('#experienciaForm input[name="fecha_inicio"]').value = fechaInicio;
        document.querySelector('#experienciaForm input[name="fecha_fin"]').value = fechaFin || '';
        document.querySelector('#experienciaForm input[name="actual"]').checked = actual;
        document.querySelector('#experienciaForm textarea[name="descripcion"]').value = descripcion;

        const fechaFinInput = document.querySelector('#experienciaForm input[name="fecha_fin"]');
        fechaFinInput.disabled = actual;

        document.querySelector('#experienciaModal .modal-title').textContent = 'Editar Experiencia Laboral';
        new bootstrap.Modal(document.getElementById('experienciaModal')).show();
    }

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
            } else {
                alert('Error: ' + JSON.stringify(data.errors || data.error));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al guardar la experiencia');
        });
    }

    window.eliminarExperiencia = function(id) {
        if (confirm('¿Estás seguro de eliminar esta experiencia?')) {
            fetch(`/ajax/experiencia/eliminar/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error al eliminar: ' + data.error);
                }
            });
        }
    }

    // =========================
    // EDUCACIÓN (mantener igual)
    // =========================
    window.mostrarModalEducacion = function() {
        educacionEditandoId = null;
        document.querySelector('#educacionModal .modal-title').textContent = 'Agregar Educación';
        document.getElementById('educacionForm').reset();
        new bootstrap.Modal(document.getElementById('educacionModal')).show();
    }

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
            } else {
                alert('Error: ' + JSON.stringify(data.errors || data.error));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al guardar la educación');
        });
    }

    window.editarEducacion = function(id, titulo, institucion, fechaInicio, fechaFin) {
        educacionEditandoId = id;
        document.querySelector('#educacionForm input[name="titulo"]').value = titulo;
        document.querySelector('#educacionForm input[name="institucion"]').value = institucion;
        document.querySelector('#educacionForm input[name="fecha_inicio"]').value = fechaInicio;
        document.querySelector('#educacionForm input[name="fecha_fin"]').value = fechaFin || '';

        document.querySelector('#educacionModal .modal-title').textContent = 'Editar Educación';
        new bootstrap.Modal(document.getElementById('educacionModal')).show();
    }

    window.eliminarEducacion = function(id) {
        if (confirm('¿Estás seguro de eliminar esta educación?')) {
            fetch(`/ajax/educacion/eliminar/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error al eliminar: ' + data.error);
                }
            });
        }
    }

    // =========================
    // HABILIDADES (mantener igual)
    // =========================
    window.mostrarModalHabilidad = function() {
        document.getElementById('habilidadForm').reset();
        new bootstrap.Modal(document.getElementById('habilidadModal')).show();
    }

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
            } else {
                alert('Error: ' + JSON.stringify(data.errors || data.error));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al guardar la habilidad');
        });
    }

    window.eliminarHabilidad = function(id) {
        if (confirm('¿Estás seguro de eliminar esta habilidad?')) {
            fetch(`/ajax/habilidad/eliminar/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error al eliminar: ' + data.error);
                }
            });
        }
    }

    // =========================
    // IDIOMAS (mantener igual)
    // =========================
    window.mostrarModalIdioma = function() {
        document.getElementById('idiomaForm').reset();
        new bootstrap.Modal(document.getElementById('idiomaModal')).show();
    }

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
            } else {
                alert('Error: ' + JSON.stringify(data.errors || data.error));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al guardar el idioma');
        });
    }

    window.eliminarIdioma = function(id) {
        if (confirm('¿Estás seguro de eliminar este idioma?')) {
            fetch(`/ajax/idioma/eliminar/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Elimina solo el idioma del DOM, no recargues la página
                    const elem = document.querySelector(`.idioma-item[data-id="${id}"]`);
                    if (elem) elem.remove();
                    mostrarFeedback('Idioma eliminado', 'success');
                } else {
                    mostrarFeedback('Error al eliminar: ' + data.error, 'danger');
                }
            });
        }
    }

    // =========================
    // EVENT LISTENERS PARA CV
    // =========================
    const actualCheck = document.getElementById('actualCheck');
    if (actualCheck) {
        actualCheck.addEventListener('change', function() {
            const fechaFin = document.querySelector('#experienciaForm input[name="fecha_fin"]');
            if (this.checked) {
                fechaFin.disabled = true;
                fechaFin.value = '';
            } else {
                fechaFin.disabled = false;
            }
        });
    }

    // Limpiar modales al cerrar
    document.getElementById('experienciaModal')?.addEventListener('hidden.bs.modal', function () {
        experienciaEditandoId = null;
        document.querySelector('#experienciaModal .modal-title').textContent = 'Agregar Experiencia Laboral';
    });

    document.getElementById('educacionModal')?.addEventListener('hidden.bs.modal', function () {
        educacionEditandoId = null;
        document.querySelector('#educacionModal .modal-title').textContent = 'Agregar Educación';
    });

    // ===================================================================
    // AUTOGUARDADO Y VALIDACIONES PARA EL FORMULARIO CV
    // ===================================================================
    
    const formulario = document.getElementById('cvForm');
    if (formulario) {
        const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Detectar cambios en resumen profesional
        let resumenTimeout;
        const resumenInput = formulario.elements['resumen_profesional'];
        if (resumenInput) {
            resumenInput.addEventListener('input', function (e) {
                clearTimeout(resumenTimeout);
                resumenTimeout = setTimeout(() => {
                    autoguardarResumenProfesionalAJAX(e.target.value, csrf);
                }, 1200);
            });
        }

        // Detectar cambios en campos personales
        let personalTimeout;
        ['nombre', 'apellido_paterno', 'apellido_materno', 'telefono', 'municipio', 'codigo_postal', 'fecha_nacimiento'].forEach(campo => {
            const elemento = formulario.elements[campo];
            if (elemento) {
                elemento.addEventListener('input', function (e) {
                    clearTimeout(personalTimeout);
                    personalTimeout = setTimeout(() => {
                        let datos = {};
                        ['nombre', 'apellido_paterno', 'apellido_materno', 'telefono', 'municipio', 'codigo_postal', 'fecha_nacimiento'].forEach(c => {
                            datos[c] = formulario.elements[c]?.value || '';
                        });
                        autoguardarInformacionPersonalAJAX(datos, csrf);
                    }, 1000);
                });
            }
        });
    }

    // ===================================================================
    // FUNCIONES DE AUTOGUARDADO
    // ===================================================================
    
    function autoguardarResumenProfesionalAJAX(valor, csrf) {
        fetch('/ajax/autoguardar_resumen_profesional/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf
            },
            body: JSON.stringify({ resumen_profesional: valor })
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                document.getElementById('resumen_profesional').classList.add('is-valid');
                setTimeout(() => document.getElementById('resumen_profesional').classList.remove('is-valid'), 1000);
            }
        });
    }

    function autoguardarInformacionPersonalAJAX(datos, csrf) {
        fetch('/ajax/autoguardar_informacion_personal/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf
            },
            body: JSON.stringify(datos)
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                // Feedback visual opcional
            }
        });
    }

    // ===================================================================
    // VALIDACIONES PARA EL BOTÓN DE DESCARGA DE CV
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

        // 2. Validar foto de perfil - CORREGIDO
        const fotoPreview = document.querySelector('.profile-photo');
        const fotoPlaceholder = document.querySelector('.profile-photo-placeholder');
        
        // Verificar si tiene foto: debe existir un elemento .profile-photo O si no hay placeholder
        const tieneFoto = fotoPreview || !fotoPlaceholder;
        
        if (!tieneFoto) {
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

    function verificarEstadoBotonGuardarCV() {
        const btnGuardarCV = document.getElementById('btnDescargarCV');
        if (!btnGuardarCV) {
            console.log('Botón de descarga no encontrado'); // Debug
            return;
        }

        const validacionCompleta = validarFormularioCompleto();
        
        console.log('Estado de validación:', validacionCompleta); // Debug

        if (validacionCompleta.esValido) {
            btnGuardarCV.disabled = false;
            btnGuardarCV.title = 'Descargar CV - Todos los campos están completos';
            btnGuardarCV.innerHTML = '<i class="bi bi-download"></i> Descargar PDF';
            btnGuardarCV.classList.remove('btn-secondary');
            btnGuardarCV.classList.add('btn-primary');
            btnGuardarCV.classList.add('text-white');
            console.log('Botón habilitado'); // Debug
        } else {
            btnGuardarCV.disabled = true;
            btnGuardarCV.title = 'Campos faltantes:\n' + validacionCompleta.camposFaltantes.join('\n');
            btnGuardarCV.innerHTML = '<i class="bi bi-exclamation-circle"></i> <span class="fw-bold">CV Incompleto</span>';
            btnGuardarCV.classList.remove('btn-primary');
            btnGuardarCV.classList.add('btn-secondary');
            console.log('Botón deshabilitado. Campos faltantes:', validacionCompleta.camposFaltantes); // Debug
        }
    }

    // Validación del botón de descarga
    const btnDescargarCV = document.getElementById('btnDescargarCV');
    if (btnDescargarCV) {
        btnDescargarCV.addEventListener('click', function(e) {
            console.log('Botón de descarga clickeado'); // Debug
            
            const validacionCompleta = validarFormularioCompleto();
            
            console.log('Validación completa:', validacionCompleta); // Debug

            if (!validacionCompleta.esValido) {
                e.preventDefault();
                e.stopPropagation();

                console.log('Validación falló:', validacionCompleta.camposFaltantes); // Debug

                const mensajeError = 'No se puede descargar el CV. Faltan los siguientes campos:\n\n' +
                                   validacionCompleta.camposFaltantes.join('\n') +
                                   '\n\nPor favor, completa toda la información antes de continuar.';
                alert(mensajeError);
                return false;
            }
            
            console.log('Validación exitosa, procediendo con descarga...'); // Debug
        });
    }

    // Verificación inicial y observadores de cambios
    verificarEstadoBotonGuardarCV();

    const observerConfig = { childList: true, subtree: true };
    const observerCallback = function(mutationsList) {
        verificarEstadoBotonGuardarCV();
    };

    const observer = new MutationObserver(observerCallback);
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

    // Observar cambios en los inputs del formulario
    const camposFormulario = [
        '#nombre', '#apellido_paterno', '#apellido_materno',
        '#telefono', '#fecha_nacimiento', '#municipio',
        '#codigo_postal', '#resumen_profesional'
    ];

    camposFormulario.forEach(selector => {
        const campo = document.querySelector(selector);
        if (campo) {
            campo.addEventListener('input', verificarEstadoBotonGuardarCV);
            campo.addEventListener('change', verificarEstadoBotonGuardarCV);
            campo.addEventListener('blur', verificarEstadoBotonGuardarCV);
        }
    });

    // ===================================================================
    // FUNCIÓN DE FEEDBACK
    // ===================================================================
    
    function mostrarFeedback(mensaje, tipo = 'success') {
        let alerta = document.createElement('div');
        alerta.className = `alert alert-${tipo} fixed-top m-3 fade show`;
        alerta.style.zIndex = 9999;
        alerta.style.right = '20px';
        alerta.style.left = 'auto';
        alerta.innerHTML = `<span>${mensaje} ✅</span>`;
        document.body.appendChild(alerta);
        setTimeout(() => alerta.remove(), 2000);
    }

    // ===================================================================
    // VALIDACIÓN DEL FORMULARIO CV AL ENVIAR
    // ===================================================================
    
    const cvForm = document.getElementById('cvForm');
    if (cvForm) {
        cvForm.addEventListener('submit', function(e) {
            const validacionCompleta = validarFormularioCompleto();

            if (!validacionCompleta.esValido) {
                e.preventDefault();
                e.stopPropagation();

                const mensajeError = 'Por favor, completa todos los campos obligatorios:\n\n' +
                                   validacionCompleta.camposFaltantes.join('\n');
                alert(mensajeError);

                this.classList.add('was-validated');
                return false;
            }

            if (!this.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                alert('Por favor, revisa que todos los campos estén correctamente completados.');
                this.classList.add('was-validated');
                return false;
            }
        });
    }
});