/* static/js/theme.js */

(function() {
    // 1. LÓGICA INMEDIATA (Evita el parpadeo blanco)
    // Se ejecuta antes de que el navegador termine de dibujar el HTML.
    
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Si hay tema guardado 'dark' O no hay nada guardado pero el sistema es oscuro
    if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
        document.documentElement.classList.add('dark-mode');
    } else {
        document.documentElement.classList.remove('dark-mode');
    }
})();

// 2. LÓGICA DE INTERACCIÓN (Espera a que cargue el botón)
document.addEventListener('DOMContentLoaded', () => {
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const htmlElement = document.documentElement;

    if (darkModeToggle) {
        // Sincronizar el estado del checkbox con la clase actual
        // (Por si la lógica inmediata activó el modo oscuro, marcamos el checkbox)
        if (htmlElement.classList.contains('dark-mode')) {
            darkModeToggle.checked = true;
        }

        // Escuchar cambios manuales
        darkModeToggle.addEventListener('change', () => {
            if (darkModeToggle.checked) {
                htmlElement.classList.add('dark-mode');
                localStorage.setItem('theme', 'dark');
            } else {
                htmlElement.classList.remove('dark-mode');
                localStorage.setItem('theme', 'light');
            }
        });
    }
});