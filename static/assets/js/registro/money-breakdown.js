// =============================================================================
// GESTIÓN DEL DESGLOSE DE BILLETES Y MONEDAS
// =============================================================================

function initializeMoneyBreakdown() {
    // Event listeners para los inputs de dinero
    $('.money-input').on('input', function() {
        calculateMoneyTotals();
        validateMoneyBreakdown();
    });
    
    // Event listeners específicos para validación de entradas y salidas
    $('.entrada-input').on('input blur', function() {
        validateEntradaInput(this);
    });
    
    $('.salida-input').on('input blur', function() {
        validateSalidaInput(this);
    });
    
    // Validación adicional en tiempo real para inputs de salida que exceden cantidad
    $('.salida-input').on('input', function() {
        const $input = $(this);
        const value = parseInt($input.val()) || 0;
        const available = parseInt($input.data('available')) || 0;
        
        // Validación visual inmediata sin corregir el valor aún
        if (value > available && available >= 0) {
            $input.addClass('exceeds-available');
            $input.closest('.money-item').addClass('has-error');
        } else {
            $input.removeClass('exceeds-available');
            $input.closest('.money-item').removeClass('has-error');
        }
    });
    
    // Prevenir pegado de valores negativos
    $('.money-input').on('paste', function(e) {
        setTimeout(() => {
            const value = parseInt($(this).val()) || 0;
            if (value < 0) {
                $(this).val(0);
                showTemporaryMessage($(this), 'No se permiten valores negativos', 'warning');
            }
            
            // Validar límites si es salida
            if ($(this).hasClass('salida-input')) {
                validateSalidaInput(this);
            }
            
            calculateMoneyTotals();
            validateMoneyBreakdown();
        }, 100);
    });
    
    // Botón para calcular desde total
    $('#calcularDesdeTotal').on('click', function() {
        calculateFromTotal();
    });
    
    // Botón para limpiar desglose
    $('#limpiarDesglose').on('click', function() {
        clearMoneyBreakdown();
    });
    
    // Calcular totales inicial
    calculateMoneyTotals();
}

function calculateMoneyTotals() {
    let totalEntrada = 0;
    let totalSalida = 0;
    
    $('.entrada-input').each(function() {
        const cantidad = parseInt($(this).val()) || 0;
        const valor = parseFloat($(this).data('valor'));
        totalEntrada += cantidad * valor;
    });
    
    $('.salida-input').each(function() {
        const cantidad = parseInt($(this).val()) || 0;
        const valor = parseFloat($(this).data('valor'));
        totalSalida += cantidad * valor;
    });
    
    const totalNeto = totalEntrada - totalSalida;
    
    $('#totalEntrada').text(totalEntrada.toFixed(2) + '€');
    $('#totalSalida').text(totalSalida.toFixed(2) + '€');
    $('#totalNeto').text(totalNeto.toFixed(2) + '€');
    
    // Actualizar el color del total neto
    const $totalNeto = $('#totalNeto');
    $totalNeto.removeClass('text-success text-danger text-info');
    if (totalNeto > 0) {
        $totalNeto.addClass('text-success');
    } else if (totalNeto < 0) {
        $totalNeto.addClass('text-danger');
    } else {
        $totalNeto.addClass('text-info');
    }
    
    return {
        entrada: totalEntrada,
        salida: totalSalida,
        neto: totalNeto
    };
}

function validateMoneyBreakdown() {
    const importeMovimiento = parseFloat($('#importe').val()) || 0;
    const totales = calculateMoneyTotals();
    
    // Verificar si el total neto coincide con la cantidad del movimiento
    const diferencia = Math.abs(totales.neto - importeMovimiento);
    const tolerance = 0.01; // Tolerancia de 1 céntimo
    
    const $totalNeto = $('#totalNeto').parent();
    $totalNeto.removeClass('border border-warning border-success');
    
    if (importeMovimiento > 0) {
        if (diferencia <= tolerance) {
            // Coincide exactamente - mostrar como correcto
            $totalNeto.addClass('border border-success');
        } else {
            // No coincide - mostrar como error
            $totalNeto.addClass('border border-warning');
        }
    }
    
    // Retornar si la validación es correcta (será usado en el submit del formulario)
    return diferencia <= tolerance;
}

