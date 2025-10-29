// src/App.js
import React, { useState, useEffect } from "react";
import Dashboard from "./pages/Dashboard";

/* ================= Helpers ================= */
const labelCategoria = (c) =>
  ({ SKC: "Despejado", FEW: "Pocas nubes", SCT: "Nubes dispersas", BKN: "Muy nublado", OVC: "Cubierto" }[c] ||
    c ||
    "--");

/* ================= UI Primitives ================= */
const Card = ({ className = "", children }) => (
  <div
    className={[
      "relative rounded-2xl",
      "border border-white/10",
      "bg-[#0b0f15]/90",
      "shadow-[0_6px_18px_rgba(0,0,0,.45),0_1px_0_rgba(255,255,255,.04)_inset]",
      "backdrop-blur-sm p-5",
      className,
    ].join(" ")}
  >
    <div className="pointer-events-none absolute inset-0 rounded-2xl ring-1 ring-white/5" />
    {children}
  </div>
);

/* ================ Gauge (botón) ==================== */
function ConfidenceRing({ value = 0, size = 120, stroke = 12, onClick }) {
  const pct = Math.max(0, Math.min(1, Number(value) || 0));
  const r = (size - stroke) / 2;
  const C = 2 * Math.PI * r;
  const offset = C * (1 - pct);

  return (
    <button
      type="button"
      onClick={onClick}
      title={`Confianza ${Math.round(pct * 100)}%`}
      className="relative grid place-items-center rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/70 active:scale-[0.99] transition"
      style={{ width: size, height: size }}
    >
      <svg className="relative z-10" width={size} height={size} aria-hidden>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,.08)" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={pct >= 0.7 ? "#16a34a" : pct >= 0.5 ? "#eab308" : "#ef4444"}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={C}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset .6s ease" }}
          className="drop-shadow-[0_0_10px_rgba(34,197,94,.35)]"
        />
      </svg>
      <div className="pointer-events-none absolute inset-[18%] rounded-full bg-gradient-to-br from-slate-900/70 to-slate-800/30" />
      {/* OJO: quitamos el porcentaje debajo para no duplicar */}
    </button>
  );
}

/* ================ Tarjeta Cámara ==================== */
function CameraCard({ cameraUrl, fechaActual, clima, octas }) {
  return (
    <div className="relative w-full">
      <figure className="relative w-full aspect-[16/10] overflow-hidden rounded-[22px] bg-[#0a0f16] ring-1 ring-white/10 shadow-[0_10px_30px_rgba(0,0,0,.55),inset_0_0_0_2px_rgba(255,255,255,.04)]">
        <img
          src={cameraUrl}
          alt="Cielo Río Grande"
          className="absolute inset-0 h-full w-full object-cover"
          onError={(e) => (e.currentTarget.style.opacity = 0.25)}
        />
        {/* overlays */}
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(120%_80%_at_50%_10%,rgba(0,0,0,.15),transparent_60%)]" />
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(rgba(255,255,255,0.04)_1px,transparent_1px)] bg-[size:3px_3px]" />

        {/* HUDs con safe padding */}
        <div className="absolute inset-0 p-3 md:p-4">
          <div className="absolute top-2 left-2 md:top-3 md:left-3 text-[12px] md:text-[13px] font-extrabold tracking-[0.22em] text-white/90 drop-shadow-sm">
            GoPro
          </div>

          <div className="absolute top-2 right-2 md:top-3 md:right-3 flex items-center gap-2 px-3 py-1 rounded-full bg-black/70 font-mono text-[10px] md:text-xs font-semibold">
            <span className="h-3 w-3 rounded-full bg-red-500 animate-pulse" />
            <span className="text-red-400 tracking-widest">REC</span>
          </div>

          <div className="absolute left-3 bottom-16 md:bottom-14 rounded-md bg-black/55 px-2 py-1 text-[10px] md:text-[11px] font-mono font-semibold text-slate-200 tracking-wider">
            ISO 400 | f/2.8 | 1/60s | EV 0.0 | 1080p60
          </div>
          <div className="absolute left-3 bottom-5 rounded-md bg-black/65 px-2 py-1 text-[10px] md:text-[11px] font-mono font-semibold text-slate-200 tracking-wider">
            IAP Camera RIOG 53.8°S 67.8°W
          </div>
          <div className="absolute right-3 bottom-5 rounded-md bg-black/65 px-2 py-1 text-[10px] md:text-[11px] font-mono font-semibold text-slate-200 tracking-wider text-right">
            FECHA: {fechaActual}
            <br />
            TEMP: {clima?.temp ?? "--"} °C · NUB: {octas?.octas_predichas ?? "--"} OCTAS
          </div>
        </div>

        <div className="pointer-events-none absolute inset-0 rounded-[22px] ring-1 ring-white/10" />
      </figure>

      <div className="mt-2 ml-1 text-xs tracking-widest font-extrabold text-slate-400/90">HERD 9</div>
    </div>
  );
}

