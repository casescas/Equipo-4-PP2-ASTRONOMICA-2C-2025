import { useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { filterByDateRange } from "../../api/registros";

export default function ConfianzaPorHora({ rows, from, to }) {
  const filtered = useMemo(() => filterByDateRange(rows, from, to), [rows, from, to]);
  const byHour = useMemo(() => {
    const map = new Map();
    for (const r of filtered) {
      if (!map.has(r.hour)) map.set(r.hour, []);
      map.get(r.hour).push(r.confianza);
    }
    return Array.from({ length: 24 }, (_, h) => {
      const arr = map.get(h) || [];
      const avg = arr.length ? arr.reduce((a,b)=>a+b,0)/arr.length : 0;
      return { hour: `${h.toString().padStart(2,"0")}:00`, confianza: Number((avg*100).toFixed(1)) };
    });
  }, [filtered]);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
      <h3 className="text-lg font-semibold mb-3">Confianza promedio por hora (%)</h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={byHour}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="hour" />
          <YAxis domain={[0,100]} />
          <Tooltip formatter={(v)=>`${v}%`} />
          <Bar dataKey="confianza" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
