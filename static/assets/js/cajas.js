$(document).ready(function() {
    const defaultEjercicioId = $('#ejercicioSelect').val();
    if (defaultEjercicioId) {
        loadCajasData();
    } else {
        $('#cajasTabsContainer').hide();
        $('#noEjercicioMessage').show();
    }
    $('#ejercicioSelect').on('change', function() {
        loadCajasData();
    });
});

function loadCajasData() {
    const ejercicioId = $('#ejercicioSelect').val();
    if (!ejercicioId) {
        $('#cajasTabsContainer').hide();
        $('#noEjercicioMessage').show();
        return;
    }
    $.ajax({
        url: "/cajas/",
        method: "GET",
        data: {
            'ejercicio_id': ejercicioId,
            'ajax': 'true'
        },
        success: function(data) {
            if (data.success && data.cajas && data.cajas.length > 0) {
                renderCajasTabs(data.cajas);
                $('#cajasTabsContainer').show();
                $('#noEjercicioMessage').hide();
            } else {
                $('#cajasTabsContainer').hide();
                $('#noEjercicioMessage').show();
            }
        },
        error: function() {
            $('#cajasTabsContainer').hide();
            $('#noEjercicioMessage').show();
        }
    });
}

function renderCajasTabs(cajas) {
    const tabs = $('#cajasTabs');
    tabs.empty();
    const tabContent = $('#cajasTabContent');
    tabContent.empty();

    cajas.forEach(function(caja, idx) {
        tabs.append(`
            <li class="nav-item">
                <a class="nav-link ${idx === 0 ? 'active' : ''}" id="tab-caja-${caja.id}" data-toggle="tab" href="#caja-${caja.id}" role="tab">
                    <i class="tim-icons icon-wallet-43"></i> ${caja.nombre}
                </a>
            </li>
        `);

        tabContent.append(`
            <div class="tab-pane fade ${idx === 0 ? 'show active' : ''}" id="caja-${caja.id}" role="tabpanel">
                <div class="row">
                    <div class="col-md-6">
                        <div class="card mt-3">
                            <div class="card">
                                <div class="card-header">
                                    <h4 class="card-title">
                                        <i class="tim-icons icon-coins mr-2"></i>
                                        Desglose Actual de las Cajas
                                    </h4>
                                </div>
                                <div class="card-body">
                                    <div id="desgloseActualContainer">
                                        <div class="text-center text-muted py-3" id="noDesgloseMessage-${caja.id}">
                                            <i class="tim-icons icon-wallet-43" style="font-size: 2rem;"></i>
                                            <p class="mt-2">Selecciona un ejercicio para ver el desglose de sus cajas</p>
                                        </div>
                                        <div id="desgloseContent-${caja.id}" style="display: none;">
                                            <div id="desgloseCaja-${caja.id}">
                                                <!-- El desglose de la caja se cargará aquí -->
                                            </div>
                                            <hr>
                                            <div class="row">
                                                <div class="col-md-6">
                                                    <div class="d-flex justify-content-between">
                                                        <strong>Total calculado desde desglose:</strong>
                                                        <span id="totalDesglose-${caja.id}" class="text-success">--</span>
                                                    </div>
                                                </div>
                                                <div class="col-md-6">
                                                    <div class="d-flex justify-content-between">
                                                        <strong>Saldo oficial:</strong>
                                                        <span id="saldoOficial-${caja.id}" class="text-info">--</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div id="diferenciaSaldo-${caja.id}" class="alert alert-warning mt-2" style="display: none;">
                                                <i class="tim-icons icon-alert-circle-exc mr-1"></i>
                                                <strong>Atención:</strong> Hay una diferencia entre el saldo oficial y el calculado desde el desglose.
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="card mt-3">
                            <div class="card-header">
                                <h5 class="card-title section-title"><i class="tim-icons icon-refresh-01"></i> Movimientos de Dinero</h5>
                            </div>
                            <div class="card-body">
                                <div id="movimientosDineroCaja-${caja.id}" class="movements-search-bar">
                                    <div class="spinner-border text-primary" role="status"><span class="sr-only">Cargando...</span></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card mt-3">
                            <div class="card-header">
                                <h5 class="card-title section-title"><i class="tim-icons icon-notes"></i> Movimientos de la Caja</h5>
                            </div>
                            <div class="card-body">
                                <div id="movimientosCaja-${caja.id}">
                                    <div class="spinner-border text-primary" role="status"><span class="sr-only">Cargando...</span></div>
                                </div>
                            </div>
                        </div>
                        <div class="card mt-3">
                            <div class="card-header">
                                <h5 class="card-title section-title"><i class="tim-icons icon-chart-bar-32"></i> Gráficos de Utilidad</h5>
                            </div>
                            <div class="card-body">
                                <div id="graficosCaja-${caja.id}">
                                    <div class="spinner-border text-primary" role="status"><span class="sr-only">Cargando...</span></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `);

        loadDesgloseCaja(caja.id);
        loadMovimientosCaja(caja.id);
        loadMovimientosDineroCaja(caja.id);
        loadGraficosCaja(caja.id);
    });

    // Activar pestañas Bootstrap
    tabs.find('a[data-toggle="tab"]').on('click', function(e) {
        e.preventDefault();
        $(this).tab('show');
    });
}

