// Script de prueba para verificar que los totales se actualizan correctamente
// Ejecutar en la consola del navegador en la página de registro

console.log('=== TESTING TOTALS UPDATE FUNCTIONALITY ===');

// Test 1: Verificar que las funciones existen
console.log('1. Verificando funciones...');
const requiredFunctions = [
    'updateTotalsFromVisibleMovements',
    'updateTotalsDisplay',
    'applyFilters',
    'toggleTipoFilter',
    'toggleIngresosGastosFilter'
];

requiredFunctions.forEach(funcName => {
    if (typeof window[funcName] === 'function') {
        console.log(`✅ ${funcName} - OK`);
    } else {
        console.log(`❌ ${funcName} - MISSING`);
    }
});

// Test 2: Verificar variables globales
console.log('\n2. Verificando variables globales...');
const requiredVars = [
    'currentMovimientos',
    'filteredMovimientos',
    'currentTipoFilter',
    'currentIngresosGastosFilter'
];

requiredVars.forEach(varName => {
    if (typeof window[varName] !== 'undefined') {
        console.log(`✅ ${varName} - OK (value: ${window[varName]})`);
    } else {
        console.log(`❌ ${varName} - MISSING`);
    }
});

// Test 3: Verificar elementos del DOM
console.log('\n3. Verificando elementos del DOM...');
const requiredElements = [
    '#totalIngresosHeader',
    '#totalGastosHeader', 
    '#saldoActual',
    '#filterTipo',
    '#filterIngresosGastos',
    '.totals-section'
];

requiredElements.forEach(selector => {
    const element = document.querySelector(selector);
    if (element) {
        console.log(`✅ ${selector} - OK`);
    } else {
        console.log(`❌ ${selector} - NOT FOUND`);
    }
});

// Test 4: Simular filtros
console.log('\n4. Probando funcionalidad de filtros...');
if (typeof updateTotalsDisplay === 'function') {
    console.log('Probando updateTotalsDisplay(100, 50, 50)...');
    updateTotalsDisplay(100, 50, 50);
    
    const ingresos = document.querySelector('#totalIngresosHeader').textContent;
    const gastos = document.querySelector('#totalGastosHeader').textContent;
    const saldo = document.querySelector('#saldoActual').textContent;
    
    console.log(`Ingresos: ${ingresos}, Gastos: ${gastos}, Saldo: ${saldo}`);
}

console.log('\n=== TEST COMPLETED ===');
