// static/js/session-timeout.js - Sistema de auto-logout por inactividad

class SessionTimeout {
    constructor(options = {}) {
        // Configuración por defecto
        this.config = {
            timeoutMinutes: options.timeoutMinutes || 15, // 15 minutos por defecto
            warningMinutes: options.warningMinutes || 2,  // Advertencia 2 minutos antes
            checkInterval: options.checkInterval || 30000, // Verificar cada 30 segundos
            logoutUrl: options.logoutUrl || '/logout/',
            extendUrl: options.extendUrl || '/ajax/extend-session/',
            ...options
        };

        // Variables de estado
        this.timeoutDuration = this.config.timeoutMinutes * 60 * 1000; // Convertir a millisegundos
        this.warningDuration = this.config.warningMinutes * 60 * 1000;
        this.lastActivity = Date.now();
        this.warningShown = false;
        this.sessionEnded = false;
        
        // Timers
        this.checkTimer = null;
        this.warningTimer = null;
        this.logoutTimer = null;

        this.init();
    }

    init() {
        // Solo activar para usuarios autenticados
        if (!this.isUserAuthenticated()) {
            return;
        }

        
        this.setupEventListeners();
        this.startActivityCheck();
        this.resetActivity(); // Marcar actividad inicial
    }

    isUserAuthenticated() {
        // Verificar si hay elementos que indican sesión activa
        return document.querySelector('[data-user-authenticated="true"]') !== null ||
               document.querySelector('.navbar .nav-link[href*="logout"]') !== null ||
               document.body.classList.contains('authenticated');
    }

