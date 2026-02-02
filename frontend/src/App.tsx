import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { CommandConsole } from './pages/CommandConsole';
import { LiveTelemetry } from './pages/LiveTelemetry';
import { SecurityCore } from './pages/SecurityCore';
import { FleetNetwork } from './pages/FleetNetwork';
import { KernelLogs } from './pages/KernelLogs';
import { Parameters } from './pages/Parameters';

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public route - Landing/Login page */}
          <Route path="/login" element={<Login />} />

          {/* Protected dashboard routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<CommandConsole />} />
            <Route path="telemetry" element={<LiveTelemetry />} />
            <Route path="security" element={<SecurityCore />} />
            <Route path="fleet" element={<FleetNetwork />} />
            <Route path="logs" element={<KernelLogs />} />
            <Route path="parameters" element={<Parameters />} />
          </Route>

          {/* Redirect root to login (landing page) */}
          <Route path="/" element={<Navigate to="/login" replace />} />

          {/* Catch-all redirect */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
