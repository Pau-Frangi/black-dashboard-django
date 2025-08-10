// =============================================================================
// GESTIÓN DE FORMULARIOS Y VALIDACIONES
// =============================================================================

function prepareModal() {
    console.log('Preparando modal');
    
    // Verificar que hay un ejercicio seleccionado
    const ejercicioId = $('#ejercicioSelect').val();
    if (!ejercicioId) {
        showWarning('Por favor selecciona un ejercicio antes de añadir un movimiento');
        return false;
    }
    
    // Clear editing mode for new movements
    editingMovimiento = null;
    
    // Update modal title for new movement
    $('#addMovementModalLabel').html(`
        <i class="tim-icons icon-simple-add"></i>
        Añadir Nuevo Movimiento
    `);
    
    // Establecer el ejercicio_id en el formulario
    $('#ejercicioIdInput').val(ejercicioId);
    console.log('Ejercicio ID establecido en modal:', ejercicioId);
    
    // Load turnos for the selected ejercicio
    loadTurnosForEjercicio(ejercicioId);
    
    // Resetear el formulario y estilos
    resetModalForm();
    
    return true;
}

function resetModalForm() {
    console.log('Reseteando formulario del modal');
    
    // Reset form fields
    $('#addMovementForm')[0].reset();
    
    // Reset date and time to current values (only for new movements)
    if (!editingMovimiento) {
        $('#fecha').val(new Date().toISOString().split('T')[0]);
        $('#hora').val(new Date().toTimeString().slice(0, 5));
    }
    
    // Re-enable fields that might have been disabled during editing
    $('#canal_movimiento').prop('disabled', false).removeClass('disabled-field');
    $('#concepto').prop('disabled', false).removeClass('disabled-field');
    
    // Reset concept field styles
    $('#concepto').removeClass('border-success border-warning');
    
    // Hide all conditional fields and sections
    $('#justificanteFields').hide();
    $('#justificanteFieldsBanco').hide();
    $('#camposEfectivo').hide();
    $('#camposBanco').hide();
    $('#cajaSelectionRow').hide();
    $('#desgloseDineroSection').hide();
    
    // Reset required attributes
    $('#cajaSelect').prop('required', false);
    
    // Clear all form values
    $('#justificante').val('');
    $('#archivo_justificante').val('');
    $('#referencia_bancaria').val('');
    $('#archivo_justificante_banco').val('');
    
    // Remove file display if exists
    $('.file-display').remove();
    
    // Limpiar el desglose de dinero y validaciones
    clearMoneyBreakdown();
    
    // Reset validación de desglose
    $('#totalNeto').parent().removeClass('border border-warning border-success');
    
    // Limpiar mensajes temporales
    $('.temp-message').remove();
    $('.calculation-message').remove();
    
    // Resetear estilos de validación en inputs
    $('.money-input').removeClass('exceeds-available');
    
    console.log('Formulario reseteado completamente');
}

function editMovimiento(movimientoId, canalMovimiento) {
    console.log('Editando movimiento:', movimientoId, 'tipo:', canalMovimiento);
    
    // Verificar que hay un ejercicio seleccionado
    const ejercicioId = $('#ejercicioSelect').val();
    if (!ejercicioId) {
        showWarning('Por favor selecciona un ejercicio antes de editar un movimiento');
        return;
    }
    
    // Find the movement in our current data
    const movimiento = currentMovimientos.find(mov => mov.id === movimientoId && mov.tipo === canalMovimiento);
    
    if (!movimiento) {
        showError('No se pudo encontrar el movimiento a editar');
        return;
    }
    
    // Set editing mode
    editingMovimiento = {
        id: movimientoId,
        tipo: canalMovimiento,
        data: movimiento
    };
    
    // Prepare modal for editing
    prepareModalForEdit(movimiento);
    
    // Show the modal
    $('#addMovementModal').modal('show');
}

