// =============================================================================
// FUNCIONES DE FILTRADO Y BÚSQUEDA
// =============================================================================

/**
 * Alternar filtro de tipo de operación (caja/banco/todos)
 */
function toggleTipoFilter() {
    const states = ['todos', 'caja', 'banco'];
    const currentIndex = states.indexOf(currentTipoFilter);
    const nextIndex = (currentIndex + 1) % states.length;
    currentTipoFilter = states[nextIndex];
    
    updateTipoFilterButton();
    applyFilters();
}

/**
 * Alternar filtro de ingresos/gastos (todos/ingresos/gastos)
 */
function toggleIngresosGastosFilter() {
    const states = ['todos', 'ingresos', 'gastos'];
    const currentIndex = states.indexOf(currentIngresosGastosFilter);
    const nextIndex = (currentIndex + 1) % states.length;
    currentIngresosGastosFilter = states[nextIndex];
    
    updateIngresosGastosFilterButton();
    applyFilters();
}

/**
 * Actualizar el botón de filtro de tipo
 */
function updateTipoFilterButton() {
    const $button = $('#filterTipo');
    const $text = $('#filterTipoText');
    const $icon = $button.find('i');
    
    // Resetear clases
    $button.removeClass('btn-outline-info btn-info btn-outline-secondary btn-secondary');
    
    switch (currentTipoFilter) {
        case 'caja':
            $button.addClass('btn-secondary');
            $icon.removeClass().addClass('tim-icons icon-coins');
            $text.text('Caja');
            break;
        case 'banco':
            $button.addClass('btn-info');
            $icon.removeClass().addClass('tim-icons icon-credit-card');
            $text.text('Banco');
            break;
        default:
            $button.addClass('btn-outline-info');
            $icon.removeClass().addClass('tim-icons icon-atom');
            $text.text('Todos');
            break;
    }
}

/**
 * Actualizar el botón de filtro de ingresos/gastos
 */
function updateIngresosGastosFilterButton() {
    const $button = $('#filterIngresosGastos');
    const $text = $('#filterIngresosGastosText');
    const $icon = $button.find('i');
    
    // Resetear clases
    $button.removeClass('btn-outline-success btn-success btn-outline-danger btn-danger');
    
    switch (currentIngresosGastosFilter) {
        case 'ingresos':
            $button.addClass('btn-success');
            $icon.removeClass().addClass('tim-icons icon-simple-add');
            $text.text('Ingresos');
            break;
        case 'gastos':
            $button.addClass('btn-danger');
            $icon.removeClass().addClass('tim-icons icon-simple-remove');
            $text.text('Gastos');
            break;
        default:
            $button.addClass('btn-outline-success');
            $icon.removeClass().addClass('tim-icons icon-chart-pie-36');
            $text.text('Todos');
            break;
    }
}

/**
 * Aplicar todos los filtros activos
 */
function applyFilters() {
    if (!currentMovimientos || currentMovimientos.length === 0) {
        return;
    }

    let filtered = [...currentMovimientos];

    // Aplicar filtro de búsqueda si existe
    const searchTerm = $('#movementsSearch').val().toLowerCase().trim();
    if (searchTerm !== '') {
        filtered = filtered.filter(mov => {
            return mov.concepto.toLowerCase().includes(searchTerm) ||
                   mov.importe.toString().includes(searchTerm) ||
                   (mov.justificante && mov.justificante.toLowerCase().includes(searchTerm)) ||
                   (mov.descripcion && mov.descripcion.toLowerCase().includes(searchTerm)) ||
                   mov.turno.toLowerCase().includes(searchTerm);
        });
    }

    // Aplicar filtro de tipo
    if (currentTipoFilter !== 'todos') {
        filtered = filtered.filter(mov => {
            const canalMovimiento = mov.canal_movimiento;
            if (currentTipoFilter === 'caja') {
                return canalMovimiento === 'caja';
            } else if (currentTipoFilter === 'banco') {
                return canalMovimiento === 'banco';
            }
            return true;
        });
    }

    // Aplicar filtro de ingresos/gastos
    if (currentIngresosGastosFilter !== 'todos') {
        filtered = filtered.filter(mov => {
            if (currentIngresosGastosFilter === 'ingresos') {
                return !mov.es_gasto;
            } else if (currentIngresosGastosFilter === 'gastos') {
                return mov.es_gasto;
            }
            return true;
        });
    }

    filteredMovimientos = filtered;
    displayMovimientos(filteredMovimientos);
    updateSearchResults(filteredMovimientos.length, searchTerm !== '' || currentTipoFilter !== 'todos' || currentIngresosGastosFilter !== 'todos');
}

