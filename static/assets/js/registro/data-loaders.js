// =============================================================================
// FUNCIONES DE CARGA DE DATOS
// =============================================================================

function loadCampamentoEjercicioData() {
    const ejercicioId = $('#ejercicioSelect').val();
    const campamentoId = $('#campamentoSelect').val();

    console.log('Cargando datos del campamento ID:', campamentoId);
    console.log('Cargando datos para ejercicio ID:', ejercicioId);
    
    if (!ejercicioId || !campamentoId) {
        // No ejercicio selected
        console.log('No hay ejercicio seleccionado, ocultando elementos');
        $('#movimientosContainer').hide();
        $('#sortControls').hide();
        $('#searchSection').hide();
        $('#filterControls').hide();
        $('#addMovementSection').hide();
        $('#noEjercicioMessage').show();
        
        // Limpiar los campos del header
        updateTotalsDisplay(0, 0, 0);
        currentMovimientos = [];
        filteredMovimientos = [];
        return;
    }

    // Update saldo display
    updateSaldoDisplay();
    
    // Set ejercicio ID in the form
    $('#ejercicioIdInput').val(ejercicioId);
    
    // Load turnos for the selected ejercicio
    loadTurnosForEjercicio(ejercicioId);
    
    // Hide no ejercicio message and show add movement section
    $('#noEjercicioMessage').hide();
    $('#addMovementSection').show();

    // Cargar todos los movimientos del ejercicio
    loadEjercicioMovimientos(ejercicioId);
}

function loadEjercicioMovimientos(ejercicioId) {
    console.log('Cargando movimientos para ejercicio ID:', ejercicioId);

    const campamento_id = $('#campamentoSelect').val();
    if (!ejercicioId) {
        console.log('No hay ejercicio seleccionado, no se pueden cargar movimientos');
        currentMovimientos = [];
        filteredMovimientos = [];
        updateTotalsDisplay(0, 0, 0);
        $('#movimientosContainer').hide();
        return;
    }
    
    $.ajax({
        url: window.registroUrl || '/registro/',
        method: 'GET',
        data: {
            'ajax': 'true',
            'get_ejercicio_movimientos': 'true',
            'campamento_id': campamento_id,
            'ejercicio_id': ejercicioId
        },
        success: function(data) {
            if (data.success) {
                console.log('Movimientos del ejercicio cargados:', data.movimientos.length);

                // Mostrar los datos por console
                console.log('Resumen del ejercicio:', data.resumen);
                console.log('Datos del ejercicio:', data.ejercicio);
                console.log('Movimientos:', data.movimientos);
                
                // Update global variables
                currentMovimientos = data.movimientos;
                filteredMovimientos = [...currentMovimientos];
                
                // Update totals display
                updateTotalsDisplay(data.resumen.total_ingresos, data.resumen.total_gastos, data.resumen.saldo_actual);
                
                // Show movements and controls
                $('#movimientosContainer').show();
                $('#sortControls').show();
                $('#searchSection').show();
                $('#filterControls').show();
                
                // Render movements
                displayMovimientos(filteredMovimientos);
                
                showInfo(`Mostrando ${data.movimientos.length} movimientos del ejercicio ${data.ejercicio.nombre}`);
            } else {
                showError('Error al cargar los movimientos: ' + data.error);
                currentMovimientos = [];
                filteredMovimientos = [];
                updateTotalsDisplay(0, 0, 0);
                $('#movimientosContainer').hide();
            }
        },
        error: function(xhr, status, error) {
            console.error('Error loading ejercicio movimientos:', error);
            showError('Error al cargar los movimientos del ejercicio');
            currentMovimientos = [];
            filteredMovimientos = [];
            updateTotalsDisplay(0, 0, 0);
            $('#movimientosContainer').hide();
        }
    });
}

