import React from 'react';
import { useHealthCheck } from './hooks/useHealthCheck.js';

export default function App() {
  const { data, error, loading } = useHealthCheck('/api/health');

  return (
    <div style={{ fontFamily: 'sans-serif', padding: '24px' }}>
      <h1>React Finance Dashboard</h1>
      <p>Health API Status:</p>
      {loading && <p>Checking health status...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {data && (
        <pre style={{ background: '#f4f4f4', padding: '12px', borderRadius: '6px' }}>
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}