function validateCompleteMoneyBreakdown() {
    const importeMovimiento = parseFloat($('#importe').val()) || 0;
    
    if (importeMovimiento <= 0) {
        return {
            valid: false,
            error: 'Por favor, ingresa una cantidad válida para el movimiento.'
        };
    }
    
    // Verificar que hay al menos una entrada en el desglose
    let tieneDesglose = false;
    $('.money-input').each(function() {
        if (parseInt($(this).val()) > 0) {
            tieneDesglose = true;
            return false; // break
        }
    });
    
    if (!tieneDesglose) {
        return {
            valid: false,
            error: 'ERROR: El desglose de billetes y monedas es obligatorio. Por favor, especifica la cantidad exacta de cada denominación que entra y sale de la caja.'
        };
    }
    
    // Verificar que los totales coincidan
    const totales = calculateMoneyTotals();
    let valorCalculado = totales.neto;
    const esGasto = $('#concepto option:selected').data('es-gasto') === "True";

    if (esGasto) {
        if (valorCalculado > 0) {
            return {
                valid: false,
                error: 'ERROR: El desglose no puede ser positivo para un gasto. Por favor, verifica las cantidades.'
            };
        }
        valorCalculado = -valorCalculado; // Invertir el valor para gastos
    } else {
        if (valorCalculado < 0) {
            return {
                valid: false,
                error: 'ERROR: El desglose no puede ser negativo para un ingreso. Por favor, verifica las cantidades.'
            };
        }
    }

    const diferencia = Math.abs(valorCalculado - importeMovimiento);
    const tolerance = 0.01; // Tolerancia de 1 céntimo
    
    if (diferencia > tolerance) {
        return {
            valid: false,
            error: `ERROR: El desglose (${totales.neto.toFixed(2)}€) no coincide con la cantidad del movimiento (${importeMovimiento.toFixed(2)}€). Diferencia: ${diferencia.toFixed(2)}€. El desglose debe ser exacto.`
        };
    }
    
    return {
        valid: true,
        error: null
    };
}

function clearMoneyBreakdown() {
    $('.money-input').val('');
    $('.money-input').removeClass('exceeds-available');
    $('.temp-message').remove();
    $('.calculation-message').remove();
    $('#totalNeto').parent().removeClass('border border-warning border-success');
    calculateMoneyTotals();
}

