// api/registros.js
const BASE = "http://127.0.0.1:8000";

/** Normaliza a 'YYYY-MM-DD' o devuelve undefined si no matchea */
function normalizeToYMD(input) {
  if (!input) return undefined;

  // Date -> YYYY-MM-DD
  if (input instanceof Date && !isNaN(input.valueOf())) {
    return input.toISOString().slice(0, 10);
  }

  if (typeof input === "string") {
    // Si viene 'YYYY-MM-DDTHH:mm:ss...' -> recorto antes de la "T"
    const tIdx = input.indexOf("T");
    const maybeYmd = (tIdx > 0 ? input.slice(0, tIdx) : input).trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(maybeYmd)) return maybeYmd;
  }

  return undefined;
}

/**
 * fetchRegistros({ desde, hasta })
 * - Envía SIEMPRE YYYY-MM-DD (sin horas) y nunca params vacíos.
 * - Tolera payload: [], {items:[]}, {data:[]}.
 * - Evita corrimientos por timezone: parsea ymd/hora directo del string.
 */
export async function fetchRegistros({ desde, hasta } = {}) {
  const ymdDesde = normalizeToYMD(desde);
  const ymdHasta = normalizeToYMD(hasta);

  const params = new URLSearchParams();
  if (ymdDesde) params.set("desde", ymdDesde);
  if (ymdHasta) params.set("hasta", ymdHasta);

  const url = `${BASE}/historial${params.toString() ? `?${params.toString()}` : ""}`;

  const res = await fetch(url);
  if (!res.ok) {
    const msg = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${res.statusText} - ${msg}`);
  }

  const json = await res.json();

  // Acepta: array directo, {items:[]}, {data:[]}
  const items = Array.isArray(json)
    ? json
    : Array.isArray(json.items)
    ? json.items
    : Array.isArray(json.data)
    ? json.data
    : [];

  return items
    .map((r) => {
      const s = String(r.fecha_hora_prediccion ?? ""); // ej: '2025-10-27T13:40:00'
      const ymd = s.slice(0, 10);                      // 'YYYY-MM-DD'
      const hhStr = s.slice(11, 13);                   // 'HH'
      const hh = /^\d{2}$/.test(hhStr) ? parseInt(hhStr, 10) : 0;

      return {
        id: r.id,
        tsRaw: s,                                      // timestamp raw sin tocar (evita tz-shift)
        ymd,
        hour: hh,
        hourLabel: `${String(hh).padStart(2, "0")}:00`,
        octas: Number(r.octas_predichas ?? 0),
        confianza: Number(r.confianza ?? 0),
        categoria: r.categoria ?? "N/D",
        descripcion: r.descripcion ?? "",
        url_imagen: r.url_imagen ?? "",
      };
    })
    // ordenar por timestamp crudo (ISO asc)
    .sort((a, b) => (a.tsRaw < b.tsRaw ? -1 : a.tsRaw > b.tsRaw ? 1 : 0));
}

/** Filtro client-side por rango de fechas (YYYY-MM-DD) */
export function filterByDateRange(rows, fromYmd, toYmd) {
  if (!fromYmd && !toYmd) return rows;
  return rows.filter((r) => {
    if (fromYmd && r.ymd < fromYmd) return false;
    if (toYmd && r.ymd > toYmd) return false;
    return true;
  });
}