function loadCajasForCampamento() {
    const campamento_id = $('#campamentoSelect').val();
    
    if (!campamento_id) {
        console.log('No hay campamento seleccionado');
        return;
    }

    console.log('Cargando cajas para campamento ID:', campamento_id);

    $.ajax({
        url: window.registroUrl || '/registro/',
        method: 'GET',
        data: {
            'ajax': 'true',
            'get_cajas': 'true',
            'campamento_id': campamento_id,
        },
        success: function(data) {
            console.log('Respuesta cajas:', data);
            if (data.success) {
                // Initialize cajaSelect first
                const cajaSelect = $('#cajaSelect');
                cajaSelect.empty();
                cajaSelect.append('<option value="">-- Selecciona una caja --</option>');

                // Now populate cajas
                data.cajas.forEach(function(caja) {
                    const disabled = !caja.activa ? 'disabled style="background-color: #eee; color: #888;"' : '';
                    const label = caja.nombre + ' - ' + caja.saldo_caja + '€' + (!caja.activa ? ' [INACTIVA]' : '');
                    cajaSelect.append(`<option value="${caja.id}" data-saldo="${caja.saldo_caja}" ${disabled}>${label}</option>`);
                    console.log(`Caja cargada: ${caja.nombre} - ${caja.activa ? 'ACTIVA' : 'INACTIVA'} - Saldo: ${caja.saldo_caja}€`);
                });

                console.log('Cajas cargadas:', data.cajas.length);
                showSuccess(`${data.cajas.length} cajas cargadas correctamente`);
            } else {
                console.error('Error al cargar cajas:', data.error);
                showError('Error al cargar las cajas: ' + data.error);
            }
        },
        error: function(xhr, status, error) {
            console.error('Error AJAX loading cajas:', error);
            console.error('Response text:', xhr.responseText);
            showError('Error al cargar las cajas: ' + error);
        }
    });
}

function loadTurnosForEjercicio(ejercicioId, callback) {
    const campamentoId = $('#campamentoSelect').val();
    console.log('Cargando turnos para ejercicio ID:', ejercicioId, 'y campamento ID:', campamentoId);

    $.ajax({
        url: window.registroUrl || '/registro/',
        method: 'GET',
        data: {
            'ajax': 'true',
            'get_turnos': 'true',
            'campamento_id': campamentoId,
            'ejercicio_id': ejercicioId
        },
        success: function(data) {
            if (data.success) {
                // Clear and populate turnos
                const turnoSelect = $('#turno');
                turnoSelect.empty();
                turnoSelect.append('<option value="">-- Selecciona un turno --</option>');
                
                data.turnos.forEach(function(turno) {
                    turnoSelect.append(`<option value="${turno.id}">${turno.nombre}</option>`);
                });
                
                console.log('Turnos cargados:', data.turnos.length);
                
                if (callback) callback();
            } else {
                showError('Error al cargar los turnos: ' + data.error);
            }
        },
        error: function(xhr, status, error) {
            console.error('Error loading turnos:', error);
            showError('Error al cargar los turnos');
        }
    });
}

function loadCajaMoneyBreakdown(cajaId, ejercicioId) {
    console.log('Cargando desglose de caja para ID:', cajaId, 'Ejercicio:', ejercicioId);
    
    $.ajax({
        url: window.registroUrl || '/registro/',
        method: 'GET',
        data: {
            'ajax': 'true',
            'caja_id': cajaId,
            'ejercicio_id': ejercicioId,
        },
        success: function(data) {
            console.log('Respuesta desglose caja:', data);
            if (data.success && data.desglose_actual) {
                console.log('Desglose de caja cargado:', data.desglose_actual);
                
                // Show the money breakdown section
                $('#desgloseDineroSection').show();
                
                // Initialize money breakdown
                initializeMoneyBreakdown();
                
                // Update available quantities with actual values
                updateAvailableQuantities(data.desglose_actual);
                
                showSuccess(`Desglose de caja cargado correctamente`);
            } else {
                console.error('Error al cargar el desglose de caja:', data.error);
                showError('Error al cargar el desglose de la caja: ' + (data.error || 'Datos no disponibles'));
                // Hide breakdown section if error
                $('#desgloseDineroSection').hide();
            }
        },
        error: function(xhr, status, error) {
            console.error('Error AJAX loading caja money breakdown:', error);
            console.error('Response text:', xhr.responseText);
            showError('Error al cargar el desglose de la caja: ' + error);
            // Hide breakdown section if error
            $('#desgloseDineroSection').hide();
        }
    });
}