function calculateFromTotal() {
    const importeMovimiento = parseFloat($('#importe').val()) || 0;
    
    if (importeMovimiento <= 0) {
        showWarning('Por favor, primero ingresa la cantidad total del movimiento.');
        return;
    }
    
    // Verificar si hay un concepto seleccionado para determinar si es gasto o ingreso
    const conceptoSeleccionado = $('#concepto option:selected');
    if (!conceptoSeleccionado.val()) {
        showWarning('Por favor, primero selecciona un concepto para determinar si es gasto o ingreso.');
        return;
    }
    
    const esGasto = conceptoSeleccionado.data('es-gasto') === "True";
    const tipoInput = esGasto ? 'salida' : 'entrada';
    
    // Limpiar el desglose actual
    clearMoneyBreakdown();
    
    // Obtener denominaciones disponibles ordenadas de mayor a menor
    const denominaciones = [];
    $(`.money-input[data-tipo="${tipoInput}"]`).each(function() {
        const cantidadDisponible = esGasto ? 
            (parseInt($(this).data('available')) || 0) : 
            999999; // Para ingresos, no hay límite
        
        if (cantidadDisponible > 0) {
            denominaciones.push({
                id: $(this).data('denominacion'),
                valor: parseFloat($(this).data('valor')),
                elemento: $(this),
                disponible: cantidadDisponible
            });
        }
    });
    
    denominaciones.sort((a, b) => b.valor - a.valor);
    
    // Calcular el total disponible para gastos
    let totalDisponible = 0;
    if (esGasto) {
        denominaciones.forEach(denom => {
            totalDisponible += denom.valor * denom.disponible;
        });
    }
    
    let remainingAmount = importeMovimiento;
    let cantidadDistribuida = 0;
    const distribucion = [];
    
    // Calcular automáticamente la distribución respetando cantidades disponibles
    denominaciones.forEach(denom => {
        if (remainingAmount >= denom.valor && denom.disponible > 0) {
            const cantidadIdeal = Math.floor(remainingAmount / denom.valor);
            const cantidadUsada = Math.min(cantidadIdeal, denom.disponible);
            
            if (cantidadUsada > 0) {
                denom.elemento.val(cantidadUsada);
                const valorUsado = cantidadUsada * denom.valor;
                remainingAmount -= valorUsado;
                cantidadDistribuida += valorUsado;
                remainingAmount = Math.round(remainingAmount * 100) / 100; // Evitar errores de punto flotante
                
                distribucion.push({
                    valor: denom.valor,
                    cantidad: cantidadUsada,
                    total: valorUsado
                });
            }
        }
    });
    
    calculateMoneyTotals();
    validateMoneyBreakdown();
    
    // Verificar si se pudo alcanzar la cantidad exacta
    if (remainingAmount > 0.01) { // Tolerancia de 1 céntimo
        const porcentajeAlcanzado = ((cantidadDistribuida / importeMovimiento) * 100).toFixed(1);
        
        if (esGasto && totalDisponible < importeMovimiento) {
            // No hay suficiente dinero total en la caja
            let mensaje = `❌ No hay suficiente dinero en la caja para realizar este gasto.\n\n`;
            mensaje += `💰 Total disponible en caja: ${totalDisponible.toFixed(2)}€\n`;
            mensaje += `💸 Cantidad del gasto: ${importeMovimiento.toFixed(2)}€\n`;
            mensaje += `📉 Faltan: ${(importeMovimiento - totalDisponible).toFixed(2)}€`;
            
            showWarning(mensaje);
        } else {
            // Hay dinero suficiente pero no se puede hacer exacto
            let mensaje = `⚠️ No se puede alcanzar la cantidad exacta de ${importeMovimiento.toFixed(2)}€ con las denominaciones disponibles en la caja.\n\n`;
            mensaje += `💰 Cantidad distribuida: ${cantidadDistribuida.toFixed(2)}€ (${porcentajeAlcanzado}%)\n`;
            mensaje += `📉 Cantidad faltante: ${remainingAmount.toFixed(2)}€`;
            
            showWarning(mensaje);
        }
    } else {
        // Cálculo exitoso
        showSuccess(`✅ Cantidad distribuida correctamente: ${importeMovimiento.toFixed(2)}€`);
    }
}

function updateAvailableQuantities(desgloseActual) {
    console.log('Actualizando cantidades disponibles:', desgloseActual);
    
    // Actualizar todas las denominaciones
    $('.money-item').each(function() {
        const denominacionId = $(this).find('.salida-input').data('denominacion');
        const $availableDisplay = $(this).find('.available-quantity');
        const $salidaInput = $(this).find('.salida-input');
        const $moneyItem = $(this);
        
        if (desgloseActual[denominacionId]) {
            const cantidad = desgloseActual[denominacionId].cantidad;
            
            // Actualizar el display según la cantidad
            if (cantidad === 0) {
                $availableDisplay.find('.quantity-text').text('Sin unidades');
                $availableDisplay.addClass('no-available').removeClass('has-available');
            } else {
                $availableDisplay.find('.quantity-text').text(`Disponible: ${cantidad}`);
                $availableDisplay.removeClass('no-available').addClass('has-available');
            }
            
            // Actualizar el max del input de salida
            $salidaInput.attr('max', cantidad);
            $salidaInput.data('available', cantidad);
            
            // Validar si el valor actual excede lo disponible
            const currentValue = parseInt($salidaInput.val()) || 0;
            if (currentValue > cantidad) {
                $salidaInput.val(cantidad);
                $salidaInput.addClass('exceeds-available');
                $moneyItem.addClass('has-error');
                showTemporaryMessage($salidaInput, `Cantidad ajustada al máximo disponible: ${cantidad}`, 'exceeds-warning');
            } else {
                $salidaInput.removeClass('exceeds-available');
                $moneyItem.removeClass('has-error');
            }
        } else {
            // No hay cantidad disponible
            $availableDisplay.find('.quantity-text').text('Sin unidades');
            $availableDisplay.addClass('no-available').removeClass('has-available');
            $salidaInput.attr('max', 0);
            $salidaInput.data('available', 0);
            $salidaInput.val('');
            $salidaInput.removeClass('exceeds-available');
            $moneyItem.removeClass('has-error');
        }
    });
    
    console.log('Cantidades disponibles actualizadas');
}