function loadDesgloseCaja(cajaId) {
    const container = $('#desgloseCaja-' + cajaId);
    container.html('<div class="spinner-border text-primary" role="status"><span class="sr-only">Cargando...</span></div>');
    $.ajax({
        url: '/cajas/',
        method: 'GET',
        data: {
            'ajax': 'true',
            'action': 'get_desglose',
            'caja_id': cajaId,
            'ejercicio_id': $('#ejercicioSelect').val()
        },
        success: function(data) {
            if (data.success && data.desglose && data.desglose.length > 0) {
                let html = '<table class="table table-sm"><thead><tr><th>Denominación</th><th>Cantidad</th><th>Total (€)</th></tr></thead><tbody>';
                let total = 0;
                data.desglose.forEach(function(item) {
                    html += `<tr>
                        <td>${item.denominacion}</td>
                        <td>${item.cantidad}</td>
                        <td>${item.valor_total.toFixed(2)}</td>
                    </tr>`;
                    total += item.valor_total;
                });
                html += '</tbody></table>';
                container.html(html);
                $('#desgloseContent-' + cajaId).show();
                $('#noDesgloseMessage-' + cajaId).hide();
                $('#totalDesglose-' + cajaId).text(total.toFixed(2) + '€');
                if (data.saldo_oficial !== undefined) {
                    $('#saldoOficial-' + cajaId).text(data.saldo_oficial.toFixed(2) + '€');
                    if (Math.abs(total - data.saldo_oficial) > 0.01) {
                        $('#diferenciaSaldo-' + cajaId).show();
                    } else {
                        $('#diferenciaSaldo-' + cajaId).hide();
                    }
                }
            } else {
                container.html('<div class="text-muted py-2">No hay desglose disponible.</div>');
                $('#desgloseContent-' + cajaId).hide();
                $('#noDesgloseMessage-' + cajaId).show();
            }
        },
        error: function() {
            container.html('<div class="text-danger py-2">Error al cargar el desglose.</div>');
            $('#desgloseContent-' + cajaId).hide();
            $('#noDesgloseMessage-' + cajaId).show();
        }
    });
}

