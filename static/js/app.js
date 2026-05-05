// --- static/js/app.js ---

// ─── GLOBALES DEL FLUJO MODAL ────────────────────────────────
let selectedMatricula   = "";
let selectedPrograma    = "";
let selectedProgramTemp = "";

// ─── VALIDACIÓN DE MATRÍCULA ─────────────────────────────────
const MATRICULA_REGEX = /^[S]\d{8}$/;

window.validateMatricula = function() {
    const input = document.getElementById('matricula-input');
    const error = document.getElementById('matricula-error');
    if (!input) return;

    const value = input.value.trim().toUpperCase();

    if (!MATRICULA_REGEX.test(value)) {
        if (error) error.style.display = 'block';
        input.classList.add('input-error');
        input.focus();
        return;
    }

    selectedMatricula = value;
    if (error) error.style.display = 'none';
    input.classList.remove('input-error');

    const step0 = document.getElementById('step-matricula');
    const step1 = document.getElementById('step-program-selection');
    if (step0) step0.style.display = 'none';
    if (step1) step1.style.display = 'block';
};

// ─── PASO 1 → PASO 2 (Programa → Disclaimer) ─────────────────
window.goToDisclaimer = function(programName) {
    selectedProgramTemp = programName;
    selectedPrograma    = programName;

    const step1 = document.getElementById('step-program-selection');
    const step2 = document.getElementById('step-disclaimer');
    if (step1 && step2) {
        step1.style.display = 'none';
        step2.style.display = 'block';
    }
};

// ─── VALIDAR CHECKBOX ────────────────────────────────────────
window.toggleContinueButton = function() {
    const checkbox = document.getElementById('terms-check');
    const btn = document.getElementById('btn-continue-chat');

    if (checkbox && btn) {
        if (checkbox.checked) {
            btn.disabled = false;
            btn.style.backgroundColor = '';
            btn.style.color = '';
            btn.style.cursor = 'pointer';
            btn.style.opacity = '1';
        } else {
            btn.disabled = true;
            btn.style.backgroundColor = '';
            btn.style.color = '';
            btn.style.cursor = 'not-allowed';
            btn.style.opacity = '';
        }
    }
};

// ─── FINALIZAR ───────────────────────────────────────────────
window.finalizeLogin = function() {
    if (selectedProgramTemp) {
        window.selectProgram(selectedProgramTemp);
    } else {
        alert("Por favor selecciona un programa primero.");
    }
};

// ─── REGISTRO DE ACCESO ──────────────────────────────────────
window.selectProgram = function(programa) {
    console.log("🎓 Programa:", programa, "| Matrícula:", selectedMatricula);

    fetch('/api/register_access', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            programa:  programa,
            matricula: selectedMatricula,
            timestamp: new Date().toISOString()
        })
    })
    .then(response => response.json())
    .then(data  => console.log("Registro exitoso:", data))
    .catch(err  => console.error("Error registrando acceso:", err));

    const today = new Date().toISOString().split('T')[0];
    localStorage.setItem('goit_access_date', today);

    const modal = document.getElementById('accessModal');
    if (modal) {
        modal.style.opacity = '0';
        modal.style.transition = 'opacity 0.5s ease';
        setTimeout(() => { modal.style.display = 'none'; }, 500);
    }
};

