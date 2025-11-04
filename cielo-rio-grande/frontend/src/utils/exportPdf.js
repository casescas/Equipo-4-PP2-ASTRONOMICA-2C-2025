// exportPdf.js
// Requisitos: jspdf (^2.x) y html2canvas (^1.4+)
// npm i jspdf html2canvas

import jsPDF from "jspdf";
import html2canvas from "html2canvas";

/**
 * Exporta un nodo del DOM a PDF con paginado automático y encabezado/pie,
 * permitiendo ajustar calidad, DPI, y formato de imagen.
 *
 * @param {Object} opts
 * @param {HTMLElement} opts.node           // Nodo raíz a exportar (obligatorio)
 * @param {string} [opts.filename='export.pdf']
 * @param {string} [opts.header]            // Texto de encabezado (opcional)
 * @param {string} [opts.footer]            // Texto de pie (opcional)
 * @param {'p'|'l'} [opts.orientation='p']  // Portrait o Landscape
 * @param {string} [opts.pageSize='a4']     // a4, letter, etc.
 * @param {number} [opts.margin=12]         // Margen en mm
 * @param {number} [opts.maxScale=3]        // Límite del DPR (3 = alta calidad)
 * @param {boolean} [opts.useCORS=true]     // Habilitar CORS para imágenes
 * @param {boolean} [opts.printBackground=true] // Capturar fondos (Tailwind)
 * @param {number} [opts.headerGap=6]       // Espacio extra bajo header (mm)
 * @param {number} [opts.footerGap=6]       // Espacio extra sobre footer (mm)
 * @param {boolean} [opts.numberPages=true] // Mostrar numeración
 * @param {string} [opts.imgType='image/png'] // Tipo de imagen (PNG o JPEG)
 * @param {number} [opts.imgQuality=0.98]     // Calidad JPEG (si aplica)
 * @param {number} [opts.targetDpi]           // DPI objetivo (ej. 192, 240, 300)
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
    maxScale = 3,
    useCORS = true,
    printBackground = true,
    headerGap = 6,
    footerGap = 6,
    numberPages = true,
    imgType = "image/png",
    imgQuality = 0.98,
    targetDpi,
  } = opts;

  if (!node) throw new Error("exportNodeToPdf: 'node' es requerido");

  // 1️⃣ Esperar fuentes para evitar saltos visuales
  try { await document.fonts?.ready; } catch {}

  // 2️⃣ Congelar animaciones para evitar parpadeos
  const freeze = freezeAnimations(node);

  // 3️⃣ Calcular DPR efectivo según targetDpi (96dpi CSS base)
  const cssDpi = 96;
  const requestedScale = targetDpi ? targetDpi / cssDpi : (window.devicePixelRatio || 1);
  const dpr = Math.min(requestedScale, maxScale);

  // 4️⃣ Asegurar un id temporal si el nodo no tiene
  const hadId = typeof node.id === "string" && node.id.trim().length > 0;
  const tempId = `export-${Date.now()}`;
  if (!hadId) node.id = tempId;

  let canvas;
  try {
    // 5️⃣ Renderizar el nodo con html2canvas
    canvas = await html2canvas(node, {
      scale: dpr,
      useCORS,
      allowTaint: false,
      backgroundColor: getComputedStyle(document.body).backgroundColor || "#ffffff",
      logging: false,
      windowWidth: node.scrollWidth,
      scrollX: 0,
      scrollY: -window.scrollY,
      removeContainer: true,
      onclone: (doc) => {
        // Evita querySelector("#") inválido
        const targetId = node.id && node.id.trim().length ? node.id : null;
        const cloned = targetId ? doc.getElementById(targetId) : doc.body;
        if (cloned && cloned.style) {
          cloned.style.transform = "none";
          cloned.style.maxHeight = "none";
        }
        if (printBackground) {
          doc.documentElement.style.background = getComputedStyle(document.documentElement).background || "";
          doc.body.style.background = getComputedStyle(document.body).background || "";
        }
      },
    });
  } finally {
    if (!hadId) node.removeAttribute("id");
  }

  // 6️⃣ Crear PDF
  const pdf = new jsPDF({ orientation, unit: "mm", format: pageSize, compress: true });
  const pageW = pdf.internal.pageSize.getWidth();
  const pageH = pdf.internal.pageSize.getHeight();

  const topMargin = margin + (header ? headerGap : 0);
  const bottomMargin = margin + (footer ? footerGap : 0);
  const contentWmm = pageW - margin * 2;
  const contentHmm = pageH - topMargin - bottomMargin;

  const imgWpx = canvas.width;
  const imgHpx = canvas.height;

  const pxPerMm = imgWpx / contentWmm;
  const sliceHpx = Math.max(1, Math.floor(contentHmm * pxPerMm));
  const pages = Math.max(1, Math.ceil(imgHpx / sliceHpx));

  // 7️⃣ Generar cada página del PDF
  for (let i = 0; i < pages; i++) {
    if (i > 0) pdf.addPage();

    const sy = i * sliceHpx;
    const sh = Math.min(sliceHpx, imgHpx - sy);

    // Canvas temporal
    const pageCanvas = document.createElement("canvas");
    pageCanvas.width = imgWpx;
    pageCanvas.height = sh;

    const ctx = pageCanvas.getContext("2d");
    if (ctx) {
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = "high";
      ctx.drawImage(canvas, 0, sy, imgWpx, sh, 0, 0, imgWpx, sh);
    }

    const dataUrl = pageCanvas.toDataURL(imgType, imgQuality);

    // Encabezado
    if (header) {
      pdf.setFontSize(10);
      pdf.setTextColor(60);
      pdf.text(header, margin, margin);
    }

    // Imagen
    pdf.addImage(
      dataUrl,
      imgType === "image/png" ? "PNG" : "JPEG",
      margin,
      topMargin,
      contentWmm,
      sh / pxPerMm,
      undefined,
      "FAST"
    );

    // Pie
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

  // 8️⃣ Guardar PDF
  pdf.save(filename);

  // 9️⃣ Restaurar animaciones
  freeze.restore?.();
}

/**
 * Desactiva animaciones/transiciones para mejorar nitidez en la captura.
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

  const prevTransform = root.style.transform;
  root.style.transform = "none";

  return {
    restore: () => {
      const s = document.querySelector('style[data-export-pdf-freeze="true"]');
      if (s) s.remove();
      root.style.transform = prevTransform || "";
    },
  };
}
