// =============================================================================
// FUNCIONES DE VISUALIZACIÓN Y HELPERS DE UI
// =============================================================================

function updateSaldoDisplay() {
    const selectedOption = $('#cajaSelect option:selected');
    const saldo = selectedOption.data('saldo');
    
    console.log('Actualizando saldo display:', saldo, 'tipo:', typeof saldo);
    
    if (saldo !== undefined && saldo !== null && saldo !== '') {
        // Solo mostrar un placeholder mientras se cargan los movimientos
        // Los totales reales se actualizarán cuando se muestren los movimientos
        updateTotalsDisplay(0, 0, 0);
    } else {
        updateTotalsDisplay(0, 0, 0);
    }
}

function displayMovimientos(movimientos) {
    console.log('=== displayMovimientos ===');
    console.log('Movimientos recibidos:', movimientos);
    
    const tbody = $('#movimientosTableBody');
    console.log('tbody encontrado:', tbody.length);
    
    if (tbody.length === 0) {
        console.error('ERROR: No se encontró el tbody con ID movimientosTableBody');
        return;
    }
    
    tbody.empty();

    if (!movimientos || movimientos.length === 0) {
        console.log('No hay movimientos, mostrando mensaje');
        tbody.append(`
            <tr>
                <td colspan="8" class="text-center text-muted">
                    No hay movimientos registrados para el campamento y ejercicio seleccionados.
                </td>
            </tr>
        `);
        updateTotalsDisplay(0, 0, 0);
        return;
    }

    console.log('Procesando', movimientos.length, 'movimientos...');
    
    movimientos.forEach(function(mov, index) {
        console.log(`Procesando movimiento ${index + 1}:`, mov);
        console.log('¿Tiene caja_nombre?', mov.caja);

        const fechaDisplay = mov.fecha_display || new Date(mov.datetime_iso).toLocaleString('es-ES');
        const importeClass = mov.tipo_operacion === 'gasto' ? 'text-danger' : 'text-success';
        const importeSign = mov.tipo_operacion === 'gasto' ? '-' : '+';
        
        // Determinar el tipo de movimiento y su badge
        const canalMovimiento = mov.canal_movimiento;
        let canalMovimientoBadge;
        
        if (canalMovimiento === 'banco') {
            canalMovimientoBadge = '<span class="badge badge-info"><i class="tim-icons icon-credit-card"></i> Banco</span>';
        } else if (canalMovimiento === 'caja') {
            // Para movimientos de caja, solo badge de caja
            canalMovimientoBadge = '<span class="badge badge-secondary"><i class="tim-icons icon-coins"></i> Caja</span>';
            // El nombre de la caja se añadirá después
            if (mov.caja && mov.caja) {
                canalMovimientoBadge += `<span class="d-block mt-1 text-muted" style="font-size: 0.8rem;">${mov.caja}</span>`;
            }
        }
        
        // Badge para ingreso/gasto
        const tipoOperacionBadge = mov.tipo_operacion === 'gasto' ? 
            '<span class="badge badge-danger"><i class="tim-icons icon-simple-remove"></i> Gasto</span>' : 
            '<span class="badge badge-success"><i class="tim-icons icon-simple-add"></i> Ingreso</span>';
        
        const row = `
            <tr data-tipo="${canalMovimiento}" data-es-gasto="${mov.tipo_operacion === 'gasto'}">
                <td>
                    <div class="d-flex flex-column">
                        <strong>${fechaDisplay}</strong>
                    </div>
                </td>
                <td>${mov.turno}</td>
                <td>${canalMovimientoBadge}</td>
                <td>
                    ${mov.concepto}
                    ${tipoOperacionBadge}
                </td>
                <td>${mov.descripcion || '-'}</td>
                <td class="${importeClass}">
                    <strong>${importeSign}${mov.importe}€</strong>
                </td>
                <td>${mov.justificante || '-'}</td>
                <td>
                    <div class="btn-group" role="group">
                        <button class="btn btn-sm btn-outline-primary" onclick="editMovimiento(${mov.id}, '${canalMovimiento}')" title="Editar movimiento">
                            <i class="tim-icons icon-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteMovimiento(${mov.id}, '${canalMovimiento}')" title="Eliminar movimiento">
                            <i class="tim-icons icon-simple-remove"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
        
        tbody.append(row);
    });
    
    console.log('Terminé de añadir filas. Total filas ahora:', tbody.find('tr').length);
    console.log('HTML del tbody:', tbody.html());
    
    // Actualizar los totales basándose en los movimientos mostrados
    updateTotalsFromVisibleMovements();
    
    console.log('=== fin displayMovimientos ===');
}

function updateResumen(resumen) {
    console.log('Actualizando resumen:', resumen);
    
    // Proteger contra valores undefined/null
    const totalIngresos = parseFloat(resumen.total_ingresos) || 0;
    const totalGastos = parseFloat(resumen.total_gastos) || 0;
    const saldoActual = parseFloat(resumen.saldo_actual) || 0;
    
    $('#totalIngresos').text(totalIngresos.toFixed(2) + '€');
    $('#totalGastos').text(totalGastos.toFixed(2) + '€');
    $('#saldoResumen').text(saldoActual.toFixed(2) + '€');
}

/**
 * Actualiza los totales basándose en los movimientos filtrados/visibles
 */
function updateTotalsFromVisibleMovements() {
    if (!filteredMovimientos || filteredMovimientos.length === 0) {
        // Si no hay movimientos filtrados, mostrar ceros
        updateTotalsDisplay(0, 0, 0);
        return;
    }

    let totalIngresos = 0;
    let totalGastos = 0;

    // Calcular totales basándose en los movimientos filtrados
    filteredMovimientos.forEach(mov => {
        const importe = parseFloat(mov.importe) || 0;
        if (mov.tipo_operacion === 'gasto') {
            totalGastos += importe;
        } else if (mov.tipo_operacion === 'ingreso') {
            totalIngresos += importe;
        }
    });

    // Obtener el saldo de la caja seleccionada (saldo base)
    const selectedOption = $('#cajaSelect option:selected');
    const saldoBase = parseFloat(selectedOption.data('saldo')) || 0;
    
    // El saldo mostrado debe ser: saldo_base + ingresos_filtrados - gastos_filtrados
    // Pero esto no sería correcto porque el saldo base ya incluye todos los movimientos
    // Por eso vamos a calcular el saldo como: ingresos_filtrados - gastos_filtrados
    const saldoFiltrado = totalIngresos - totalGastos;

    console.log('Totales calculados desde movimientos filtrados:', {
        ingresos: totalIngresos,
        gastos: totalGastos,
        saldo: saldoFiltrado,
        movimientos: filteredMovimientos.length
    });

    updateTotalsDisplay(totalIngresos, totalGastos, saldoFiltrado);
}

/**
 * Actualiza la visualización de los totales en el header
 */
function updateTotalsDisplay(ingresos, gastos, saldo) {
    $('#totalIngresosHeader').text(ingresos.toFixed(2) + '€');
    $('#totalGastosHeader').text(gastos.toFixed(2) + '€');
    $('#saldoActual').text(saldo.toFixed(2) + '€');

    // Actualizar colores del saldo según el valor
    const $saldoElement = $('#saldoActual');
    $saldoElement.removeClass('text-success text-danger text-warning');
    
    if (saldo > 0) {
        $saldoElement.addClass('text-success');
    } else if (saldo < 0) {
        $saldoElement.addClass('text-danger');
    } else {
        $saldoElement.addClass('text-warning');
    }

    // Indicar si los totales están filtrados
    const isFiltered = currentTipoFilter !== 'todos' || 
                      currentIngresosGastosFilter !== 'todos' || 
                      $('#movementsSearch').val().trim() !== '';
    
    const $totalsSection = $('.totals-section');
    if (isFiltered) {
        $totalsSection.attr('title', 'Totales calculados sobre movimientos filtrados');
        $totalsSection.addClass('filtered-totals');
    } else {
        $totalsSection.attr('title', 'Totales de todos los movimientos');
        $totalsSection.removeClass('filtered-totals');
    }
}

// Expose functions to global scope
window.updateSaldoDisplay = updateSaldoDisplay;
window.displayMovimientos = displayMovimientos;
window.updateResumen = updateResumen;
window.updateTotalsFromVisibleMovements = updateTotalsFromVisibleMovements;
window.updateTotalsDisplay = updateTotalsDisplay;
