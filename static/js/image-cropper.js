// static/js/image-cropper.js - SOLUCIÓN SIMPLIFICADA
class ImageCropper {
    constructor() {
        this.cropper = null;
        this.currentFile = null;
        this.croppedBlob = null;
        this.init();
    }

    init() {
        console.log('🚀 Inicializando ImageCropper...');

        //  CONFIGURAR CUANDO EL DOM ESTÉ COMPLETAMENTE LISTO
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.setupEventListeners();
            });
        } else {
            this.setupEventListeners();
        }
    }

    setupEventListeners() {
        console.log('🔧 Configurando event listeners...');

        //  1. CONFIGURAR CLICS EN IMÁGENES DE PERFIL
        this.setupProfileImageClicks();

        //  2. CONFIGURAR MODAL CROPPER CUANDO SE ABRA
        this.setupCropperModal();

        //  3. CONFIGURAR INPUT FILE
        this.setupFileInput();

        //  4. CONFIGURAR BOTONES DEL CROPPER
        this.setupCropperButtons();
    }

    setupProfileImageClicks() {
        console.log('🖼️ Configurando clics en imágenes de perfil...');

        //  USAR DELEGATION PARA MANEJAR ELEMENTOS DINÁMICOS
        document.addEventListener('click', (e) => {
            // Verificar si el elemento clickeado es una imagen de perfil o placeholder
            if (e.target.classList.contains('clickeable-photo') ||
                e.target.closest('.clickeable-photo') ||
                e.target.classList.contains('profile-photo') ||
                e.target.closest('.profile-photo-container')) {

                e.preventDefault();
                e.stopPropagation();

                console.log('📸 Imagen de perfil clickeada:', e.target);

                // Cerrar cualquier modal abierto primero
                this.closeAllModals();

                // Abrir modal cropper
                setTimeout(() => {
                    this.openCropperModal();
                }, 100);
            }
        });

        //  TAMBIÉN MANEJAR BOTÓN "CARGAR FOTO" DENTRO DEL MODAL DE PERFIL
        document.addEventListener('click', (e) => {
            if (e.target.closest('[data-bs-target="#cropperModal"]')) {
                e.preventDefault();
                e.stopPropagation();

                console.log('🔲 Botón cargar foto clickeado');

                // Cerrar modal principal
                const editarModal = document.getElementById('editarPerfilModal');
                if (editarModal) {
                    const modal = bootstrap.Modal.getInstance(editarModal);
                    if (modal) modal.hide();
                }

                // Abrir modal cropper
                setTimeout(() => {
                    this.openCropperModal();
                }, 300);
            }
        });
    }

    closeAllModals() {
        // Cerrar modal de editar perfil si está abierto
        const editarModal = document.getElementById('editarPerfilModal');
        if (editarModal) {
            const modal = bootstrap.Modal.getInstance(editarModal);
            if (modal) modal.hide();
        }

        // Cerrar modal cropper si está abierto
        const cropperModal = document.getElementById('cropperModal');
        if (cropperModal) {
            const modal = bootstrap.Modal.getInstance(cropperModal);
            if (modal) modal.hide();
        }
    }

openCropperModal() {
    console.log('🎭 Abriendo modal cropper...');

    const cropperModalElement = document.getElementById('cropperModal');
    if (!cropperModalElement) {
        console.error('❌ Modal cropper no encontrado!');
        this.showMessage('Error: Modal no encontrado', 'error');
        return;
    }

    // Reset del estado
    this.showSelectStep();
    this.destroyCropper();

    // Abrir modal
    const cropperModal = new bootstrap.Modal(cropperModalElement, {
        backdrop: 'static',
        keyboard: false
    });
    cropperModal.show();

    // CONFIGURAR EVENTOS INMEDIATAMENTE Y DESPUÉS DEL SHOWN
    setTimeout(() => {
        this.setupCropperModalEvents();
        this.configureFileInput();
    }, 100);

    // Configurar también cuando se abra completamente
    cropperModalElement.addEventListener('shown.bs.modal', () => {
        console.log('🎭 Modal cropper abierto completamente');
        this.setupCropperModalEvents();
        this.configureFileInput();
    }, { once: true });
}

    setupCropperModal() {
        const cropperModalElement = document.getElementById('cropperModal');
        if (cropperModalElement) {
            // Limpiar cuando se cierre
            cropperModalElement.addEventListener('hidden.bs.modal', () => {
                this.destroyCropper();
                this.resetFileInput();
            });
        }
    }

