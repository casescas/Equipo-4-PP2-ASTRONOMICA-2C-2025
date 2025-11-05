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
  <div className="w-full">
    {/* Fila superior: 2 columnas iguales */}
    <div className="grid grid-cols-2 gap-6 items-end">
      {/* Radiación actual */}
      <div className="pr-6 border-r border-white/10">
        <p className="uppercase text-[11px] tracking-[.18em] text-slate-400 mb-1">
          Radiación Actual
        </p>
        <p className="tabular-nums leading-none">
          <span className="text-4xl md:text-4xl font-extrabold text-white align-baseline">
            {radiacion_solar_w_m2 ?? 'N/D'}
          </span>
          <span className="ml-2 text-sm font-medium text-slate-400 align-baseline">W/m²</span>
        </p>
      </div>

      {/* Índice UV */}
      <div className="pl-6">
        <p className="uppercase text-[11px] tracking-[.18em] text-slate-400 mb-1">
          Índice UV
        </p>
      <div className="flex items-baseline gap-2">
        <p className={`tabular-nums leading-none text-4xl md:text-4xl font-extrabold ${uvColor}`}>
      {uv_index != null ? uv_index.toFixed(1) : 'N/D'}
        </p>
        <p className={`text-base font-semibold ${uvColor}`}>
      {uvRating}
         </p>
    </div>
  </div>
</div>


    {/* Separador sutil */}
    <hr className="my-4 border-white/10" />

    {/* Fila inferior: Máx. Diaria (a lo ancho) */}
    <div className="grid grid-cols-2 items-baseline">
      <p className="uppercase text-[11px] tracking-[.18em] text-slate-400">
        Máx. diaria: 
      </p>
      <p className="tabular-nums text-right leading-none">
        <span className="text-base font-semibold text-white">
          {max_radiacion_w_m2 ?? 'N/D'}
        </span>
        <span className="ml-1 text-xs font-medium text-slate-400 align-baseline">W/m²</span>
        {max_radiacion_hora && (
          <span className="ml-2 italic text-slate-400 text-xs">({max_radiacion_hora} hs)</span>
        )}
      </p>
    </div>
  </div>
);

};

export default RadiationCard;