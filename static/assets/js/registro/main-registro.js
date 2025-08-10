// =============================================================================
// ARCHIVO PRINCIPAL DE INICIALIZACIÓN - REGISTRO DE MOVIMIENTOS
// =============================================================================

// Variables globales principales - declaradas aquí para evitar duplicados
let currentMovimientos = [];
let filteredMovimientos = [];
let currentSortField = 'fecha';
let currentSortOrder = 'desc';
let editingMovimiento = null;

// Variables globales para los filtros
let currentTipoFilter = 'todos';
let currentIngresosGastosFilter = 'todos';

// Set the global window registroUrl for AJAX requests
window.registroUrl = window.registroUrl || '/registro/';

// Function to update global variables and expose them to window
function updateGlobalVariables() {
    window.currentMovimientos = currentMovimientos;
    window.filteredMovimientos = filteredMovimientos;
    window.currentSortField = currentSortField;
    window.currentSortOrder = currentSortOrder;
    window.editingMovimiento = editingMovimiento;
    window.currentTipoFilter = currentTipoFilter;
    window.currentIngresosGastosFilter = currentIngresosGastosFilter;
}

// Initial exposure of variables
updateGlobalVariables();

$(document).ready(function () {
    console.log('Página de registro cargada');
    
    // Initialize page components
    initializePage();
    
    // Setup event listeners
    setupEventListeners();
    
    // Check if there's a default ejercicio selected and load its data
    const defaultEjercicioId = $('#ejercicioSelect').val();
    if (defaultEjercicioId) {
        console.log('Ejercicio preseleccionado detectado:', defaultEjercicioId);
        loadCampamentoEjercicioData();
    }
    
    // Update global variables after initialization
    updateGlobalVariables();
});

function initializePage() {
    console.log('Inicializando página...');
    
    // Initialize various components
    updateSaldoDisplay();
    initializeMoneyBreakdown();
    ensureAlertsContainer();
    
    // Initialize button states
    updateTipoFilterButton();
    updateIngresosGastosFilterButton();
    updateSortButtons();
    
    console.log('Página inicializada correctamente');
}

