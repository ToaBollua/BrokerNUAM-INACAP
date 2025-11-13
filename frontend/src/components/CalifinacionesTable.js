// frontend/src/components/CalificacionesTable.js
import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Table, Button, Form, Row, Col } from 'react-bootstrap';

function CalificacionesTable({ onModify, onDelete, onCreate }) {
  const [calificaciones, setCalificaciones] = useState([]);
  const [filtros, setFiltros] = useState({
    mercado: '',
    origen: '',
    periodo: '',
  });

  // Cargar lista filtrada
  const cargarCalificaciones = () => {
    let query = [];
    if (filtros.mercado) query.push(`mercado=${filtros.mercado}`);
    if (filtros.origen) query.push(`origen=${filtros.origen}`);
    if (filtros.periodo) query.push(`periodo=${filtros.periodo}`);
    let url = '/calificaciones/';
    if (query.length > 0) url += '?' + query.join('&');

    api.get(url)
      .then(resp => setCalificaciones(resp.data))
      .catch(() => alert('Error al cargar las calificaciones.'));
  };

  useEffect(() => {
    cargarCalificaciones();
  }, []);

  const handleFiltroChange = e => {
    setFiltros({...filtros, [e.target.name]: e.target.value});
  };

  const handleFiltrar = () => {
    cargarCalificaciones();
  };

  const handleLimpiar = () => {
    setFiltros({mercado: '', origen: '', periodo: ''});
    cargarCalificaciones();
  };

  return (
    <div>
      <Row className="mb-3">
        <Col>
          <Form.Control name="mercado" placeholder="Mercado" value={filtros.mercado} onChange={handleFiltroChange} />
        </Col>
        <Col>
          <Form.Control name="origen" placeholder="Origen" value={filtros.origen} onChange={handleFiltroChange} />
        </Col>
        <Col>
          <Form.Control name="periodo" placeholder="Período Comercial" value={filtros.periodo} onChange={handleFiltroChange} />
        </Col>
        <Col>
          <Button variant="primary" onClick={handleFiltrar}>Filtrar</Button>{' '}
          <Button variant="secondary" onClick={handleLimpiar}>Limpiar</Button>
        </Col>
        <Col>
          <Button variant="success" onClick={onCreate}>Ingresar Nueva</Button>
        </Col>
      </Row>

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>Instrumento</th>
            <th>Fecha de pago</th>
            <th>Origen</th>
            <th>Factor 8</th>
            {/* Agregar columnas según los factores y otros campos */}
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {calificaciones.map(cal => (
            <tr key={cal.id}>
              <td>{cal.instrumento}</td>
              <td>{cal.fechapago}</td>
              <td>{cal.origen}</td>
              <td>{cal.factor8}</td>
              {/* Agregar más columnas según modelo */}
              <td>
                <Button variant="warning" size="sm" onClick={() => onModify(cal)}>Modificar</Button>{' '}
                <Button variant="danger" size="sm" onClick={() => onDelete(cal)}>Eliminar</Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </div>
  );
}

export default CalificacionesTable;
