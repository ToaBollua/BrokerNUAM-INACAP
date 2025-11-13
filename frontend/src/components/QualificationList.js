import React, { useState, useEffect } from "react";
import axios from 'axios';
import { Link } from 'react-router-dom';

function QualificationList() {
    const [qualifications, setQualifications] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        axios.get('${process.env.REACT_APP_API_URL}calificaciones/')
        .then(res => {
            setQualifications(res.data);
            setLoading(false);
        });
    }, []);

    if (loading) return <p>Cargando...</p>;

    return (
        <div>
            <h2>Calificaciones</h2>
            <Link to="/calificaciones/nuevo">Nuevl</Link>
            <ul>
                {qualifications.map(q => (
                    <li key={q.id}>
                        Broker: {q.broker} - Calificación: {q.qualification} {' '}
                        <Link to={'/calificaciones/${q.id}'}>Editar</Link>
                    </li>
                ))}
            </ul>
        </div>

    )
}

export default QualificationList;