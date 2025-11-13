// frontend/src/App.js
import React, { useState, useEffect } from 'react';
import api from './services/api';

function App() {
  const [status, setStatus] = useState('Conectando a la API...');
  const [error, setError] = useState('');

  useEffect(() => {
    // Vamos a probar la conexión a la API.
    // Esta ruta (api-static) la definimos en nginx.conf.
    // Si da 200, significa que Nginx y el volumen de estáticos de Django funcionan.
    api.get('/api-static/admin/css/base.css')
      .then(response => {
        setStatus('¡Conexión de Nginx a Backend (Estáticos) exitosa!');
      })
      .catch(err => {
        setError('Error conectando API. Revisa los logs de Nginx.');
        console.error(err);
      });
  }, []);

  return (
    <div style={{ padding: '2em', fontFamily: 'monospace', color: '#eee' }}>
      <h1>Broker NUAM Frontend</h1>
      <p>
        Si ves esto, React está funcionando.
      </p>
      <hr />
      <p>Estado de la API: {status}</p>
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
    </div>
  );
}

export default App;