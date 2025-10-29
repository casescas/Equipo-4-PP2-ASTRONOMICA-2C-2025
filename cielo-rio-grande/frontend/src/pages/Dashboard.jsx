import React, { useEffect, useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const API = "http://127.0.0.1:8000/historial";

// Helpers
function toYMD(d) {
  return d.toISOString().slice(0, 10);
}
function ymdOffset(days) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return toYMD(d);
}
const isYMD = (s) => typeof s === "string" && /^\d{4}-\d{2}-\d{2}$/.test(s);

// util moda
const mode = (arr) => {
  const m = new Map();
  let best = null, c = 0;
  for (const x of arr) {
    const v = (m.get(x) || 0) + 1;
    m.set(x, v);
    if (v > c) { best = x; c = v; }
  }
  return best ?? "N/D";
};

export default function Dashboard() {
  // --- Filtros ---
  const [modo, setModo] = useState("dia");
  const [dia, setDia] = useState(toYMD(new Date()));
  const [desde, setDesde] = useState(ymdOffset(-7));
  const [hasta, setHasta] = useState(toYMD(new Date()));

  // --- Datos crudos ---
  const [raw, setRaw] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch según modo
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const url = new URL(API);
        if (modo === "dia") {
          if (isYMD(dia)) {
            url.searchParams.set("desde", dia);
            url.searchParams.set("hasta", dia);
          }
        } else {
          if (isYMD(desde)) url.searchParams.set("desde", desde);
          if (isYMD(hasta)) url.searchParams.set("hasta", hasta);
        }

        const res = await fetch(url.toString());
        if (!res.ok) {
          console.error("HTTP error:", res.status, await res.text());
          setRaw([]);
          return;
        }

        const json = await res.json();
        const items = Array.isArray(json)
          ? json
          : Array.isArray(json.items)
          ? json.items
          : Array.isArray(json.data)
          ? json.data
          : [];

        setRaw(items);
      } catch (e) {
        console.error("Error cargando historial:", e);
        setRaw([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [modo, dia, desde, hasta]);

  // --- Serie 1: Evolución por horas (para 'dia') ---
  const serieHoras = useMemo(() => {
    if (modo !== "dia") return [];
    const buckets = Array.from({ length: 24 }, (_, h) => ({
      h, // 0..23
      hourLabel: `${String(h).padStart(2, "0")}:00`,
      count: 0,
      sum: 0,
    }));

    raw.forEach((r) => {
      const tsStr = r?.fecha_captura ?? "";
      const ts = new Date(tsStr);
      if (!(ts instanceof Date) || isNaN(ts.getTime())) return; // fecha inválida
      const h = ts.getHours();
      const v = Number(r?.octas_predichas);
      // Validaciones fuertes: hora entera 0..23 y valor numérico finito
      if (!Number.isInteger(h) || h < 0 || h > 23) return;
      if (!Number.isFinite(v)) return;

      buckets[h].count += 1;
      buckets[h].sum += v;
    });

    return buckets.map((b) => ({
      h: b.h,
      hourLabel: b.hourLabel,
      octasProm: b.count ? Number((b.sum / b.count).toFixed(2)) : 0,
    }));
  }, [raw, modo]);

  // --- Serie 2: Promedio diario (para 'rango') ---
  const serieDiaria = useMemo(() => {
    if (modo !== "rango") return [];
    const map = new Map();
    raw.forEach((r) => {
      const ymd = (r?.fecha_captura || "").slice(0, 10);
      if (!ymd) return;
      const v = Number(r?.octas_predichas);
      if (!Number.isFinite(v)) return;
      if (!map.has(ymd)) map.set(ymd, { sum: 0, count: 0 });
      const b = map.get(ymd);
      b.sum += v;
      b.count += 1;
    });
    return Array.from(map.entries())
      .sort(([a], [b]) => (a < b ? -1 : 1))
      .map(([fecha, { sum, count }]) => ({
        fecha,
        promedio: count ? Number((sum / count).toFixed(2)) : 0,
      }));
  }, [raw, modo]);

  // --- Resumen por día (detallado) ---
  const tablaResumen = useMemo(() => {
    const agrupar = (arr) => {
      const m = new Map();
      for (const r of arr) {
        const f = (r?.fecha_captura || "").slice(0, 10);
        if (!f) continue;
        if (!m.has(f)) m.set(f, []);
        m.get(f).push(r);
      }
      return Array.from(m.entries()).map(([fecha, lista]) => {
        const octas = lista
          .map(x => Number(x?.octas_predichas))
          .filter(Number.isFinite);
        const avg = octas.length ? octas.reduce((a,b)=>a+b,0)/octas.length : 0;
        const catDom = mode(lista.map(x => x?.categoria || "N/D"));
        const descDom = mode(lista.map(x => (x?.descripcion || "—").trim()));
        return {
          fecha,
          promedio: Number(avg.toFixed(2)),
          pct: Number(((avg/8)*100).toFixed(0)),
          catDom,
          descDom,
          count: lista.length
        };
      });
    };
    if (!raw.length) return [];
    if (modo === "rango") return agrupar(raw);
    // solo el día elegido
    return agrupar(raw.filter(r => (r?.fecha_captura || "").slice(0,10) === dia));
  }, [raw, modo, dia]);

  // --- UI ---
  return (
    <div className="bg-gray-800/60 rounded-2xl p-6 shadow-lg border border-cyan-800">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-6">
        <h2 className="text-xl font-semibold text-cyan-300">
          {modo === "dia"
            ? `Evolución por horas — ${dia}`
            : "Evolución diaria — Promedio de Octas"}
        </h2>

        {/* Controles */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex gap-2">
            <button
              className={`px-3 py-1 rounded-md text-sm ${
                modo === "dia" ? "bg-cyan-600 hover:bg-cyan-500" : "bg-gray-700 hover:bg-gray-600"
              }`}
              onClick={() => setModo("dia")}
            >
              Día
            </button>
            <button
              className={`px-3 py-1 rounded-md text-sm ${
                modo === "rango" ? "bg-cyan-600 hover:bg-cyan-500" : "bg-gray-700 hover:bg-gray-600"
              }`}
              onClick={() => setModo("rango")}
            >
              Rango
            </button>
          </div>

          {modo === "dia" ? (
            <div className="flex items-center gap-2">
              <input
                type="date"
                className="bg-gray-900 text-white rounded px-2 py-1"
                value={dia}
                onChange={(e) => setDia(e.target.value)}
              />
              <button
                className="px-3 py-1 rounded-md text-sm bg-gray-700 hover:bg-gray-600"
                onClick={() => setDia(toYMD(new Date()))}
              >
                Hoy
              </button>
              <button
                className="px-3 py-1 rounded-md text-sm bg-gray-700 hover:bg-gray-600"
                onClick={() => setDia(ymdOffset(-1))}
              >
                Ayer
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <div>
                <label className="text-sm text-gray-300 mr-2">Desde</label>
                <input
                  type="date"
                  className="bg-gray-900 text-white rounded px-2 py-1"
                  value={desde}
                  onChange={(e) => setDesde(e.target.value)}
                />
              </div>
              <div>
                <label className="text-sm text-gray-300 mr-2">Hasta</label>
                <input
                  type="date"
                  className="bg-gray-900 text-white rounded px-2 py-1"
                  value={hasta}
                  onChange={(e) => setHasta(e.target.value)}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* CHART */}
      <div className="w-full h-[320px] min-h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          {modo === "dia" ? (
            <LineChart data={serieHoras} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#263244" />
              <XAxis
                dataKey="h"
                stroke="#a0b9d9"
                type="number"
                domain={[0, 23]}
                ticks={Array.from({ length: 24 }, (_, i) => i)}
                tickFormatter={(v) => `${String(v).padStart(2, "0")}:00`}
              />
              <YAxis
                stroke="#a0b9d9"
                domain={[0, 8]}
                allowDecimals={false}
                ticks={[0,1,2,3,4,5,6,7,8]}
              />
              <Tooltip
                contentStyle={{ backgroundColor: "#111827", border: "none" }}
                labelStyle={{ color: "#60a5fa" }}
                formatter={(v) => [v, "octasProm"]}
                labelFormatter={(v, p) => {
                  const pt = Array.isArray(p) ? p[0]?.payload : p?.payload;
                  return pt?.hourLabel ?? `${String(v).padStart(2, "0")}:00`;
                }}
              />
              <Line type="monotone" dataKey="octasProm" stroke="#38bdf8" strokeWidth={2} dot />
            </LineChart>
          ) : (
            <LineChart data={serieDiaria}>
              <CartesianGrid strokeDasharray="3 3" stroke="#263244" />
              <XAxis dataKey="fecha" stroke="#a0b9d9" />
              <YAxis stroke="#a0b9d9" domain={[0, 8]} allowDecimals={false} ticks={[0,1,2,3,4,5,6,7,8]} />
              <Tooltip
                contentStyle={{ backgroundColor: "#111827", border: "none" }}
                labelStyle={{ color: "#60a5fa" }}
              />
              <Line type="monotone" dataKey="promedio" stroke="#22d3ee" strokeWidth={2} dot />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* TABLA RESUMEN */}
      <div className="mt-6">
        <h3 className="text-lg font-semibold text-gray-300 mb-2">Resumen por día</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-gray-300 border-t border-gray-700">
            <thead>
              <tr className="text-cyan-400">
                <th className="text-left py-2 px-2">Fecha</th>
                <th className="text-right py-2 px-2">Prom. Octas</th>
                <th className="text-right py-2 px-2">% Nubosidad</th>
                <th className="text-left py-2 px-2">Categoría Dom.</th>
                <th className="text-left py-2 px-2">Descripción Dom.</th>
                <th className="text-right py-2 px-2">Registros</th>
              </tr>
            </thead>
            <tbody>
              {tablaResumen.map((r) => (
                <tr key={r.fecha} className="border-t border-gray-700">
                  <td className="py-2 px-2">{r.fecha}</td>
                  <td className="text-right py-2 px-2">{r.promedio}</td>
                  <td className="text-right py-2 px-2">{r.pct}%</td>
                  <td className="py-2 px-2">{r.catDom}</td>
                  <td className="py-2 px-2">{r.descDom}</td>
                  <td className="text-right py-2 px-2">{r.count}</td>
                </tr>
              ))}
              {!tablaResumen.length && !loading && (
                <tr>
                  <td colSpan={6} className="py-4 text-center text-gray-500">
                    No hay datos para el período seleccionado.
                  </td>
                </tr>
              )}
              {loading && (
                <tr>
                  <td colSpan={6} className="py-4 text-center text-gray-500">
                    Cargando…
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
