// --- static/js/app.js ---

// VARIABLE GLOBAL PARA GUARDAR LA SELECCIÓN TEMPORALMENTE
let selectedProgramTemp = "";

// 1. FUNCIONES PARA EL FLUJO DE ACCESO (MODAL)

// A) Paso 1 -> Paso 2: Guarda programa y muestra disclaimer
window.goToDisclaimer = function(programName) {
    console.log("Variando a paso 2. Programa:", programName);
    selectedProgramTemp = programName;
    
    const step1 = document.getElementById('step-program-selection');
    const step2 = document.getElementById('step-disclaimer');

    if (step1 && step2) {
        step1.style.display = 'none';
        step2.style.display = 'block';
    }
};

// B) Validar Checkbox: Habilita el botón de continuar
window.toggleContinueButton = function() {
    const checkbox = document.getElementById('terms-check');
    const btn = document.getElementById('btn-continue-chat');
    
    if (checkbox && btn) {
        if (checkbox.checked) {
            btn.disabled = false;
            btn.style.backgroundColor = '#007bff'; // Color activo
            btn.style.color = 'white';
            btn.style.cursor = 'pointer';
        } else {
            btn.disabled = true;
            btn.style.backgroundColor = '#ccc'; // Color deshabilitado
            btn.style.cursor = 'not-allowed';
        }
    }
};

// C) Finalizar: Llama a la lógica original de registro
window.finalizeLogin = function() {
    if (selectedProgramTemp) {
        window.selectProgram(selectedProgramTemp);
    } else {
        alert("Por favor selecciona un programa primero.");
    }
};

// 2. DEFINIR LA FUNCIÓN FINAL DE REGISTRO (GLOBAL)
window.selectProgram = function(programa) {
    console.log("🎓 Programa confirmado y registrando:", programa);

    // A) Enviar datos al backend
    fetch('/api/register_access', { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            programa: programa,
            timestamp: new Date().toISOString()
        })
    })
    .then(response => response.json())
    .then(data => console.log("Registro exitoso:", data))
    .catch(err => console.error("Error registrando acceso:", err));

    // B) Guardar fecha
    const today = new Date().toISOString().split('T')[0];
    localStorage.setItem('goit_access_date', today);

    // C) Cerrar el modal con animación
    const modal = document.getElementById('accessModal');
    if (modal) {
        modal.style.opacity = '0';
        modal.style.transition = 'opacity 0.5s ease';
        setTimeout(() => {
            modal.style.display = 'none';
        }, 500);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    
    // --- 3. LÓGICA DE INICIO (VISIBILIDAD DEL MODAL) ---
    const accessModal = document.getElementById('accessModal');
    
    if (accessModal) {
        // --- MODO PRUEBAS (ACTIVADO) ---
        // Forzamos que el modal se muestre SIEMPRE.
        console.log("🚧 Modo Pruebas: Mostrando modal de acceso obligatoriamente.");
        accessModal.style.display = 'flex';
        
        // Aseguramos que se muestre el Paso 1 al recargar
        const step1 = document.getElementById('step-program-selection');
        const step2 = document.getElementById('step-disclaimer');
        if(step1) step1.style.display = 'block';
        if(step2) step2.style.display = 'none';

        /* --- MODO PRODUCCIÓN (CÓDIGO COMENTADO) ---
        const today = new Date().toISOString().split('T')[0];
        const lastAccess = localStorage.getItem('goit_access_date');

        if (lastAccess === today) {
            accessModal.style.display = 'none';
        } else {
            accessModal.style.display = 'flex';
        }
        */
    }

    // --- 4. ELEMENTOS DEL CHAT ---
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input-field');
    const messagesContainer = document.getElementById('chat-messages-container');
    const loadingFace = document.getElementById('loading-face');
    const btnRegenerate = document.getElementById('btn-regenerate');

    // Validación básica por si estamos en otra página
    if (!chatForm || !messagesContainer) return;

    // --- 5. FUNCIONES DE INTERFAZ CHAT ---

    function addMessage(text, sender) {
    const div = document.createElement('div');
    div.classList.add('message', sender);
    
    if (sender === 'bot') {
        // MODIFICACIÓN: Usamos marked.parse para convertir Markdown a HTML
        // Verificamos si la librería cargó correctamente para evitar errores
        if (typeof marked !== 'undefined') {
            div.innerHTML = marked.parse(text); 
        } else {
            div.innerHTML = text; // Fallback por si falla la librería
        }
    } else {
        div.textContent = text;
    }

    messagesContainer.appendChild(div);
    
    // Scroll al fondo
    messagesContainer.scrollTo({
        top: messagesContainer.scrollHeight,
        behavior: 'smooth'
        });
    }

    function removeLastBotMessage() {
        const lastElement = messagesContainer.lastElementChild;

        if (lastElement && lastElement.classList.contains('bot')) {
            lastElement.remove();
            console.log("✅ Último mensaje del bot eliminado correctamente.");
        } else {
            const botMessages = messagesContainer.querySelectorAll('.message.bot');
            if (botMessages.length > 0) {
                botMessages[botMessages.length - 1].remove();
                console.log("✅ Último mensaje del bot eliminado (método alternativo).");
            }
        }
    }

    // --- 6. LÓGICA DE COMUNICACIÓN (FETCH) ---

    async function sendMessage(message, mode = 'normal') {
        
        // Estado de carga
        if (mode === 'regenerate') {
            if(btnRegenerate) btnRegenerate.style.display = 'none';
            if(loadingFace) loadingFace.style.display = 'block';
        } else {
            addMessage(message, 'user');
            chatInput.value = '';
            if(loadingFace) loadingFace.style.display = 'block';
            if(btnRegenerate) btnRegenerate.style.display = 'none';
        }
        
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message, mode: mode })
            });
            
            const data = await response.json();
            
            if(loadingFace) loadingFace.style.display = 'none';

            if (data.error) {
                const divError = document.createElement('div');
                divError.classList.add('message', 'bot');
                divError.style.color = 'red';
                divError.textContent = "Error: " + data.error;
                messagesContainer.appendChild(divError);
            } else {
                addMessage(data.reply, 'bot');
                if(btnRegenerate) btnRegenerate.style.display = 'inline-block';
            }

        } catch (error) {
            if(loadingFace) loadingFace.style.display = 'none';
            console.error("Error:", error);
            addMessage("Error de conexión.", 'bot');
        }
    }

    // --- 7. EVENTOS DEL CHAT ---

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (message) {
            sendMessage(message, 'normal');
        }
    });

    if (btnRegenerate) {
        btnRegenerate.addEventListener('click', () => {
            console.log("🔄 Botón regenerar presionado.");
            const userMessages = messagesContainer.querySelectorAll('.message.user');
            if (userMessages.length > 0) {
            const lastUserMessage = userMessages[userMessages.length - 1].textContent;
            
            // 3. Borramos la respuesta anterior del bot visualmente
            removeLastBotMessage();
            
            // 4. Reenviamos el texto exacto que el usuario escribió antes
            // Nota: Enviamos 'regenerate' como modo para que el backend sepa qué hacer si quiere
            sendMessage(lastUserMessage, 'regenerate'); 
        } else {
            console.error("No hay mensajes de usuario para regenerar.");
        }
        });
    }
});