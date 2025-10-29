export default function UltimasCapturas({ rows, limit = 8 }) {
  const last = [...rows].slice(-limit).reverse();
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
      <h3 className="text-lg font-semibold mb-3">Últimas capturas</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {last.map((r) => (
          <a key={r.id} href={r.url_imagen} target="_blank" rel="noreferrer"
             className="block bg-gray-800 rounded-lg overflow-hidden border border-gray-700">
            <img src={r.url_imagen} alt={r.descripcion || r.categoria} className="w-full h-28 object-cover" />
            <div className="p-2 text-xs text-gray-300 flex justify-between">
              <span>{r.ymd} {r.hourLabel}</span>
              <span>{r.octas} octas</span>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
