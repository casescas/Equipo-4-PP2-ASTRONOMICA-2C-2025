import { useState, useEffect } from "react";

export default function EvolucionSelector({ onChange }) {
  const [mode, setMode] = useState("hoy"); // hoy | ayer | fecha
  const [date, setDate] = useState(() => new Date().toISOString().slice(0,10));

  useEffect(() => {
    if (mode === "hoy") {
      onChange({ mode, date: new Date().toISOString().slice(0,10) });
    } else if (mode === "ayer") {
      const d = new Date(); d.setDate(d.getDate() - 1);
      onChange({ mode, date: d.toISOString().slice(0,10) });
    } else {
      onChange({ mode, date });
    }
  }, [mode, date, onChange]);

  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="inline-flex rounded-lg overflow-hidden border border-gray-700">
        <button className={`px-3 py-2 ${mode==="hoy"?"bg-blue-600":"bg-gray-800 hover:bg-gray-700"}`} onClick={() => setMode("hoy")}>Hoy</button>
        <button className={`px-3 py-2 ${mode==="ayer"?"bg-blue-600":"bg-gray-800 hover:bg-gray-700"}`} onClick={() => setMode("ayer")}>Ayer</button>
        <button className={`px-3 py-2 ${mode==="fecha"?"bg-blue-600":"bg-gray-800 hover:bg-gray-700"}`} onClick={() => setMode("fecha")}>Fecha exacta</button>
      </div>
      {mode === "fecha" && (
        <input type="date" value={date} onChange={e=>setDate(e.target.value)} className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2" />
      )}
    </div>
  );
}
