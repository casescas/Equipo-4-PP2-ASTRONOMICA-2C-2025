import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { exportNodeToPdf } from "../utils/exportPdf";

// =================== Config ===================
const API = "http://127.0.0.1:8000/historial";

const CAT_COLORS = {
  SCT: "#22d3ee",
  BKN: "#60a5fa",
  OVC: "#06b6d4",
  FEW: "#a78bfa",
  SKC: "#93c5fd",
};

const CAT_DESC = {
  SCT: "Nubes dispersas",
  BKN: "Muy nublado",
  OVC: "Cubierto",
  FEW: "Poco nublado",
  SKC: "Despejado",
};

const MESES_ES = [
  "enero","febrero","marzo","abril","mayo","junio",
  "julio","agosto","septiembre","octubre","noviembre","diciembre"
];

// =================== Helpers ===================
const isYMD = (s) => typeof s === "string" && /^\d{4}-\d{2}-\d{2}$/.test(s);

function toYMD(date) {
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 10);
}
function ymdOffset(days, baseYmd) {
  const d = baseYmd ? new Date(baseYmd) : new Date();
  d.setDate(d.getDate() + days);
  return toYMD(d);
}
function toDateArg(iso) {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}
function toDM(ymd) {
  const [y, m, d] = ymd.split("-");
  return `${d}/${m}`;
}
function weekStartYMDFrom(date) {
  const d = new Date(date);
  const day = d.getDay(); // 0=dom..6=sáb
  const diffToMonday = (day + 6) % 7;
  d.setDate(d.getDate() - diffToMonday);
  return toYMD(d);
}
function monthKeyFrom(date) {
  const d = new Date(date);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  return `${y}-${m}`;
}
function monthStartEndFromParts(year, month01to12) {
  const y = Number(year);
  const m = Number(month01to12);
  const start = new Date(y, m - 1, 1);
  const endExclusive = new Date(y, m, 1);
  const endInclusive = new Date(endExclusive);
  endInclusive.setDate(endInclusive.getDate() - 1);
  return { from: toYMD(start), to: toYMD(endInclusive), toExclusive: toYMD(endExclusive) };
}
function monthLabelES(ym) {
  const [y, m] = ym.split("-");
  return `${MESES_ES[Number(m) - 1]} ${y}`;
}

// CSV
function toCsvText(headers, rows) {
  const esc = (v) => {
    const s = String(v ?? "");
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const headerLine = headers.map(esc).join(",");
  const body = rows.map((r) => r.map(esc).join(",")).join("\n");
  return "\ufeff" + headerLine + "\n" + body;
}
function downloadBlob({ blob, filename }) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

/* ======== Regresión lineal ======== */
function withTrend(data, xKey, yKey) {
  if (!data.length) return [];
  const n = data.length;
  const xs = data.map((d) => Number(d[xKey]));
  const ys = data.map((d) => Number(d[yKey]));
  const sumX = xs.reduce((a, b) => a + b, 0);
  const sumY = ys.reduce((a, b) => a + b, 0);
  const sumXY = xs.reduce((a, x, i) => a + x * ys[i], 0);
  const sumXX = xs.reduce((a, x) => a + x * x, 0);
  const denom = n * sumXX - sumX * sumX;
  const b = denom === 0 ? 0 : (n * sumXY - sumX * sumY) / denom;
  const a = (sumY - b * sumX) / n;
  return data.map((d) => ({ ...d, trend: Number((a + b * Number(d[xKey])).toFixed(2)) }));
}

/* ======== Tooltip custom del donut ======== */
function DonutTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const p = payload[0];
  const name = p?.name ?? "";
  const value = p?.value ?? 0;
  const desc = CAT_DESC[name] || "—";
  return (
    <div
      style={{
        background: "rgba(2,6,23,0.95)",
        border: "1px solid #334155",
        padding: "6px 10px",
        borderRadius: 8,
        color: "#e5e7eb",
        fontSize: 12,
        boxShadow: "0 6px 24px rgba(0,0,0,0.35)",
        pointerEvents: "none",
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 2 }}>{name} — {desc}</div>
      <div style={{ opacity: 0.9 }}>{value} registros</div>
    </div>
  );
}

