import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { CommandConsole } from './pages/CommandConsole';
import { LiveTelemetry } from './pages/LiveTelemetry';
import { SecurityCore } from './pages/SecurityCore';
import { FleetNetwork } from './pages/FleetNetwork';
import { KernelLogs } from './pages/KernelLogs';
import { Parameters } from './pages/Parameters';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<CommandConsole />} />
          <Route path="telemetry" element={<LiveTelemetry />} />
          <Route path="security" element={<SecurityCore />} />
          <Route path="fleet" element={<FleetNetwork />} />
          <Route path="logs" element={<KernelLogs />} />
          <Route path="parameters" element={<Parameters />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
