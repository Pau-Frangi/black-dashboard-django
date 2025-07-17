$(document).ready(function() {
    // Preselección automática y carga inicial
    const defaultEjercicioId = $('#ejercicioSelect').val();
    if (defaultEjercicioId) {
        loadCajasData();
    }
});

function loadCajasData() {
    const ejercicioId = $('#ejercicioSelect').val();
    if (!ejercicioId) {
        $('#cajasTabsContainer').hide();
        $('#noEjercicioMessage').show();
        return;
    }
    $('#noEjercicioMessage').hide();
    // AJAX para obtener cajas del ejercicio y sus datos
    $.ajax({
        url: $("#ejercicioSelect").data("ajax-url") || "/cajas/",
        method: "GET",
        data: {
            'ejercicio_id': ejercicioId,
            'ajax': 'true'
        },
        success: function(data) {
            if (data.success) {
                renderCajasTabs(data.cajas);
                $('#cajasTabsContainer').show();
            } else {
                alert('Error: ' + data.error);
                $('#cajasTabsContainer').hide();
                $('#noEjercicioMessage').show();
            }
        },
        error: function(xhr, status, error) {
            alert('Error al cargar las cajas: ' + error);
            $('#cajasTabsContainer').hide();
            $('#noEjercicioMessage').show();
        }
    });
}

// Renderiza las pestañas y el contenido de cada caja
function renderCajasTabs(cajas) {
    const tabs = $('#cajasTabs');
    const tabContent = $('#cajasTabContent');
    tabs.empty();
    tabContent.empty();
    if (!cajas || cajas.length === 0) {
        $('#cajasTabsContainer').hide();
        $('#noEjercicioMessage').show();
        return;
    }
    cajas.forEach(function(caja, idx) {
        // Pestaña
        tabs.append(`
            <li class="nav-item">
                <a class="nav-link ${idx === 0 ? 'active' : ''}" id="tab-caja-${caja.id}" data-toggle="tab" href="#caja-${caja.id}" role="tab">
                    <i class="tim-icons icon-wallet-43"></i> ${caja.nombre}
                </a>
            </li>
        `);
        // Contenido de la caja
        tabContent.append(`
            <div class="tab-pane fade ${idx === 0 ? 'show active' : ''}" id="caja-${caja.id}" role="tabpanel">
                <div class="row mb-3">
                    <div class="col-md-6">
                        <h5>Desglose por Denominaciones</h5>
                        <div id="desgloseCaja-${caja.id}">
                            <!-- Desglose se carga por AJAX -->
                        </div>
                        <button class="btn btn-info mt-3" onclick="openCambioDineroModal(${caja.id})">
                            <i class="tim-icons icon-refresh-01"></i> Cambio de Dinero
                        </button>
                    </div>
                    <div class="col-md-6">
                        <h5>Gráficos de Utilidad</h5>
                        <div id="graficosCaja-${caja.id}">
                            <!-- Gráficos se cargan por JS -->
                        </div>
                    </div>
                </div>
                <div class="row mb-3">
                    <div class="col-md-6">
                        <h5>Movimientos de la Caja</h5>
                        <div id="movimientosCaja-${caja.id}">
                            <!-- Listado de movimientos de caja por AJAX -->
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h5>Movimientos de Dinero</h5>
                        <div id="movimientosDineroCaja-${caja.id}">
                            <!-- Listado de movimientos de dinero por AJAX -->
                        </div>
                    </div>
                </div>
            </div>
        `);
        // Cargar desglose, movimientos y gráficos por AJAX/JS
        loadDesgloseCaja(caja.id);
        loadMovimientosCaja(caja.id);
        loadMovimientosDineroCaja(caja.id);
        loadGraficosCaja(caja.id);
    });
}