function setupEventListeners() {
    console.log('Configurando event listeners...');
    
    // =============================================================================
    // FILE UPLOAD HANDLERS
    // =============================================================================
    $('#archivo_justificante').on('change', function() {
        handleFileUpload(this);
    });
    
    $('#archivo_justificante_banco').on('change', function() {
        handleFileUpload(this);
    });

    // =============================================================================
    // SEARCH FUNCTIONALITY
    // =============================================================================
    $('#movementsSearch').on('input', function() {
        const searchTerm = $(this).val().toLowerCase().trim();
        
        if (searchTerm === '') {
            $('#clearSearch').hide();
        } else {
            $('#clearSearch').show();
        }
        
        applyFilters();
    });

    $('#clearSearch').on('click', function() {
        $('#movementsSearch').val('');
        $(this).hide();
        applyFilters();
    });
    
    // =============================================================================
    // FILTER CONTROLS
    // =============================================================================
    $('#filterTipo').on('click', function() {
        toggleTipoFilter();
    });
    
    $('#filterIngresosGastos').on('click', function() {
        toggleIngresosGastosFilter();
    });
    
    // =============================================================================
    // FORM VALIDATION
    // =============================================================================
    $('#importe').on('input', function() {
        validateMoneyBreakdown();
    });
    
    // =============================================================================
    // MODAL AND FORM HANDLING
    // =============================================================================
    $('#concepto').on('change', function() {
        const selectedOption = $(this).find('option:selected');
        const esGasto = selectedOption.data('es-gasto') === "True";
        
        console.log('Concepto seleccionado:', selectedOption.text(), 'Es gasto:', esGasto);
        
        // Get current operation type to determine which justificante fields to show
        const canalMovimiento = $('#canal_movimiento').val();
        
        if (selectedOption.val()) {
            // Hay concepto seleccionado
            if (esGasto) {
                $(this).removeClass('border-success').addClass('border-warning');
            } else {
                $(this).removeClass('border-warning').addClass('border-success');
            }
            
            // Mostrar campos según tipo de operación
            if (canalMovimiento === 'caja') {
                // Para efectivo: solo gastos necesitan justificante
                if (esGasto) {
                    $('#justificanteFields').removeClass('d-none').addClass('show').show();
                } else {
                    $('#justificanteFields').removeClass('show').hide();
                }
                $('#justificanteFieldsBanco').hide();
            } else if (canalMovimiento === 'banco') {
                // Para bancos: SIEMPRE mostrar justificante (ingreso o gasto)
                $('#justificanteFieldsBanco').removeClass('d-none').addClass('show').show();
                $('#justificanteFields').hide();
                
                // Actualizar las etiquetas según si es gasto o ingreso
                updateBankJustificanteLabels(esGasto);
            }
            
            console.log('Campos de justificante actualizados para:', esGasto ? 'gasto' : 'ingreso');
        } else {
            // No hay selección - ocultar campos y resetear estilos
            $(this).removeClass('border-success border-warning');
            $('#justificanteFields, #justificanteFieldsBanco').removeClass('show').hide();
            $('#justificante, #referencia_bancaria').val('');
            $('#archivo_justificante, #archivo_justificante_banco').val('');
            $('.file-display').remove();
            console.log('Sin selección - ocultando campos');
        }
    });

    // Handle canal movimiento changes
    $('#canal_movimiento').on('change', function() {
        const canalMovimiento = $(this).val();
        console.log('Canal de movimiento seleccionado:', canalMovimiento);
        
        if (canalMovimiento === 'caja') {
            $('#cajaSelect').prop('required', true);
            $('#cuenta_bancaria').prop('required', false);
            $('#via_movimiento_bancario').prop('required', false);

            // Mostrar selector de caja y campos de efectivo
            $('#cajaSelectionRow').show();
            $('#camposEfectivo').show();
            $('#camposBanco').hide();
            
            // Ocultar desglose hasta que se seleccione una caja
            $('#desgloseDineroSection').hide();
            
            // Cargar cajas del campamento seleccionado
            loadCajasForCampamento();
            
            // Si hay un concepto seleccionado, aplicar lógica de justificante para efectivo
            const concepto = $('#concepto').find('option:selected');
            const esGasto = concepto.data('es-gasto') === "True";
            if (concepto.val()) {
                // Para efectivo: solo gastos necesitan justificante
                if (esGasto) {
                    $('#justificanteFields').show();
                } else {
                    $('#justificanteFields').hide();
                }
                $('#justificanteFieldsBanco').hide();
            }
            
        } else if (canalMovimiento === 'banco') {
            $('#cajaSelect').prop('required', false);
            $('#cuenta_bancaria').prop('required', true);
            $('#via_movimiento_bancario').prop('required', true);

            // Ocultar selector de caja para operaciones bancarias
            $('#cajaSelectionRow').hide();
            $('#cajaSelect').val(''); // Limpiar selección de caja
            
            // Ocultar desglose para operaciones bancarias
            $('#desgloseDineroSection').hide();
            
            // Mostrar campos de banco y ocultar campos de efectivo
            $('#camposBanco').show();
            $('#camposEfectivo').hide();
            
            // Si hay un concepto seleccionado, SIEMPRE mostrar justificante bancario
            const concepto = $('#concepto').find('option:selected');
            const esGasto = concepto.data('es-gasto') === "True";
            if (concepto.val()) {
                $('#justificanteFieldsBanco').show();
                $('#justificanteFields').hide();
                
                // Actualizar las etiquetas según si es gasto o ingreso
                updateBankJustificanteLabels(esGasto);
            }
            loadCuentasAndVias();
            
        } else {
            // Sin selección - ocultar todos los campos específicos
            $('#camposEfectivo').hide();
            $('#camposBanco').hide();
            $('#desgloseDineroSection').hide();
            
            // Hacer NO obligatorio el selector de caja cuando no hay selección
            $('#cajaSelect').prop('required', false);
        }
        
        // Limpiar los campos del tipo no seleccionado
        if (canalMovimiento === 'caja') {
            $('#referencia_bancaria').val('');
            $('#archivo_justificante_banco').val('');
        } else if (canalMovimiento === 'banco') {
            $('#justificante').val('');
            $('#archivo_justificante').val('');
            // Limpiar también campos de desglose de dinero
            $('.money-input').val('');
            calculateMoneyTotals();
        }
    });

    // Handle caja selection changes for money breakdown
    $(document).on('change', '#cajaSelect', function() {
        const cajaId = $(this).val();
        const ejercicio_id = $('#ejercicioSelect').val();
        const canalMovimiento = $('#canal_movimiento').val();
        
        console.log('Caja seleccionada:', cajaId, 'Canal movimiento:', canalMovimiento);
        
        if (cajaId && canalMovimiento === 'caja') {
            // Load money breakdown data for the selected caja and show the desglose section
            loadCajaMoneyBreakdown(cajaId, ejercicio_id);
        } else if (canalMovimiento === 'caja') {
            // Hide breakdown if no caja selected
            $('#desgloseDineroSection').hide();
            // Reset available quantities display
            $('.available-quantity .quantity-text').text('Disponible: --');
            $('.available-quantity').removeClass('has-available no-available');
        }
    });

    // =============================================================================
    // FORM SUBMISSION
    // =============================================================================
    $('#addMovementForm').on('submit', function(e) {
        e.preventDefault();
        
        console.log('Enviando formulario de movimiento');

        const campamento_id = $('#campamentoSelect').val();
        if (!campamento_id) {
            showWarning('Por favor selecciona un campamento', {floating: true});
            return;
        }
        console.log('Campamento ID:', campamento_id);

        // Verificar que hay un ejercicio seleccionado
        const ejercicioId = $('#ejercicioSelect').val();
        if (!ejercicioId) {
            showWarning('Por favor selecciona un ejercicio', {floating: true});
            return;
        } 
        console.log('Ejercicio ID seleccionado:', ejercicioId);
        
        // Verificar que se ha seleccionado un canal de movimiento
        const canalMovimiento = $('#canal_movimiento').val();
        if (!canalMovimiento) {
            showWarning('Por favor selecciona el canal de movimiento', {floating: true});
            return;
        }
        console.log('Canal de movimiento seleccionado:', canalMovimiento);

        // Verificar que se ha seleccionado un turno
        const turnoId = $('#turno').val();
        if (!turnoId) {
            showWarning('Por favor selecciona un turno', {floating: true});
            return;
        }
        console.log('Turno ID seleccionado:', turnoId);

        // Verificar que se ha seleccionado un concepto
        const conceptoId = $('#concepto').val();
        if (!conceptoId) {
            showWarning('Por favor selecciona un concepto', {floating: true});
            return;
        }
        console.log('Concepto ID seleccionado:', conceptoId);

        // Verificar que se ha introducido un importe
        const importe = $('#importe').val();
        if (!importe || isNaN(importe) || parseFloat(importe) <= 0) {
            showWarning('Por favor introduce un importe válido', {floating: true});
            return;
        }
        console.log('Importe introducido:', importe);
        
        // Validación específica según el canal de movimiento
        if (canalMovimiento === 'caja') {
            // Para movimientos de caja, verificar que hay una caja seleccionada
            const cajaId = $('#cajaSelect').val();
            if (!cajaId) {
                showWarning('Por favor selecciona una caja para movimientos de efectivo', {floating: true});
                return;
            }
            console.log('Caja seleccionada para efectivo:', cajaId);
            
            // Validar desglose para movimientos de caja (tanto nuevos como editados)
            const validationResult = validateCompleteMoneyBreakdown();
            if (!validationResult.valid) {
                showError(validationResult.error, {floating: true});
                return;
            }
            console.log('Desglose de caja validado correctamente');
            
            // Asegurar que el caja_id esté establecido en el formulario
            $('#cajaIdInput').val(cajaId);
            console.log('Caja ID:', cajaId);
            
        } else if (canalMovimiento === 'banco') {
            // Para bancos, verificar cuentas y vías
            const cuenta_bancariaId = $('#cuenta_bancaria').val();
            if (!cuenta_bancariaId) {
                showWarning('Por favor selecciona una cuenta bancaria para movimientos de banco', {floating: true});
                return;
            }
            console.log('Cuenta bancaria seleccionada para banco:', cuenta_bancariaId);

            const viaMovimientoBancarioId = $('#via_movimiento_bancario').val();
            if (!viaMovimientoBancarioId) {
                showWarning('Por favor selecciona una vía de movimiento bancario', {floating: true});
                return;
            }

            console.log('Datos bancarios validados correctamente');
        }
        
        // Create FormData object to handle file upload
        const formData = new FormData(this);
        
        // Determine action based on editing state
        if (editingMovimiento) {
            formData.append('action', 'edit');
            formData.append('movimiento_id', editingMovimiento.id);
            formData.append('tipo_movimiento', editingMovimiento.tipo);
        } else {
            formData.append('action', 'add');
        }
        
        formData.append('canal_movimiento', canalMovimiento);
        formData.append('campamento_id', campamento_id);

        console.log('Datos del formulario preparados para enviar');
        
        $.ajax({
            url: window.registroUrl || '/registro/',
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(data) {
                console.log('Respuesta guardar:', data);
                if (data.success) {
                    // Determine message before clearing editing state
                    const message = editingMovimiento ? 'Movimiento actualizado correctamente' : 'Movimiento añadido correctamente';
                    
                    $('#addMovementModal').modal('hide');
                    
                    // Clear editing state
                    editingMovimiento = null;
                    
                    resetModalForm();
                    
                    // Recargar los movimientos para obtener el saldo actualizado
                    const ejercicioId = $('#ejercicioSelect').val();
                    if (ejercicioId) {
                        loadEjercicioMovimientos(ejercicioId);
                    }
                    
                    showSuccess(message);
                } else {
                    showError('Error: ' + data.error);
                }
            },
            error: function(xhr, status, error) {
                console.error('Error al guardar:', error);
                console.error('Response:', xhr.responseText);
                showError('Error al guardar el movimiento: ' + error);
            }
        });
    });
    
    console.log('Event listeners configurados correctamente');
}

