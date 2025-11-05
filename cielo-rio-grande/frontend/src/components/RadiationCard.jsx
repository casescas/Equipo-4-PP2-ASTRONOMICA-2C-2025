import React from 'react';

const RadiationCard = ({ clima }) => {
  const {
    radiacion_solar_w_m2,
    max_radiacion_w_m2,
    max_radiacion_hora,
    uv_index,
    error_radiacion
  } = clima;

  let uvColor = 'text-gray-500';
  let uvRating = 'N/D';
  if (uv_index !== null) {
    if (uv_index < 3) { uvColor = 'text-green-500'; uvRating = 'Bajo'; }
    else if (uv_index < 6) { uvColor = 'text-yellow-500'; uvRating = 'Moderado'; }
    else if (uv_index < 8) { uvColor = 'text-orange-500'; uvRating = 'Alto'; }
    else { uvColor = 'text-red-600'; uvRating = 'Muy Alto'; }
  }

  if (error_radiacion) {
    return (
      <div className="bg-red-100 border border-red-400 rounded-xl text-red-700 shadow-md col-span-full p-4">
        <p className="font-bold mb-1">Radiación Solar y UV ⚠️</p>
        <p>Error al obtener datos locales: {error_radiacion}</p>
      </div>
    );
  }

  // 👇 sin p-3; dejá que el padding lo aporte <Card>
  return (
    <>
      <div className="grid grid-cols-2 gap-3">
        <div className="border-r border-white/10 pr-3">
          <p className="text-xs font-semibold text-slate-400">Radiación Actual</p>
          <p className="text-2xl font-black text-white">
            {radiacion_solar_w_m2 || 'N/D'}
            <span className="text-sm font-normal text-slate-400"> W/m²</span>
          </p>
        </div>

        <div className="pl-3">
          <p className="text-xs font-semibold text-slate-400">Índice UV</p>
          <p className={`text-2xl font-black ${uvColor}`}>
            {uv_index != null ? uv_index.toFixed(1) : 'N/D'}
          </p>
          <p className={`text-sm font-bold ${uvColor}`}>{uvRating}</p>
        </div>
      </div>

      <hr className="my-3 border-white/10" />

      <div className="flex justify-between text-xs text-slate-300">
        <span className="font-medium">Máx. Diaria:</span>
        <span className="font-bold text-white">
          {max_radiacion_w_m2 || 'N/D'} W/m²
          {max_radiacion_hora && <span className="ml-1 italic text-slate-400">({max_radiacion_hora} hs)</span>}
        </span>
      </div>
    </>
  );
};

export default RadiationCard;