function prepareModalForEdit(movimiento) {
    console.log('Preparando modal para edición:', movimiento);
    
    // Update modal title
    $('#addMovementModalLabel').html(`
        <i class="tim-icons icon-pencil"></i>
        Editar Movimiento
    `);
    
    // Reset form first
    resetModalForm();
    
    // Set ejercicio ID
    const currentEjercicioId = $('#ejercicioSelect').val();
    $('#ejercicioIdInput').val(currentEjercicioId);
    
    // Set caja ID only if it's available (for cash movements)
    if (movimiento.caja_id) {
        $('#cajaIdInput').val(movimiento.caja_id);
    }
    
    // Parse fecha from movimiento
    const fecha = new Date(movimiento.datetime_iso);
    const fechaStr = fecha.toISOString().split('T')[0];
    const horaStr = fecha.toTimeString().slice(0, 5);
    
    // Populate basic fields    
    $('#fecha').val(fechaStr);
    $('#hora').val(horaStr);
    $('#importe').val(movimiento.importe);
    $('#descripcion').val(movimiento.descripcion);
    
    // Set operation type based on movement type
    const canalMovimiento = movimiento.tipo === 'banco' ? 'banco' : 'caja';
    $('#canal_movimiento').val(canalMovimiento);
    
    // Disable operation type field (not allowed to change)
    $('#canal_movimiento').prop('disabled', true);
    $('#canal_movimiento').addClass('disabled-field');
    
    // Load turnos and set the correct one
    const editEjercicioId = $('#ejercicioSelect').val();
    if (editEjercicioId) {
        loadTurnosForEjercicio(editEjercicioId, function() {
            if (movimiento.turno_id) {
                $('#turno').val(movimiento.turno_id);
                console.log('Turno preseleccionado por ID:', movimiento.turno_id, '(' + movimiento.turno + ')');
            }
        });
    }
    
    // Find and select the correct concepto by ID
    if (movimiento.concepto_id) {
        $('#concepto').val(movimiento.concepto_id);
        console.log('Concepto preseleccionado por ID:', movimiento.concepto_id, '(' + movimiento.concepto + ')');
        
        // Disable concept field (not allowed to change)
        $('#concepto').prop('disabled', true);
        $('#concepto').addClass('disabled-field');
        
        // Trigger change event to show/hide justificante fields
        $('#concepto').trigger('change');
    }
    
    // Handle specific fields based on movement type
    if (movimiento.canal_movimiento === 'banco') {
        // Show bank fields
        $('#camposBanco').show();
        $('#camposEfectivo').hide();
        
        // Set bank-specific fields
        $('#referencia_bancaria').val(movimiento.referencia_bancaria || '');
        
    } else {
        // Show cash fields
        $('#camposEfectivo').show();
        $('#camposBanco').hide();
        
        // Set cash-specific fields
        $('#justificante').val(movimiento.justificante || '');
        
        // Load money breakdown for cash movements
        loadMovimientoDesglose(movimiento.id);
    }
    
    // Trigger operation type change to show appropriate fields
    $('#canal_movimiento').trigger('change');
}

function deleteMovimiento(movimientoId, canalMovimiento = 'caja') {
    if (!confirm('¿Estás seguro de que quieres eliminar este movimiento?')) {
        return;
    }

    console.log('Eliminando movimiento ID:', movimientoId, 'Tipo:', canalMovimiento);

    $.ajax({
        url: window.registroUrl || '/registro/',
        method: 'POST',
        data: {
            'action': 'delete',
            'movimiento_id': movimientoId,
            'tipo_movimiento': canalMovimiento,
            'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(data) {
            console.log('Respuesta eliminar:', data);
            if (data.success) {
                // Reload movements for the current ejercicio
                const ejercicioId = $('#ejercicioSelect').val();
                if (ejercicioId) {
                    loadEjercicioMovimientos(ejercicioId);
                }
                showSuccess('Movimiento eliminado correctamente', {floating: true});
            } else {
                showError('Error: ' + data.error, {floating: true});
            }
        },
        error: function(xhr, status, error) {
            console.error('Error al eliminar:', error);
            showError('Error al eliminar el movimiento: ' + error, {floating: true});
        }
    });
}

