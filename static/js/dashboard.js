/**
 * static/js/dashboard.js
 * Lógica para el Panel de Administración
 */

document.addEventListener('DOMContentLoaded', () => {
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
    const modals = ['logModal', 'urlModal', 'pdfModal', 'chatDetailModal', 'faqAddModal', 'faqEditModal'];
    modals.forEach(id => {
        const modal = document.getElementById(id);
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// ─── FILTRO DE CHAT LOGS ──────────────────────────────────────
function filterChatLogs() {
    const searchText  = (document.getElementById('chatSearch')?.value  || '').toLowerCase().trim();
    const modelFilter = (document.getElementById('chatModelFilter')?.value || '').toLowerCase();
    const rows = document.querySelectorAll('#chatLogsTable .chat-log-row');

    rows.forEach(row => {
        const matricula = row.getAttribute('data-matricula') || '';
        const modelo    = row.getAttribute('data-modelo')    || '';

        const matchesSearch = !searchText  || matricula.includes(searchText);
        const matchesModel  = !modelFilter || modelo.includes(modelFilter);

        row.style.display = (matchesSearch && matchesModel) ? '' : 'none';
    });
}

// ─── MODAL DETALLE DE PREGUNTA ────────────────────────────────
function openChatDetail(row) {
    const d = row.dataset;
    const matricula = d.dMatricula || '';
    const programa  = d.dPrograma  || '';
    const fecha     = d.dFecha     || '';
    const hora      = d.dHora      || '';
    const modelo    = d.dModelo    || '';
    const pregunta  = d.dPregunta  || '';
    const respuesta = d.dRespuesta || '';

    const isKnn = modelo.includes('KNN');
    const badgeClass = isKnn ? 'badge-knn' : 'badge-llm';
    const badgeLabel = isKnn ? 'KNN' : 'LLM';

    document.getElementById('chatDetailContent').innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem 1.5rem; margin-bottom: 1.25rem; font-size: 0.85rem; color: var(--text-secondary);">
            <div><strong style="color: var(--text-color);">Matrícula</strong><br><span style="font-family: monospace; font-weight: 700; color: var(--primary-color);">${matricula || '—'}</span></div>
            <div><strong style="color: var(--text-color);">Programa</strong><br>${programa || '—'}</div>
            <div><strong style="color: var(--text-color);">Fecha</strong><br>${fecha}</div>
            <div><strong style="color: var(--text-color);">Hora</strong><br>${hora} &nbsp;<span class="model-badge ${badgeClass}">${badgeLabel}</span></div>
        </div>
        <div style="margin-bottom: 1rem;">
            <p style="font-weight: 600; margin-bottom: 0.4rem; color: var(--text-color); font-size: 0.88rem;">Pregunta</p>
            <div style="background: var(--bg-color); border: 1px solid var(--border-color); border-radius: 10px; padding: 0.9rem 1rem; font-size: 0.88rem; line-height: 1.6; color: var(--text-color);">${escHtml(pregunta)}</div>
        </div>
        <div>
            <p style="font-weight: 600; margin-bottom: 0.4rem; color: var(--text-color); font-size: 0.88rem;">Respuesta</p>
            <div style="background: var(--bg-color); border: 1px solid var(--border-color); border-radius: 10px; padding: 0.9rem 1rem; font-size: 0.88rem; line-height: 1.6; color: var(--text-color); white-space: pre-wrap;">${escHtml(respuesta)}</div>
        </div>
    `;
    document.getElementById('chatDetailModal').style.display = 'flex';
}

function escHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
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

// ─── GESTIÓN DE FAQs ──────────────────────────────────────────

function filterFaqs() {
    const searchText  = (document.getElementById('faqSearch')?.value || '').toLowerCase().trim();
    const blockFilter = (document.getElementById('faqBlockFilter')?.value || '');
    const rows = document.querySelectorAll('#faqTable .faq-row');

    rows.forEach(row => {
        const pregunta  = (row.getAttribute('data-pregunta')  || '').toLowerCase();
        const respuesta = (row.getAttribute('data-respuesta') || '').toLowerCase();
        const bloqueado = row.getAttribute('data-bloqueado') === 'true';

        const matchesSearch = !searchText || pregunta.includes(searchText) || respuesta.includes(searchText);
        const matchesBlock  = !blockFilter
            || (blockFilter === 'bloqueada' && bloqueado)
            || (blockFilter === 'normal'    && !bloqueado);

        row.style.display = (matchesSearch && matchesBlock) ? '' : 'none';
    });
}

function closeFaqModals() {
    document.getElementById('faqAddModal').style.display = 'none';
    document.getElementById('faqEditModal').style.display = 'none';
}

function openFaqAddModal() {
    document.getElementById('faqAddPregunta').value = '';
    document.getElementById('faqAddRespuesta').value = '';
    _hideFaqMsg('faqAddMsg');
    document.getElementById('faqAddModal').style.display = 'flex';
}

function openFaqEditModal(row) {
    const id       = row.getAttribute('data-id');
    const pregunta = row.getAttribute('data-pregunta');
    const respuesta = row.getAttribute('data-respuesta');

    document.getElementById('faqEditId').value = id;
    document.getElementById('faqEditPregunta').value = pregunta;
    document.getElementById('faqEditRespuesta').value = respuesta;
    _hideFaqMsg('faqEditMsg');
    document.getElementById('faqEditModal').style.display = 'flex';
}

async function submitFaqAdd() {
    const pregunta  = document.getElementById('faqAddPregunta').value.trim();
    const respuesta = document.getElementById('faqAddRespuesta').value.trim();

    if (!pregunta || !respuesta) {
        _showFaqMsg('faqAddMsg', 'Completa todos los campos.', false);
        return;
    }

    const result = await _faqFetch(FAQ_URLS.add, { pregunta, respuesta });
    if (result.ok) {
        closeFaqModals();
        location.reload();
    } else {
        _showFaqMsg('faqAddMsg', result.message, false);
    }
}

async function submitFaqEdit() {
    const id        = document.getElementById('faqEditId').value.trim();
    const pregunta  = document.getElementById('faqEditPregunta').value.trim();
    const respuesta = document.getElementById('faqEditRespuesta').value.trim();

    if (!pregunta || !respuesta) {
        _showFaqMsg('faqEditMsg', 'Completa todos los campos.', false);
        return;
    }

    const result = await _faqFetch(FAQ_URLS.edit, { id, pregunta, respuesta });
    if (result.ok) {
        closeFaqModals();
        location.reload();
    } else {
        _showFaqMsg('faqEditMsg', result.message, false);
    }
}

async function deleteFaq(row) {
    const id = row.getAttribute('data-id');
    const pregunta = row.getAttribute('data-pregunta') || '';
    const preview = pregunta.length > 60 ? pregunta.slice(0, 60) + '...' : pregunta;

    if (!confirm(`¿Eliminar la FAQ?\n\n"${preview}"\n\nEsta acción no se puede deshacer.`)) return;

    const result = await _faqFetch(FAQ_URLS.delete, { id });
    if (result.ok) {
        row.remove();
        _updateFaqCount();
    } else {
        alert('Error: ' + result.message);
    }
}

async function toggleFaqBlock(row) {
    const id        = row.getAttribute('data-id');
    const bloqueado = row.getAttribute('data-bloqueado') === 'true';
    const accion    = bloqueado ? 'desbloquear' : 'bloquear';

    if (!confirm(`¿${accion.charAt(0).toUpperCase() + accion.slice(1)} esta FAQ?\n\n` +
        (bloqueado
            ? 'La respuesta volverá a ser regenerable por el sistema.'
            : 'La respuesta quedará fija y no podrá ser regenerada por el sistema.')
    )) return;

    const result = await _faqFetch(FAQ_URLS.toggleBlock, { id });
    if (result.ok) {
        location.reload();
    } else {
        alert('Error: ' + result.message);
    }
}

// ─── Utilidades FAQ (privadas) ────────────────────────────────

async function _faqFetch(url, body) {
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        return { ok: data.status === 'ok', message: data.message || '' };
    } catch (e) {
        return { ok: false, message: 'Error de red. Intenta de nuevo.' };
    }
}

function _showFaqMsg(elId, msg, success) {
    const el = document.getElementById(elId);
    el.style.display = 'block';
    el.style.background = success ? 'rgba(34,197,94,0.12)' : 'rgba(239,68,68,0.12)';
    el.style.color = success ? 'var(--success-color)' : 'var(--error-color)';
    el.style.border = `1px solid ${success ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`;
    el.textContent = msg;
}

function _hideFaqMsg(elId) {
    const el = document.getElementById(elId);
    if (el) el.style.display = 'none';
}

function _updateFaqCount() {
    const rows = document.querySelectorAll('#faqTable .faq-row');
    const countEl = document.getElementById('faqCount');
    if (countEl) countEl.textContent = `(${rows.length})`;
}

// ─── FIN FAQ ──────────────────────────────────────────────────

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