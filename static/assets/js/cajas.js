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

    // Inicializa los totales con la primera caja
    if (cajas.length > 0) {
        updateTotalsDisplay(
            cajas[0].ingresos_caja || 0,
            cajas[0].gastos_caja || 0,
            cajas[0].saldo_caja || 0
        );
    }

    cajas.forEach(function(caja, idx) {
        tabs.append(`
            <li class="nav-item">
                <a class="nav-link ${idx === 0 ? 'active' : ''}" id="tab-caja-${caja.id}" data-toggle="tab" href="#caja-${caja.id}" role="tab"
                   data-ingresos="${caja.ingresos_caja}" data-gastos="${caja.gastos_caja}" data-saldo="${caja.saldo_caja}">
                    <i class="tim-icons icon-wallet-43"></i> ${caja.nombre}
                    <span class="badge badge-${caja.activa ? 'success' : 'secondary'} ml-2">
                        ${caja.activa ? 'Activa' : 'Inactiva'}
                    </span>
                </a>
            </li>
        `);

        tabContent.append(`
            <div class="tab-pane fade ${idx === 0 ? 'show active' : ''}" id="caja-${caja.id}" role="tabpanel">
                <div class="row">
                    <div class="col-md-6">
                        <div class="card mt-3">
                            <div class="card-header">
                                <h4 class="card-title">
                                    <i class="tim-icons icon-coins mr-2"></i>
                                    Desglose Actual de ${caja.nombre}
                                </h4>
                            </div>
                            <div class="card-body">
                                <div id="desgloseActualContainer-${caja.id}">
                                    <div class="text-center text-muted py-3" id="noDesgloseMessage-${caja.id}">
                                        <i class="tim-icons icon-wallet-43" style="font-size: 2rem;"></i>
                                        <p class="mt-2">Cargando desglose...</p>
                                    </div>
                                    <div id="desgloseContent-${caja.id}" style="display: none;">
                                        <div id="desgloseCaja-${caja.id}">
                                            <!-- El desglose de la caja se cargará aquí -->
                                        </div>
                                        <hr>
                                        <div class="row">
                                            <div class="col-md-6">
                                                <div class="d-flex justify-content-between">
                                                    <strong>Total desde desglose:</strong>
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
                        <div class="card mt-3">
                            <div class="card-header">
                                <h5 class="card-title">
                                    <i class="tim-icons icon-refresh-01"></i> 
                                    Movimientos de Efectivo
                                </h5>
                            </div>
                            <div class="card-body">
                                <div id="movimientosDineroCaja-${caja.id}">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="sr-only">Cargando...</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card mt-3">
                            <div class="card-header">
                                <h5 class="card-title">
                                    <i class="tim-icons icon-notes"></i> 
                                    Movimientos de ${caja.nombre}
                                </h5>
                            </div>
                            <div class="card-body">
                                <div id="movimientosCaja-${caja.id}">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="sr-only">Cargando...</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="card mt-3">
                            <div class="card-header">
                                <h5 class="card-title">
                                    <i class="tim-icons icon-chart-bar-32"></i> 
                                    Evolución del Saldo
                                </h5>
                            </div>
                            <div class="card-body">
                                <div id="graficosCaja-${caja.id}">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="sr-only">Cargando...</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `);
        
        // Load data for each caja
        loadDesgloseCaja(caja.id);
        loadMovimientosCaja(caja.id);
        loadMovimientosDineroCaja(caja.id);
        loadGraficosCaja(caja.id);
    });

    // Activar pestañas Bootstrap y actualizar totales al cambiar de caja
    tabs.find('a[data-toggle="tab"]').on('click', function(e) {
        e.preventDefault();
        $(this).tab('show');
        // Actualizar totales con los datos de la caja activa
        const ingresos = parseFloat($(this).data('ingresos')) || 0;
        const gastos = parseFloat($(this).data('gastos')) || 0;
        const saldo = parseFloat($(this).data('saldo')) || 0;
        updateTotalsDisplay(ingresos, gastos, saldo);
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
                let html = `
                    <div class="table-responsive">
                        <table class="table table-sm table-striped">
                            <thead>
                                <tr>
                                    <th>Denominación</th>
                                    <th>Tipo</th>
                                    <th>Cantidad</th>
                                    <th>Total (€)</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                let total = 0;
                data.desglose.forEach(function(item) {
                    const tipoIcon = item.tipo === 'billete' ? 'tim-icons icon-paper' : 'tim-icons icon-coins';
                    const tipoBadge = item.tipo === 'billete' ? 'badge-primary' : 'badge-info';
                    
                    html += `<tr>
                        <td>${item.denominacion}</td>
                        <td>
                            <span class="badge ${tipoBadge}">
                                <i class="${tipoIcon}"></i> ${item.tipo}
                            </span>
                        </td>
                        <td>${item.cantidad}</td>
                        <td><strong>${item.valor_total.toFixed(2)}€</strong></td>
                    </tr>`;
                    total += item.valor_total;
                });
                
                html += '</tbody></table></div>';
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
                container.html('<div class="text-muted py-2"><i class="tim-icons icon-alert-circle-exc"></i> No hay desglose disponible.</div>');
                $('#desgloseContent-' + cajaId).hide();
                $('#noDesgloseMessage-' + cajaId).show();
            }
        },
        error: function() {
            container.html('<div class="text-danger py-2"><i class="tim-icons icon-alert-circle-exc"></i> Error al cargar el desglose.</div>');
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
                let html = `
                    <div class="table-responsive">
                        <table class="table table-sm table-striped">
                            <thead>
                                <tr>
                                    <th>Fecha</th>
                                    <th>Concepto</th>
                                    <th>Importe</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                data.movimientos.forEach(function(mov) {
                    const clase = mov.es_gasto ? 'text-danger' : 'text-success';
                    const signo = mov.es_gasto ? '-' : '+';
                    const icon = mov.es_gasto ? 'tim-icons icon-simple-remove' : 'tim-icons icon-simple-add';
                    
                    html += `<tr>
                        <td>${mov.fecha_display}</td>
                        <td>${mov.concepto}</td>
                        <td class="${clase}">
                            <i class="${icon}"></i>
                            <strong>${signo}${mov.cantidad.toFixed(2)}€</strong>
                        </td>
                    </tr>`;
                });
                
                html += '</tbody></table></div>';
                container.html(html);
            } else {
                container.html('<div class="text-muted py-2"><i class="tim-icons icon-bell-55"></i> No hay movimientos registrados para este ejercicio.</div>');
            }
        },
        error: function() {
            container.html('<div class="text-danger py-2"><i class="tim-icons icon-alert-circle-exc"></i> Error al cargar los movimientos.</div>');
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
                let html = `
                    <div class="table-responsive">
                        <table class="table table-sm table-striped">
                            <thead>
                                <tr>
                                    <th>Denominación</th>
                                    <th>Entrada</th>
                                    <th>Salida</th>
                                    <th>Neto</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                data.movimientos_dinero.forEach(function(mov) {
                    const neto = mov.cantidad_entrada - mov.cantidad_salida;
                    const netoClass = neto > 0 ? 'text-success' : (neto < 0 ? 'text-danger' : 'text-muted');
                    
                    html += `<tr>
                        <td>${mov.denominacion}</td>
                        <td class="text-success">+${mov.cantidad_entrada}</td>
                        <td class="text-danger">-${mov.cantidad_salida}</td>
                        <td class="${netoClass}"><strong>${neto}</strong></td>
                    </tr>`;
                });
                
                html += '</tbody></table></div>';
                container.html(html);
            } else {
                container.html('<div class="text-muted py-2"><i class="tim-icons icon-bell-55"></i> No hay movimientos de efectivo registrados.</div>');
            }
        },
        error: function() {
            container.html('<div class="text-danger py-2"><i class="tim-icons icon-alert-circle-exc"></i> Error al cargar los movimientos de efectivo.</div>');
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
            if (data.success && data.grafico && data.grafico.labels.length > 0) {
                container.html('<canvas id="graficoCajaCanvas-' + cajaId + '" height="120"></canvas>');
                const canvas = document.getElementById('graficoCajaCanvas-' + cajaId);
                if (canvas) {
                    const ctx = canvas.getContext('2d');
                    new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: data.grafico.labels,
                            datasets: [{
                                label: 'Saldo (€)',
                                data: data.grafico.saldos,
                                borderColor: '#1d8cf8',
                                backgroundColor: 'rgba(29,140,248,0.1)',
                                fill: true,
                                tension: 0.1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    labels: {
                                        color: '#ffffff'
                                    }
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: {
                                        callback: function(value) { 
                                            return value.toFixed(2) + '€'; 
                                        },
                                        color: '#ffffff'
                                    },
                                    grid: {
                                        color: 'rgba(255,255,255,0.1)'
                                    }
                                },
                                x: {
                                    ticks: {
                                        color: '#ffffff'
                                    },
                                    grid: {
                                        color: 'rgba(255,255,255,0.1)'
                                    }
                                }
                            }
                        }
                    });
                } else {
                    container.html('<div class="text-danger">No se pudo crear el gráfico (canvas no disponible).</div>');
                }
            } else {
                container.html('<div class="text-muted py-2"><i class="tim-icons icon-bell-55"></i> No hay datos suficientes para generar el gráfico.</div>');
            }
        },
        error: function() {
            container.html('<div class="text-danger py-2"><i class="tim-icons icon-alert-circle-exc"></i> Error al cargar el gráfico.</div>');
        }
    });
}

function updateTotalsDisplay(ingresos, gastos, saldo) {
    $('#totalIngresosHeader').text(ingresos.toFixed(2) + '€');
    $('#totalGastosHeader').text(gastos.toFixed(2) + '€');
    $('#saldoActual').text(saldo.toFixed(2) + '€');
    
    // Update color classes based on values
    $('#totalIngresosHeader').removeClass('text-success text-muted').addClass(ingresos > 0 ? 'text-success' : 'text-muted');
    $('#totalGastosHeader').removeClass('text-danger text-muted').addClass(gastos > 0 ? 'text-danger' : 'text-muted');
    $('#saldoActual').removeClass('text-success text-danger text-muted').addClass(
        saldo > 0 ? 'text-success' : (saldo < 0 ? 'text-danger' : 'text-muted')
    );
}

