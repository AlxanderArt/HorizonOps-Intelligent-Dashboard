import React, { useState, useEffect } from 'react';
import {
  RefreshCw,
  Settings,
  ChevronRight,
  Terminal,
  Zap,
  Search,
  Info
} from 'lucide-react';
import {
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  CartesianGrid,
  PieChart,
  Pie,
  Cell
} from 'recharts';

const MACHINE_ID = "CNC-ALPHA-921";
const API_BASE = "http://localhost:8000/api/v1";

type TelemetryPoint = {
  time: string;
  vibration: number;
  temp: number;
  power: number;
};

type LogEntry = {
  id: string;
  timestamp: string;
  message: string;
  type: 'info' | 'warning' | 'critical';
};

const PIE_DATA = [
  { name: 'Active', value: 85, color: '#3FB950' },
  { name: 'Maintenance', value: 10, color: '#F5A623' },
  { name: 'Idle', value: 5, color: '#2C2F36' },
];

export function CommandConsole() {
  const [telemetry, setTelemetry] = useState<TelemetryPoint[]>(
    Array.from({ length: 40 }, (_, i) => ({
      time: `${i}:00`,
      vibration: 18 + Math.random() * 4,
      temp: 42 + Math.random() * 2,
      power: 11 + Math.random() * 1,
    }))
  );
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isAiAnalyzing, setIsAiAnalyzing] = useState(false);
  const [aiInsight, setAiInsight] = useState<string | null>(null);
  const [systemStatus, setSystemStatus] = useState<'nominal' | 'degraded' | 'critical'>('nominal');

  useEffect(() => {
    const interval = setInterval(() => {
      setTelemetry((prev) => {
        const nextTime = new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        });
        const last = prev[prev.length - 1];
        const isAnomaly = Math.random() > 0.98;

        const newPoint = {
          time: nextTime,
          vibration: isAnomaly ? 55 + Math.random() * 25 : 20 + Math.random() * 4,
          temp: last.temp + (Math.random() - 0.45),
          power: 12 + Math.random() * 0.5,
        };

        if (isAnomaly && systemStatus === 'nominal') {
          addLog('critical', `Anomaly: Spindle vibration threshold exceeded (${newPoint.vibration.toFixed(1)}Hz)`);
          setSystemStatus('degraded');
        }

        return [...prev.slice(1), newPoint];
      });
    }, 3000);

    return () => clearInterval(interval);
  }, [systemStatus]);

  const addLog = (type: LogEntry['type'], message: string) => {
    const newEntry: LogEntry = {
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      message,
      type,
    };
    setLogs((prev) => [newEntry, ...prev].slice(0, 15));
  };

  const runAiAnalysis = async () => {
    setIsAiAnalyzing(true);
    setAiInsight(null);

    try {
      const latestTelemetry = telemetry[telemetry.length - 1];
      const response = await fetch(`${API_BASE}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          machine_id: MACHINE_ID,
          features: {
            vibration_rms: latestTelemetry.vibration,
            vibration_peak: latestTelemetry.vibration * 1.6,
            vibration_kurtosis: systemStatus === 'degraded' ? 5.2 : 3.2,
            temperature: latestTelemetry.temp,
            temp_rate_of_change: 0.1,
            power_consumption: latestTelemetry.power,
            power_deviation: ((latestTelemetry.power - 12) / 12) * 100,
            time_since_maintenance: 280,
            cumulative_cycles: 125000,
          },
        }),
      });
      const data = await response.json();
      const insight = `Risk Level: ${data.risk_level.toUpperCase()} (${data.risk_score}%). ${data.explanation?.natural_language || data.recommended_action}`;
      setAiInsight(insight);
    } catch (error) {
      setAiInsight('AI Uplink Failed. Switching to manual override.');
    } finally {
      setIsAiAnalyzing(false);
    }
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Mission Control Console</h1>
          <p className="text-xs text-slate-500 mt-1 uppercase tracking-widest font-medium">
            Asset ID: {MACHINE_ID} • Aerospace Manufacturing Cluster
          </p>
        </div>
        <div
          className={`px-4 py-2 rounded border flex items-center gap-3 ${
            systemStatus === 'nominal'
              ? 'border-[#3FB950]/20 bg-[#3FB950]/5 text-[#3FB950]'
              : 'border-[#D64545]/20 bg-[#D64545]/5 text-[#D64545]'
          }`}
        >
          <div
            className={`w-2 h-2 rounded-full ${
              systemStatus === 'nominal' ? 'bg-[#3FB950]' : 'bg-[#D64545] status-pulse-red'
            }`}
          />
          <span className="text-xs font-bold uppercase tracking-widest">
            SYSTEM_{systemStatus.toUpperCase()}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Key Metrics */}
        <div className="lg:col-span-4 space-y-6">
          <div className="command-card p-6 grid grid-cols-2 gap-4">
            <StatusMetric label="Health" value="98%" trend="+12% ↑" trendColor="text-[#3FB950]" />
            <StatusMetric label="Risk" value="0.2%" trend="-2% ↓" trendColor="text-[#3FB950]" />
            <StatusMetric label="Throughput" value="1,132" trend="+3% ↑" trendColor="text-[#3FB950]" />
            <StatusMetric label="Efficiency" value="94.1%" trend="Stable" trendColor="text-slate-500" />
          </div>

          <div className="command-card p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-sm font-bold uppercase tracking-widest text-white">Utilization Matrix</h3>
              <ChevronRight size={14} className="text-slate-500" />
            </div>
            <div className="flex items-center justify-center py-4 relative">
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie data={PIE_DATA} innerRadius={50} outerRadius={70} paddingAngle={5} dataKey="value">
                    {PIE_DATA.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#0d1624', border: 'none', borderRadius: '4px' }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute flex flex-col items-center">
                <span className="text-lg font-bold">85%</span>
                <span className="text-[10px] text-slate-500 uppercase font-bold">Uptime</span>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 mt-4">
              {PIE_DATA.map((item) => (
                <div key={item.name} className="flex flex-col items-center">
                  <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-[10px] text-slate-400 font-bold">{item.name}</span>
                  </div>
                  <span className="text-xs font-bold">{item.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Middle: Main Telemetry */}
        <div className="lg:col-span-8 command-card p-6 flex flex-col min-h-[400px]">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-widest text-white">
                Vibration Profile (Spindle A1)
              </h3>
              <p className="text-[10px] text-slate-500 font-bold mt-1 uppercase tracking-widest italic">
                Streaming: 100Hz / 16-bit PCM Ingest
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button className="p-1.5 rounded bg-white/5 hover:bg-white/10 text-slate-400 transition-colors">
                <Settings size={14} />
              </button>
              <button
                onClick={() => setSystemStatus('nominal')}
                className="px-3 py-1 bg-[#4fa3d1] text-white text-[10px] font-bold uppercase tracking-widest rounded hover:bg-[#4389b1] transition-all"
              >
                Recalibrate Baseline
              </button>
            </div>
          </div>

          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={telemetry}>
                <defs>
                  <linearGradient id="areaColor" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4fa3d1" stopOpacity={0.1} />
                    <stop offset="95%" stopColor="#4fa3d1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.03)" />
                <XAxis dataKey="time" hide />
                <YAxis stroke="#4a5568" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#151d29',
                    border: '1px solid rgba(255,255,255,0.05)',
                    borderRadius: '4px',
                    fontSize: '10px',
                  }}
                  itemStyle={{ color: '#4fa3d1', fontWeight: 'bold' }}
                />
                <Area
                  type="monotone"
                  dataKey="vibration"
                  stroke="#4fa3d1"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#areaColor)"
                  animationDuration={500}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Logs Area */}
        <div className="lg:col-span-2 command-card p-6 h-[400px] flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-sm font-bold uppercase tracking-widest text-white flex items-center gap-2">
              <Terminal size={16} className="text-slate-500" />
              Kernel Log Matrix
            </h3>
            <div className="px-2 py-0.5 rounded bg-white/5 text-[9px] font-bold text-slate-500 uppercase tracking-widest">
              Live Feed
            </div>
          </div>
          <div className="flex-1 overflow-y-auto space-y-3 font-mono text-[11px]">
            {logs.map((log) => (
              <div
                key={log.id}
                className="flex gap-4 items-start border-l border-white/5 pl-3 group py-1 hover:bg-white/[0.02]"
              >
                <span className="text-slate-600 whitespace-nowrap">[{log.timestamp}]</span>
                <span
                  className={`px-1.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-widest ${
                    log.type === 'critical'
                      ? 'bg-[#D64545]/20 text-[#D64545]'
                      : log.type === 'warning'
                      ? 'bg-[#F5A623]/20 text-[#F5A623]'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {log.type}
                </span>
                <span className="text-slate-400 group-hover:text-slate-200">{log.message}</span>
              </div>
            ))}
            {logs.length === 0 && <p className="text-slate-700 italic">Listening for system interrupts...</p>}
          </div>
        </div>

        {/* AI Advisor Panel */}
        <div className="command-card p-6 flex flex-col border-[#4fa3d1]/10 bg-[#1a2333]">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-[#4fa3d1]/10 rounded flex items-center justify-center text-[#4fa3d1]">
              <Zap size={20} className="fill-current" />
            </div>
            <div>
              <h3 className="text-sm font-bold uppercase tracking-widest text-white">AI Tactical Module</h3>
              <p className="text-[9px] font-bold text-[#4fa3d1] uppercase tracking-[0.2em]">Operational Oversight</p>
            </div>
          </div>
          <p className="text-xs text-slate-400 font-medium leading-relaxed mb-8 italic border-l-2 border-[#4fa3d1]/30 pl-3">
            "Synthesizing high-frequency telemetry patterns against historical failure benchmarks to provide immediate
            mitigation strategies."
          </p>
          <div className="space-y-3 mt-auto">
            <button
              onClick={runAiAnalysis}
              disabled={isAiAnalyzing}
              className="w-full py-3 bg-[#4fa3d1] hover:bg-[#4389b1] text-white rounded text-[10px] font-bold uppercase tracking-widest flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              {isAiAnalyzing ? <RefreshCw className="animate-spin" size={14} /> : <Search size={14} />}
              {isAiAnalyzing ? 'Synthesizing...' : 'Generate Forensic Brief'}
            </button>
            <button className="w-full py-3 bg-[#151d29] border border-white/5 text-slate-400 rounded text-[10px] font-bold uppercase tracking-widest hover:bg-white/5 transition-all">
              Manual Diagnostic
            </button>
          </div>

          {aiInsight && (
            <div className="mt-6 p-4 bg-black/40 rounded border border-[#4fa3d1]/20">
              <div className="flex items-center gap-2 mb-2">
                <Info size={12} className="text-[#4fa3d1]" />
                <span className="text-[9px] font-bold uppercase text-[#4fa3d1]">Briefing Output</span>
              </div>
              <p className="text-[11px] font-medium leading-relaxed text-slate-300">{aiInsight}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatusMetric({ label, value, trend, trendColor }: { label: string; value: string; trend: string; trendColor: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">{label}</span>
      <span className="text-xl font-bold text-white tracking-tight">{value}</span>
      <span className={`text-[10px] font-bold mt-1 ${trendColor}`}>{trend}</span>
    </div>
  );
}
