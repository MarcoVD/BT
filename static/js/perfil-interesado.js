// static/js/perfil-interesado.js - VERSIÓN CORREGIDA

console.log('📋 Cargando perfil-interesado.js...');

// Función para verificar disponibilidad de ImageCropper
function initializePerfilInteresado() {
    console.log('🔍 Verificando disponibilidad de ImageCropper...');

    if (typeof window.imageCropper !== 'undefined' && window.imageCropper) {
        console.log('✅ ImageCropper disponible, inicializando funcionalidades...');
        setupPerfilEventListeners();
    } else {
        console.log('⏳ ImageCropper no disponible aún, reintentando en 500ms...');
        setTimeout(initializePerfilInteresado, 500);
    }
}

function setupPerfilEventListeners() {
    console.log('🎯 Configurando event listeners del perfil...');

    // Event listeners para modales de CV
    setupModalEventListeners();

    // Event listeners para formularios
    setupFormEventListeners();

    console.log('✅ Perfil interesado inicializado correctamente');
}

function setupModalEventListeners() {
    // Experiencia laboral
    window.mostrarModalExperiencia = function() {
        const modal = new bootstrap.Modal(document.getElementById('experienciaModal'));
        document.getElementById('experienciaForm').reset();
        modal.show();
    };

    window.editarExperiencia = function(id, puesto, empresa, fechaInicio, fechaFin, actual, descripcion) {
        const modal = new bootstrap.Modal(document.getElementById('experienciaModal'));
        const form = document.getElementById('experienciaForm');

        form.querySelector('[name="puesto"]').value = puesto;
        form.querySelector('[name="empresa"]').value = empresa;
        form.querySelector('[name="fecha_inicio"]').value = fechaInicio;
        form.querySelector('[name="fecha_fin"]').value = fechaFin || '';
        form.querySelector('[name="actual"]').checked = actual;
        form.querySelector('[name="descripcion"]').value = descripcion;

        // Cambiar el botón de guardar para edición
        const saveBtn = modal._element.querySelector('[onclick="guardarExperiencia()"]');
        saveBtn.setAttribute('onclick', `actualizarExperiencia(${id})`);

        modal.show();
    };

    // Educación
    window.mostrarModalEducacion = function() {
        const modal = new bootstrap.Modal(document.getElementById('educacionModal'));
        document.getElementById('educacionForm').reset();
        modal.show();
    };

    window.editarEducacion = function(id, titulo, institucion, fechaInicio, fechaFin, descripcion) {
        const modal = new bootstrap.Modal(document.getElementById('educacionModal'));
        const form = document.getElementById('educacionForm');

        form.querySelector('[name="titulo"]').value = titulo;
        form.querySelector('[name="institucion"]').value = institucion;
        form.querySelector('[name="fecha_inicio"]').value = fechaInicio;
        form.querySelector('[name="fecha_fin"]').value = fechaFin || '';
        form.querySelector('[name="descripcion"]').value = descripcion || '';

        const saveBtn = modal._element.querySelector('[onclick="guardarEducacion()"]');
        saveBtn.setAttribute('onclick', `actualizarEducacion(${id})`);

        modal.show();
    };

    // Habilidades
    window.mostrarModalHabilidad = function() {
        const modal = new bootstrap.Modal(document.getElementById('habilidadModal'));
        document.getElementById('habilidadForm').reset();
        modal.show();
    };

    // Idiomas
    window.mostrarModalIdioma = function() {
        const modal = new bootstrap.Modal(document.getElementById('idiomaModal'));
        document.getElementById('idiomaForm').reset();
        modal.show();
    };
}

function setupFormEventListeners() {
    // Funciones para guardar entidades

    window.guardarExperiencia = function() {
        const form = document.getElementById('experienciaForm');
        const formData = new FormData(form);
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        fetch('/ajax/experiencia/agregar/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error: ' + (data.error || 'Error desconocido'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error de conexión');
        });
    };

    window.guardarEducacion = function() {
        const form = document.getElementById('educacionForm');
        const formData = new FormData(form);
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        fetch('/ajax/educacion/agregar/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error: ' + (data.error || 'Error desconocido'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error de conexión');
        });
    };

    window.guardarHabilidad = function() {
        const form = document.getElementById('habilidadForm');
        const formData = new FormData(form);
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        fetch('/ajax/habilidad/agregar/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error: ' + (data.error || 'Error desconocido'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error de conexión');
        });
    };

    window.guardarIdioma = function() {
        const form = document.getElementById('idiomaForm');
        const formData = new FormData(form);
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        fetch('/ajax/idioma/agregar/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error: ' + (data.error || 'Error desconocido'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error de conexión');
        });
    };

    // Funciones para eliminar
    window.eliminarExperiencia = function(id) {
        if (confirm('¿Estás seguro de eliminar esta experiencia?')) {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            fetch(`/ajax/experiencia/eliminar/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error: ' + (data.error || 'Error desconocido'));
                }
            });
        }
    };

    window.eliminarEducacion = function(id) {
        if (confirm('¿Estás seguro de eliminar esta educación?')) {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            fetch(`/ajax/educacion/eliminar/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error: ' + (data.error || 'Error desconocido'));
                }
            });
        }
    };

    window.eliminarHabilidad = function(id) {
        if (confirm('¿Estás seguro de eliminar esta habilidad?')) {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            fetch(`/ajax/habilidad/eliminar/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error: ' + (data.error || 'Error desconocido'));
                }
            });
        }
    };

    window.eliminarIdioma = function(id) {
        if (confirm('¿Estás seguro de eliminar este idioma?')) {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            fetch(`/ajax/idioma/eliminar/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error: ' + (data.error || 'Error desconocido'));
                }
            });
        }
    };
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePerfilInteresado);
} else {
    initializePerfilInteresado();
}