import { useMemo } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { filterByDateRange } from "../../api/registros";

export default function DistribucionCategorias({ rows, from, to }) {
  const filtered = useMemo(() => filterByDateRange(rows, from, to), [rows, from, to]);
  const counts = useMemo(() => {
    const m = new Map();
    for (const r of filtered) m.set(r.categoria, (m.get(r.categoria)||0)+1);
    return Array.from(m.entries()).map(([name, value]) => ({ name, value }));
  }, [filtered]);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
      <h3 className="text-lg font-semibold mb-3">Distribución por categoría</h3>
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie data={counts} dataKey="value" nameKey="name" outerRadius={90}>
            {counts.map((_, idx) => <Cell key={idx} />)}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
