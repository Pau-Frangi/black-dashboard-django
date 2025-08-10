// ==============================================
// SISTEMA DE ALERTAS MEJORADO
// ==============================================

/**
 * Crea un contenedor para alertas flotantes si no existe
 */
function ensureAlertsContainer() {
    if (!$('.alerts-container').length) {
        $('body').append('<div class="alerts-container"></div>');
    }
}

/**
 * Muestra una alerta mejorada con animaciones y estilos consistentes
 * @param {string} message - Mensaje a mostrar
 * @param {string} type - Tipo: success, warning, danger, info, primary
 * @param {object} options - Opciones adicionales
 */
function showEnhancedAlert(message, type = 'info', options = {}) {
    ensureAlertsContainer();
    
    const defaults = {
        duration: 4000,
        closable: true,
        icon: true,
        floating: false,
        container: null
    };
    
    const opts = {...defaults, ...options};
    
    // Iconos por tipo
    const icons = {
        success: 'icon-check-2',
        warning: 'icon-alert-circle-exc',
        danger: 'icon-simple-remove',
        info: 'icon-bell-55',
        primary: 'icon-app'
    };
    
    // Crear elemento de alerta
    const alertId = 'alert-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    const iconHtml = opts.icon ? `<i class="tim-icons ${icons[type] || icons.info}"></i>` : '';
    const closeHtml = opts.closable ? 
        `<button type="button" class="close" onclick="closeEnhancedAlert('${alertId}')">
            <span>&times;</span>
        </button>` : '';
    
    const alertHtml = `
        <div id="${alertId}" class="alert alert-${type} alert-enhanced fade-in ${opts.closable ? 'alert-dismissible' : ''}" role="alert">
            ${iconHtml}
            <span class="alert-message">${message}</span>
            ${closeHtml}
        </div>
    `;
    
    // Insertar alerta
    const $alert = $(alertHtml);
    
    if (opts.floating) {
        $('.alerts-container').prepend($alert);
    } else if (opts.container) {
        $(opts.container).prepend($alert);
    } else {
        $('.alerts-container').prepend($alert);
    }
    
    // Auto-remover si se especifica duración
    if (opts.duration > 0) {
        setTimeout(() => {
            closeEnhancedAlert(alertId);
        }, opts.duration);
    }
    
    return alertId;
}

/**
 * Cierra una alerta específica con animación
 */
function closeEnhancedAlert(alertId) {
    const $alert = $(`#${alertId}`);
    if ($alert.length) {
        $alert.removeClass('fade-in').addClass('fade-out');
        setTimeout(() => {
            $alert.remove();
        }, 300);
    }
}

/**
 * Reemplaza alert() nativo con versión mejorada
 */
function enhancedAlert(message, type = 'info') {
    return showEnhancedAlert(message, type, {
        floating: true,
        duration: 5000
    });
}

/**
 * Muestra alerta de éxito
 */
function showSuccess(message, options = {}) {
    return showEnhancedAlert(message, 'success', options);
}

/**
 * Muestra alerta de advertencia
 */
function showWarning(message, options = {}) {
    return showEnhancedAlert(message, 'warning', options);
}

/**
 * Muestra alerta de error
 */
function showError(message, options = {}) {
    return showEnhancedAlert(message, 'danger', options);
}

/**
 * Muestra alerta de información
 */
function showInfo(message, options = {}) {
    return showEnhancedAlert(message, 'info', options);
}

/**
 * Cierra todas las alertas flotantes
 */
function closeAllAlerts() {
    $('.alerts-container .alert').each(function() {
        const alertId = $(this).attr('id');
        if (alertId) {
            closeEnhancedAlert(alertId);
        }
    });
}

// Inicializar contenedor de alertas al cargar la página
$(document).ready(function() {
    ensureAlertsContainer();
});
