/**
 * validar_login.js
 * Script de validación en tiempo real para formularios de registro
 * Ubicación: BT/static/js/validar_login.js
 *
 * Funcionalidades:
 * - Validación de email en tiempo real
 * - Validación de contraseña con requisitos visuales
 * - Verificación de confirmación de contraseña
 * - Indicadores visuales de fortaleza de contraseña
 * - Control del estado del botón de envío
 */

class ValidadorRegistro {
    constructor(options = {}) {
        // Configuración por defecto
        this.config = {
            formId: 'registroForm',
            emailFieldId: null,
            password1FieldId: null,
            password2FieldId: null,
            submitButtonId: 'submitBtn',
            ...options
        };

        // Lista de contraseñas comunes
        this.commonPasswords = [
            '123456', 'password', '123456789', '12345678', '12345', '1234567',
            '1234567890', 'qwerty', 'abc123', 'password123', 'admin', 'letmein',
            '123123', 'welcome', 'monkey', '1234', 'password1', '123', 'qwerty123',
            'football', 'iloveyou', 'princess', 'dragon', 'baseball', 'sunshine',
            'superman', 'trustno1', 'starwars', 'whatever', '1qaz2wsx', 'shadow'
        ];

        // Estado de validación
        this.validationState = {
            email: false,
            password1: false,
            password2: false
        };

        // Elementos del DOM
        this.elements = {};

        // Inicializar cuando el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    /**
     * Inicializa el validador
     */
    init() {
        try {
            this.setupElements();
            this.setupEventListeners();
            this.updateSubmitButton();
            console.log('✅ ValidadorRegistro inicializado correctamente');
        } catch (error) {
            console.error('❌ Error al inicializar ValidadorRegistro:', error);
        }
    }

    /**
     * Configura las referencias a elementos del DOM
     */
    setupElements() {
        // Formulario
        this.elements.form = document.getElementById(this.config.formId);
        if (!this.elements.form) {
            throw new Error(`Formulario con ID '${this.config.formId}' no encontrado`);
        }

        // Campos de entrada (auto-detectar si no se especifican)
        this.elements.emailInput = this.findInput(this.config.emailFieldId, ['email', 'correo']);
        this.elements.password1Input = this.findInput(this.config.password1FieldId, ['password1', 'password']);
        this.elements.password2Input = this.findInput(this.config.password2FieldId, ['password2', 'confirm']);

        // Botón de envío
        this.elements.submitBtn = document.getElementById(this.config.submitButtonId);

        // Elementos de validación visual
        this.elements.emailIcon = document.getElementById('emailIcon');
        this.elements.password1Icon = document.getElementById('password1Icon');
        this.elements.password2Icon = document.getElementById('password2Icon');

        this.elements.emailFeedback = document.getElementById('emailFeedback');
        this.elements.password1Feedback = document.getElementById('password1Feedback');
        this.elements.password2Feedback = document.getElementById('password2Feedback');

        // Elementos de requisitos de contraseña
        this.elements.reqLength = document.getElementById('req-length');
        this.elements.reqNotCommon = document.getElementById('req-not-common');
        this.elements.reqNotNumeric = document.getElementById('req-not-numeric');
        this.elements.reqNotPersonal = document.getElementById('req-not-personal');

        // Elementos de fortaleza
        this.elements.strengthFill = document.getElementById('strengthFill');
        this.elements.strengthText = document.getElementById('strengthText');
    }

    /**
     * Busca un input por ID o por atributos comunes
     */
    findInput(specificId, fallbackSelectors) {
        if (specificId) {
            return document.getElementById(specificId);
        }

        // Buscar por selectores comunes
        for (const selector of fallbackSelectors) {
            const input = document.querySelector(`input[name*="${selector}"], input[id*="${selector}"]`);
            if (input) return input;
        }

        return null;
    }

    /**
     * Configura los event listeners
     */
    setupEventListeners() {
        // Validación de email
        if (this.elements.emailInput) {
            this.elements.emailInput.addEventListener('input', (e) => this.validateEmail(e));
            this.elements.emailInput.addEventListener('blur', (e) => this.validateEmail(e));
        }

        // Validación de contraseña
        if (this.elements.password1Input) {
            this.elements.password1Input.addEventListener('input', (e) => this.validatePassword1(e));
        }

        // Validación de confirmación de contraseña
        if (this.elements.password2Input) {
            this.elements.password2Input.addEventListener('input', (e) => this.validatePassword2(e));
        }

        // Prevenir envío si no es válido
        if (this.elements.form) {
            this.elements.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }
    }

    /**
     * Valida el campo de email
     */
    validateEmail(event) {
        const email = event.target.value.trim();

        if (email === '') {
            this.validationState.email = false;
            this.updateValidation(
                this.elements.emailInput,
                this.elements.emailIcon,
                this.elements.emailFeedback,
                false,
                ''
            );
        } else if (this.isValidEmail(email)) {
            this.validationState.email = true;
            this.updateValidation(
                this.elements.emailInput,
                this.elements.emailIcon,
                this.elements.emailFeedback,
                true,
                'Correo electrónico válido'
            );
        } else {
            this.validationState.email = false;
            this.updateValidation(
                this.elements.emailInput,
                this.elements.emailIcon,
                this.elements.emailFeedback,
                false,
                'Por favor, ingresa un correo electrónico válido'
            );
        }

        this.updateSubmitButton();
    }

    /**
     * Valida la contraseña principal
     */
    validatePassword1(event) {
        const password = event.target.value;

        if (password === '') {
            this.validationState.password1 = false;
            this.updateValidation(
                this.elements.password1Input,
                this.elements.password1Icon,
                this.elements.password1Feedback,
                false,
                ''
            );
            this.updatePasswordStrength('');
            this.updatePasswordRequirements('');
        } else {
            const allRequirementsMet = this.updatePasswordRequirements(password);
            this.updatePasswordStrength(password);

            if (allRequirementsMet) {
                this.validationState.password1 = true;
                this.updateValidation(
                    this.elements.password1Input,
                    this.elements.password1Icon,
                    this.elements.password1Feedback,
                    true,
                    'Contraseña segura'
                );
            } else {
                this.validationState.password1 = false;
                this.updateValidation(
                    this.elements.password1Input,
                    this.elements.password1Icon,
                    this.elements.password1Feedback,
                    false,
                    'La contraseña no cumple todos los requisitos'
                );
            }
        }

        // Revalidar confirmación de contraseña si existe
        if (this.elements.password2Input && this.elements.password2Input.value) {
            this.validatePassword2({ target: this.elements.password2Input });
        }

        this.updateSubmitButton();
    }

    /**
     * Valida la confirmación de contraseña
     */
    validatePassword2(event) {
        const password2 = event.target.value;
        const password1 = this.elements.password1Input ? this.elements.password1Input.value : '';

        if (password2 === '') {
            this.validationState.password2 = false;
            this.updateValidation(
                this.elements.password2Input,
                this.elements.password2Icon,
                this.elements.password2Feedback,
                false,
                ''
            );
        } else if (password2 === password1) {
            this.validationState.password2 = true;
            this.updateValidation(
                this.elements.password2Input,
                this.elements.password2Icon,
                this.elements.password2Feedback,
                true,
                'Las contraseñas coinciden'
            );
        } else {
            this.validationState.password2 = false;
            this.updateValidation(
                this.elements.password2Input,
                this.elements.password2Icon,
                this.elements.password2Feedback,
                false,
                'Las contraseñas no coinciden'
            );
        }

        this.updateSubmitButton();
    }

    /**
     * Valida formato de email
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Verifica si la contraseña es común
     */
    isCommonPassword(password) {
        return this.commonPasswords.includes(password.toLowerCase());
    }

    /**
     * Verifica si la contraseña es solo numérica
     */
    isNumericOnly(password) {
        return /^\d+$/.test(password);
    }

    /**
     * Calcula la fortaleza de la contraseña
     */
    calculatePasswordStrength(password) {
        let score = 0;

        // Criterios positivos
        if (password.length >= 8) score += 25;
        if (password.length >= 12) score += 10;
        if (/[a-z]/.test(password)) score += 15;
        if (/[A-Z]/.test(password)) score += 15;
        if (/[0-9]/.test(password)) score += 15;
        if (/[^A-Za-z0-9]/.test(password)) score += 20;

        // Penalizaciones
        if (this.isCommonPassword(password)) score -= 30;
        if (this.isNumericOnly(password)) score -= 25;
        if (password.length < 8) score -= 20;

        score = Math.max(0, Math.min(100, score));

        return {
            score: score,
            level: score < 25 ? 'weak' : score < 50 ? 'fair' : score < 75 ? 'good' : 'strong'
        };
    }

    /**
     * Actualiza la visualización de validación
     */
    updateValidation(input, icon, feedback, isValid, message) {
        if (!input) return;

        // Limpiar clases existentes
        input.classList.remove('is-valid', 'is-invalid');

        if (icon) {
            icon.classList.remove('show', 'valid', 'invalid', 'bi-check-circle-fill', 'bi-x-circle-fill');
        }

        if (feedback) {
            feedback.classList.remove('show', 'valid', 'invalid');
        }

        // Si el campo está vacío, no mostrar validación
        if (input.value.trim() === '') {
            return;
        }

        // Aplicar estilos según validación
        if (isValid) {
            input.classList.add('is-valid');
            if (icon) {
                icon.classList.add('show', 'valid', 'bi-check-circle-fill');
            }
            if (feedback && message) {
                feedback.textContent = message;
                feedback.classList.add('show', 'valid');
            }
        } else {
            input.classList.add('is-invalid');
            if (icon) {
                icon.classList.add('show', 'invalid', 'bi-x-circle-fill');
            }
            if (feedback && message) {
                feedback.textContent = message;
                feedback.classList.add('show', 'invalid');
            }
        }
    }

    /**
     * Actualiza los requisitos de contraseña
     */
    updatePasswordRequirements(password) {
        if (!password || !this.elements.reqLength) return false;

        // Verificar longitud
        const hasLength = password.length >= 8;
        this.updateRequirement(this.elements.reqLength, hasLength);

        // Verificar que no sea común
        const notCommon = !this.isCommonPassword(password);
        this.updateRequirement(this.elements.reqNotCommon, notCommon);

        // Verificar que no sea solo numérica
        const notNumeric = !this.isNumericOnly(password);
        this.updateRequirement(this.elements.reqNotNumeric, notNumeric);

        // Verificar que no sea personal (básico)
        const emailUser = this.elements.emailInput ?
            this.elements.emailInput.value.split('@')[0].toLowerCase() : '';
        const notPersonal = !password.toLowerCase().includes(emailUser);
        this.updateRequirement(this.elements.reqNotPersonal, notPersonal);

        return hasLength && notCommon && notNumeric && notPersonal;
    }

    /**
     * Actualiza un requisito individual
     */
    updateRequirement(element, isMet) {
        if (!element) return;

        const icon = element.querySelector('i');
        element.classList.remove('met', 'unmet');

        if (icon) {
            icon.classList.remove('bi-check-circle-fill', 'bi-circle');
        }

        if (isMet) {
            element.classList.add('met');
            if (icon) icon.classList.add('bi-check-circle-fill');
        } else {
            element.classList.add('unmet');
            if (icon) icon.classList.add('bi-circle');
        }
    }

    /**
     * Actualiza la barra de fortaleza de contraseña
     */
    updatePasswordStrength(password) {
        if (!this.elements.strengthFill || !this.elements.strengthText) return;

        if (password.length === 0) {
            this.elements.strengthFill.style.width = '0%';
            this.elements.strengthText.textContent = '';
            this.elements.strengthFill.className = 'strength-fill';
            return;
        }

        const strength = this.calculatePasswordStrength(password);
        this.elements.strengthFill.style.width = strength.score + '%';
        this.elements.strengthFill.className = 'strength-fill strength-' + strength.level;

        const strengthLabels = {
            weak: 'Débil',
            fair: 'Regular',
            good: 'Buena',
            strong: 'Fuerte'
        };

        this.elements.strengthText.textContent = 'Fortaleza: ' + strengthLabels[strength.level];
    }

    /**
     * Actualiza el estado del botón de envío
     */
    updateSubmitButton() {
        if (!this.elements.submitBtn) return;

        const allValid = Object.values(this.validationState).every(state => state);
        this.elements.submitBtn.disabled = !allValid;

        // Agregar clase visual si es necesario
        if (allValid) {
            this.elements.submitBtn.classList.remove('btn-disabled');
        } else {
            this.elements.submitBtn.classList.add('btn-disabled');
        }
    }

    /**
     * Maneja el envío del formulario
     */
    handleSubmit(event) {
        const allValid = Object.values(this.validationState).every(state => state);

        if (!allValid) {
            event.preventDefault();

            // Mostrar mensaje de error más amigable
            const invalidFields = [];
            if (!this.validationState.email) invalidFields.push('correo electrónico');
            if (!this.validationState.password1) invalidFields.push('contraseña');
            if (!this.validationState.password2) invalidFields.push('confirmación de contraseña');

            const message = `Por favor, corrige los siguientes campos: ${invalidFields.join(', ')}`;

            // Usar toast si está disponible, sino alert
            if (typeof showToast === 'function') {
                showToast(message, 'error');
            } else {
                alert(message);
            }

            console.warn('❌ Envío de formulario bloqueado - Validación incompleta');
        } else {
            console.log('✅ Formulario válido - Permitiendo envío');
        }
    }

    /**
     * Método público para validar manualmente
     */
    validate() {
        if (this.elements.emailInput) this.validateEmail({ target: this.elements.emailInput });
        if (this.elements.password1Input) this.validatePassword1({ target: this.elements.password1Input });
        if (this.elements.password2Input) this.validatePassword2({ target: this.elements.password2Input });

        return Object.values(this.validationState).every(state => state);
    }

    /**
     * Método público para resetear validación
     */
    reset() {
        this.validationState = {
            email: false,
            password1: false,
            password2: false
        };

        // Limpiar estilos visuales
        const inputs = [this.elements.emailInput, this.elements.password1Input, this.elements.password2Input];
        inputs.forEach(input => {
            if (input) {
                input.classList.remove('is-valid', 'is-invalid');
                input.value = '';
            }
        });

        this.updateSubmitButton();
        console.log('🔄 ValidadorRegistro reseteado');
    }
}
    
// Función de conveniencia para inicializar con configuración por defecto
function initValidadorRegistro(options = {}) {
    return new ValidadorRegistro(options);
}

// Auto-inicializar si los elementos están presentes
document.addEventListener('DOMContentLoaded', function() {
    // Solo inicializar si existe el formulario de registro
    if (document.getElementById('registroForm')) {
        window.validadorRegistro = new ValidadorRegistro();
    }
});

// Exportar para uso en módulos (si es necesario)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ValidadorRegistro, initValidadorRegistro };
}