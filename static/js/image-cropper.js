// static/js/image-cropper.js - VERSIÓN SIMPLIFICADA SIN CROP PREVIEW
class ImageCropper {
    constructor() {
        this.cropper = null;
        this.currentFile = null;
        this.croppedBlob = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Event listeners para los contenedores de foto de perfil
        const profileContainers = document.querySelectorAll('.profile-photo-container, .clickeable-photo');
        profileContainers.forEach(container => {
            container.addEventListener('click', () => this.abrirModalCropper());
        });

        // Event listener para el drop zone
        const dropZone = document.getElementById('dropZone');
        if (dropZone) {
            dropZone.addEventListener('click', () => this.abrirSelectorArchivo());
            dropZone.addEventListener('dragover', (e) => this.handleDragOver(e));
            dropZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
            dropZone.addEventListener('drop', (e) => this.handleDrop(e));
        }

        // Event listener para el input file hidden
        const fileInput = document.getElementById('foto_perfil');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }

        // Botones del cropper
        document.addEventListener('click', (e) => {
            if (e.target.id === 'cropButton') this.cropAndSaveImage();
            if (e.target.id === 'resetCropButton') this.resetCropper();
            if (e.target.id === 'cancelCropButton') this.cancelCrop();
        });
    }

    abrirModalCropper() {
        // Abrir modal del cropper en el paso de selección
        const cropperModal = new bootstrap.Modal(document.getElementById('cropperModal'));
        cropperModal.show();
        
        // Asegurar que esté en el paso de selección
        document.getElementById('cropStep').classList.remove('active');
        document.getElementById('selectStep').classList.add('active');
    }

    abrirSelectorArchivo() {
        const fileInput = document.getElementById('foto_perfil');
        if (fileInput) {
            fileInput.click();
        }
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.processFile(file);
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
            this.processFile(files[0]);
        }
    }

    processFile(file) {
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
        const reader = new FileReader();
        reader.onload = (e) => {
            // Ir directamente al paso de recorte
            this.showCropperModal();
            this.initializeCropper(e.target.result);
        };
        reader.readAsDataURL(file);
    }

    showCropperModal() {
        // Mostrar solo el modal del cropper
        const cropperModal = new bootstrap.Modal(document.getElementById('cropperModal'));
        cropperModal.show();
        
        // Ir directamente al paso de recorte
        document.getElementById('selectStep').classList.remove('active');
        document.getElementById('cropStep').classList.add('active');
    }

    initializeCropper(imageSrc) {
        const imageElement = document.getElementById('cropperImage');
        imageElement.src = imageSrc;
        imageElement.style.display = 'block';

        // Destruir cropper existente si hay uno
        this.destroyCropper();

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
            minCropBoxHeight: 100
        });
    }

 // En image-cropper.js - REEMPLAZAR el método cropAndSaveImage() existente

cropAndSaveImage() {
    if (!this.cropper) return;

    // Mostrar loading en el botón
    const cropButton = document.getElementById('cropButton');
    const originalText = cropButton.innerHTML;
    cropButton.innerHTML = '<i class="bi bi-hourglass-split"></i> Guardando...';
    cropButton.disabled = true;

    const canvas = this.cropper.getCroppedCanvas({
        width: 160,
        height: 160,
        fillColor: '#fff',
        imageSmoothingEnabled: true,
        imageSmoothingQuality: 'high'
    });

    canvas.toBlob((blob) => {
        this.croppedBlob = blob;
        const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
        
        // Guardar la imagen inmediatamente
        this.saveImageToServer(blob, dataUrl)
            .then(() => {
                // ✅ SOLUCIÓN RÁPIDA: Mostrar mensaje y recargar página
                this.showMessage('Imagen guardada exitosamente. Recargando página...', 'success');
                
                // Cerrar modal inmediatamente
                this.closeCropperModal();
                
                // ✅ RECARGAR PÁGINA DESPUÉS DE 1.5 SEGUNDOS
                setTimeout(() => {
                    console.log('🔄 Recargando página para actualizar estado de la imagen...');
                    window.location.reload();
                }, 1500);
                
            })
            .catch((error) => {
                console.error('Error:', error);
                this.showMessage('Error al guardar la imagen', 'error');
                
                // Restaurar botón en caso de error
                cropButton.innerHTML = originalText;
                cropButton.disabled = false;
            });
    }, 'image/jpeg', 0.9);
}

    async saveImageToServer(blob, dataUrl) {
        // Crear FormData solo con la imagen
        const formData = new FormData();
        formData.append('foto_perfil', blob, 'profile.jpg');

        // Obtener token CSRF
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const updateUrl = '/ajax/actualizar-foto-perfil/'; // URL específica para fotos

        const response = await fetch(updateUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken
            }
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Error desconocido');
        }

        return data;
    }

    updateAllProfileImages(imageUrl) {
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
    }

    resetCropper() {
        if (this.cropper) {
            this.cropper.reset();
        }
    }

    cancelCrop() {
        // Resetear el input file
        const fileInput = document.getElementById('foto_perfil');
        if (fileInput) {
            fileInput.value = '';
        }
        
        // Limpiar la imagen del cropper
        const cropperImage = document.getElementById('cropperImage');
        if (cropperImage) {
            cropperImage.src = '';
            cropperImage.style.display = 'none';
        }
        
        // Destruir el cropper
        this.destroyCropper();
        
        // Volver al paso de selección
        document.getElementById('cropStep').classList.remove('active');
        document.getElementById('selectStep').classList.add('active');
        
        // NO cerrar el modal, solo regresar al paso 1
        // El usuario puede volver a seleccionar una imagen o cerrar manualmente
        
        this.showMessage('Operación cancelada. Puedes seleccionar otra imagen.', 'info');
    }

    destroyCropper() {
        if (this.cropper) {
            this.cropper.destroy();
            this.cropper = null;
        }
    }

    closeCropperModal() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('cropperModal'));
        if (modal) {
            modal.hide();
        }
        
        // Limpiar el estado
        this.destroyCropper();
        
        // Resetear pasos del modal
        document.getElementById('cropStep').classList.remove('active');
        document.getElementById('selectStep').classList.add('active');
    }

    showMessage(mensaje, tipo) {
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

        // Determinar duración específica según el mensaje
        let delay = 4000; // Por defecto 4 segundos
        
        if (mensaje === 'Imagen guardada exitosamente') {
            delay = 3000; // 3 segundos específicamente para este mensaje
        } else if (tipo === 'success') {
            delay = 3000; // 3 segundos para otros mensajes de éxito
        } else if (tipo === 'info') {
            delay = 2000; // 2 segundos para info
        }
        
        const toast = new bootstrap.Toast(toastDiv, {
            autohide: true,
            delay: delay
        });
        toast.show();

        // Remover del DOM después de que se oculte
        toastDiv.addEventListener('hidden.bs.toast', function() {
            toastDiv.remove();
        });
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.imageCropper = new ImageCropper();
});