// ─── DOM READY ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

    // LÓGICA DE INICIO (visibilidad del modal)
    const accessModal = document.getElementById('accessModal');

    if (accessModal) {
        console.log("🚧 Modo Pruebas: Mostrando modal de acceso obligatoriamente.");
        accessModal.style.display = 'flex';

        // Mostrar paso 0 (matrícula), ocultar el resto
        const step0 = document.getElementById('step-matricula');
        const step1 = document.getElementById('step-program-selection');
        const step2 = document.getElementById('step-disclaimer');
        if (step0) step0.style.display = 'block';
        if (step1) step1.style.display = 'none';
        if (step2) step2.style.display = 'none';

        // Enter en campo de matrícula avanza al siguiente paso
        const matriculaInput = document.getElementById('matricula-input');
        if (matriculaInput) {
            matriculaInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') window.validateMatricula();
            });
        }
    }

    // ELEMENTOS DEL CHAT
    const chatForm          = document.getElementById('chat-form');
    const chatInput         = document.getElementById('chat-input-field');
    const messagesContainer = document.getElementById('chat-messages-container');
    const loadingFace       = document.getElementById('loading-face');
    const btnRegenerate     = document.getElementById('btn-regenerate');

    if (!chatForm || !messagesContainer) return;

    // Historial de conversación en memoria: [{role, content}, ...]
    // Se envía con cada petición para que el LLM mantenga contexto
    const conversationHistory = [];

    // FUNCIONES DE INTERFAZ CHAT
    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.classList.add('message', sender);

        if (sender === 'bot') {
            if (typeof marked !== 'undefined') {
                div.innerHTML = marked.parse(text);
            } else {
                div.innerHTML = text;
            }
        } else {
            div.textContent = text;
        }

        messagesContainer.appendChild(div);
        messagesContainer.scrollTo({ top: messagesContainer.scrollHeight, behavior: 'smooth' });
    }

    function removeLastBotMessage() {
        const lastElement = messagesContainer.lastElementChild;
        if (lastElement && lastElement.classList.contains('bot')) {
            lastElement.remove();
        } else {
            const botMessages = messagesContainer.querySelectorAll('.message.bot');
            if (botMessages.length > 0) botMessages[botMessages.length - 1].remove();
        }
    }

    // FETCH AL BACKEND (incluye matrícula, programa e historial de conversación)
    async function sendMessage(message, mode = 'normal') {
        if (mode === 'regenerate') {
            // En regenerar: quitamos la última respuesta del historial para reemplazarla
            if (conversationHistory.length > 0 &&
                conversationHistory[conversationHistory.length - 1].role === 'assistant') {
                conversationHistory.pop();
            }
            if (btnRegenerate) btnRegenerate.style.display = 'none';
            if (loadingFace)   loadingFace.style.display   = 'block';
        } else {
            // Mensaje nuevo: añadimos al historial antes de enviar
            conversationHistory.push({ role: 'user', content: message });
            addMessage(message, 'user');
            chatInput.value = '';
            if (loadingFace)   loadingFace.style.display   = 'block';
            if (btnRegenerate) btnRegenerate.style.display = 'none';
        }

        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try {
            const response = await fetch('/chat', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message:   message,
                    mode:      mode,
                    matricula: selectedMatricula,
                    programa:  selectedPrograma,
                    history:   conversationHistory.slice(-8),   // últimos 4 intercambios
                })
            });

            const data = await response.json();
            if (loadingFace) loadingFace.style.display = 'none';

            if (data.error) {
                const divError = document.createElement('div');
                divError.classList.add('message', 'bot');
                divError.style.color = 'red';
                divError.textContent = "Error: " + data.error;
                messagesContainer.appendChild(divError);
            } else {
                addMessage(data.reply, 'bot');
                // Guardar respuesta del asistente en el historial
                conversationHistory.push({ role: 'assistant', content: data.reply });

                // Si la respuesta está bloqueada por el admin, ocultar botón de regenerar
                if (btnRegenerate) {
                    btnRegenerate.style.display = data.bloqueado ? 'none' : 'inline-block';
                    btnRegenerate.title = data.bloqueado
                        ? 'Esta respuesta no puede ser regenerada'
                        : 'Regenerar respuesta';
                }
            }
        } catch (error) {
            if (loadingFace) loadingFace.style.display = 'none';
            console.error("Error:", error);
            addMessage("Error de conexión.", 'bot');
        }
    }

    // EVENTOS
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (message) sendMessage(message, 'normal');
    });

    if (btnRegenerate) {
        btnRegenerate.addEventListener('click', () => {
            const userMessages = messagesContainer.querySelectorAll('.message.user');
            if (userMessages.length > 0) {
                const lastUserMessage = userMessages[userMessages.length - 1].textContent;
                removeLastBotMessage();
                sendMessage(lastUserMessage, 'regenerate');
            }
        });
    }
});
