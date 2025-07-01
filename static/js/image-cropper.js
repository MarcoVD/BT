// static/js/image-cropper.js - VERSIÓN CORREGIDA
class ImageCropper {
    constructor() {
        this.cropper = null;
        this.currentFile = null;
        this.croppedBlob = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        console.log('ImageCropper inicializado correctamente');
    }

    setupEventListeners() {
        const fileInput = document.getElementById('foto_perfil');
        const dropZone = document.getElementById('dropZone');
        const activarInputBtn = document.getElementById('activarInputFoto');

        // ✅ CORREGIDO: Event listener para el botón activador
        if (activarInputBtn && fileInput) {
            activarInputBtn.addEventListener('click', () => {
                console.log('Activando input de foto...');
                fileInput.click();
            });
        }

        // ✅ CORREGIDO: Event listener para el input file
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                console.log('Archivo seleccionado:', e.target.files[0]);
                this.handleFileSelect(e);
            });
        }

        // ✅ Drop zone events (solo si existe)
        if (dropZone) {
            dropZone.addEventListener('click', () => {
                console.log('Drop zone clickeado');
                if (fileInput) fileInput.click();
            });

            dropZone.addEventListener('dragover', (e) => this.handleDragOver(e));
            dropZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
            dropZone.addEventListener('drop', (e) => this.handleDrop(e));
        }

        // ✅ Botones del cropper (solo si existen)
        this.setupCropperButtons();
    }

    setupCropperButtons() {
        // Usar delegación de eventos para botones que pueden no existir aún
        document.addEventListener('click', (e) => {
            if (e.target.id === 'cropButton' || e.target.closest('#cropButton')) {
                e.preventDefault();
                console.log('Botón crop clickeado');
                this.cropImage();
            }
            if (e.target.id === 'resetCropButton' || e.target.closest('#resetCropButton')) {
                e.preventDefault();
                console.log('Botón reset clickeado');
                this.resetCropper();
            }
            if (e.target.id === 'cancelCropButton' || e.target.closest('#cancelCropButton')) {
                e.preventDefault();
                console.log('Botón cancel clickeado');
                this.cancelCrop();
            }
        });
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        console.log('Procesando archivo:', file);

        if (file) {
            this.processFile(file);
        } else {
            console.log('No se seleccionó archivo');
        }
    }

    handleDragOver(event) {
        event.preventDefault();
        event.currentTarget.classList.add('dragover');
    }

    handleDragLeave(event) {
        event.currentTarget.classList.remove('dragover');
    }

    handleDrop(event) {
        event.preventDefault();
        event.currentTarget.classList.remove('dragover');

        const files = event.dataTransfer.files;
        if (files.length > 0) {
            console.log('Archivo dropeado:', files[0]);
            this.processFile(files[0]);
        }
    }

    processFile(file) {
        console.log('Validando archivo:', file.name, file.type, file.size);

        // Validar tipo de archivo
        if (!file.type.match(/^image\/(jpeg|jpg)$/i)) {
            this.showMessage('Solo se permiten archivos JPG', 'error');
            return;
        }

        // Validar tamaño (5MB)
        if (file.size > 5 * 1024 * 1024) {
            this.showMessage('El archivo es demasiado grande. Máximo 5MB', 'error');
            return;
        }

        this.currentFile = file;
        this.loadImageForCropping(file);
    }

    loadImageForCropping(file) {
        console.log('Cargando imagen para cropping...');

        const reader = new FileReader();
        reader.onload = (e) => {
            console.log('Imagen cargada, mostrando modal...');
            this.showCropperModal();
            this.showCropperStep();
            this.initializeCropper(e.target.result);
        };
        reader.onerror = () => {
            console.error('Error leyendo archivo');
            this.showMessage('Error al leer el archivo', 'error');
        };
        reader.readAsDataURL(file);
    }

    showCropperModal() {
        const modal = document.getElementById('cropperModal');
        if (modal) {
            console.log('Mostrando modal del cropper...');
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        } else {
            console.error('Modal cropperModal no encontrado');
        }
    }

    showCropperStep() {
        const selectStep = document.getElementById('selectStep');
        const cropStep = document.getElementById('cropStep');

        if (selectStep) selectStep.classList.remove('active');
        if (cropStep) cropStep.classList.add('active');
    }

    showSelectStep() {
        const selectStep = document.getElementById('selectStep');
        const cropStep = document.getElementById('cropStep');

        if (cropStep) cropStep.classList.remove('active');
        if (selectStep) selectStep.classList.add('active');
        this.destroyCropper();
    }

    initializeCropper(imageSrc) {
        const imageElement = document.getElementById('cropperImage');

        if (!imageElement) {
            console.error('Elemento cropperImage no encontrado');
            return;
        }

        console.log('Inicializando cropper...');
        imageElement.src = imageSrc;

        // Destruir cropper existente si hay uno
        this.destroyCropper();

        // Esperar a que la imagen se cargue antes de inicializar el cropper
        imageElement.onload = () => {
            console.log('Imagen cargada, creando cropper...');

            // Verificar que Cropper esté disponible
            if (typeof Cropper === 'undefined') {
                console.error('Cropper.js no está disponible');
                this.showMessage('Error: Biblioteca de recorte no disponible', 'error');
                return;
            }

            try {
                // Inicializar nuevo cropper
                this.cropper = new Cropper(imageElement, {
                    aspectRatio: 1, // Cuadrado 1:1
                    viewMode: 1,
                    dragMode: 'move',
                    autoCropArea: 0.8,
                    restore: false,
                    guides: true,
                    center: true,
                    highlight: false,
                    cropBoxMovable: true,
                    cropBoxResizable: true,
                    toggleDragModeOnDblclick: false,
                    modal: true,
                    background: true,
                    responsive: true,
                    checkOrientation: false,
                    minCropBoxWidth: 100,
                    minCropBoxHeight: 100,
                    ready: () => {
                        console.log('Cropper listo');
                        this.updatePreview();
                    },
                    cropend: () => {
                        this.updatePreview();
                    }
                });
            } catch (error) {
                console.error('Error inicializando cropper:', error);
                this.showMessage('Error al inicializar el recortador de imagen', 'error');
            }
        };

        imageElement.onerror = () => {
            console.error('Error cargando imagen');
            this.showMessage('Error al cargar la imagen', 'error');
        };
    }

    updatePreview() {
        if (!this.cropper) {
            console.log('No hay cropper disponible para preview');
            return;
        }

        try {
            const canvas = this.cropper.getCroppedCanvas({
                width: 160,
                height: 160,
                fillColor: '#fff',
                imageSmoothingEnabled: true,
                imageSmoothingQuality: 'high'
            });

            const previewContainer = document.getElementById('cropPreview');
            if (!previewContainer) {
                console.log('Preview container no encontrado');
                return;
            }

            const previewImg = previewContainer.querySelector('img');

            if (previewImg) {
                previewImg.src = canvas.toDataURL('image/jpeg', 0.9);
            } else {
                const img = document.createElement('img');
                img.src = canvas.toDataURL('image/jpeg', 0.9);
                img.alt = 'Preview';
                previewContainer.appendChild(img);
            }

            previewContainer.style.display = 'block';
        } catch (error) {
            console.error('Error actualizando preview:', error);
        }
    }

    cropImage() {
        if (!this.cropper) {
            console.error('No hay cropper disponible');
            return;
        }

        console.log('Recortando imagen...');

        try {
            const canvas = this.cropper.getCroppedCanvas({
                width: 160,
                height: 160,
                fillColor: '#fff',
                imageSmoothingEnabled: true,
                imageSmoothingQuality: 'high'
            });

            canvas.toBlob((blob) => {
                if (blob) {
                    console.log('Imagen recortada exitosamente');
                    this.croppedBlob = blob;
                    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
                    this.updateMainPreview(dataUrl);
                    this.closeCropperModal();

                    // Guardar automáticamente la imagen recortada
                    this.saveImageAutomatically(blob, dataUrl);
                } else {
                    console.error('Error generando blob');
                    this.showMessage('Error al procesar la imagen', 'error');
                }
            }, 'image/jpeg', 0.9);
        } catch (error) {
            console.error('Error en cropImage:', error);
            this.showMessage('Error al recortar la imagen', 'error');
        }
    }

    updateMainPreview(dataUrl) {
        // Actualizar preview en el modal principal
        const mainPreviewContainer = document.getElementById('photoPreviewContainer');
        const mainPhotoPreview = document.getElementById('photoPreview');
        const mainPhotoPlaceholder = document.getElementById('photoPlaceholder');

        if (mainPhotoPreview) {
            mainPhotoPreview.src = dataUrl;
        } else if (mainPhotoPlaceholder && mainPreviewContainer) {
            const imgElement = document.createElement('img');
            imgElement.src = dataUrl;
            imgElement.alt = 'Foto de perfil';
            imgElement.className = 'profile-photo';
            imgElement.id = 'photoPreview';
            mainPreviewContainer.replaceChild(imgElement, mainPhotoPlaceholder);
        }
    }

    resetCropper() {
        if (this.cropper) {
            console.log('Reseteando cropper...');
            this.cropper.reset();
            this.updatePreview();
        }
    }

    cancelCrop() {
        console.log('Cancelando crop...');
        this.showSelectStep();
        const fileInput = document.getElementById('foto_perfil');
        if (fileInput) fileInput.value = '';

        const cropPreview = document.getElementById('cropPreview');
        if (cropPreview) cropPreview.style.display = 'none';

        this.closeCropperModal();
    }

    destroyCropper() {
        if (this.cropper) {
            console.log('Destruyendo cropper...');
            this.cropper.destroy();
            this.cropper = null;
        }
    }

    closeCropperModal() {
        const modal = document.getElementById('cropperModal');
        if (modal) {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        }

        // Regresar al modal principal después de cerrar el cropper
        setTimeout(() => {
            const mainModal = document.getElementById('editarPerfilModal');
            if (mainModal) {
                const bsMainModal = new bootstrap.Modal(mainModal);
                bsMainModal.show();
            }
        }, 300);
    }

    saveImageAutomatically(blob, dataUrl) {
        console.log('Guardando imagen automáticamente...');

        // Mostrar mensaje de guardando
        this.showMessage('Guardando imagen...', 'info');

        // Crear FormData solo con la imagen
        const formData = new FormData();
        formData.append('foto_perfil', blob, 'profile.jpg');

        // Obtener token CSRF
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (!csrfToken) {
            console.error('Token CSRF no encontrado');
            this.showMessage('Error: Token de seguridad no encontrado', 'error');
            return;
        }

        const updateUrl = '/ajax/actualizar-perfil/';

        // Enviar solo la imagen
        fetch(updateUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken.value
            }
        })
        .then(response => {
            console.log('Respuesta del servidor:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Datos recibidos:', data);
            if (data.success) {
                // Actualizar todas las imágenes en la página con la nueva URL
                this.updateAllProfileImages(data.data.foto_url || dataUrl);
                this.showMessage('Imagen guardada exitosamente', 'success');
            } else {
                console.error('Error del servidor:', data.error);
                this.showMessage('Error al guardar: ' + (data.error || 'Error desconocido'), 'error');
            }
        })
        .catch(error => {
            console.error('Error en fetch:', error);
            this.showMessage('Error de conexión al guardar la imagen', 'error');
        });
    }

    updateAllProfileImages(imageUrl) {
        console.log('Actualizando todas las imágenes de perfil con:', imageUrl);

        // Actualizar imagen en el card principal del perfil
        const mainProfileImages = document.querySelectorAll('.profile-photo');
        const mainProfilePlaceholders = document.querySelectorAll('.profile-photo-placeholder');

        // Actualizar imágenes existentes
        mainProfileImages.forEach(img => {
            img.src = imageUrl;
        });

        // Reemplazar placeholders con imágenes
        mainProfilePlaceholders.forEach(placeholder => {
            const imgElement = document.createElement('img');
            imgElement.src = imageUrl;
            imgElement.alt = 'Foto de perfil';
            imgElement.className = 'profile-photo';
            placeholder.parentNode.replaceChild(imgElement, placeholder);
        });

        // También actualizar en el modal si está abierto
        const modalPreview = document.getElementById('photoPreview');
        const modalPlaceholder = document.getElementById('photoPlaceholder');

        if (modalPreview) {
            modalPreview.src = imageUrl;
        } else if (modalPlaceholder) {
            const imgElement = document.createElement('img');
            imgElement.src = imageUrl;
            imgElement.alt = 'Foto de perfil';
            imgElement.className = 'profile-photo';
            imgElement.id = 'photoPreview';
            modalPlaceholder.parentNode.replaceChild(imgElement, modalPlaceholder);
        }
    }

    getCroppedFile() {
        return this.croppedBlob;
    }

    showMessage(mensaje, tipo) {
        console.log(`Mensaje ${tipo}:`, mensaje);

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

        let bgClass = 'success';
        let icon = 'check-circle';

        switch(tipo) {
            case 'error':
                bgClass = 'danger';
                icon = 'exclamation-circle';
                break;
            case 'info':
                bgClass = 'info';
                icon = 'info-circle';
                break;
            case 'warning':
                bgClass = 'warning';
                icon = 'exclamation-triangle';
                break;
        }

        toastDiv.className = `toast align-items-center text-bg-${bgClass} border-0`;
        toastDiv.setAttribute('role', 'alert');
        toastDiv.setAttribute('aria-live', 'assertive');
        toastDiv.setAttribute('aria-atomic', 'true');

        toastDiv.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-${icon} me-2"></i>
                    ${mensaje}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        toastContainer.appendChild(toastDiv);

        // Mostrar toast
        const toast = new bootstrap.Toast(toastDiv, {
            autohide: true,
            delay: tipo === 'info' ? 2000 : 4000
        });
        toast.show();

        // Remover del DOM después de que se oculte
        toastDiv.addEventListener('hidden.bs.toast', function() {
            toastDiv.remove();
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM cargado, inicializando ImageCropper...');

    // Verificar que Bootstrap esté disponible
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap no está disponible');
        return;
    }

    // Inicializar ImageCropper
    try {
        window.imageCropper = new ImageCropper();
        console.log('ImageCropper inicializado y asignado a window.imageCropper');
    } catch (error) {
        console.error('Error inicializando ImageCropper:', error);
    }
});