/* ================ Clima Detallado ==================== */
function WeatherDetails({ clima }) {
  const Row = ({ k, v, suf = "" }) => (
    <div className="grid grid-cols-[1fr_auto] items-center py-2 border-b border-white/5 last:border-b-0">
      <div className="text-slate-200">{k}</div>
      <div className="text-right text-slate-50 tabular-nums">{v != null ? `${v}${suf}` : "--"}</div>
    </div>
  );
  return (
    <>
      <h3 className="text-xl font-semibold text-cyan-300 mb-3">Clima Detallado</h3>
      <div className="text-sm">
        <Row k="Temperatura:" v={clima?.temp} suf=" °C" />
        <Row k="Sensación térmica:" v={clima?.feels_like} suf=" °C" />
        <Row k="Humedad:" v={clima?.humedad} suf="%" />
        <Row k="Viento:" v={clima?.viento} suf=" m/s" />
        <Row k="Dirección del viento:" v={clima?.viento_dir} suf="°" />
        <Row k="Presión atmosférica:" v={clima?.presion} suf=" hPa" />
      </div>
    </>
  );
}

/* ================ App ====================== */
export default function App() {
  const [clima, setClima] = useState({});
  const [octas, setOctas] = useState({});
  const [timestamp, setTimestamp] = useState(Date.now());
  const [satImgUrl, setSatImgUrl] = useState(null);
  const [loadingSat, setLoadingSat] = useState(false);

  // tick cada 10 min
  useEffect(() => {
    const it = setInterval(() => setTimestamp(Date.now()), 600000);
    return () => clearInterval(it);
  }, []);

  // fetch clima + octas
  useEffect(() => {
    fetch("http://127.0.0.1:8000/clima").then((r) => r.json()).then(setClima).catch(() => setClima({}));
    fetch("http://127.0.0.1:8000/octas").then((r) => r.json()).then(setOctas).catch(() => setOctas({}));
  }, [timestamp]);

  console.log(octas)
  // cleanup blob
  useEffect(
    () => () => {
      if (satImgUrl) URL.revokeObjectURL(satImgUrl);
    },
    [satImgUrl]
  );

  const cameraUrl = `http://127.0.0.1:8000/imagen?ts=${timestamp}`;
  const fechaActual = new Date(timestamp).toLocaleDateString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    year: "2-digit",
  });

  const coberturaPct =
    octas?.octas_predichas != null ? Math.round((Number(octas.octas_predichas) / 8) * 100) : null;
  const confianzaPct = Math.round((Number(octas?.confianza) || 0) * 100);

  const fetchSatellite = async (layer = "clouds_new") => {
    setLoadingSat(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/satellite?layer=${layer}&ts=${timestamp}`);
      if (!res.ok) throw new Error("No sat image");
      const blob = await res.blob();
      setSatImgUrl(URL.createObjectURL(blob));
    } catch (e) {
      console.error(e);
      setSatImgUrl(null);
    } finally {
      setLoadingSat(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#05060a] to-[#0a0c13] text-white pb-16 font-sans">
      {/* Título principal */}
      <header className="py-6">
        <h1 className="text-center text-4xl lg:text-6xl font-extrabold tracking-tight text-balance">
          <span className="bg-gradient-to-r from-cyan-400 via-blue-300 to-violet-400 bg-clip-text text-transparent">
            ☁️ Nubosidad Río Grande
          </span>
        </h1>
        <p className="mt-2 text-center text-sm text-slate-400">
          Actualizado: {new Date(timestamp).toLocaleTimeString("es-AR")}
        </p>
      </header>

      <main className="max-w-7xl mx-auto px-4 space-y-8">
        {/* ===== Tarjeta Cámara + Métricas ===== */}
        <Card>
          <div className="grid grid-cols-1 xl:grid-cols-[720px_1fr] gap-8 items-center">
            {/* Cámara */}
            <CameraCard cameraUrl={cameraUrl} fechaActual={fechaActual} clima={clima} octas={octas} />

            {/* Métricas: mini-tarjetas */}
            <div className="flex flex-col gap-5">
              <h2 className="text-3xl lg:text-4xl font-extrabold leading-tight text-sky-50">
                Modelo de Clasificación de Nubes
              </h2>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {/* Cobertura */}
                <div className="bg-[#121821]/90 p-4 rounded-xl border border-white/10">
                  <p className="uppercase text-[11px] tracking-[.18em] text-slate-400">Cobertura</p>
                  <p className="text-4xl font-extrabold mt-1">
                    {coberturaPct != null ? `${coberturaPct}%` : "--"}
                  </p>
                </div>

                {/* Tipo dominante */}
                <div className="bg-[#121821]/90 p-4 rounded-xl border border-white/10 col-span-2">
                  <p className="uppercase text-[11px] tracking-[.18em] text-slate-400">Tipo dominante</p>
                  <p className="text-2xl font-bold mt-1">
                    {octas?.categoria || "--"} — {labelCategoria(octas?.categoria)}
                  </p>
                </div>

                {/* Oktas (centrado) */}
                <div className="bg-[#121821]/90 p-4 rounded-xl border border-white/10">
                  <p className="uppercase text-[11px] tracking-[.18em] text-slate-400">Oktas</p>
                  <div className="h-24 flex items-center justify-center">
                    <span className="text-4xl font-extrabold">{octas?.octas_predichas ?? "--"}</span>
                  </div>
                </div>

                {/* Confianza (gauge botón + texto a la derecha; sin % debajo) */}
                <div className="bg-[#121821]/90 p-4 rounded-xl border border-white/10 col-span-2">
                  <p className="uppercase text-[11px] tracking-[.18em] text-slate-400 mb-2">Confianza</p>
                  <div className="flex items-center gap-4">
                    <ConfidenceRing value={Number(octas?.confianza || 0)} onClick={() => {}} />
                    <div className="text-slate-300">
                      <div className="text-xs uppercase tracking-[.18em] text-slate-400">Valor</div>
                      <div className="text-lg font-semibold">{confianzaPct}%</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Etiqueta técnica */}
              <p className="text-[11px] text-slate-400/80">
                Modelo: <span className="text-slate-300">600EPOC — CNN (Keras)</span> · Inferencia local
              </p>
            </div>
          </div>
        </Card>

        {/* ===== Abajo: Clima (izq) + Radar (der) ===== */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Clima Detallado (mejor alineado) */}
          <Card>
            <WeatherDetails clima={clima} />
          </Card>

          {/* Satélite / Radar */}
          <Card className="bg-gradient-to-br from-[#0c0f14]/90 to-[#131821]/90">
            <h3 className="text-lg font-semibold text-cyan-300 mb-3">🛰️ Satélite / Radar</h3>

            <div className="relative rounded-xl overflow-hidden border border-cyan-300/10 bg-[radial-gradient(1200px_400px_at_10%_0,rgba(0,255,255,.08),transparent_40%)]">
              {satImgUrl ? (
                <img src={satImgUrl} alt="Radar" className="h-60 w-full object-cover" />
              ) : (
                <div className="h-60 w-full grid place-items-center text-[11px] tracking-[.2em] text-cyan-100/80">
                  RADAR PREVIEW — tocá “Ver Nubes”
                </div>
              )}
              <div className="absolute left-2 top-2 rounded-md border border-white/10 bg-black/50 px-2 py-1 text-[11px] tracking-widest text-cyan-100 backdrop-blur">
                RADAR PREVIEW
              </div>
            </div>

            <div className="mt-3 flex justify-center gap-3">
              <button
                className="rounded-lg bg-gradient-to-br from-sky-600 to-sky-700 px-4 py-2 font-bold shadow hover:scale-[1.02] transition disabled:opacity-60"
                onClick={() => fetchSatellite("clouds_new")}
                disabled={loadingSat}
              >
                {loadingSat ? "Cargando..." : "Ver Nubes"}
              </button>
              <button
                className="rounded-lg bg-slate-800 px-4 py-2 font-semibold shadow hover:bg-slate-700 transition disabled:opacity-60"
                onClick={() => setSatImgUrl(null)}
                disabled={loadingSat || !satImgUrl}
              >
                Limpiar
              </button>
            </div>
          </Card>
        </section>

        {/* ===== Dashboard ===== */}
        <section className="px-1 pt-8">
          <h3 className="text-center text-3xl md:text-4xl font-extrabold mb-6">
            <span className="align-middle mr-2"></span>
            <span className="bg-gradient-to-r from-cyan-400 via-blue-300 to-violet-400 bg-clip-text text-transparent">
              Analíticas de Nubosidad – Evolución y Comportamiento
            </span>
          </h3>
           <Dashboard />
        </section>
      </main>
    </div>
  );
}