/* ========= Línea MEMOIZADA (no “salta” con hover del donut) ========= */
const StableLineChart = React.memo(
  function StableLineChart({ data, modo, ticksReduced, xTickFormatter }) {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 32 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#263244" />
          <XAxis
            dataKey={modo === "dia" ? "x" : "label"}
            ticks={ticksReduced}
            stroke="#a0b9d9"
            tickMargin={8}
            tickLine={false}
            minTickGap={10}
            angle={0}
            textAnchor="middle"
            tickFormatter={xTickFormatter}
          />
          <YAxis stroke="#a0b9d9" domain={[0, 8]} allowDecimals={false} ticks={[0,1,2,3,4,5,6,7,8]} />
          <Tooltip contentStyle={{ backgroundColor: "#111827", border: "none" }} labelStyle={{ color: "#60a5fa" }} />
          <Line type="monotone" dataKey="y" stroke="#22d3ee" strokeWidth={2} dot />
          <Line type="linear" dataKey="trend" stroke="#b3a7ff" strokeDasharray="5 6" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    );
  },
  (prev, next) => {
    // Evita re-render si el hover del donut cambia estados ajenos a estos props
    const sameData = prev.data === next.data;
    const sameModo = prev.modo === next.modo;
    const sameFormatter = prev.xTickFormatter === next.xTickFormatter;
    const sameTicks =
      Array.isArray(prev.ticksReduced) &&
      Array.isArray(next.ticksReduced) &&
      prev.ticksReduced.length === next.ticksReduced.length &&
      prev.ticksReduced.every((v, i) => v === next.ticksReduced[i]);
    return sameData && sameModo && sameFormatter && sameTicks;
  }
);