    setupEventListeners() {
        // Eventos que indican actividad del usuario
        const activityEvents = [
            'mousedown', 'mousemove', 'keypress', 'scroll', 
            'touchstart', 'click', 'focus', 'blur'
        ];

        activityEvents.forEach(event => {
            document.addEventListener(event, () => this.resetActivity(), true);
        });

        // Eventos de visibilidad de la página
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.resetActivity();
            }
        });

        // Detectar cambios de foco en la ventana
        window.addEventListener('focus', () => this.resetActivity());
    }

    resetActivity() {
        if (this.sessionEnded) return;

        this.lastActivity = Date.now();
        this.warningShown = false;

        // Limpiar timers existentes
        this.clearTimers();

        // Programar nueva advertencia
        this.warningTimer = setTimeout(() => {
            this.showWarning();
        }, this.timeoutDuration - this.warningDuration);

        // Programar logout automático
        this.logoutTimer = setTimeout(() => {
            this.performLogout();
        }, this.timeoutDuration);
    }

    startActivityCheck() {
        // Verificar actividad cada intervalo configurado
        this.checkTimer = setInterval(() => {
            this.checkSession();
        }, this.config.checkInterval);
    }

    checkSession() {
        if (this.sessionEnded) return;

        const now = Date.now();
        const timeSinceActivity = now - this.lastActivity;
        const timeUntilWarning = this.timeoutDuration - this.warningDuration - timeSinceActivity;
        const timeUntilLogout = this.timeoutDuration - timeSinceActivity;

        // Mostrar advertencia si es tiempo
        if (timeUntilWarning <= 0 && !this.warningShown) {
            this.showWarning();
        }

        // Hacer logout si es tiempo
        if (timeUntilLogout <= 0) {
            this.performLogout();
        }
    }

    showWarning() {
        if (this.warningShown || this.sessionEnded) return;

        this.warningShown = true;
        const remainingMinutes = Math.ceil(this.config.warningMinutes);

        // Crear modal de advertencia
        this.createWarningModal(remainingMinutes);
    }

    createWarningModal(remainingMinutes) {
        // Eliminar modal existente si existe
        const existingModal = document.getElementById('sessionTimeoutModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Crear estructura del modal
        const modalHTML = `
            <div class="modal fade" id="sessionTimeoutModal" tabindex="-1" aria-labelledby="sessionTimeoutModalLabel" aria-hidden="true" data-bs-backdrop="static" data-bs-keyboard="false">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-warning">
                        <div class="modal-header bg-warning text-dark">
                            <h5 class="modal-title" id="sessionTimeoutModalLabel">
                                <i class="bi bi-clock-fill me-2"></i>Sesión por Expirar
                            </h5>
                        </div>
                        <div class="modal-body text-center">
                            <div class="mb-3">
                                <i class="bi bi-exclamation-triangle-fill text-warning" style="font-size: 3rem;"></i>
                            </div>
                            <h6>Tu sesión expirará en <span id="countdownMinutes">${remainingMinutes}</span> minuto(s)</h6>
                            <p class="text-muted">
                                Por seguridad, tu sesión se cerrará automáticamente debido a inactividad.
                            </p>
                            <div class="alert alert-info">
                                <small>
                                    <i class="bi bi-info-circle me-1"></i>
                                    Haz clic en "Continuar Sesión" para permanecer conectado.
                                </small>
                            </div>
                        </div>
                        <div class="modal-footer justify-content-center">
                            <button type="button" class="btn btn-outline-secondary" id="logoutNowBtn">
                                <i class="bi bi-box-arrow-right me-1"></i>Cerrar Sesión Ahora
                            </button>
                            <button type="button" class="btn btn-primary" id="extendSessionBtn">
                                <i class="bi bi-arrow-clockwise me-1"></i>Continuar Sesión
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Agregar modal al DOM
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Configurar evento listeners del modal
        this.setupModalEvents();

        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('sessionTimeoutModal'));
        modal.show();

        // Iniciar countdown
        this.startCountdown();
    }

    setupModalEvents() {
        // Botón para extender sesión
        document.getElementById('extendSessionBtn').addEventListener('click', () => {
            this.extendSession();
        });

        // Botón para cerrar sesión inmediatamente
        document.getElementById('logoutNowBtn').addEventListener('click', () => {
            this.performLogout();
        });
    }

    startCountdown() {
        let remainingSeconds = this.config.warningMinutes * 60;
        const countdownElement = document.getElementById('countdownMinutes');

        const countdownTimer = setInterval(() => {
            if (this.sessionEnded || !countdownElement) {
                clearInterval(countdownTimer);
                return;
            }

            remainingSeconds--;
            const minutes = Math.floor(remainingSeconds / 60);
            const seconds = remainingSeconds % 60;

            if (remainingSeconds > 60) {
                countdownElement.textContent = minutes;
            } else {
                countdownElement.textContent = `${seconds}s`;
            }

            if (remainingSeconds <= 0) {
                clearInterval(countdownTimer);
                this.performLogout();
            }
        }, 1000);
    }

    extendSession() {
        // Cerrar modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('sessionTimeoutModal'));
        if (modal) {
            modal.hide();
        }

        // Hacer petición AJAX para extender sesión
        fetch(this.config.extendUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                extend: true
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.resetActivity();
                this.showToast('Sesión extendida exitosamente', 'success');
            } else {
                throw new Error('Error al extender sesión');
            }
        })
        .catch(error => {
            console.error('Error al extender sesión:', error);
            this.showToast('Error al extender sesión. Redirigiendo...', 'error');
            setTimeout(() => this.performLogout(), 2000);
        });
    }

    performLogout() {
        if (this.sessionEnded) return;

        this.sessionEnded = true;
        this.clearTimers();

        // Cerrar modal si está abierto
        const modal = bootstrap.Modal.getInstance(document.getElementById('sessionTimeoutModal'));
        if (modal) {
            modal.hide();
        }

        // Mostrar mensaje de logout
        this.showToast('Sesión cerrada por inactividad', 'info');

        // Redirigir al logout después de un breve delay
        setTimeout(() => {
            window.location.href = this.config.logoutUrl;
        }, 1500);
    }

    clearTimers() {
        if (this.checkTimer) {
            clearInterval(this.checkTimer);
            this.checkTimer = null;
        }
        if (this.warningTimer) {
            clearTimeout(this.warningTimer);
            this.warningTimer = null;
        }
        if (this.logoutTimer) {
            clearTimeout(this.logoutTimer);
            this.logoutTimer = null;
        }
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    showToast(message, type = 'info') {
        // Crear contenedor de toasts si no existe
        let toastContainer = document.getElementById('toast-container-timeout');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container-timeout';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }

        // Crear toast
        const toastId = 'toast-timeout-' + Date.now();
        const toastDiv = document.createElement('div');
        toastDiv.id = toastId;

        let bgClass = 'primary';
        let icon = 'info-circle';

        switch(type) {
            case 'success':
                bgClass = 'success';
                icon = 'check-circle';
                break;
            case 'error':
                bgClass = 'danger';
                icon = 'exclamation-circle';
                break;
            case 'warning':
                bgClass = 'warning';
                icon = 'exclamation-triangle';
                break;
        }

        toastDiv.className = `toast align-items-center text-bg-${bgClass} border-0`;
        toastDiv.setAttribute('role', 'alert');

        toastDiv.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-${icon} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        toastContainer.appendChild(toastDiv);

        // Mostrar toast
        const toast = new bootstrap.Toast(toastDiv, {
            autohide: true,
            delay: 3000
        });
        toast.show();

        // Remover del DOM después de ocultarse
        toastDiv.addEventListener('hidden.bs.toast', function() {
            toastDiv.remove();
        });
    }

    // Método público para destruir la instancia
    destroy() {
        this.sessionEnded = true;
        this.clearTimers();
        
        // Remover modal si existe
        const modal = document.getElementById('sessionTimeoutModal');
        if (modal) {
            modal.remove();
        }
    }
}

// Inicializar automáticamente cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Solo inicializar si no existe ya una instancia
    if (!window.sessionTimeout) {
        window.sessionTimeout = new SessionTimeout({
            timeoutMinutes: 15,     // 15 minutos de inactividad
            warningMinutes: 2,      // Advertencia 2 minutos antes
            checkInterval: 30000,   // Verificar cada 30 segundos
            logoutUrl: '/logout/',
            extendUrl: '/ajax/extend-session/'
        });
    }
});