setupCropperModalEvents() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('foto_perfil');

    console.log('Configurando eventos del modal cropper...', { dropZone, fileInput });

    if (dropZone && fileInput) {
        // LIMPIAR eventos anteriores
        dropZone.replaceWith(dropZone.cloneNode(true));
        const newDropZone = document.getElementById('dropZone');

        // CLICK EN DROP ZONE
        newDropZone.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('🎯 Drop zone clickeado, abriendo selector...');
            fileInput.click();
        });

        // DRAG AND DROP
        newDropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            newDropZone.classList.add('dragover');
        });

        newDropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            newDropZone.classList.remove('dragover');
        });

        newDropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            newDropZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.processFile(files[0]);
            }
        });
    }
}

setupFileInput() {
    // Configurar cuando el DOM esté listo
    document.addEventListener('DOMContentLoaded', () => {
        this.configureFileInput();
    });

    // También configurar inmediatamente por si ya está listo
    if (document.readyState === 'complete') {
        this.configureFileInput();
    }
}

configureFileInput() {
    const fileInput = document.getElementById('foto_perfil');
    if (fileInput) {
        console.log('📁 Configurando input file...');

        // LIMPIAR evento anterior
        fileInput.removeEventListener('change', this.handleFileChange);

        // Crear handler bound
        this.handleFileChange = (e) => {
            console.log('📁 Archivo seleccionado:', e.target.files);
            const file = e.target.files[0];
            if (file) {
                this.processFile(file);
            }
        };

        // Agregar evento
        fileInput.addEventListener('change', this.handleFileChange);
    }
}

    setupCropperButtons() {
        console.log('🔲 Configurando botones del cropper...');

        //  USAR EVENT DELEGATION
        document.addEventListener('click', (e) => {
            const target = e.target;

            if (target.id === 'cropButton') {
                e.preventDefault();
                console.log('✂️ Botón recortar clickeado');
                this.cropImage();
            }

            if (target.id === 'resetCropButton') {
                e.preventDefault();
                console.log('🔄 Botón reset clickeado');
                this.resetCropper();
            }

            if (target.id === 'cancelCropButton') {
                e.preventDefault();
                console.log('❌ Botón cancelar clickeado');
                this.cancelCrop();
            }
        });
    }

    processFile(file) {
        console.log('📋 Procesando archivo:', file);

        // Validar tipo
            if (!file.type.match(/^image\/(jpeg|jpg|png)$/i)) {
                this.showMessage('Solo se permiten archivos JPG, JPEG o PNG', 'error');
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
        console.log('🖼️ Cargando imagen para recorte...');

        const reader = new FileReader();
        reader.onload = (e) => {
            console.log(' Imagen cargada');
            this.showCropperStep();
            this.initializeCropper(e.target.result);
        };
        reader.onerror = () => {
            console.error('❌ Error al leer archivo');
            this.showMessage('Error al leer el archivo', 'error');
        };
        reader.readAsDataURL(file);
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
    }

    initializeCropper(imageSrc) {
        console.log('⚙️ Inicializando cropper...');

        const imageElement = document.getElementById('cropperImage');
        if (!imageElement) {
            console.error('❌ Elemento imagen del cropper no encontrado');
            return;
        }

        // Verificar que Cropper.js esté disponible
        if (typeof Cropper === 'undefined') {
            console.error('❌ Cropper.js no está cargado');
            this.showMessage('Error: Cropper.js no disponible', 'error');
            return;
        }

        // Destruir cropper anterior
        this.destroyCropper();

        // Configurar imagen
        imageElement.src = imageSrc;
        imageElement.style.display = 'block';

        // Esperar a que se cargue la imagen
        imageElement.onload = () => {
            console.log(' Imagen cargada, creando cropper...');

            try {
                this.cropper = new Cropper(imageElement, {
                    aspectRatio: 1,
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
                        console.log(' Cropper listo');
                        this.updatePreview();
                    },
                    cropend: () => {
                        this.updatePreview();
                    }
                });
            } catch (error) {
                console.error('❌ Error al crear cropper:', error);
                this.showMessage('Error al inicializar el cropper', 'error');
            }
        };
    }

    updatePreview() {
        if (!this.cropper) return;

        try {
            const canvas = this.cropper.getCroppedCanvas({
                width: 160,
                height: 160,
                fillColor: '#fff',
                imageSmoothingEnabled: true,
                imageSmoothingQuality: 'high'
            });

            const previewContainer = document.getElementById('cropPreview');
            if (previewContainer) {
                const previewImg = previewContainer.querySelector('img') || document.createElement('img');
                previewImg.src = canvas.toDataURL('image/jpeg', 0.9);
                previewImg.alt = 'Preview';

                if (!previewImg.parentNode) {
                    previewContainer.innerHTML = '';
                    previewContainer.appendChild(previewImg);
                }

                previewContainer.style.display = 'block';
            }
        } catch (error) {
            console.error('❌ Error al actualizar preview:', error);
        }
    }

    cropImage() {
        if (!this.cropper) {
            console.error('❌ No hay cropper disponible');
            return;
        }

        console.log('✂️ Recortando imagen...');

        try {
            const canvas = this.cropper.getCroppedCanvas({
                width: 160,
                height: 160,
                fillColor: '#fff',
                imageSmoothingEnabled: true,
                imageSmoothingQuality: 'high'
            });

            canvas.toBlob((blob) => {
                if (!blob) {
                    console.error('❌ Error al crear blob');
                    this.showMessage('Error al procesar la imagen', 'error');
                    return;
                }

                console.log(' Imagen recortada exitosamente');
                this.croppedBlob = blob;
                const dataUrl = canvas.toDataURL('image/jpeg', 0.9);

                // Cerrar modal
                this.closeCropperModal();

                // Guardar imagen
                this.saveImageAutomatically(blob, dataUrl);

            }, 'image/jpeg', 0.9);
        } catch (error) {
            console.error('❌ Error al recortar:', error);
            this.showMessage('Error al recortar la imagen', 'error');
        }
    }

    resetCropper() {
        if (this.cropper) {
            this.cropper.reset();
            this.updatePreview();
        }
    }

    cancelCrop() {
        console.log('❌ Cancelando recorte...');
        this.closeCropperModal();
        this.resetFileInput();
    }

    resetFileInput() {
        const fileInput = document.getElementById('foto_perfil');
        if (fileInput) {
            fileInput.value = '';
        }
    }

    destroyCropper() {
        if (this.cropper) {
            try {
                this.cropper.destroy();
            } catch (error) {
                console.warn('⚠️ Error al destruir cropper:', error);
            }
            this.cropper = null;
        }
    }

    closeCropperModal() {
        const cropperModalElement = document.getElementById('cropperModal');
        if (cropperModalElement) {
            const modal = bootstrap.Modal.getInstance(cropperModalElement);
            if (modal) {
                modal.hide();
            }
        }
    }

    saveImageAutomatically(blob, dataUrl) {
        console.log('💾 Guardando imagen...');

        this.showMessage('Guardando imagen...', 'info');

        const formData = new FormData();
        formData.append('foto_perfil', blob, 'profile.jpg');

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        if (!csrfToken) {
            console.error('❌ Token CSRF no encontrado');
            this.showMessage('Error: Token de seguridad no encontrado', 'error');
            return;
        }

        fetch('/ajax/actualizar-perfil/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            console.log('📡 Respuesta del servidor:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(' Respuesta:', data);
            if (data.success) {
                this.updateAllProfileImages(data.data.foto_url || dataUrl);
                this.showMessage('Imagen guardada exitosamente', 'success');
            } else {
                this.showMessage('Error: ' + (data.error || 'Error desconocido'), 'error');
            }
        })
        .catch(error => {
            console.error('❌ Error al guardar:', error);
            this.showMessage('Error de conexión: ' + error.message, 'error');
        });
    }

    updateAllProfileImages(imageUrl) {
        console.log('🔄 Actualizando todas las imágenes con:', imageUrl);

        const timestamp = Date.now();
        const newImageUrl = imageUrl + '?v=' + timestamp;

        // Actualizar todas las imágenes de perfil
        const profileImages = document.querySelectorAll('.profile-photo');
        profileImages.forEach(img => {
            console.log('🖼️ Actualizando imagen:', img);
            img.src = newImageUrl;
        });

        // Actualizar placeholders
        const placeholders = document.querySelectorAll('.profile-photo-placeholder');
        placeholders.forEach(placeholder => {
            console.log('🔄 Reemplazando placeholder:', placeholder);
            const img = document.createElement('img');
            img.src = newImageUrl;
            img.alt = 'Foto de perfil';
            img.className = 'profile-photo img-fluid rounded-circle clickeable-photo';
            img.style.cursor = 'pointer';

            placeholder.parentNode.replaceChild(img, placeholder);
        });

        // Actualizar en modales
        const modalImages = document.querySelectorAll('#photoPreview');
        modalImages.forEach(img => {
            img.src = newImageUrl;
        });
    }

    showMessage(mensaje, tipo) {
        console.log(`📢 ${tipo.toUpperCase()}: ${mensaje}`);

        // Crear toast
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }

        const toastElement = document.createElement('div');
        toastElement.className = `toast align-items-center text-bg-${tipo === 'error' ? 'danger' : tipo === 'success' ? 'success' : 'info'} border-0`;

        toastElement.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${mensaje}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        toastContainer.appendChild(toastElement);

        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: tipo === 'info' ? 2000 : 4000
        });

        toast.show();

        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
}

//  INICIALIZAR INMEDIATAMENTE
console.log('🚀 Creando instancia de ImageCropper...');
window.imageCropper = new ImageCropper();