function loadMovimientosCaja(cajaId) {
    const container = $('#movimientosCaja-' + cajaId);
    container.html('<div class="spinner-border text-primary" role="status"><span class="sr-only">Cargando...</span></div>');
    $.ajax({
        url: '/cajas/',
        method: 'GET',
        data: {
            'ajax': 'true',
            'action': 'get_movimientos',
            'caja_id': cajaId,
            'ejercicio_id': $('#ejercicioSelect').val()
        },
        success: function(data) {
            if (data.success && data.movimientos && data.movimientos.length > 0) {
                let html = '<table class="table table-sm"><thead><tr><th>Fecha</th><th>Concepto</th><th>Cantidad</th></tr></thead><tbody>';
                data.movimientos.forEach(function(mov) {
                    html += `<tr>
                        <td>${mov.fecha_display}</td>
                        <td>${mov.concepto}</td>
                        <td class="${mov.es_gasto ? 'text-danger' : 'text-success'}"><strong>${mov.es_gasto ? '-' : '+'}${mov.cantidad.toFixed(2)}€</strong></td>
                    </tr>`;
                });
                html += '</tbody></table>';
                container.html(html);
            } else {
                container.html('<div class="text-muted py-2">No hay movimientos registrados.</div>');
            }
        },
        error: function() {
            container.html('<div class="text-danger py-2">Error al cargar los movimientos.</div>');
        }
    });
}

function loadMovimientosDineroCaja(cajaId) {
    const container = $('#movimientosDineroCaja-' + cajaId);
    container.html('<div class="spinner-border text-primary" role="status"><span class="sr-only">Cargando...</span></div>');
    $.ajax({
        url: '/cajas/',
        method: 'GET',
        data: {
            'ajax': 'true',
            'action': 'get_movimientos_dinero',
            'caja_id': cajaId,
            'ejercicio_id': $('#ejercicioSelect').val()
        },
        success: function(data) {
            if (data.success && data.movimientos_dinero && data.movimientos_dinero.length > 0) {
                let html = '<table class="table table-sm"><thead><tr><th>Denominación</th><th>Entrada</th><th>Salida</th></tr></thead><tbody>';
                data.movimientos_dinero.forEach(function(mov) {
                    html += `<tr>
                        <td>${mov.denominacion}</td>
                        <td>${mov.cantidad_entrada}</td>
                        <td>${mov.cantidad_salida}</td>
                    </tr>`;
                });
                html += '</tbody></table>';
                container.html(html);
            } else {
                container.html('<div class="text-muted py-2">No hay movimientos de dinero registrados.</div>');
            }
        },
        error: function() {
            container.html('<div class="text-danger py-2">Error al cargar los movimientos de dinero.</div>');
        }
    });
}

function loadGraficosCaja(cajaId) {
    const container = $('#graficosCaja-' + cajaId);
    container.html('<div class="spinner-border text-primary" role="status"><span class="sr-only">Cargando...</span></div>');
    $.ajax({
        url: '/cajas/',
        method: 'GET',
        data: {
            'ajax': 'true',
            'action': 'get_graficos',
            'caja_id': cajaId,
            'ejercicio_id': $('#ejercicioSelect').val()
        },
        success: function(data) {
            if (data.success && data.grafico) {
                container.html('<canvas id="graficoCajaCanvas-' + cajaId + '" height="120"></canvas>');
                const canvas = document.getElementById('graficoCajaCanvas-' + cajaId);
                if (canvas) {
                    const ctx = canvas.getContext('2d');
                    new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: data.grafico.labels,
                            datasets: [{
                                label: 'Saldo',
                                data: data.grafico.saldos,
                                borderColor: '#1d8cf8',
                                backgroundColor: 'rgba(29,140,248,0.1)',
                                fill: true
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: {
                                        callback: function(value) { return value.toFixed(2) + '€'; }
                                    }
                                }
                            }
                        }
                    });
                } else {
                    container.html('<div class="text-danger">No se pudo crear el gráfico (canvas no disponible).</div>');
                }
            } else {
                container.html('<div class="text-muted py-2">No hay datos de gráficos disponibles.</div>');
            }
        },
        error: function() {
            container.html('<div class="text-danger py-2">Error al cargar el gráfico.</div>');
        }
    });
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