function validateSalidaInput(input) {
    const $input = $(input);
    const value = parseInt($input.val()) || 0;
    const available = parseInt($input.data('available')) || 0;
    const $moneyItem = $input.closest('.money-item');
    
    // Limpiar estados anteriores
    $input.removeClass('exceeds-available');
    $moneyItem.removeClass('has-error');
    $moneyItem.find('.temp-message').remove();
    
    // Validar que no sea negativo
    if (value < 0) {
        $input.val(0);
        $input.addClass('exceeds-available');
        $moneyItem.addClass('has-error');
        showTemporaryMessage($input, 'No se permiten valores negativos', 'warning');
        return false;
    }
    
    // Validar que no exceda lo disponible
    if (value > available) {
        $input.addClass('exceeds-available');
        $moneyItem.addClass('has-error');
        
        // Mostrar mensaje temporal más descriptivo
        if (available === 0) {
            showTemporaryMessage($input, 'No hay unidades disponibles de esta denominación', 'exceeds-warning');
            $input.val(0);
        } else {
            showTemporaryMessage($input, `Máximo disponible: ${available} unidades`, 'exceeds-warning');
            $input.val(available);
        }
        return false;
    }
    
    return true;
}

function validateEntradaInput(input) {
    const $input = $(input);
    const value = parseInt($input.val()) || 0;
    const $moneyItem = $input.closest('.money-item');
    
    // Limpiar estados anteriores
    $input.removeClass('exceeds-available');
    $moneyItem.removeClass('has-error');
    $moneyItem.find('.temp-message').remove();
    
    // Validar que no sea negativo
    if (value < 0) {
        $input.val(0);
        $input.addClass('exceeds-available');
        $moneyItem.addClass('has-error');
        showTemporaryMessage($input, 'No se permiten valores negativos', 'warning');
        return false;
    }
    
    return true;
}

function showTemporaryMessage(input, message, type) {
    const $input = $(input);
    const $container = $input.closest('.money-item');
    
    // Remover mensaje anterior si existe
    $container.find('.temp-message').remove();
    
    // Determinar la clase del mensaje según el tipo
    let alertClass = 'alert-info';
    let iconClass = 'tim-icons icon-alert-circle-exc';
    
    if (type === 'warning') {
        alertClass = 'alert-warning';
        iconClass = 'tim-icons icon-alert-circle-exc';
    } else if (type === 'exceeds-warning') {
        alertClass = 'exceeds-warning';
        iconClass = 'tim-icons icon-simple-remove';
    }
    
    // Crear mensaje temporal mejorado
    const $message = $(`
        <div class="temp-message alert alert-enhanced ${alertClass} fade-in mt-2 mb-0" style="font-size: 0.75rem;">
            <i class="${iconClass}"></i>
            ${message}
        </div>
    `);
    
    // Insertar después del input-group
    $input.closest('.input-group').after($message);
    
    // Efecto de entrada
    $message.hide().fadeIn(300);
    
    // Remover después de 4 segundos (más tiempo para mensajes críticos)
    const fadeTime = type === 'exceeds-warning' ? 5000 : 3000;
    setTimeout(() => {
        $message.fadeOut(300, function() {
            $(this).remove();
        });
    }, fadeTime);
}

// Expose functions to global scope
window.initializeMoneyBreakdown = initializeMoneyBreakdown;
window.calculateMoneyTotals = calculateMoneyTotals;
window.validateMoneyBreakdown = validateMoneyBreakdown;
window.validateCompleteMoneyBreakdown = validateCompleteMoneyBreakdown;
window.clearMoneyBreakdown = clearMoneyBreakdown;
window.calculateFromTotal = calculateFromTotal;
window.updateAvailableQuantities = updateAvailableQuantities;
window.validateSalidaInput = validateSalidaInput;
window.validateEntradaInput = validateEntradaInput;
window.showTemporaryMessage = showTemporaryMessage;
