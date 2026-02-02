import React, { useState, useEffect } from 'react';
import { Globe, Server, Wifi, AlertCircle, CheckCircle, Activity, MapPin } from 'lucide-react';
import { API_BASE } from '../config';

type MachineStatus = {
  machine_id: string;
  health_score: number;
  status: string;
  location: string;
  last_alert: string | null;
};

type FleetSummary = {
  total_machines: number;
  optimal: number;
  good: number;
  moderate: number;
  degraded: number;
  critical: number;
  average_health: number;
};

export function FleetNetwork() {
  const [machines, setMachines] = useState<MachineStatus[]>([]);
  const [summary, setSummary] = useState<FleetSummary | null>(null);
  const [selectedMachine, setSelectedMachine] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchFleetHealth();
    const interval = setInterval(fetchFleetHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchFleetHealth = async () => {
    try {
      const response = await fetch(`${API_BASE}/health/fleet`);
      const data = await response.json();
      setMachines(data.machines || []);
      setSummary(data.summary);
    } catch (error) {
      console.error('Failed to fetch fleet health:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'optimal': return 'bg-emerald-500';
      case 'good': return 'bg-[#3FB950]';
      case 'moderate': return 'bg-yellow-500';
      case 'degraded': return 'bg-orange-500';
      case 'critical': return 'bg-red-500';
      default: return 'bg-slate-500';
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'optimal': return 'border-emerald-500/20 bg-emerald-500/5';
      case 'good': return 'border-[#3FB950]/20 bg-[#3FB950]/5';
      case 'moderate': return 'border-yellow-500/20 bg-yellow-500/5';
      case 'degraded': return 'border-orange-500/20 bg-orange-500/5';
      case 'critical': return 'border-red-500/20 bg-red-500/5';
      default: return 'border-slate-500/20 bg-slate-500/5';
    }
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Fleet Network</h1>
          <p className="text-xs text-slate-500 mt-1 uppercase tracking-widest font-medium">
            Machine fleet monitoring • {summary?.total_machines || 0} assets online
          </p>
        </div>
        <button
          onClick={fetchFleetHealth}
          className="px-4 py-2 bg-[#4fa3d1] text-white text-xs font-bold uppercase tracking-widest rounded hover:bg-[#4389b1] transition-all"
        >
          Refresh Fleet
        </button>
      </div>

      {/* Fleet Summary */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-7 gap-4">
          <div className="command-card p-4">
            <div className="text-2xl font-bold text-white">{summary.total_machines}</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-widest">Total Fleet</div>
          </div>
          <div className="command-card p-4">
            <div className="text-2xl font-bold text-emerald-500">{summary.optimal}</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-widest">Optimal</div>
          </div>
          <div className="command-card p-4">
            <div className="text-2xl font-bold text-[#3FB950]">{summary.good}</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-widest">Good</div>
          </div>
          <div className="command-card p-4">
            <div className="text-2xl font-bold text-yellow-500">{summary.moderate}</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-widest">Moderate</div>
          </div>
          <div className="command-card p-4">
            <div className="text-2xl font-bold text-orange-500">{summary.degraded}</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-widest">Degraded</div>
          </div>
          <div className="command-card p-4">
            <div className="text-2xl font-bold text-red-500">{summary.critical}</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-widest">Critical</div>
          </div>
          <div className="command-card p-4 border-[#4fa3d1]/20 bg-[#4fa3d1]/5">
            <div className="text-2xl font-bold text-[#4fa3d1]">{summary.average_health.toFixed(1)}%</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-widest">Avg Health</div>
          </div>
        </div>
      )}

      {/* Machine Grid */}
      <div className="command-card p-6">
        <h3 className="text-sm font-bold uppercase tracking-widest text-white mb-6">Fleet Status Grid</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {machines.map((machine) => (
            <div
              key={machine.machine_id}
              onClick={() => setSelectedMachine(machine.machine_id)}
              className={`p-4 rounded border cursor-pointer transition-all hover:scale-[1.02] ${
                selectedMachine === machine.machine_id
                  ? 'border-[#4fa3d1] bg-[#4fa3d1]/10'
                  : getStatusBg(machine.status)
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <Server size={20} className="text-slate-400" />
                <div className={`w-3 h-3 rounded-full ${getStatusColor(machine.status)}`} />
              </div>
              <div className="text-sm font-bold text-white mb-1">{machine.machine_id}</div>
              <div className="flex items-center gap-2 text-[10px] text-slate-500 mb-3">
                <MapPin size={10} />
                {machine.location}
              </div>
              <div className="flex items-center justify-between">
                <div className="text-xl font-bold text-white">{machine.health_score.toFixed(0)}%</div>
                <span className={`text-[9px] px-2 py-0.5 rounded font-bold uppercase ${
                  machine.status === 'optimal' || machine.status === 'good'
                    ? 'bg-[#3FB950]/20 text-[#3FB950]'
                    : machine.status === 'moderate'
                    ? 'bg-yellow-500/20 text-yellow-500'
                    : 'bg-red-500/20 text-red-500'
                }`}>
                  {machine.status}
                </span>
              </div>
              {machine.last_alert && (
                <div className="mt-3 pt-3 border-t border-white/5 flex items-center gap-2 text-[10px] text-orange-500">
                  <AlertCircle size={12} />
                  <span>Alert active</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Network Topology Placeholder */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="command-card p-6">
          <h3 className="text-sm font-bold uppercase tracking-widest text-white mb-6">Network Topology</h3>
          <div className="h-[300px] flex items-center justify-center border border-dashed border-white/10 rounded">
            <div className="text-center">
              <Globe size={48} className="text-slate-600 mx-auto mb-4" />
              <p className="text-sm text-slate-500">Network topology visualization</p>
              <p className="text-[10px] text-slate-600 mt-1">All nodes connected via industrial ethernet</p>
            </div>
          </div>
        </div>

        <div className="command-card p-6">
          <h3 className="text-sm font-bold uppercase tracking-widest text-white mb-6">Connection Status</h3>
          <div className="space-y-4">
            <ConnectionStatus label="Primary Gateway" ip="192.168.1.1" latency="2ms" status="connected" />
            <ConnectionStatus label="Backup Gateway" ip="192.168.1.2" latency="4ms" status="standby" />
            <ConnectionStatus label="SCADA Server" ip="192.168.10.50" latency="8ms" status="connected" />
            <ConnectionStatus label="Historian DB" ip="192.168.10.100" latency="12ms" status="connected" />
            <ConnectionStatus label="Cloud Sync" ip="cloud.horizonops.io" latency="45ms" status="connected" />
          </div>
        </div>
      </div>
    </div>
  );
}

function ConnectionStatus({
  label,
  ip,
  latency,
  status
}: {
  label: string;
  ip: string;
  latency: string;
  status: 'connected' | 'standby' | 'disconnected';
}) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-white/5">
      <div className="flex items-center gap-3">
        <div className={`w-2 h-2 rounded-full ${
          status === 'connected' ? 'bg-[#3FB950]' :
          status === 'standby' ? 'bg-yellow-500' : 'bg-red-500'
        }`} />
        <div>
          <div className="text-sm text-white font-medium">{label}</div>
          <div className="text-[10px] text-slate-500 font-mono">{ip}</div>
        </div>
      </div>
      <div className="text-right">
        <div className="text-sm text-white font-medium">{latency}</div>
        <div className={`text-[9px] font-bold uppercase ${
          status === 'connected' ? 'text-[#3FB950]' :
          status === 'standby' ? 'text-yellow-500' : 'text-red-500'
        }`}>
          {status}
        </div>
      </div>
    </div>
  );
}