// Update global variables whenever they change
function syncGlobalVariables() {
    window.currentMovimientos = currentMovimientos;
    window.filteredMovimientos = filteredMovimientos;
    window.currentSortField = currentSortField;
    window.currentSortOrder = currentSortOrder;
    window.editingMovimiento = editingMovimiento;
    window.currentTipoFilter = currentTipoFilter;
    window.currentIngresosGastosFilter = currentIngresosGastosFilter;
}

// Override variables to keep global scope updated
Object.defineProperty(window, 'updateCurrentMovimientos', {
    value: function(value) {
        currentMovimientos = value;
        syncGlobalVariables();
    }
});

Object.defineProperty(window, 'updateFilteredMovimientos', {
    value: function(value) {
        filteredMovimientos = value;
        syncGlobalVariables();
    }
});

// Expose main initialization functions to global scope
window.initializePage = initializePage;
window.setupEventListeners = setupEventListeners;
window.updateGlobalVariables = updateGlobalVariables;
window.syncGlobalVariables = syncGlobalVariables;

// Override assignment functions to keep global scope updated
const originalCurrentMovimientos = currentMovimientos;
const originalFilteredMovimientos = filteredMovimientos;

// Create a proxy to automatically update window variables when local variables change
Object.defineProperty(window, 'setCurrentMovimientos', {
    value: function(value) {
        currentMovimientos = value;
        window.currentMovimientos = value;
    }
});

