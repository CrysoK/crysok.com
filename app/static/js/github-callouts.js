/**
 * GitHub-style callout blocks transformer
 * Transforms markdown callout blocks like:
 * > [!NOTE]
 * > This is a note
 * 
 * Into HTML with proper styling
 */
document.addEventListener('DOMContentLoaded', function () {
  // Obtener el contenedor del contenido del post
  const postContent = document.querySelector('.post-content');
  if (!postContent) return;

  // Función para crear un elemento de título para el bloque de callout
  function createCalloutTitle(type) {
    const title = document.createElement('div');
    title.className = 'callout-title';

    let icon = '';
    const typeKey = type.toLowerCase();

    switch (typeKey) {
      case 'note': icon = '📝'; break;
      case 'warning': icon = '⚠️'; break;
      case 'important': icon = '🔴'; break;
      case 'tip': icon = '💡'; break;
      case 'caution': icon = '🚧'; break;
      default: icon = 'ℹ️';
    }

    // Usar traducciones si están disponibles
    let translatedTitle = type.charAt(0).toUpperCase() + type.slice(1).toLowerCase();

    if (window.calloutTranslations && window.calloutTranslations[typeKey]) {
      translatedTitle = window.calloutTranslations[typeKey];
    }

    title.textContent = `${icon} ${translatedTitle}`;
    return title;
  }

  // Función para procesar un blockquote que puede contener múltiples callouts
  function processBlockquote(blockquote) {
    // Buscar todos los párrafos dentro del blockquote
    const paragraphs = Array.from(blockquote.querySelectorAll('p'));
    if (paragraphs.length === 0) return false;

    // Verificar si hay múltiples callouts en un solo blockquote
    let calloutFound = false;
    let currentCalloutType = null;
    let currentCalloutElements = [];
    let newBlockquotes = [];

    // Primero, verificar si hay múltiples callouts en este blockquote
    let hasMultipleCallouts = false;
    let calloutCount = 0;

    for (const p of paragraphs) {
      const text = p.innerHTML;
      for (const type of ['NOTE', 'WARNING', 'IMPORTANT', 'TIP', 'CAUTION']) {
        if (text.includes(`[!${type}]`)) {
          calloutCount++;
          if (calloutCount > 1) {
            hasMultipleCallouts = true;
            break;
          }
        }
      }
      if (hasMultipleCallouts) break;
    }

    // Si hay múltiples callouts, necesitamos procesarlos de manera especial
    if (hasMultipleCallouts) {
      console.log('Found multiple callouts in one blockquote');

      // Crear un contenedor para reemplazar el blockquote original
      const container = document.createElement('div');
      container.className = 'github-callouts-container';

      // Iterar sobre todos los párrafos para encontrar y procesar callouts
      for (let i = 0; i < paragraphs.length; i++) {
        const p = paragraphs[i];
        const text = p.innerHTML;
        let calloutType = null;

        // Verificar si este párrafo contiene un marcador de callout
        for (const type of ['NOTE', 'WARNING', 'IMPORTANT', 'TIP', 'CAUTION']) {
          if (text.includes(`[!${type}]`)) {
            calloutType = type;
            break;
          }
        }

        // Si encontramos un nuevo tipo de callout, crear un nuevo blockquote
        if (calloutType) {
          // Si ya estábamos procesando un callout, finalizar el blockquote anterior
          if (currentCalloutType) {
            const newBlockquote = document.createElement('blockquote');
            newBlockquote.className = 'github-callout';
            newBlockquote.setAttribute('data-type', currentCalloutType.toLowerCase());

            // Añadir el título
            newBlockquote.appendChild(createCalloutTitle(currentCalloutType));

            // Añadir todos los elementos acumulados para este callout
            currentCalloutElements.forEach(el => {
              newBlockquote.appendChild(el.cloneNode(true));
            });

            // Añadir el nuevo blockquote al contenedor
            container.appendChild(newBlockquote);

            // Limpiar para el próximo callout
            currentCalloutElements = [];
          }

          // Iniciar un nuevo callout
          currentCalloutType = calloutType;

          // Crear un nuevo párrafo sin el marcador de callout y sin <br> que lo siga
          const newP = document.createElement('p');
          // Reemplazar el marcador y cualquier <br> que lo siga
          newP.innerHTML = text.replace(`[!${calloutType}]<br>`, '').replace(`[!${calloutType}]`, '').trim();

          // Solo añadir el párrafo si tiene contenido
          if (newP.innerHTML.trim()) {
            currentCalloutElements.push(newP);
          }
        }
        // Si no es un marcador de callout y estamos procesando un callout, añadir este párrafo al callout actual
        else if (currentCalloutType) {
          currentCalloutElements.push(p.cloneNode(true));
        }
      }

      // Procesar el último callout si existe
      if (currentCalloutType) {
        const newBlockquote = document.createElement('blockquote');
        newBlockquote.className = 'github-callout';
        newBlockquote.setAttribute('data-type', currentCalloutType.toLowerCase());

        // Añadir el título
        newBlockquote.appendChild(createCalloutTitle(currentCalloutType));

        // Añadir todos los elementos acumulados para este callout
        currentCalloutElements.forEach(el => {
          newBlockquote.appendChild(el.cloneNode(true));
        });

        // Añadir el nuevo blockquote al contenedor
        container.appendChild(newBlockquote);
      }

      // Reemplazar el blockquote original con el nuevo contenedor
      blockquote.parentNode.replaceChild(container, blockquote);
      return true;
    }
    // Si solo hay un callout, procesarlo normalmente
    else {
      const firstP = paragraphs[0];
      const text = firstP.innerHTML;

      // Verificar si contiene alguno de los patrones de callout
      for (const type of ['NOTE', 'WARNING', 'IMPORTANT', 'TIP', 'CAUTION']) {
        if (text.includes(`[!${type}]`)) {
          console.log(`Found ${type} callout in blockquote`);

          // Aplicar estilos
          blockquote.className = 'github-callout';
          blockquote.setAttribute('data-type', type.toLowerCase());

          // Reemplazar el texto del párrafo para eliminar el marcador y cualquier <br> que lo siga
          firstP.innerHTML = text.replace(`[!${type}]<br>`, '').replace(`[!${type}]`, '').trim();

          // Si el párrafo está vacío después de eliminar el marcador, eliminarlo
          if (!firstP.innerHTML.trim()) {
            firstP.remove();
          }

          // Crear y añadir el título del callout
          blockquote.insertBefore(createCalloutTitle(type), blockquote.firstChild);

          return true; // Callout procesado
        }
      }
    }

    return false; // No se encontró ningún callout
  }

  // Procesar todos los blockquotes
  const blockquotes = postContent.querySelectorAll('blockquote');
  blockquotes.forEach(processBlockquote);

  // Buscar también fuera de blockquotes (para casos donde el markdown no generó blockquotes correctamente)
  const paragraphs = postContent.querySelectorAll('p');

  paragraphs.forEach(p => {
    if (p.parentElement.tagName === 'BLOCKQUOTE') return; // Ya procesado arriba

    const text = p.innerHTML;

    for (const type of ['NOTE', 'WARNING', 'IMPORTANT', 'TIP', 'CAUTION']) {
      const pattern = `&gt; [!${type}]`;

      if (text.includes(pattern)) {
        console.log(`Found ${type} callout in paragraph`);

        // Crear un nuevo blockquote
        const blockquote = document.createElement('blockquote');
        blockquote.className = 'github-callout';
        blockquote.setAttribute('data-type', type.toLowerCase());

        // Añadir el título
        blockquote.appendChild(createCalloutTitle(type));

        // Reemplazar el párrafo con el blockquote
        p.parentNode.replaceChild(blockquote, p);

        // Buscar párrafos siguientes que comiencen con '&gt;' (>) para incluirlos en el blockquote
        let nextP = blockquote.nextElementSibling;
        while (nextP && nextP.tagName === 'P' && nextP.innerHTML.trim().startsWith('&gt;')) {
          const nextContent = nextP.innerHTML.replace('&gt;', '').trim();
          const contentP = document.createElement('p');
          contentP.innerHTML = nextContent;
          blockquote.appendChild(contentP);

          // Guardar referencia al siguiente antes de eliminar
          const toRemove = nextP;
          nextP = nextP.nextElementSibling;
          toRemove.remove();
        }
      }
    }
  });
});
