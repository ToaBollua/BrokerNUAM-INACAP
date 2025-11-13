// frontend/src/components/QualificationForm.js
import React, { useState, useEffect } from 'react';
import api from '../services/api'; // Asumiendo que tienes un 'api.js' como en tus otros archivos
import { useNavigate, useParams } from 'react-router-dom';
import { Form, Button } from 'react-bootstrap';

function QualificationForm({ qualificationId, onSave }) {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    instrumento: '',
    fecha_pago: '',
    factor_8: 0.0,
    // ... Agrega aquí el resto de los 29 factores ...
  });

  useEffect(() => {
    // Si pasamos un ID, es para editar. Lo cargamos.
    if (qualificationId && qualificationId !== 'nuevo') {
      api.get(`/calificaciones/${qualificationId}/`)
        .then(res => {
          setFormData(res.data);
        })
        .catch(e => alert("Error cargando la calificación para editar"));
    } else {
      // Si es 'nuevo', reseteamos el formulario
      setFormData({
        instrumento: '',
        fecha_pago: '',
        factor_8: 0.0,
        // ... resetea los demás factores ...
      });
    }
  }, [qualificationId]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (qualificationId === 'nuevo') {
        // Crear
        await api.post('/calificaciones/', formData);
      } else {
        // Actualizar
        await api.put(`/calificaciones/${qualificationId}/`, formData);
      }
      onSave(); // Llama a la función onSave (que debería recargar la tabla)
    } catch (error) {
      alert('Error guardando la calificación');
      console.error(error.response.data); // Muestra el error del backend
    }
  };

  return (
    <div>
      <h2>{qualificationId === 'nuevo' ? 'Ingresar Nueva' : 'Modificar'} Calificación</h2>
      <Form onSubmit={handleSubmit}>
        <Form.Group>
          <Form.Label>Instrumento</Form.Label>
          <Form.Control
            type="text"
            name="instrumento"
            value={formData.instrumento}
            onChange={handleChange}
            required
          />
        </Form.Group>

        <Form.Group>
          <Form.Label>Fecha de Pago</Form.Label>
          <Form.Control
            type="date"
            name="fecha_pago"
            value={formData.fecha_pago}
            onChange={handleChange}
            required
          />
        </Form.Group>

        <Form.Group>
          <Form.Label>Factor 8</Form.Label>
          <Form.Control
            type="number"
            step="0.000000001" // Precisión de 9 decimales
            name="factor_8"
            value={formData.factor_8}
            onChange={handleChange}
            required
          />
        </Form.Group>

        {/* ... Agrega los Form.Group para los demás factores ... */}

        <Button variant="primary" type="submit">Guardar</Button>
        <Button variant="secondary" onClick={() => onSave()}>Cancelar</Button>
      </Form>
    </div>
  );
}

export default QualificationForm;