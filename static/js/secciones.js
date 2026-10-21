// Omnis: comportamiento de las secciones de historia (visible_si, filas de tabla, editor de secciones).
(function () {
  'use strict';

  function valorDe(contenedor, nombre) {
    const els = contenedor.querySelectorAll('[name="' + nombre + '"]');
    if (!els.length) return null;
    const el = els[0];
    if (el.type === 'radio') {
      const marcado = Array.from(els).find(function (x) { return x.checked; });
      if (!marcado) return null;
      return marcado.value === 'si' ? true : marcado.value === 'no' ? false : marcado.value;
    }
    if (el.type === 'checkbox') return Array.from(els).filter(function (x) { return x.checked; }).map(function (x) { return x.value; });
    return el.value;
  }

  function cumple(cond, valor) {
    if ('igual' in cond) return valor === cond.igual || (Array.isArray(valor) && valor.indexOf(cond.igual) >= 0);
    if ('en' in cond) return cond.en.indexOf(valor) >= 0;
    if ('distinto' in cond) return valor !== cond.distinto;
    return !!valor;
  }

  function actualizar(seccion) {
    seccion.querySelectorAll('[data-visible-si]').forEach(function (el) {
      const cond = JSON.parse(el.dataset.visibleSi);
      const prefijo = el.name.indexOf('-') >= 0 ? el.name.slice(0, el.name.lastIndexOf('-') + 1) : '';
      const ver = cumple(cond, valorDe(seccion, prefijo + cond.campo));
      const caja = el.closest('[data-campo]');
      if (caja) caja.hidden = !ver;
    });
  }

  document.querySelectorAll('[data-seccion]').forEach(function (s) {
    actualizar(s);
    s.addEventListener('change', function () { actualizar(s); });
  });

  // Tablas: «Agregar fila» clona la última fila con índices nuevos
  document.addEventListener('click', function (e) {
    const btn = e.target.closest('[data-agregar-fila]');
    if (!btn) return;
    const cuerpo = document.getElementById(btn.dataset.agregarFila);
    const filas = cuerpo.querySelectorAll('tr');
    const ultima = filas[filas.length - 1];
    const nueva = ultima.cloneNode(true);
    const n = filas.length;
    nueva.querySelectorAll('input, select, textarea').forEach(function (el) {
      el.name = el.name.replace(/__\d+__/, '__' + n + '__');
      if (el.id) el.id = el.id.replace(/__\d+__/, '__' + n + '__');
      if (el.tagName === 'SELECT') el.selectedIndex = 0; else el.value = '';
    });
    cuerpo.appendChild(nueva);
  });

  // Editor de secciones personalizadas (formset): agregar campo, mover y mostrar opciones según el tipo
  const editor = document.getElementById('editor-campos');
  if (editor) {
    const total = document.getElementById('id_campos-TOTAL_FORMS');
    const molde = document.getElementById('molde-campo').innerHTML;
    function opcionesSegunTipo(fila) {
      const tipo = fila.querySelector('[name$="-tipo"]').value;
      fila.querySelectorAll('[data-para]').forEach(function (el) {
        el.hidden = el.dataset.para.split(' ').indexOf(tipo) < 0;
      });
    }
    function renumerar() {
      editor.querySelectorAll('.js-campo').forEach(function (fila, i) {
        const orden = fila.querySelector('[name$="-orden"]'); if (orden) orden.value = i;
      });
    }
    editor.querySelectorAll('.js-campo').forEach(opcionesSegunTipo);
    renumerar();
    editor.addEventListener('change', function (e) {
      if (e.target.name && e.target.name.endsWith('-tipo')) opcionesSegunTipo(e.target.closest('.js-campo'));
    });
    document.getElementById('agregar-campo').addEventListener('click', function () {
      const n = parseInt(total.value, 10);
      const div = document.createElement('div');
      div.innerHTML = molde.replace(/__prefix__/g, n);
      const fila = div.firstElementChild;
      editor.appendChild(fila);
      total.value = n + 1;
      opcionesSegunTipo(fila); renumerar();
      fila.querySelector('[name$="-etiqueta"]').focus();
    });
    editor.addEventListener('click', function (e) {
      const b = e.target.closest('[data-mover]');
      if (!b) return;
      const fila = b.closest('.js-campo');
      if (b.dataset.mover === 'arriba' && fila.previousElementSibling) fila.parentNode.insertBefore(fila, fila.previousElementSibling);
      if (b.dataset.mover === 'abajo' && fila.nextElementSibling) fila.parentNode.insertBefore(fila.nextElementSibling, fila);
      renumerar();
    });
  }
})();