/**
 * Resetear todos los filtros
 */
function resetFilters() {
    currentTipoFilter = 'todos';
    currentIngresosGastosFilter = 'todos';
    updateTipoFilterButton();
    updateIngresosGastosFilterButton();
    $('#movementsSearch').val('');
    $('#clearSearch').hide();
    applyFilters();
}

function sortMovimientos(field) {
    console.log('Ordenando por:', field);
    
    // Si es el mismo campo, cambiar orden, sino usar descendente por defecto
    if (currentSortField === field) {
        currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortField = field;
        currentSortOrder = 'desc';
    }
    
    // Ordenar los movimientos
    filteredMovimientos.sort(function(a, b) {
        let valueA, valueB;
        
        if (field === 'fecha') {
            valueA = new Date(a.datetime_iso);
            valueB = new Date(b.datetime_iso);
        } else if (field === 'importe') {
            valueA = parseFloat(a.importe);
            valueB = parseFloat(b.importe);
        }
        
        if (currentSortOrder === 'asc') {
            return valueA > valueB ? 1 : -1;
        } else {
            return valueA < valueB ? 1 : -1;
        }
    });
    
    // Mostrar los movimientos ordenados
    displayMovimientos(filteredMovimientos);
    
    // Actualizar los botones
    updateSortButtons();
}

function updateSortButtons() {
    // Resetear todos los botones
    $('#sortByDate, #sortByAmount').removeClass('btn-primary').addClass('btn-outline-secondary');
    $('#sortDateIcon, #sortAmountIcon').html('');
    
    // Activar el botón actual
    let activeButton, activeIcon;
    switch (currentSortField) {
        case 'fecha':
            activeButton = '#sortByDate';
            activeIcon = '#sortDateIcon';
            break;
        case 'importe':
            activeButton = '#sortByAmount';
            activeIcon = '#sortAmountIcon';
            break;
    }
    
    if (activeButton) {
        $(activeButton).removeClass('btn-outline-secondary').addClass('btn-primary');
        const icon = currentSortOrder === 'asc' ? '↑' : '↓';
        $(activeIcon).html(icon);
    }
}

function updateSearchResults(count, isSearching) {
    $('#resultsCount').text(count);
    
    if (isSearching) {
        $('#resultsText').text(count === 1 ? 'resultado encontrado' : 'resultados encontrados');
        $('#searchResultsInfo').removeClass('text-muted').addClass(count > 0 ? 'text-success' : 'text-warning');
        $('#searchResultsInfo i').removeClass('tim-icons icon-check-2').addClass(
            count > 0 ? 'tim-icons icon-check-2' : 'tim-icons icon-alert-circle-exc'
        );
    } else {
        $('#resultsText').text('movimientos en total');
        $('#searchResultsInfo').removeClass('text-success text-warning').addClass('text-muted');
        $('#searchResultsInfo i').removeClass().addClass('tim-icons icon-check-2');
    }
}

// Expose functions to global scope
window.toggleTipoFilter = toggleTipoFilter;
window.toggleIngresosGastosFilter = toggleIngresosGastosFilter;
window.updateTipoFilterButton = updateTipoFilterButton;
window.updateIngresosGastosFilterButton = updateIngresosGastosFilterButton;
window.applyFilters = applyFilters;
window.resetFilters = resetFilters;
window.sortMovimientos = sortMovimientos;
window.updateSortButtons = updateSortButtons;
window.updateSearchResults = updateSearchResults;
