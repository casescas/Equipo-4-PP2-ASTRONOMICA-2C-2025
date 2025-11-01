// exportPdf.js
// Requisitos: jspdf (^2.x) y html2canvas (^1.4+)
// npm i jspdf html2canvas

import jsPDF from "jspdf";
import html2canvas from "html2canvas";

/**
 * Exporta un nodo del DOM a PDF con paginado automático y encabezado/pie.
 *
 * @param {Object} opts
 * @param {HTMLElement} opts.node           // Nodo raíz a exportar (obligatorio)
 * @param {string} [opts.filename='export.pdf']
 * @param {string} [opts.header]            // Texto de encabezado (opcional)
 * @param {string} [opts.footer]            // Texto de pie (opcional)
 * @param {'p'|'l'} [opts.orientation='p']  // Portrait o Landscape
 * @param {string} [opts.pageSize='a4']     // a4, letter, etc.
 * @param {number} [opts.margin=12]         // Margen en mm (aplica a los 4 lados)
 * @param {number} [opts.maxScale=2]        // Límite para DPR efectivo (2 = buena calidad sin matar memoria)
 * @param {boolean} [opts.useCORS=true]     // Habilitar CORS para imágenes
 * @param {boolean} [opts.printBackground=true] // Capturar fondos (Tailwind, etc.)
 * @param {number} [opts.headerGap=6]       // Espacio extra bajo header en mm
 * @param {number} [opts.footerGap=6]       // Espacio extra sobre footer en mm
 * @param {boolean} [opts.numberPages=true] // Mostrar "pág. X de Y" en el pie
 */
export async function exportNodeToPdf(opts = {}) {
  const {
    node,
    filename = "export.pdf",
    header,
    footer,
    orientation = "p",
    pageSize = "a4",
    margin = 12,
    maxScale = 2,
    useCORS = true,
    printBackground = true,
    headerGap = 6,
    footerGap = 6,
    numberPages = true,
  } = opts;

  if (!node) throw new Error("exportNodeToPdf: 'node' es requerido");

  // 1) Esperar fuentes web → evita “salto” de tipografías y borrosidad
  await document.fonts?.ready?.catch(() => {});

  // 2) Congelar animaciones/transiciones durante el render para evitar parpadeos
  const freeze = freezeAnimations(node);

  // 3) Calcular scale efectivo (DPR capado)
  const dpr = Math.min(window.devicePixelRatio || 1, maxScale);

  // 4) Render a canvas con html2canvas
  const canvas = await html2canvas(node, {
    scale: dpr,
    useCORS,
    allowTaint: false,
    backgroundColor: getComputedStyle(document.body).backgroundColor || "#ffffff",
    logging: false,
    windowWidth: node.scrollWidth, // asegura ancho completo
    scrollX: 0,
    scrollY: -window.scrollY,
    removeContainer: true,
    onclone: (doc) => {
      // Opcional: fuerzo el nodo a "width:auto" y sin transform para evitar recortes
      const cloned = doc.querySelector(`#${node.id}`) || doc.body;
      cloned.style.transform = "none";
      cloned.style.maxHeight = "none";
    },
  });

  // 5) Crear PDF y convertir mm ⇄ px
  const pdf = new jsPDF({ orientation, unit: "mm", format: pageSize, compress: true });
  const pageW = pdf.internal.pageSize.getWidth();
  const pageH = pdf.internal.pageSize.getHeight();

  // Área útil descontando márgenes + header/footer
  const topMargin = margin + (header ? headerGap : 0);
  const bottomMargin = margin + (footer ? footerGap : 0);
  const contentWmm = pageW - margin * 2;
  const contentHmm = pageH - topMargin - bottomMargin;

  // Dimensiones canvas en px
  const imgWpx = canvas.width;
  const imgHpx = canvas.height;

  // Escala para que el canvas quepa en el ancho util del PDF
  const pxPerMm = imgWpx / contentWmm; // cuántos px hay en 1 mm al ajustar al ancho
  const sliceHmm = contentHmm;         // alto util por página (mm)
  const sliceHpx = Math.floor(sliceHmm * pxPerMm);

  // 6) Cortar el canvas en “tiras” por página para evitar escalados extremos
  const pages = Math.ceil(imgHpx / sliceHpx);
  const imgType = "image/jpeg"; // JPEG suele pesar menos que PNG
  const imgQuality = 0.92;

  for (let i = 0; i < pages; i++) {
    if (i > 0) pdf.addPage();

    const sy = i * sliceHpx;                      // origen Y en px
    const sh = Math.min(sliceHpx, imgHpx - sy);   // alto de la tira en px

    // Canvas temporal con la “tira”
    const pageCanvas = document.createElement("canvas");
    pageCanvas.width = imgWpx;
    pageCanvas.height = sh;
    const ctx = pageCanvas.getContext("2d", { willReadFrequently: false });
    // Recorta la porción
    ctx.drawImage(canvas, 0, sy, imgWpx, sh, 0, 0, imgWpx, sh);

    // Convertir a dataURL
    const dataUrl = pageCanvas.toDataURL(imgType, imgQuality);

    // 7) Encabezado
    if (header) {
      pdf.setFontSize(10);
      pdf.setTextColor(60);
      pdf.text(header, margin, margin);
    }

    // 8) Imagen en página
    pdf.addImage(
      dataUrl,
      "JPEG",
      margin,
      topMargin,
      contentWmm,
      (sh / pxPerMm), // alto en mm proporcional
      undefined,
      "FAST"          // Hint de compresión
    );

    // 9) Pie de página + numeración
    const bottomY = pageH - margin;
    if (footer || numberPages) {
      pdf.setFontSize(9);
      pdf.setTextColor(80);
      const leftText = footer || "";
      const rightText = numberPages ? `pág. ${i + 1} de ${pages}` : "";
      if (leftText) pdf.text(leftText, margin, bottomY, { align: "left" });
      if (rightText) pdf.text(rightText, pageW - margin, bottomY, { align: "right" });
    }
  }

  // 10) Descargar
  pdf.save(filename);

  // 11) Restaurar estilos
  freeze.restore?.();
}

/**
 * Desactiva transiciones/animaciones en el subárbol para capturar más nítido.
 * Devuelve un objeto con restore().
 */
function freezeAnimations(root) {
  const style = document.createElement("style");
  style.setAttribute("data-export-pdf-freeze", "true");
  style.textContent = `
    * {
      transition: none !important;
      animation: none !important;
      caret-color: transparent !important;
    }
  `;
  document.head.appendChild(style);

  // Tailwind a veces usa transform/translate para animar
  const prev = root.style.transform;
  root.style.transform = "none";

  return {
    restore: () => {
      const s = document.querySelector('style[data-export-pdf-freeze="true"]');
      if (s) s.remove();
      root.style.transform = prev || "";
    },
  };
}
