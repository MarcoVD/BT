// static/js/busqueda-vacantes.js
class BusquedaVacantes {
    constructor() {
        this.searchForm = document.getElementById('searchForm');
        this.searchInput = document.querySelector('input[name="q"]');
        this.clearBtn = document.getElementById('clearBtn');
        this.suggestions = document.querySelectorAll('.search-suggestion');
        this.filtros = document.querySelectorAll('select[name="tipo_empleo"], select[name="municipio"]');

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupAutocompletado();
        this.highlightSearchTerms();
    }

    setupEventListeners() {
        // Limpiar formulario
        if (this.clearBtn) {
            this.clearBtn.addEventListener('click', () => {
                this.limpiarFormulario();
            });
        }

        // Sugerencias de búsqueda
        this.suggestions.forEach(button => {
            button.addEventListener('click', (e) => {
                this.aplicarSugerencia(e.target.dataset.query);
            });
        });

        // Auto-submit en cambio de filtros (solo si hay texto de búsqueda)
        this.filtros.forEach(select => {
            select.addEventListener('change', () => {
                if (this.searchInput.value.trim()) {
                    this.submitFormulario();
                }
            });
        });

        // Mejorar UX del formulario
        if (this.searchForm) {
            this.searchForm.addEventListener('submit', (e) => {
                this.handleSubmit(e);
            });
        }

        // Búsqueda mientras escribes (con debounce)
        if (this.searchInput) {
            let timeoutId;
            this.searchInput.addEventListener('input', (e) => {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => {
                    this.handleLiveSearch(e.target.value);
                }, 500); // Esperar 500ms después de que el usuario deje de escribir
            });
        }
    }

    setupAutocompletado() {
        // Lista de términos populares para autocompletado
        const terminosPopulares = [
            'desarrollador', 'contador', 'ventas', 'administrador', 'ingeniero',
            'marketing', 'recursos humanos', 'finanzas', 'diseñador', 'analista',
            'gerente', 'asistente', 'coordinador', 'supervisor', 'técnico'
        ];

        if (this.searchInput) {
            // Crear datalist para autocompletado
            const datalist = document.createElement('datalist');
            datalist.id = 'search-suggestions';

            terminosPopulares.forEach(termino => {
                const option = document.createElement('option');
                option.value = termino;
                datalist.appendChild(option);
            });

            document.body.appendChild(datalist);
            this.searchInput.setAttribute('list', 'search-suggestions');
        }
    }

    limpiarFormulario() {
        if (this.searchForm) {
            this.searchForm.reset();
            window.location.href = window.location.pathname; // Limpiar parámetros GET
        }
    }

    aplicarSugerencia(query) {
        if (this.searchInput) {
            this.searchInput.value = query;
            this.submitFormulario();
        }
    }

    submitFormulario() {
        if (this.searchForm) {
            this.mostrarCarga(true);
            this.searchForm.submit();
        }
    }

    handleSubmit(e) {
        const query = this.searchInput.value.trim();

        if (!query && !this.tieneFilters()) {
            e.preventDefault();
            this.mostrarMensaje('Por favor ingresa un término de búsqueda o selecciona un filtro', 'warning');
            return;
        }

        this.mostrarCarga(true);

        // Agregar clase visual al botón de submit
        const submitBtn = this.searchForm.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Buscando...';
            submitBtn.disabled = true;
        }
    }

    handleLiveSearch(query) {
        // Solo hacer búsqueda en vivo si hay más de 2 caracteres
        if (query.length > 2) {
            this.mostrarSugerenciasRelacionadas(query);
        }
    }

    mostrarSugerenciasRelacionadas(query) {
        // Buscar en los términos populares que coincidan
        const terminosRelacionados = [
            'desarrollador web', 'desarrollador mobile', 'contador público',
            'vendedor', 'gerente de ventas', 'administrador de sistemas',
            'ingeniero civil', 'ingeniero sistemas', 'marketing digital'
        ].filter(termino =>
            termino.toLowerCase().includes(query.toLowerCase())
        );

        // Actualizar sugerencias dinámicamente
        const suggestionsContainer = document.querySelector('.d-flex.flex-wrap.gap-1');
        if (suggestionsContainer && terminosRelacionados.length > 0) {
            const nuevasSugerencias = terminosRelacionados.slice(0, 3).map(termino =>
                `<button type="button" class="btn btn-outline-success btn-sm search-suggestion" data-query="${termino}">
                    ${termino}
                </button>`
            ).join('');

            suggestionsContainer.innerHTML = nuevasSugerencias;

            // Re-agregar event listeners
            suggestionsContainer.querySelectorAll('.search-suggestion').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    this.aplicarSugerencia(e.target.dataset.query);
                });
            });
        }
    }

    tieneFilters() {
        return Array.from(this.filtros).some(select => select.value !== '');
    }

    mostrarCarga(mostrar) {
        const container = document.querySelector('.container');
        if (mostrar) {
            container.style.cursor = 'wait';
        } else {
            container.style.cursor = 'default';
        }
    }

    highlightSearchTerms() {
        // Resaltar términos de búsqueda en los resultados
        const urlParams = new URLSearchParams(window.location.search);
        const query = urlParams.get('q');

        if (query) {
            const vacanteTitles = document.querySelectorAll('.vacante-card .card-title');
            const vacanteDescriptions = document.querySelectorAll('.vacante-card .card-text');

            const highlightText = (elements, searchTerm) => {
                elements.forEach(element => {
                    const text = element.innerHTML;
                    const highlightedText = text.replace(
                        new RegExp(`(${searchTerm})`, 'gi'),
                        '<mark class="bg-warning">$1</mark>'
                    );
                    element.innerHTML = highlightedText;
                });
            };

            highlightText(vacanteTitles, query);
            highlightText(vacanteDescriptions, query);
        }
    }

    mostrarMensaje(mensaje, tipo) {
        // Crear alerta temporal
        const alerta = document.createElement('div');
        alerta.className = `alert alert-${tipo} alert-dismissible fade show position-fixed`;
        alerta.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';

        alerta.innerHTML = `
            ${mensaje}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(alerta);

        // Auto-remover después de 4 segundos
        setTimeout(() => {
            if (alerta.parentNode) {
                alerta.remove();
            }
        }, 4000);
    }

    // Método para filtros avanzados (expandible en el futuro)
    mostrarFiltrosAvanzados() {
        const filtrosAvanzados = document.getElementById('filtrosAvanzados');
        if (filtrosAvanzados) {
            filtrosAvanzados.classList.toggle('d-none');
        }
    }

    // Guardar búsquedas recientes en localStorage
    guardarBusquedaReciente(query) {
        if (!query.trim()) return;

        let busquedasRecientes = JSON.parse(localStorage.getItem('busquedasRecientes') || '[]');

        // Agregar nueva búsqueda al inicio, evitar duplicados
        busquedasRecientes = busquedasRecientes.filter(b => b !== query);
        busquedasRecientes.unshift(query);

        // Mantener solo las últimas 5 búsquedas
        busquedasRecientes = busquedasRecientes.slice(0, 5);

        localStorage.setItem('busquedasRecientes', JSON.stringify(busquedasRecientes));
    }

    // Cargar búsquedas recientes
    cargarBusquedasRecientes() {
        const busquedasRecientes = JSON.parse(localStorage.getItem('busquedasRecientes') || '[]');

        if (busquedasRecientes.length > 0) {
            const container = document.querySelector('.search-suggestions-container');
            if (container) {
                const recientesHTML = busquedasRecientes.map(busqueda =>
                    `<button type="button" class="btn btn-outline-secondary btn-sm search-suggestion" data-query="${busqueda}">
                        <i class="bi bi-clock-history"></i> ${busqueda}
                    </button>`
                ).join('');

                container.innerHTML = `
                    <h6 class="text-muted mb-2">Búsquedas recientes:</h6>
                    ${recientesHTML}
                `;
            }
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.busquedaVacantes = new BusquedaVacantes();
});

// Función auxiliar para búsqueda rápida
function busquedaRapida(termino) {
    const searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        searchInput.value = termino;
        document.getElementById('searchForm').submit();
    }
}