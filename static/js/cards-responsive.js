// // ==============================================
// // SISTEMA DE PAGINACIÓN RESPONSIVA REUTILIZABLE
// // ==============================================
//
// class ResponsiveCardsPagination {
//     constructor(options = {}) {
//         // Configuración por defecto
//         this.options = {
//             containerSelector: '.responsive-cards-container',
//             itemSelector: '.responsive-card-item',
//             controlsSelector: '#pagination-controls',
//             prevBtnSelector: '#prev-btn',
//             nextBtnSelector: '#next-btn',
//             pageInfoSelector: '#page-info',
//             showingInfoSelector: '#showing-info',
//
//             // Configuración de items por página según dispositivo
//             itemsPerPage: {
//                 mobile: 3,    // Móviles: 3 cards por vista
//                 tablet: 3,    // Tablets: 3 cards por vista
//                 laptop: 4,    // Laptops: 4 cards por vista
//                 desktop: 5    // PC: 5 cards por vista
//             },
//
//             // Breakpoints (deben coincidir con CSS)
//             breakpoints: {
//                 mobile: 767,
//                 tablet: 991,
//                 laptop: 1199
//             },
//
//             animationDuration: 300,
//             autoInit: true,
//             showControlsThreshold: 1, // Mostrar controles cuando hay más de 1 página
//
//             ...options
//         };
//
//         // Estado interno
//         this.currentPage = 1;
//         this.totalPages = 1;
//         this.currentDevice = 'desktop';
//         this.totalItems = 0;
//
//         // Elementos DOM
//         this.container = null;
//         this.items = [];
//         this.controls = null;
//         this.prevBtn = null;
//         this.nextBtn = null;
//         this.pageInfo = null;
//         this.showingInfo = null;
//
//         // Inicializar si está configurado para auto-init
//         if (this.options.autoInit) {
//             this.init();
//         }
//     }
//
//     // ==============================================
//     // MÉTODOS DE INICIALIZACIÓN
//     // ==============================================
//
//     init() {
//         try {
//             this.findElements();
//             this.setupEventListeners();
//             this.detectDevice();
//             this.calculatePagination();
//             this.updateDisplay();
//
//             console.log('ResponsiveCardsPagination inicializado correctamente');
//         } catch (error) {
//             console.error('Error inicializando ResponsiveCardsPagination:', error);
//         }
//     }
//
//     findElements() {
//         this.container = document.querySelector(this.options.containerSelector);
//         if (!this.container) {
//             throw new Error(`Contenedor no encontrado: ${this.options.containerSelector}`);
//         }
//
//         this.items = Array.from(this.container.querySelectorAll(this.options.itemSelector));
//         this.totalItems = this.items.length;
//
//         // Elementos de control
//         this.controls = document.querySelector(this.options.controlsSelector);
//         this.prevBtn = document.querySelector(this.options.prevBtnSelector);
//         this.nextBtn = document.querySelector(this.options.nextBtnSelector);
//         this.pageInfo = document.querySelector(this.options.pageInfoSelector);
//         this.showingInfo = document.querySelector(this.options.showingInfoSelector);
//
//         if (this.totalItems === 0) {
//             console.warn('No se encontraron items para paginar');
//             return;
//         }
//     }
//
//     setupEventListeners() {
//         // Eventos de navegación
//         if (this.prevBtn) {
//             this.prevBtn.addEventListener('click', () => this.previousPage());
//         }
//
//         if (this.nextBtn) {
//             this.nextBtn.addEventListener('click', () => this.nextPage());
//         }
//
//         // Evento de redimensionamiento de ventana
//         let resizeTimeout;
//         window.addEventListener('resize', () => {
//             clearTimeout(resizeTimeout);
//             resizeTimeout = setTimeout(() => {
//                 this.handleResize();
//             }, 250);
//         });
//
//         // Eventos de teclado para accesibilidad
//         document.addEventListener('keydown', (e) => {
//             if (e.target.closest(this.options.controlsSelector)) {
//                 this.handleKeyboardNavigation(e);
//             }
//         });
//     }
//
//     // ==============================================
//     // DETECCIÓN DE DISPOSITIVO Y CÁLCULOS
//     // ==============================================
//
//     detectDevice() {
//         const width = window.innerWidth;
//
//         if (width <= this.options.breakpoints.mobile) {
//             this.currentDevice = 'mobile';
//         } else if (width <= this.options.breakpoints.tablet) {
//             this.currentDevice = 'tablet';
//         } else if (width <= this.options.breakpoints.laptop) {
//             this.currentDevice = 'laptop';
//         } else {
//             this.currentDevice = 'desktop';
//         }
//     }
//
//     calculatePagination() {
//         const itemsPerPage = this.options.itemsPerPage[this.currentDevice];
//         this.totalPages = Math.ceil(this.totalItems / itemsPerPage);
//
//         // Ajustar página actual si excede el total
//         if (this.currentPage > this.totalPages) {
//             this.currentPage = Math.max(1, this.totalPages);
//         }
//     }
//
//     getCurrentItemsPerPage() {
//         return this.options.itemsPerPage[this.currentDevice];
//     }
//
//     // ==============================================
//     // MÉTODOS DE NAVEGACIÓN
//     // ==============================================
//
//     nextPage() {
//         if (this.currentPage < this.totalPages) {
//             this.currentPage++;
//             this.updateDisplay();
//         }
//     }
//
//     previousPage() {
//         if (this.currentPage > 1) {
//             this.currentPage--;
//             this.updateDisplay();
//         }
//     }
//
//     goToPage(page) {
//         if (page >= 1 && page <= this.totalPages) {
//             this.currentPage = page;
//             this.updateDisplay();
//         }
//     }
//
//     // ==============================================
//     // ACTUALIZACIÓN DE DISPLAY
//     // ==============================================
//
//     updateDisplay() {
//         this.showCurrentPageItems();
//         this.updateControls();
//         this.updatePageInfo();
//     }
//
//     showCurrentPageItems() {
//         const itemsPerPage = this.getCurrentItemsPerPage();
//         const startIndex = (this.currentPage - 1) * itemsPerPage;
//         const endIndex = startIndex + itemsPerPage;
//
//         // Ocultar todos los items primero
//         this.items.forEach((item, index) => {
//             if (index >= startIndex && index < endIndex) {
//                 this.showItem(item);
//             } else {
//                 this.hideItem(item);
//             }
//         });
//     }
//
//     showItem(item) {
//         item.classList.remove('hidden', 'fade-out');
//         item.classList.add('fade-in');
//
//         // Limpiar la clase de animación después de que termine
//         setTimeout(() => {
//             item.classList.remove('fade-in');
//         }, this.options.animationDuration);
//     }
//
//     hideItem(item) {
//         item.classList.add('hidden');
//         item.classList.remove('fade-in', 'fade-out');
//     }
//
//     updateControls() {
//         if (!this.controls) return;
//
//         // Mostrar/ocultar controles basado en el número de páginas
//         if (this.totalPages <= this.options.showControlsThreshold) {
//             this.controls.style.display = 'none';
//             return;
//         } else {
//             this.controls.style.display = 'block';
//         }
//
//         // Actualizar estado de botones
//         if (this.prevBtn) {
//             this.prevBtn.disabled = this.currentPage <= 1;
//         }
//
//         if (this.nextBtn) {
//             this.nextBtn.disabled = this.currentPage >= this.totalPages;
//         }
//     }
//
//     updatePageInfo() {
//         if (this.pageInfo) {
//             this.pageInfo.textContent = `Página ${this.currentPage} de ${this.totalPages}`;
//         }
//
//         if (this.showingInfo) {
//             const itemsPerPage = this.getCurrentItemsPerPage();
//             const startIndex = (this.currentPage - 1) * itemsPerPage + 1;
//             const endIndex = Math.min(this.currentPage * itemsPerPage, this.totalItems);
//
//             this.showingInfo.textContent = `Mostrando ${startIndex}-${endIndex} de ${this.totalItems}`;
//         }
//     }
//
//     // ==============================================
//     // MANEJO DE EVENTOS
//     // ==============================================
//
//     handleResize() {
//         const previousDevice = this.currentDevice;
//         this.detectDevice();
//
//         // Solo recalcular si cambió el tipo de dispositivo
//         if (previousDevice !== this.currentDevice) {
//             this.calculatePagination();
//             this.updateDisplay();
//
//             console.log(`Dispositivo cambió de ${previousDevice} a ${this.currentDevice}`);
//         }
//     }
//
//     handleKeyboardNavigation(e) {
//         switch (e.key) {
//             case 'ArrowLeft':
//                 e.preventDefault();
//                 this.previousPage();
//                 break;
//             case 'ArrowRight':
//                 e.preventDefault();
//                 this.nextPage();
//                 break;
//             case 'Home':
//                 e.preventDefault();
//                 this.goToPage(1);
//                 break;
//             case 'End':
//                 e.preventDefault();
//                 this.goToPage(this.totalPages);
//                 break;
//         }
//     }
//
//     // ==============================================
//     // MÉTODOS PÚBLICOS PARA CONTROL EXTERNO
//     // ==============================================
//
//     refresh() {
//         this.findElements();
//         this.calculatePagination();
//         this.updateDisplay();
//     }
//
//     addItem(itemHtml, index = -1) {
//         const tempDiv = document.createElement('div');
//         tempDiv.innerHTML = itemHtml;
//         const newItem = tempDiv.firstElementChild;
//
//         if (index === -1 || index >= this.items.length) {
//             this.container.appendChild(newItem);
//         } else {
//             this.container.insertBefore(newItem, this.items[index]);
//         }
//
//         this.refresh();
//     }
//
//     removeItem(index) {
//         if (index >= 0 && index < this.items.length) {
//             this.items[index].remove();
//             this.refresh();
//         }
//     }
//
//     getState() {
//         return {
//             currentPage: this.currentPage,
//             totalPages: this.totalPages,
//             currentDevice: this.currentDevice,
//             totalItems: this.totalItems,
//             itemsPerPage: this.getCurrentItemsPerPage()
//         };
//     }
//
//     // ==============================================
//     // MÉTODOS DE CONFIGURACIÓN
//     // ==============================================
//
//     updateOptions(newOptions) {
//         this.options = { ...this.options, ...newOptions };
//         this.refresh();
//     }
//
//     setItemsPerPage(device, count) {
//         this.options.itemsPerPage[device] = count;
//         this.calculatePagination();
//         this.updateDisplay();
//     }
// }
//
// // ==============================================
// // INICIALIZACIÓN AUTOMÁTICA
// // ==============================================
//
// document.addEventListener('DOMContentLoaded', function() {
//     // Verificar si existe el contenedor de vacantes
//     const vacantesContainer = document.querySelector('#vacantes-grid');
//
//     if (vacantesContainer) {
//         // Inicializar sistema de paginación para vacantes
//         window.vacantesPagination = new ResponsiveCardsPagination({
//             containerSelector: '#vacantes-grid',
//             itemSelector: '.responsive-card-item'
//         });
//
//         console.log('Sistema de paginación de vacantes inicializado');
//     }
// });
//
// // ==============================================
// // FUNCIÓN GLOBAL PARA CREAR NUEVAS INSTANCIAS
// // ==============================================
//
// window.createCardsPagination = function(options) {
//     return new ResponsiveCardsPagination(options);
// };
//
// // ==============================================
// // EXPORT PARA USO EN MÓDULOS
// // ==============================================
//
// if (typeof module !== 'undefined' && module.exports) {
//     module.exports = ResponsiveCardsPagination;
// }