// File upload handler
function handleFileUpload(input) {
    const file = input.files[0];
    const $fileGroup = $(input).closest('.form-group');
    
    // Remove any existing file display
    $fileGroup.find('.file-display').remove();
    
    if (file) {
        // Validate file size (10MB max)
        const maxSize = 10 * 1024 * 1024; // 10MB in bytes
        if (file.size > maxSize) {
            showError('El archivo es demasiado grande. El tamaño máximo permitido es 10MB.', {floating: true});
            $(input).val('');
            return;
        }
        
        // Validate file type
        const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png', 'image/bmp'];
        if (!allowedTypes.includes(file.type)) {
            showError('Tipo de archivo no permitido. Solo se permiten archivos PDF, JPG, PNG y BMP.', {floating: true});
            $(input).val('');
            return;
        }
        
        // Create file display element
        const fileDisplay = $(`
            <div class="file-display mt-3">
                <div class="d-flex align-items-center justify-content-between p-3" style="
                    background: linear-gradient(135deg, rgba(81, 203, 206, 0.1) 0%, rgba(81, 203, 206, 0.05) 100%);
                    border: 2px solid rgba(81, 203, 206, 0.3);
                    border-radius: 12px;
                    transition: all 0.3s ease;
                ">
                    <div class="d-flex align-items-center">
                        <i class="tim-icons icon-attach-87 mr-3" style="
                            color: #51cbce;
                            font-size: 1.2rem;
                        "></i>
                        <div>
                            <div class="file-name" style="
                                color: #fff;
                                font-weight: 600;
                                font-size: 0.9rem;
                                margin-bottom: 2px;
                            ">${file.name}</div>
                            <div class="file-size" style="
                                color: rgba(156, 163, 175, 0.8);
                                font-size: 0.8rem;
                            ">${formatFileSize(file.size)}</div>
                        </div>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-danger remove-file" style="
                        border-radius: 8px;
                        padding: 6px 12px;
                        font-size: 0.8rem;
                        transition: all 0.3s ease;
                    ">
                        <i class="tim-icons icon-simple-remove"></i>
                        Cambiar
                    </button>
                </div>
            </div>
        `);
        
        // Add remove functionality
        fileDisplay.find('.remove-file').on('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            $(input).val('');
            fileDisplay.fadeOut(300, function() {
                $(this).remove();
            });
        });
        
        // Insert after the input
        $fileGroup.find('small.form-text').after(fileDisplay);
        
        // Add entrance animation
        fileDisplay.hide().fadeIn(300);
    }
}

// Function to format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Function to update bank justificante labels based on expense/income
function updateBankJustificanteLabels(esGasto) {
    const labelText = esGasto ? 'Justificante de Factura' : 'Justificante de Pago';
    const helpText = esGasto ? 'Número de justificante de la factura/gasto' : 'Número de justificante del pago/ingreso';
    
    // Update label text
    $('label[for="archivo_justificante_banco"]').text(`Archivo ${labelText}`);
    
    // Update help text
    $('#archivo_justificante_banco').next('small').find('i').next().text(helpText);
    
    console.log('Etiquetas de justificante bancario actualizadas para:', esGasto ? 'gasto' : 'ingreso');
}

// Expose functions to global scope
window.prepareModal = prepareModal;
window.resetModalForm = resetModalForm;
window.editMovimiento = editMovimiento;
window.prepareModalForEdit = prepareModalForEdit;
window.deleteMovimiento = deleteMovimiento;
window.handleFileUpload = handleFileUpload;
window.formatFileSize = formatFileSize;
window.updateBankJustificanteLabels = updateBankJustificanteLabels;
