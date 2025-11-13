import React, { useState } from 'react';
import api from '../services/api';
import { Button, Form, Table } from 'react-bootstrap';

function FileUpload({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState([]);

  // Previsualización antes de cargar
  const handlePreview = () => {
    const formData = new FormData();
    formData.append('file', file);
    api.post('/calificaciones/previsualizar-csv/', formData)
      .then(resp => setPreview(resp.data.preview))
      .catch(e => alert('Error previsualizando el archivo'));
  };

  const handleUpload = () => {
    const formData = new FormData();
    formData.append('file', file);
    api.post('/calificaciones/carga-masiva/', formData)
      .then(resp => { onUploaded(); })
      .catch(e => alert('Error en la carga masiva'));
  };

  return (
    <div>
      <Form.File onChange={e => setFile(e.target.files[0])} />
      <Button onClick={handlePreview}>Previsualizar</Button>
      <Button onClick={handleUpload}>Cargar</Button>
      {/* Previsualización tabla */}
      <Table>
         {/* Renderiza la previsualización */}
         <tbody>
            {preview.map((row, idx) => (
              <tr key={idx}>
                {row.map((cell, j) => <td key={j}>{cell}</td>)}
              </tr>
            ))}
         </tbody>
      </Table>
    </div>
  );
}

export default FileUpload;
