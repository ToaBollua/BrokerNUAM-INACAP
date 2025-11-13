import React from 'react';
import { Routes, Route } from 'react-router-dom';
import QualificationList from './components/QualificationList';
import QualificationForm from './components/QualificationForm';

function App() {
  return (
    <Routes>
      <Route path="/" element={<QualificationList />} />
      <Route path="/calificaciones/nuevo" element={<QualificationForm />} />
      <Route path="/calificaciones/:id" element={<QualificationForm />} />
    </Routes>
  );
}

export default App;
