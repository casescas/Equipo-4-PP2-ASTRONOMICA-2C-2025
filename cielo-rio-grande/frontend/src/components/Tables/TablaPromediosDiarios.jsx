import { useMemo, useState } from "react";
import { filterByDateRange } from "../../api/registros";

// moda genérica
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
      const count = list.length || 0;
      const sumOctas = octasArr.reduce((a,b)=>a+b,0);
      const avg = count ? Number((sumOctas / count).toFixed(2)) : 0;

      const catDom = mode(list.map(x => x.categoria || "N/D"));
      const descDom = mode(list.map(x => (x.descripcion || "").trim() || "—"));

      return {
        ymd,
        count,
        avg,
        min: count ? Math.min(...octasArr) : 0,
        max: count ? Math.max(...octasArr) : 0,
        pct: count ? Number(((avg / 8) * 100).toFixed(0)) : 0, // % de nubosidad promedio
        catDom,
        descDom,
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
              <th className="text-left p-2">Fecha</th>
              <th className="text-right p-2">Prom. octas</th>
              <th className="text-right p-2">% Nubosidad</th>
              <th className="text-right p-2">Mín</th>
              <th className="text-right p-2">Máx</th>
              <th className="text-left p-2">Cat. dominante</th>
              <th className="text-left p-2">Descripción dominante</th>
              <th className="text-right p-2">Registros</th>
              <th className="p-2"></th>
            </tr>
          </thead>
          <tbody>
            {days.map(d => (
              <tr key={d.ymd} className="odd:bg-gray-900 even:bg-gray-950">
                <td className="p-2">{d.ymd}</td>
                <td className="p-2 text-right">{d.avg}</td>
                <td className="p-2 text-right">{d.pct}%</td>
                <td className="p-2 text-right">{d.min}</td>
                <td className="p-2 text-right">{d.max}</td>
                <td className="p-2">{d.catDom}</td>
                <td className="p-2">{d.descDom}</td>
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