// Funciones para cargar desglose, movimientos y gráficos (implementa AJAX según tu backend)
function loadDesgloseCaja(cajaId) {
    // AJAX para desglose de la caja
    $.ajax({
        url: '/cajas/', // Ajusta si tienes un endpoint específico
        method: 'GET',
        data: {
            'ajax': 'true',
            'action': 'get_desglose',
            'caja_id': cajaId
        },
        success: function(data) {
            const container = $('#desgloseCaja-' + cajaId);
            if (data.success && data.desglose) {
                let html = '<ul class="list-group">';
                data.desglose.forEach(function(item) {
                    html += `<li class="list-group-item d-flex justify-content-between align-items-center">
                        <span>${item.denominacion}:</span>
                        <span><strong>${item.cantidad}</strong> <small class="text-muted">(${item.valor_total.toFixed(2)}€)</small></span>
                    </li>`;
                });
                html += '</ul>';
                container.html(html);
            } else {
                container.html('<div class="text-muted">No hay desglose disponible.</div>');
            }
        },
        error: function() {
            $('#desgloseCaja-' + cajaId).html('<div class="text-danger">Error al cargar el desglose.</div>');
        }
    });
}

function loadMovimientosCaja(cajaId) {
    // AJAX para movimientos de la caja
    $.ajax({
        url: '/cajas/', // Ajusta si tienes un endpoint específico
        method: 'GET',
        data: {
            'ajax': 'true',
            'action': 'get_movimientos',
            'caja_id': cajaId
        },
        success: function(data) {
            const container = $('#movimientosCaja-' + cajaId);
            if (data.success && data.movimientos) {
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
                container.html('<div class="text-muted">No hay movimientos registrados.</div>');
            }
        },
        error: function() {
            $('#movimientosCaja-' + cajaId).html('<div class="text-danger">Error al cargar los movimientos.</div>');
        }
    });
}

function loadMovimientosDineroCaja(cajaId) {
    // AJAX para movimientos de dinero de la caja
    $.ajax({
        url: '/cajas/', // Ajusta si tienes un endpoint específico
        method: 'GET',
        data: {
            'ajax': 'true',
            'action': 'get_movimientos_dinero',
            'caja_id': cajaId
        },
        success: function(data) {
            const container = $('#movimientosDineroCaja-' + cajaId);
            if (data.success && data.movimientos_dinero) {
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
                container.html('<div class="text-muted">No hay movimientos de dinero registrados.</div>');
            }
        },
        error: function() {
            $('#movimientosDineroCaja-' + cajaId).html('<div class="text-danger">Error al cargar los movimientos de dinero.</div>');
        }
    });
}

function loadGraficosCaja(cajaId) {
    // JS para gráficos de utilidad (ejemplo simple con Chart.js)
    $.ajax({
        url: '/cajas/', // Ajusta si tienes un endpoint específico
        method: 'GET',
        data: {
            'ajax': 'true',
            'action': 'get_graficos',
            'caja_id': cajaId
        },
        success: function(data) {
            const container = $('#graficosCaja-' + cajaId);
            if (data.success && data.grafico) {
                // Ejemplo: grafico de saldo por día
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
                                yAxes: [{
                                    ticks: {
                                        callback: function(value) { return value.toFixed(2) + '€'; }
                                    }
                                }]
                            }
                        }
                    });
                } else {
                    container.html('<div class="text-danger">No se pudo crear el gráfico (canvas no disponible).</div>');
                }
            } else {
                container.html('<div class="text-muted">No hay datos de gráficos disponibles.</div>');
            }
        },
        error: function() {
            $('#graficosCaja-' + cajaId).html('<div class="text-danger">Error al cargar el gráfico.</div>');
        }
    });
}

// Modal para cambio de dinero
function openCambioDineroModal(cajaId) {
    // Cargar denominaciones y desglose actual por AJAX
    // Rellena #cambioDineroInputs
    $('#cambioDineroModal').modal('show');
}

// Manejo del formulario de cambio de dinero
$('#cambioDineroForm').on('submit', function(e) {
    e.preventDefault();
    // Recoge datos y envía AJAX para realizar el cambio
    // Actualiza desglose y movimientos tras éxito
    $('#cambioDineroModal').modal('hide');
});
