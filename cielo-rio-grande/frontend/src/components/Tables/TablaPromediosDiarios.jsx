import { useMemo, useState } from "react";
import { filterByDateRange } from "../../api/registros";

// Clasificación según promedio de octas (basada en esquema WMO)
function categorizeByAvgOctas(o) {
  if (!Number.isFinite(o)) return { cat: "N/D", desc: "—" };
  if (o <= 0.5)  return { cat: "SKC", desc: "Despejado (0/8)" };
  if (o <= 2.5)  return { cat: "FEW", desc: "Poco nublado (1–2/8)" };
  if (o <= 5.5)  return { cat: "SCT", desc: "Nubes dispersas (3–5/8)" };
  if (o <= 7.5)  return { cat: "BKN", desc: "Muy nublado (6–7/8)" };
  return { cat: "OVC", desc: "Cubierto (8/8)" };
}

// moda genérica (la dejamos para otros usos)
function mode(arr) {
  const freq = new Map();
  let best = null, bestC = 0;
  for (const x of arr) {
    const c = (freq.get(x) || 0) + 1;
    freq.set(x, c);
    if (c > bestC) { best = x; bestC = c; }
  }
  return best ?? "N/D";
}

function groupDaily(rows) {
  const map = new Map();
  for (const r of rows) {
    if (!map.has(r.ymd)) map.set(r.ymd, []);
    map.get(r.ymd).push(r);
  }

  return Array.from(map.entries())
    .map(([ymd, list]) => {
      const octasArr = list.map(x => Number(x.octas || 0));
      const confArr = list
        .map(x => Number(x.confianza ?? x.confidence ?? x.score ?? x.probabilidad))
        .filter(Number.isFinite);

      const count = list.length || 0;
      const sumOctas = octasArr.reduce((a,b)=>a+b,0);
      const avg = count ? Number((sumOctas / count).toFixed(2)) : 0;

      const confAvgRaw = confArr.length ? confArr.reduce((a,b)=>a+b,0) / confArr.length : 0;
      const confPct = confAvgRaw <= 1 ? Math.round(confAvgRaw * 100) : Math.round(confAvgRaw);

      // Clasificación derivada del PROMEDIO diario
      const { cat: catAvg, desc: descAvg } = categorizeByAvgOctas(avg);

      // Frecuencia absoluta de categorías individuales del día
      const faMap = list.reduce((acc, x) => {
        const c = (x.categoria || "N/D").trim();
        acc[c] = (acc[c] || 0) + 1;
        return acc;
      }, {});
      const faStr = Object.entries(faMap)
        .sort((a,b)=>b[1]-a[1])
        .map(([k,v]) => `${k}: ${v}`)
        .join(" · ");

      return {
        ymd,
        count,
        avg,
        min: count ? Math.min(...octasArr) : 0,
        max: count ? Math.max(...octasArr) : 0,
        pct: count ? Number(((avg / 8) * 100).toFixed(0)) : 0, // % nubosidad promedio
        catAvg,
        descAvg,
        faStr,
        confPct,
      };
    })
    .sort((a,b) => a.ymd.localeCompare(b.ymd));
}

export default function TablaPromediosDiarios({ rows, onPickDay }) {
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");

  const filtered = useMemo(
    () => filterByDateRange(rows, from || undefined, to || undefined),
    [rows, from, to]
  );
  const days = useMemo(() => groupDaily(filtered), [filtered]);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
      <div className="flex items-end gap-3 mb-3">
        <div>
          <label className="block text-sm text-gray-400">Desde</label>
          <input
            type="date"
            value={from}
            onChange={(e)=>setFrom(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-400">Hasta</label>
          <input
            type="date"
            value={to}
            onChange={(e)=>setTo(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2"
          />
        </div>
      </div>

      <div className="overflow-auto max-h-[420px]">
        <table className="min-w-full text-sm">
          <thead className="sticky top-0 bg-gray-800">
            <tr>
              <th className="text-left p-2 text-cyan-400 font-semibold">Fecha</th>
              <th className="text-right p-2 text-cyan-400 font-semibold">Prom. Octas</th>
              <th className="text-right p-2 text-cyan-400 font-semibold">% Nubosidad</th>
              <th className="text-right p-2 text-cyan-400 font-semibold">Conf. prom.</th>
              <th className="text-left p-2 text-cyan-400 font-semibold">Categoría Dom.</th>
              <th className="text-left p-2 text-cyan-400 font-semibold">Descripción Dom.</th>
              <th className="text-left p-2 text-cyan-400 font-semibold">Frec. ABS categoría</th>
              <th className="text-right p-2 text-cyan-400 font-semibold">Registros</th>
              <th className="p-2"></th>
            </tr>
          </thead>
          <tbody>
            {days.map(d => (
              <tr key={d.ymd} className="odd:bg-gray-900 even:bg-gray-950">
                <td className="p-2">{d.ymd}</td>
                <td className="p-2 text-right">{d.avg}</td>
                <td className="p-2 text-right">{d.pct}%</td>
                <td className="p-2 text-right">{d.confPct}%</td>
                <td className="p-2">{d.catAvg}</td>
                <td className="p-2">{d.descAvg}</td>
                <td className="p-2">{d.faStr}</td>
                <td className="p-2 text-right">{d.count}</td>
                <td className="p-2 text-right">
                  <button
                    onClick={() => onPickDay?.(d.ymd)}
                    className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 rounded-lg"
                  >
                    Ver evolución
                  </button>
                </td>
              </tr>
            ))}
            {!days.length && (
              <tr>
                <td className="p-3 text-gray-400" colSpan={9}>
                  Sin datos para el rango seleccionado.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
