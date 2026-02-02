import React, { useState, useEffect } from 'react';
import { Activity, Thermometer, Zap, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import { API_BASE } from '../config';

const MACHINES = [
  "CNC-ALPHA-921",
  "CNC-ALPHA-922",
  "CNC-BETA-101",
  "CNC-BETA-102",
  "MILL-GAMMA-301",
  "MILL-GAMMA-302",
  "LATHE-DELTA-401",
  "LATHE-DELTA-402"
];

type TelemetryReading = {
  timestamp: string;
  vibration_rms: number;
  vibration_peak: number;
  vibration_kurtosis: number;
  temperature: number;
  power_consumption: number;
  anomaly_flag: boolean;
};

export function LiveTelemetry() {
  const [selectedMachine, setSelectedMachine] = useState(MACHINES[0]);
  const [telemetryData, setTelemetryData] = useState<TelemetryReading[]>([]);
  const [latestReading, setLatestReading] = useState<TelemetryReading | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchTelemetry();
    const interval = setInterval(fetchLatest, 2000);
    return () => clearInterval(interval);
  }, [selectedMachine]);

  const fetchTelemetry = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/telemetry/${selectedMachine}?limit=50`);
      const data = await response.json();
      setTelemetryData(data.data || []);
    } catch (error) {
      console.error('Failed to fetch telemetry:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchLatest = async () => {
    try {
      const response = await fetch(`${API_BASE}/telemetry/${selectedMachine}/latest`);
      const data = await response.json();
      setLatestReading(data.reading);

      // Add to chart data
      setTelemetryData(prev => {
        const newPoint = {
          timestamp: new Date().toLocaleTimeString(),
          ...data.reading
        };
        return [...prev.slice(-49), newPoint];
      });
    } catch (error) {
      console.error('Failed to fetch latest:', error);
    }
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Live Telemetry</h1>
          <p className="text-xs text-slate-500 mt-1 uppercase tracking-widest font-medium">
            Real-time sensor data streaming • 1Hz refresh rate
          </p>
        </div>
        <select
          value={selectedMachine}
          onChange={(e) => setSelectedMachine(e.target.value)}
          className="px-4 py-2 bg-[#151d29] border border-white/10 rounded text-sm text-white focus:outline-none focus:border-[#4fa3d1]"
        >
          {MACHINES.map((machine) => (
            <option key={machine} value={machine}>{machine}</option>
          ))}
        </select>
      </div>

      {/* Live Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={Activity}
          label="Vibration RMS"
          value={latestReading?.vibration_rms?.toFixed(1) || '--'}
          unit="mm/s"
          trend={latestReading && latestReading.vibration_rms > 25 ? 'up' : 'stable'}
          alert={latestReading?.anomaly_flag}
        />
        <MetricCard
          icon={Activity}
          label="Peak Amplitude"
          value={latestReading?.vibration_peak?.toFixed(1) || '--'}
          unit="mm/s"
          trend="stable"
        />
        <MetricCard
          icon={Thermometer}
          label="Temperature"
          value={latestReading?.temperature?.toFixed(1) || '--'}
          unit="°C"
          trend={latestReading && latestReading.temperature > 50 ? 'up' : 'stable'}
        />
        <MetricCard
          icon={Zap}
          label="Power Draw"
          value={latestReading?.power_consumption?.toFixed(2) || '--'}
          unit="kW"
          trend="stable"
        />
      </div>

      {/* Vibration Chart */}
      <div className="command-card p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-widest text-white">Vibration Analysis</h3>
            <p className="text-[10px] text-slate-500 mt-1">RMS & Peak values over time</p>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-2">
              <div className="w-3 h-0.5 bg-[#4fa3d1]"></div>
              <span className="text-slate-400">RMS</span>
            </span>
            <span className="flex items-center gap-2">
              <div className="w-3 h-0.5 bg-[#F5A623]"></div>
              <span className="text-slate-400">Peak</span>
            </span>
          </div>
        </div>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={telemetryData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="timestamp" hide />
              <YAxis stroke="#4a5568" fontSize={10} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#151d29',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                }}
              />
              <Line type="monotone" dataKey="vibration_rms" stroke="#4fa3d1" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="vibration_peak" stroke="#F5A623" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Temperature & Power Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="command-card p-6">
          <h3 className="text-sm font-bold uppercase tracking-widest text-white mb-6">Temperature Profile</h3>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={telemetryData}>
                <defs>
                  <linearGradient id="tempGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="timestamp" hide />
                <YAxis stroke="#4a5568" fontSize={10} tickLine={false} axisLine={false} domain={[35, 60]} />
                <Tooltip contentStyle={{ backgroundColor: '#151d29', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} />
                <Area type="monotone" dataKey="temperature" stroke="#ef4444" fill="url(#tempGradient)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="command-card p-6">
          <h3 className="text-sm font-bold uppercase tracking-widest text-white mb-6">Power Consumption</h3>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={telemetryData}>
                <defs>
                  <linearGradient id="powerGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="timestamp" hide />
                <YAxis stroke="#4a5568" fontSize={10} tickLine={false} axisLine={false} domain={[10, 15]} />
                <Tooltip contentStyle={{ backgroundColor: '#151d29', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} />
                <Area type="monotone" dataKey="power_consumption" stroke="#22c55e" fill="url(#powerGradient)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Kurtosis Indicator */}
      <div className="command-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-widest text-white">Vibration Kurtosis</h3>
            <p className="text-[10px] text-slate-500 mt-1">Bearing health indicator (normal: 3.0 ± 0.5)</p>
          </div>
          <div className="flex items-center gap-4">
            <div className={`text-3xl font-bold ${
              latestReading && latestReading.vibration_kurtosis > 4 ? 'text-red-500' : 'text-[#3FB950]'
            }`}>
              {latestReading?.vibration_kurtosis?.toFixed(2) || '--'}
            </div>
            {latestReading && latestReading.vibration_kurtosis > 4 && (
              <div className="flex items-center gap-2 px-3 py-1 bg-red-500/10 border border-red-500/20 rounded">
                <AlertTriangle size={14} className="text-red-500" />
                <span className="text-xs text-red-500 font-bold">ELEVATED</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  unit,
  trend,
  alert
}: {
  icon: any;
  label: string;
  value: string;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  alert?: boolean;
}) {
  return (
    <div className={`command-card p-4 ${alert ? 'border-red-500/30 bg-red-500/5' : ''}`}>
      <div className="flex items-center justify-between mb-3">
        <Icon size={18} className={alert ? 'text-red-500' : 'text-[#4fa3d1]'} />
        {trend === 'up' && <TrendingUp size={14} className="text-yellow-500" />}
        {trend === 'down' && <TrendingDown size={14} className="text-green-500" />}
      </div>
      <div className="text-2xl font-bold text-white">
        {value}
        <span className="text-sm text-slate-500 ml-1">{unit}</span>
      </div>
      <div className="text-[10px] text-slate-500 uppercase tracking-widest mt-1">{label}</div>
      {alert && (
        <div className="mt-2 text-[10px] text-red-500 font-bold uppercase">Anomaly Detected</div>
      )}
    </div>
  );
}