// =================== Componente ===================
export default function Dashboard() {
  const [modo, setModo] = useState("dia"); // dia | semana | mes | rango
  const [dia, setDia] = useState(toYMD(new Date()));
  const [desde, setDesde] = useState(ymdOffset(-7));
  const [hasta, setHasta] = useState(toYMD(new Date()));

  // Mes/Año
  const now = new Date();
  const [selectedYear, setSelectedYear] = useState(now.getFullYear());
  const [selectedMonth, setSelectedMonth] = useState(now.getMonth() + 1); // 1..12
  const [monthRange, setMonthRange] = useState({ from: "", to: "", toExclusive: "" });

  // Datos
  const [raw, setRaw] = useState([]);
  const [rawGlobal, setRawGlobal] = useState([]);
  const [loading, setLoading] = useState(false);

  // Hover donut ↔ cards
  const [hoveredCat, setHoveredCat] = useState(null);

  const exportRef = useRef(null);

  const vizHeight = 340;
  const donutSize = 220;

  // ----- Global KPIs -----
  useEffect(() => {
    const fetchGlobal = async () => {
      try {
        const res = await fetch(API);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        const items = json?.items && Array.isArray(json.items) ? json.items : [];
        setRawGlobal(items);
      } catch {
        setRawGlobal([]);
      }
    };
    fetchGlobal();
  }, []);

  // Al entrar en MES o cambiar mes/año → fija 1..último día
  useEffect(() => {
    if (modo !== "mes") return;
    const r = monthStartEndFromParts(selectedYear, selectedMonth);
    setMonthRange(r);
    setDesde(r.from);
    setHasta(r.to); // guardo inclusive para mostrar/CSV; para API uso toExclusive
  }, [modo, selectedYear, selectedMonth]);

  // ----- Fetch filtrado (server) -----
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const url = new URL(API);
        if (modo === "dia") {
          url.searchParams.set("desde", dia);
          url.searchParams.set("hasta", dia);
        } else if (modo === "mes") {
          const r = monthRange.from ? monthRange : monthStartEndFromParts(selectedYear, selectedMonth);
          url.searchParams.set("desde", r.from);
          // Ventana half-open para incluir último día
          url.searchParams.set("hasta", r.toExclusive);
        } else {
          if (isYMD(desde)) url.searchParams.set("desde", desde);
          if (isYMD(hasta)) {
            const d = new Date(hasta);
            d.setDate(d.getDate() + 1); // incluir “hasta” inclusive
            url.searchParams.set("hasta", toYMD(d));
          }
        }
        const res = await fetch(url.toString());
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        const items = json?.items && Array.isArray(json.items) ? json.items : [];
        setRaw(items);
      } catch {
        setRaw([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [modo, dia, desde, hasta, selectedYear, selectedMonth, monthRange]);

  /* ======== FILTRO LOCAL EXTRA (garantiza 1..fin de mes) ======== */
  const filteredRaw = useMemo(() => {
    if (!raw?.length) return [];

    if (modo === "mes") {
      const r = monthRange.from ? monthRange : monthStartEndFromParts(selectedYear, selectedMonth);
      // [from, toExclusive)
      return raw.filter((x) => {
        const ymd = (x?.fecha_captura || "").slice(0, 10);
        return ymd >= r.from && ymd < r.toExclusive;
      });
    }

    if (modo === "rango" || modo === "semana") {
      const endPlusOne = (() => {
        const d = new Date(hasta);
        d.setDate(d.getDate() + 1);
        return toYMD(d);
      })();
      return raw.filter((x) => {
        const ymd = (x?.fecha_captura || "").slice(0, 10);
        return ymd >= desde && ymd < endPlusOne;
      });
    }

    if (modo === "dia") {
      return raw.filter((x) => (x?.fecha_captura || "").slice(0, 10) === dia);
    }

    return raw;
  }, [raw, modo, dia, desde, hasta, monthRange, selectedYear, selectedMonth]);

  // ======== SERIES ========
  // Serie por hora (modo día)
  const serieHoras = useMemo(() => {
    if (modo !== "dia") return [];
    const buckets = Array.from({ length: 24 }, (_, h) => ({
      h, hourLabel: `${String(h).padStart(2, "0")}:00`, count: 0, sum: 0,
    }));
    filteredRaw.forEach((r) => {
      const ts = new Date(r?.fecha_captura);
      if (isNaN(ts)) return;
      const h = ts.getHours();
      const v = Number(r?.octas_predichas);
      if (!Number.isFinite(v)) return;
      buckets[h].count++; buckets[h].sum += v;
    });
    const arr = buckets.map((b) => ({
      x: b.h, label: b.hourLabel, y: b.count ? Number((b.sum / b.count).toFixed(2)) : 0,
    }));
    return withTrend(arr, "x", "y");
  }, [filteredRaw, modo]);

  // Serie agregada:
  // - rango: por día
  // - semana: por lunes de la semana
  // - mes: por DÍA del mes (01..fin de mes)
  const serieAgregada = useMemo(() => {
    if (modo === "dia") return [];

    if (modo === "mes") {
      const start = new Date(selectedYear, selectedMonth - 1, 1);
      const end = new Date(selectedYear, selectedMonth, 0); // último día
      const daysInMonth = end.getDate();

      const dailyBuckets = Array.from({ length: daysInMonth }, (_, i) => ({
        x: i + 1,
        label: `${String(i + 1).padStart(2, "0")}-${String(selectedMonth).padStart(2, "0")}`,
        count: 0,
        sum: 0,
      }));

      filteredRaw.forEach((r) => {
        const d = new Date(r.fecha_captura);
        const day = d.getDate();
        const v = Number(r.octas_predichas);
        if (Number.isFinite(v) && day >= 1 && day <= daysInMonth) {
          dailyBuckets[day - 1].count++;
          dailyBuckets[day - 1].sum += v;
        }
      });

      const arr = dailyBuckets.map((b) => ({
        x: b.x,
        label: b.label,
        y: b.count ? Number((b.sum / b.count).toFixed(2)) : 0,
      }));
      return withTrend(arr, "x", "y");
    }

    // Semana / Rango
    const group = new Map();
    filteredRaw.forEach((r) => {
      const ymd = (r?.fecha_captura || "").slice(0, 10);
      if (!ymd) return;
      const v = Number(r?.octas_predichas);
      if (!Number.isFinite(v)) return;
      let key;
      if (modo === "rango") key = ymd;
      else if (modo === "semana") key = weekStartYMDFrom(ymd);
      else key = monthKeyFrom(ymd);
      if (!group.has(key)) group.set(key, { sum: 0, count: 0 });
      const b = group.get(key);
      b.sum += v; b.count++;
    });

    const arr = Array.from(group.entries())
      .sort(([a], [b]) => (a < b ? -1 : 1))
      .map(([k, { sum, count }], idx) => ({
        key: k, x: idx, label: k, y: count ? Number((sum / count).toFixed(2)) : 0,
      }));

    return withTrend(arr, "x", "y");
  }, [filteredRaw, modo, selectedMonth, selectedYear]);

  const series = modo === "dia" ? serieHoras : serieAgregada;

  // ======== Donut + diccionario ========
  const donutData = useMemo(() => {
    const m = new Map();
    filteredRaw.forEach((r) => {
      const cat = (r?.categoria || "N/D").trim();
      if (!m.has(cat)) m.set(cat, 0);
      m.set(cat, m.get(cat) + 1);
    });
    return Array.from(m.entries())
      .filter(([k]) => k in CAT_COLORS)
      .sort((a, b) => b[1] - a[1])
      .map(([name, value]) => ({ name, value }));
  }, [filteredRaw]);

  // ======== Tabla ========
  const tablaResumen = useMemo(() => {
    const build = (lista, keyExtractor) => {
      const m = new Map();
      for (const r of lista) {
        const ymd = (r?.fecha_captura || "").slice(0, 10);
        if (!ymd) continue;
        const key = keyExtractor(ymd);
        if (!m.has(key)) m.set(key, []);
        m.get(key).push(r);
      }
      return Array.from(m.entries())
        .sort(([a], [b]) => (a < b ? -1 : 1))
        .map(([key, rows]) => {
          const octas = rows.map((x) => Number(x?.octas_predichas)).filter(Number.isFinite);
          const avg = octas.length ? octas.reduce((a, b) => a + b, 0) / octas.length : 0;

          const confVals = rows
            .map((x) => Number(x?.confianza ?? x?.confidence ?? x?.score ?? x?.probabilidad))
            .filter(Number.isFinite);
          const confAvg = confVals.length ? confVals.reduce((a, b) => a + b, 0) / confVals.length : 0;
          const confPct = confAvg <= 1 ? Math.round(confAvg * 100) : Math.round(confAvg);

          const freq = rows.reduce((acc, x) => {
            const c = (x?.categoria || "N/D").trim();
            acc[c] = (acc[c] || 0) + 1;
            return acc;
          }, {});
          const sorted = Object.entries(freq).sort((a, b) => b[1] - a[1]);
          const [catDom] = sorted[0] || ["N/D", 0];
          const faStr = sorted.map(([c, v]) => `${c}: ${v}`).join(" · ");

          let keyLabel;
          if (modo === "mes") keyLabel = monthLabelES(key);
          else if (modo === "semana") {
            const lunes = key;
            const domingo = ymdOffset(6, key);
            keyLabel = `${toDateArg(lunes)} — ${toDateArg(domingo)}`;
          } else keyLabel = toDateArg(key);

          return {
            key,
            keyLabel,
            promedio: Number(avg.toFixed(2)),
            pct: Number(((avg / 8) * 100).toFixed(0)),
            confPct,
            catDom,
            descDom: CAT_DESC[catDom] || "—",
            faStr,
            count: rows.length,
          };
        });
    };

    if (modo === "dia") return build(filteredRaw, (ymd) => ymd);
    if (modo === "rango") return build(filteredRaw, (ymd) => ymd);
    if (modo === "semana") return build(filteredRaw, (ymd) => weekStartYMDFrom(ymd));
    if (modo === "mes") {
      const monthKeySel = `${selectedYear}-${String(selectedMonth).padStart(2, "0")}`;
      return build(filteredRaw, (ymd) => monthKeyFrom(ymd)).filter((r) => r.key === monthKeySel);
    }
    return [];
  }, [filteredRaw, modo, selectedMonth, selectedYear]);

  // ======== KPIs ========
  const kpis = useMemo(() => {
    const src = rawGlobal;
    if (!src.length) return { totalImgs: 0, avgPredTime: 0.05, avgOctas: 0, avgConf: 0 };
    const totalImgs = src.length;
    const avgPredTime = 0.05;
    const octas = src.map((r) => Number(r?.octas_predichas)).filter(Number.isFinite);
    const avgOctas = octas.length ? Number((octas.reduce((a, b) => a + b, 0) / octas.length).toFixed(2)) : 0;
    const confs = src
      .map((r) => Number(r?.confianza ?? r?.confidence ?? r?.score ?? r?.probabilidad))
      .filter(Number.isFinite);
    const confAvgRaw = confs.length ? confs.reduce((a, b) => a + b, 0) / confs.length : 0;
    const avgConf = confAvgRaw <= 1 ? Math.round(confAvgRaw * 100) : Math.round(confAvgRaw);
    return { totalImgs, avgPredTime, avgOctas, avgConf };
  }, [rawGlobal]);

  // ======== Export ========
  const handleExportPdf = async () => {
    const titulo =
      modo === "dia"
        ? `Analíticas — Día ${dia}`
        : modo === "rango"
        ? `Analíticas — Rango ${desde} a ${hasta}`
        : `Analíticas — ${modo[0].toUpperCase() + modo.slice(1)}`;
    await exportNodeToPdf({
      node: exportRef.current,
      filename: `Analitica_${modo === "dia" ? dia : modo}.pdf`,
      header: titulo,
      footer: "Proyecto Cielo Río Grande • generado automáticamente",
    });
  };
  const handleExportCsv = () => {
    const headers = [
      modo === "mes" ? "Mes" : modo === "semana" ? "Semana (del — al)" : "Fecha",
      "Prom. Octas","% Nubosidad","Conf. prom.","Categoría Dom.","Descripción Dom.","Frec. Abs. categoría","Registros",
    ];
    const rows = tablaResumen.map((r) => [r.keyLabel, r.promedio, `${r.pct}%`, `${r.confPct}%`, r.catDom, r.descDom, r.faStr, r.count]);
    const csv = toCsvText(headers, rows);
    downloadBlob({ blob: new Blob([csv], { type: "text/csv;charset=utf-8" }), filename: `Resumen_${modo}_${new Date().toISOString().slice(0, 10)}.csv` });
  };
  const handleExportExcel = async () => {
    const XLSX = await import("xlsx");
    const data = tablaResumen.map((r) => ({
      [modo === "mes" ? "Mes" : modo === "semana" ? "Semana (del — al)" : "Fecha"]: r.keyLabel,
      "Prom. Octas": r.promedio, "% Nubosidad": r.pct, "Conf. prom.": r.confPct,
      "Categoría Dom.": r.catDom, "Descripción Dom.": r.descDom, "Frec. Abs. categoría": r.faStr, Registros: r.count,
    }));
    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Resumen");
    const wbout = XLSX.write(wb, { bookType: "xlsx", type: "array" });
    downloadBlob({
      blob: new Blob([wbout], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=utf-8" }),
      filename: `Resumen_${modo}_${new Date().toISOString().slice(0, 10)}.xlsx`,
    });
  };

  // ======== Eje X (memoizados para referencia estable) ========
  const MAX_TICKS = 8;

  const xTickFormatter = useMemo(() => {
    if (modo === "dia") return (v) => `${String(v).padStart(2, "0")}:00`;
    if (modo === "semana" || modo === "rango") return (v) => toDM(v);
    return (v) => v; // en mes usamos "dd-mm" ya armado en label
  }, [modo]);

  const ticksReduced = useMemo(() => {
    if (modo === "dia") {
      const xs = series.map((d) => d.x);
      return xs.filter((_, i) => i % 2 === 0);
    } else {
      const labels = series.map((d) => d.label);
      const step = Math.max(1, Math.ceil(labels.length / MAX_TICKS));
      return labels.filter((_, i) => i % step === 0);
    }
  }, [series, modo]);

  return (
    <div ref={exportRef} className="bg-gray-800/60 rounded-2xl p-6 shadow-lg border border-cyan-800">
      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6 justify-items-center">
        <Kpi title="Total Imágenes Procesadas" value={kpis.totalImgs} />
        <Kpi title="Tiempo de Predicción Prom." value={`${kpis.avgPredTime} s`} />
        <Kpi title="Octas Global Prom." value={kpis.avgOctas} />
        <Kpi title="Confianza Promedio" value={`${kpis.avgConf}%`} />
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap items-center gap-3 mb-2">
        <ModeButton label="Día" active={modo === "dia"} onClick={() => setModo("dia")} />
        <ModeButton label="Semana" active={modo === "semana"} onClick={() => setModo("semana")} />
        <ModeButton label="Mes" active={modo === "mes"} onClick={() => setModo("mes")} />
        <ModeButton label="Rango" active={modo === "rango"} onClick={() => setModo("rango")} />

        {modo === "dia" && (
          <input type="date" className="bg-gray-900 text-white rounded px-2 py-1 ml-2" value={dia} onChange={(e) => setDia(e.target.value)} />
        )}

        {(modo === "semana" || modo === "rango") && (
          <div className="flex items-center gap-2">
            <div>
              <label className="text-sm text-gray-300 mr-2">Desde</label>
              <input type="date" className="bg-gray-900 text-white rounded px-2 py-1" value={desde} onChange={(e) => setDesde(e.target.value)} />
            </div>
            <div>
              <label className="text-sm text-gray-300 mr-2">Hasta</label>
              <input type="date" className="bg-gray-900 text-white rounded px-2 py-1" value={hasta} onChange={(e) => setHasta(e.target.value)} />
            </div>
          </div>
        )}

        {modo === "mes" && (
          <>
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-300">Mes</label>
              <select className="bg-gray-900 text-white rounded px-2 py-1" value={selectedMonth} onChange={(e) => setSelectedMonth(Number(e.target.value))}>
                {MESES_ES.map((m, idx) => (
                  <option key={m} value={idx + 1}>{m}</option>
                ))}
              </select>

              <label className="text-sm text-gray-300 ml-2">Año</label>
              <select className="bg-gray-900 text-white rounded px-2 py-1" value={selectedYear} onChange={(e) => setSelectedYear(Number(e.target.value))}>
                {Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i).map((y) => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
            {!!monthRange.from && !!monthRange.to && (
              <div className="text-xs text-gray-400 ml-2">
                Período: {toDateArg(monthRange.from)} — {toDateArg(monthRange.to)}
              </div>
            )}
          </>
        )}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-12 gap-6">
        {/* Línea 3/4 */}
        <div className="col-span-12 lg:col-span-9 bg-gray-900 border border-cyan-800 rounded-xl p-4 flex flex-col">
          <h4 className="text-sm text-gray-300 mb-2 text-center">
            {modo === "dia" ? "Octas por hora"
            : modo === "rango" ? "Promedio de octas por día"
            : modo === "semana" ? "Promedio semanal de octas"
            : "Promedio mensual de octas"}
          </h4>
          <div className="flex-1 flex justify-center items-center" style={{ height: vizHeight }}>
            <StableLineChart
              data={series}
              modo={modo}
              ticksReduced={ticksReduced}
              xTickFormatter={xTickFormatter}
            />
          </div>
        </div>

        {/* Donut 1/4 */}
        <div className="col-span-12 lg:col-span-3 bg-gray-900 border border-cyan-800 rounded-xl p-4">
          <h4 className="text-sm text-gray-300 mb-2 text-center">Distribución de categorías</h4>
          <div className="flex justify-center">
            <PieChart width={donutSize} height={donutSize}>
              <Tooltip content={<DonutTooltip />} />
              <Pie
                data={donutData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={58}
                outerRadius={88}
                paddingAngle={2}
                onMouseEnter={(e) => setHoveredCat(e?.name ?? null)}
                onMouseLeave={() => setHoveredCat(null)}
              >
                {donutData.map((d, i) => (
                  <Cell
                    key={i}
                    fill={CAT_COLORS[d.name] || "#999"}
                    fillOpacity={hoveredCat && hoveredCat !== d.name ? 0.4 : 1}
                    stroke={hoveredCat === d.name ? "#a78bfa" : "transparent"}
                    strokeWidth={hoveredCat === d.name ? 2 : 0}
                  />
                ))}
              </Pie>
            </PieChart>
          </div>

          {/* Diccionario */}
          <div className="mt-4 grid grid-cols-1 gap-3 justify-items-center">
            {donutData.map((d, idx) => {
              const isLastOdd = donutData.length % 2 === 1 && idx === donutData.length - 1;
              const desc = CAT_DESC[d.name] || "—";
              const active = hoveredCat === d.name;
              return (
                <div
                  key={d.name}
                  title={`${d.name} — ${desc}: ${d.value} registros`}
                  onMouseEnter={() => setHoveredCat(d.name)}
                  onMouseLeave={() => setHoveredCat(null)}
                  className={
                    `bg-gray-800/70 border rounded-lg p-3 flex items-start gap-3 w-full transition
                     ${isLastOdd ? "justify-self-center" : ""}
                     ${active ? "border-cyan-300 ring-2 ring-cyan-300/40 shadow-md shadow-cyan-900/30" : "border-cyan-800"}`
                  }
                >
                  <span
                    className="mt-1 inline-block rounded-sm"
                    style={{ width: 12, height: 12, background: CAT_COLORS[d.name] || "#999" }}
                  />
                  <div className="text-sm">
                    <div className={`font-medium ${active ? "text-cyan-200" : "text-gray-200"}`}>
                      {d.name} — {desc}
                    </div>
                    <div className={`${active ? "text-cyan-300" : "text-gray-400"}`}>
                      {d.value} registros
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* TABLA */}
      <div className="mt-6">
        <h3 className="text-lg font-semibold text-gray-300 mb-2">Resumen</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-gray-300 border-t border-gray-700">
            <thead>
              <tr className="text-cyan-400">
                <th className="text-left py-2 px-2">
                  {modo === "mes" ? "Mes" : modo === "semana" ? "Semana (del — al)" : "Fecha"}
                </th>
                <th className="text-right py-2 px-2">Prom. Octas</th>
                <th className="text-right py-2 px-2">% Nubosidad</th>
                <th className="text-right py-2 px-2">Conf. prom.</th>
                <th className="text-left py-2 px-2">Categoría Dom.</th>
                <th className="text-left py-2 px-2">Descripción Dom.</th>
                <th className="text-left py-2 px-2">Frec. Abs. categoría</th>
                <th className="text-right py-2 px-2">Registros</th>
              </tr>
            </thead>
            <tbody>
              {tablaResumen.map((r) => (
                <tr key={r.key} className="border-t border-gray-700">
                  <td className="py-2 px-2">{r.keyLabel}</td>
                  <td className="text-right py-2 px-2">{r.promedio}</td>
                  <td className="text-right py-2 px-2">{r.pct}%</td>
                  <td className="text-right py-2 px-2">{r.confPct}%</td>
                  <td className="py-2 px-2">{r.catDom}</td>
                  <td className="py-2 px-2">{r.descDom}</td>
                  <td className="py-2 px-2">{r.faStr}</td>
                  <td className="text-right py-2 px-2">{r.count}</td>
                </tr>
              ))}
              {!tablaResumen.length && !loading && (
                <tr><td colSpan={8} className="py-4 text-center text-gray-500">No hay datos para el período seleccionado.</td></tr>
              )}
              {loading && (
                <tr><td colSpan={8} className="py-4 text-center text-gray-500">Cargando…</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Export */}
        <div className="flex flex-wrap justify-center gap-3 mt-6">
          <button onClick={handleExportPdf} className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-md shadow-md transition">📄 PDF</button>
          <button onClick={handleExportCsv} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-md shadow-md transition">🧾 CSV</button>
          <button onClick={handleExportExcel} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md shadow-md transition">📊 Excel</button>
        </div>
      </div>
    </div>
  );
}

/* =================== Subcomponentes =================== */
function Kpi({ title, value }) {
  return (
    <div className="bg-gray-900 border border-cyan-800 rounded-xl p-5 text-center shadow w-full">
      <h4 className="text-sm text-gray-400">{title}</h4>
      <p className="text-4xl font-semibold text-cyan-300 mt-1">{value}</p>
    </div>
  );
}

function ModeButton({ label, active, onClick }) {
  return (
    <button
      className={`px-3 py-1.5 rounded-md text-sm ${active ? "bg-cyan-600 hover:bg-cyan-500" : "bg-gray-700 hover:bg-gray-600"}`}
      onClick={onClick}
    >
      {label}
    </button>
  );
}
