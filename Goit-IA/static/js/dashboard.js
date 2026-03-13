/**
 * static/js/dashboard.js
 * Lógica para el Panel de Administración
 */

document.addEventListener('DOMContentLoaded', () => {
    // Inicializar filtros al cargar
    filterAndSort('pdf');
    filterAndSort('url');
});

// --- LÓGICA DE MODALES ---

// Abrir Modal URL
function openUrlModal(name, url) {
    document.getElementById('edit_url_original').value = url;
    document.getElementById('edit_url_name').value = name;
    document.getElementById('edit_url_value').value = url;
    document.getElementById('urlModal').style.display = 'flex';
}

// Abrir Modal PDF
function openPdfModal(filename) {
    document.getElementById('edit_pdf_original').value = filename;
    // Quitamos la extensión visualmente para que sea más fácil editar
    const nameWithoutExt = filename.replace('.pdf', '');
    document.getElementById('edit_pdf_new').value = nameWithoutExt;
    document.getElementById('pdfModal').style.display = 'flex';
}

// Cerrar al hacer clic fuera (Cualquier modal)
window.onclick = function(event) {
    const modals = ['logModal', 'urlModal', 'pdfModal'];
    modals.forEach(id => {
        const modal = document.getElementById(id);
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    });
}

// --- LÓGICA DE FILTRADO Y ORDENAMIENTO ---

function filterAndSort(type) {
    // 'type' será 'pdf' o 'url'
    const inputId = type + 'Search';
    const sortId = type + 'Sort';
    const tableId = type + 'Table';

    const searchText = document.getElementById(inputId).value.toLowerCase();
    const sortValue = document.getElementById(sortId).value;
    const tableBody = document.querySelector('#' + tableId + ' tbody');
    
    // Convertimos las filas a un array para poder ordenarlas
    const rows = Array.from(tableBody.querySelectorAll('tr'));

    // 1. FILTRADO (Búsqueda)
    rows.forEach(row => {
        // Buscamos dentro de la celda que tiene la clase 'searchable-name'
        const nameCell = row.querySelector('.searchable-name');
        if (nameCell) {
            const text = nameCell.innerText.toLowerCase();
            row.style.display = text.includes(searchText) ? '' : 'none';
        }
    });

    // 2. ORDENAMIENTO
    // Filtramos solo las filas que son de datos (ignoramos mensajes de "Sin datos")
    const dataRows = rows.filter(r => r.hasAttribute('data-index'));

    dataRows.sort((a, b) => {
        const indexA = parseInt(a.getAttribute('data-index'));
        const indexB = parseInt(b.getAttribute('data-index'));
        
        const textA = a.querySelector('.searchable-name').innerText.toLowerCase().trim();
        const textB = b.querySelector('.searchable-name').innerText.toLowerCase().trim();

        if (sortValue === 'az') {
            return textA.localeCompare(textB);
        } else if (sortValue === 'za') {
            return textB.localeCompare(textA);
        } else if (sortValue === 'newest') {
            return indexB - indexA; 
        } else {
            return indexA - indexB;
        }
    });

    // Re-inyectamos las filas ordenadas
    dataRows.forEach(row => tableBody.appendChild(row));
}

// --- LÓGICA DE ENTRENAMIENTO IA ---

function startTraining() {
    const btnTrain = document.getElementById('btnTrain');
    const container = document.getElementById('terminalContainer');
    const terminal = document.getElementById('terminalOutput');
    
    // Obtenemos la URL desde el atributo data del botón
    const streamUrl = btnTrain.getAttribute('data-stream-url');
    
    let entrenamientoExitoso = false;

    // 1. Preparar UI
    btnTrain.disabled = true;
    btnTrain.innerText = "⏳ Entrenando...";
    btnTrain.style.opacity = "0.6";
    
    container.style.display = 'block';
    terminal.style.display = 'block';
    terminal.innerHTML = '<div class="terminal-line blinking-cursor">Iniciando conexión...</div>';

    // 2. Iniciar conexión SSE usando la URL obtenida
    const eventSource = new EventSource(streamUrl);

    eventSource.onmessage = function(event) {
        if (event.data === 'close') {
            eventSource.close();
            finishTrainingProcess();
            return;
        }

        if (event.data.includes("Entrenamiento exitoso") || event.data.includes("FINALIZADO")) {
            entrenamientoExitoso = true;
        }

        const line = document.createElement('div');
        line.className = 'terminal-line';
        line.textContent = '> ' + event.data;
        terminal.appendChild(line);
        terminal.scrollTop = terminal.scrollHeight;
    };

    eventSource.onerror = function(err) {
        if (entrenamientoExitoso) {
            console.log("Cierre de conexión esperado.");
            eventSource.close();
            finishTrainingProcess();
            return;
        }

        console.error("Error de SSE:", err);
        
        if (eventSource.readyState === 2) {
             eventSource.close();
             finishTrainingProcess();
        } else {
            const line = document.createElement('div');
            line.className = 'terminal-line';
            line.style.color = '#ff4444';
            line.textContent = '> ⚠️ La conexión se perdió. Si ves mensajes de éxito arriba, ignora esto.';
            terminal.appendChild(line);
            
            eventSource.close();
            btnTrain.disabled = false;
            btnTrain.innerText = "Reintentar";
        }
    };
}

function finishTrainingProcess() {
    const terminal = document.getElementById('terminalOutput');
    const btnFinish = document.getElementById('btnFinish');
    const btnTrain = document.getElementById('btnTrain');

    // Obtenemos la URL de finalización
    const completeUrl = btnTrain.getAttribute('data-complete-url');
    
    if (terminal.lastElementChild.textContent.includes("Todos los procesos completados")) return;

    const line = document.createElement('div');
    line.className = 'terminal-line';
    line.style.color = '#fff';
    line.style.fontWeight = 'bold';
    line.textContent = '==========================================';
    terminal.appendChild(line);
    
    const successLine = document.createElement('div');
    successLine.className = 'terminal-line';
    successLine.style.color = '#00ff00';
    successLine.textContent = '> ✅ Todos los procesos completados.';
    terminal.appendChild(successLine);
    terminal.scrollTop = terminal.scrollHeight;

    // Actualizar estado en servidor
    fetch(completeUrl, {method: 'POST'})
        .then(() => {
            btnFinish.style.display = 'inline-block';
            btnTrain.innerText = "Entrenamiento Completo";
        })
        .catch(err => console.error("Error actualizando estado final:", err));
}