import React, { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [clima, setClima] = useState({});
  const [octas, setOctas] = useState({});
  const [timestamp, setTimestamp] = useState(Date.now());
  const [satImgUrl, setSatImgUrl] = useState(null);
  const [showSatellite, setShowSatellite] = useState(false);
  const [loadingSat, setLoadingSat] = useState(false);

  // Actualizar imagen y clima cada 10 minutos
  useEffect(() => {
    const interval = setInterval(() => setTimestamp(Date.now()), 600000);
    return () => clearInterval(interval);
  }, []);

  // Obtener clima
  useEffect(() => {
    fetch("http://127.0.0.1:8000/clima")
      .then((res) => res.json())
      .then((data) => setClima(data))
      .catch(() => setClima({}));
  }, [timestamp]);

  // Obtener octas
  useEffect(() => {
    fetch("http://127.0.0.1:8000/octas")
      .then((res) => res.json())
      .then((data) => setOctas(data))
      .catch(() => setOctas({}));
  }, [timestamp]);

  const cameraUrl = `http://127.0.0.1:8000/imagen?ts=${timestamp}`;

  const fetchSatellite = async (layer = "clouds_new") => {
    setLoadingSat(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/satellite?layer=${layer}&ts=${timestamp}`);
      if (!res.ok) throw new Error("No sat image");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setSatImgUrl(url);
    } catch (e) {
      console.error("Error al obtener satélite:", e);
      setSatImgUrl(null);
    } finally {
      setLoadingSat(false);
    }
  };

  useEffect(() => {
    if (showSatellite) fetchSatellite();
    return () => {
      if (satImgUrl) URL.revokeObjectURL(satImgUrl);
    };
  }, [showSatellite, timestamp]);

  return (
    <div className="App">
      <h1 className="title">☁️ Nubosidad Río Grande</h1>

      <div className="dashboard">
        <div className="left-column">
          <div className="image-wrapper">
            <img src={cameraUrl} alt="Cielo Río Grande" className="sky-image" />
            <div className="hud-left">
              <div className="hud-row">⏱️ {new Date(timestamp).toLocaleTimeString()}</div>
            </div>
          </div>

          <div className="controls">
            <button className="btn" onClick={() => setShowSatellite((s) => !s)}>
              {showSatellite ? "Cerrar Satélite" : "Ver Satélite / Radar"}
            </button>

            <div className="small-metrics">
              <div>🌡️ {clima.temp ?? "--"} °C</div>
              <div>💧 {clima.humedad ?? "--"}%</div>
              <div>🌬️ {clima.viento ?? "--"} m/s</div>
            </div>
          </div>
        </div>

        <div className="right-column">
          {/* Clima Detallado */}
          <div className={`weather-panel ${clima.nubosidad_api > 80 ? "high-nubosidad" : ""} ${clima.viento > 10 ? "high-viento" : ""}`}>
            <h2>🌤️ Clima Detallado</h2>
            <div className="weather-item">🌡️ Temp: {clima.temp ?? "--"} °C</div>
            <div className="weather-item">🤖 Sensación: {clima.feels_like ?? "--"} °C</div>
            <div className="weather-item">💧 Humedad: {clima.humedad ?? "--"}%</div>
            <div className="weather-item">🌬️ Viento: {clima.viento ?? "--"} m/s</div>
            <div className="weather-item">🧭 Dir. viento: {clima.viento_dir ?? "--"}°</div>
            <div className="weather-item">🧭 Presión: {clima.presion ?? "--"} hPa</div>
          </div>

          {/* Octas */}
          <div className="weather-panel">
            <h2>☁️ Modelo Predicción de Nubosidad</h2>
            <div className="weather-item">Octas Predichas: {octas.octas_predichas ?? "--"}</div>
            <div className="weather-item">Confianza: {octas.confianza ?? "--"}</div>
            <div className="weather-item">Categoría: {octas.categoria ?? "--"}</div>
            <div className="weather-item">Descripción: {octas.descripcion ?? "--"}</div>
          </div>

          {/* Satélite */}
          <div className="sat-info">
            <h3>🛰️ Satélite / Radar</h3>
            <div className="sat-controls">
              <button className="btn-ghost" onClick={() => fetchSatellite("clouds_new")}>Nubes</button>
            </div>

            {loadingSat && <div className="loading">Cargando satélite...</div>}

            {satImgUrl && (
              <div className="sat-thumb">
                <img src={satImgUrl} alt="Satélite" />
                <div className="sat-caption">Fuente: OpenWeatherMap tiles (proxy)</div>
              </div>
            )}

            {!satImgUrl && !loadingSat && <div className="hint">Presioná "Nubes" para cargar imagen satelital</div>}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