Object.defineProperty(window, 'setFilteredMovimientos', {
    value: function(value) {
        filteredMovimientos = value;
        window.filteredMovimientos = value;
    }
});

Object.defineProperty(window, 'setCurrentSortField', {
    value: function(value) {
        currentSortField = value;
        window.currentSortField = value;
    }
});

Object.defineProperty(window, 'setCurrentSortOrder', {
    value: function(value) {
        currentSortOrder = value;
        window.currentSortOrder = value;
    }
});

Object.defineProperty(window, 'setEditingMovimiento', {
    value: function(value) {
        editingMovimiento = value;
        window.editingMovimiento = value;
    }
});

Object.defineProperty(window, 'setCurrentTipoFilter', {
    value: function(value) {
        currentTipoFilter = value;
        window.currentTipoFilter = value;
    }
});

Object.defineProperty(window, 'setCurrentIngresosGastosFilter', {
    value: function(value) {
        currentIngresosGastosFilter = value;
        window.currentIngresosGastosFilter = value;
    }
});

// Expose functions to global scope for template usage
window.prepareModal = prepareModal;
window.editMovimiento = editMovimiento;
window.deleteMovimiento = deleteMovimiento;
window.sortMovimientos = sortMovimientos;
window.toggleTipoFilter = toggleTipoFilter;
window.toggleIngresosGastosFilter = toggleIngresosGastosFilter;
window.resetFilters = resetFilters;
window.closeEnhancedAlert = closeEnhancedAlert;
