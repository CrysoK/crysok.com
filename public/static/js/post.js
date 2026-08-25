/**
 * Script para aplicar traducciones a los títulos de los admonitions
 * Reemplaza los títulos por defecto con las traducciones definidas en window.admonitionTranslations
 * y agrega íconos de Boxicons
 */
document.addEventListener('DOMContentLoaded', function () {
  // Obtener el contenedor del contenido del post
  const postContent = document.querySelector('.post-content');
  if (!postContent) return;

  // Verificar si existen traducciones
  if (!window.admonitionTranslations) return;

  // Mapeo de tipos de admonition a íconos de Boxicons
  const iconMap = {
    note: 'bx bx-note',
    warning: 'bx bx-error',
    important: 'bx bx-error-circle',
    tip: 'bx bx-bulb',
    caution: 'bx bx-shield-quarter'
  };

  // Obtener todos los admonitions
  const admonitions = postContent.querySelectorAll('.admonition');

  // Aplicar traducciones a cada admonition
  admonitions.forEach(admonition => {
    // Determinar el tipo de admonition
    const types = ['note', 'warning', 'important', 'tip', 'caution'];
    let type = null;

    for (const t of types) {
      if (admonition.classList.contains(t)) {
        type = t;
        break;
      }
    }

    if (!type) return;

    // Buscar el título del admonition
    const titleElement = admonition.querySelector('.admonition-title');
    if (!titleElement) return;

    // Obtener la traducción
    const translation = window.admonitionTranslations[type];
    if (!translation) return;

    // Crear el ícono
    const iconClass = iconMap[type];
    const icon = document.createElement('i');
    icon.className = iconClass;
    icon.style.marginRight = '0.5rem';
    icon.style.verticalAlign = 'middle';
    icon.style.fontSize = '1.2em';

    // Limpiar el contenido actual y agregar el ícono y la traducción
    titleElement.textContent = '';
    titleElement.appendChild(icon);
    titleElement.appendChild(document.createTextNode(translation));
  });
});
