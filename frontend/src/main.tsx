import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import AdminApp from './AdminApp';
import './styles.css';

const isAdmin = window.location.pathname.replace(/\/$/, '') === '/admin';
createRoot(document.getElementById('root')!).render(
  <React.StrictMode>{isAdmin ? <AdminApp /> : <App />}</React.StrictMode>,
);