function loadMovimientoDesglose(movimientoId) {
    console.log('Cargando desglose para movimiento:', movimientoId);
    
    $.ajax({
        url: window.registroUrl || '/registro/',
        method: 'GET',
        data: {
            'ajax': 'true',
            'get_movimiento_desglose': 'true',
            'movimiento_id': movimientoId
        },
        success: function(data) {
            if (data.success) {
                console.log('Desglose cargado:', data.desglose);
                
                // Initialize money breakdown first
                initializeMoneyBreakdown();
                
                // Populate the money breakdown inputs with the loaded data
                Object.keys(data.desglose).forEach(function(denominacionId) {
                    const desglose = data.desglose[denominacionId];
                    
                    // Set entrada and salida values
                    if (desglose.cantidad_entrada > 0) {
                        $(`#entrada_${denominacionId}`).val(desglose.cantidad_entrada);
                    }
                    if (desglose.cantidad_salida > 0) {
                        $(`#salida_${denominacionId}`).val(desglose.cantidad_salida);
                    }
                    
                    console.log(`Denominación ${denominacionId}: entrada=${desglose.cantidad_entrada}, salida=${desglose.cantidad_salida}`);
                });
                
                // Recalculate totals after loading the data
                calculateMoneyTotals();
                
            } else {
                console.error('Error al cargar el desglose:', data.error);
                showError('Error al cargar el desglose del movimiento: ' + data.error);
                // Fall back to empty money breakdown
                initializeMoneyBreakdown();
            }
        },
        error: function(xhr, status, error) {
            console.error('Error loading movimiento desglose:', error);
            showError('Error al cargar el desglose del movimiento');
            // Fall back to empty money breakdown
            initializeMoneyBreakdown();
        }
    });
}

function loadCuentasAndVias() {
    $.ajax({
        url: window.registroUrl || '/registro/',
        method: 'GET',
        data: {
            'ajax': 'true',
            'get_cuentas_vias': 'true',
        },
        success: function(data) {
            if (data.success) {
                // Populate cuentas bancarias
                const cuentaSelect = $('#cuenta_bancaria');
                cuentaSelect.empty();
                cuentaSelect.append('<option value="">-- Selecciona una cuenta --</option>');
                data.cuentas.forEach(function(cuenta) {
                    cuentaSelect.append(`<option value="${cuenta.id}">${cuenta.nombre} - ${cuenta.IBAN}</option>`);
                });

                // Populate vías de movimiento bancario
                const viaSelect = $('#via_movimiento_bancario');
                viaSelect.empty();
                viaSelect.append('<option value="">-- Selecciona una vía --</option>');
                data.vias.forEach(function(via) {
                    viaSelect.append(`<option value="${via.id}">${via.nombre}</option>`);
                });
            } else {
                showError('Error al cargar cuentas/vías: ' + data.error);
            }
        },
        error: function(xhr, status, error) {
            showError('Error al cargar cuentas/vías');
        }
    });
}

// Expose functions to global scope
window.loadCampamentoEjercicioData = loadCampamentoEjercicioData;
window.loadEjercicioMovimientos = loadEjercicioMovimientos;
window.loadCajasForCampamento = loadCajasForCampamento;
window.loadTurnosForEjercicio = loadTurnosForEjercicio;
window.loadCajaMoneyBreakdown = loadCajaMoneyBreakdown;
window.loadMovimientoDesglose = loadMovimientoDesglose;
window.loadCuentasAndVias = loadCuentasAndVias;
