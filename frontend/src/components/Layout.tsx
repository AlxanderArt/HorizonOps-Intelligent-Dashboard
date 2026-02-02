import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  ShieldCheck,
  Activity,
  Globe,
  Terminal,
  Settings,
  LayoutGrid,
  LogOut,
  Search,
  Clock,
  Bell
} from 'lucide-react';

const NAV_ITEMS = [
  { to: '/', icon: LayoutGrid, label: 'Command Console' },
  { to: '/telemetry', icon: Activity, label: 'Live Telemetry' },
  { to: '/security', icon: ShieldCheck, label: 'Security Core' },
  { to: '/fleet', icon: Globe, label: 'Fleet Network' },
  { to: '/logs', icon: Terminal, label: 'Kernel Logs' },
  { to: '/parameters', icon: Settings, label: 'Parameters' },
];

export function Layout() {
  return (
    <div className="flex h-screen overflow-hidden bg-[#0b1320] text-[#e2e8f0]">
      {/* Sidebar */}
      <aside className="w-16 lg:w-64 bg-[#0d1624] border-r border-white/5 flex flex-col items-center lg:items-stretch">
        <div className="p-6 flex items-center gap-3">
          <div className="w-8 h-8 bg-[#4fa3d1] rounded flex items-center justify-center text-white shrink-0">
            <ShieldCheck size={20} />
          </div>
          <span className="hidden lg:block font-bold tracking-tight text-lg uppercase italic text-white">
            HorizonOps <span className="text-[#4fa3d1] not-italic">Command</span>
          </span>
        </div>

        <nav className="flex-1 mt-6">
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-4 px-6 py-4 cursor-pointer transition-all border-l-3 border-transparent group ${
                  isActive
                    ? 'sidebar-item-active text-white'
                    : 'text-slate-500 hover:text-slate-300 hover:bg-white/[0.02]'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <span className={isActive ? 'text-[#4fa3d1]' : 'group-hover:text-slate-300'}>
                    <Icon size={20} />
                  </span>
                  <span className="hidden lg:block text-xs font-bold uppercase tracking-widest">
                    {label}
                  </span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-white/5">
          <div className="flex items-center gap-3 p-2 rounded hover:bg-white/5 cursor-pointer">
            <div className="w-8 h-8 rounded-full bg-slate-700 overflow-hidden">
              <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Operator" alt="User" />
            </div>
            <div className="hidden lg:block">
              <p className="text-xs font-bold text-white leading-none">Guy Hawkins</p>
              <p className="text-[10px] text-slate-500 font-medium">Ops Lead</p>
            </div>
            <LogOut size={14} className="ml-auto hidden lg:block text-slate-600" />
          </div>
        </div>
      </aside>

      {/* Main Area */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Top Command Bar */}
        <header className="h-16 border-b border-white/5 bg-[#0b1320] flex items-center justify-between px-8 shrink-0">
          <div className="flex items-center gap-6">
            <div className="flex items-center bg-[#151d29] border border-white/5 rounded px-3 py-1.5 w-64">
              <Search size={14} className="text-slate-500 mr-2" />
              <input
                type="text"
                placeholder="Search project, analytics"
                className="bg-transparent border-none outline-none text-xs w-full text-slate-300"
              />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-[#151d29] border border-white/5 rounded text-xs text-slate-400">
              <Clock size={14} />
              <span className="mono">{new Date().toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
            </div>
            <button className="p-2 text-slate-500 hover:text-white transition-colors relative">
              <Bell size={18} />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-y-auto">
          <Outlet />
        </div>

        {/* Global Footer */}
        <footer className="h-10 bg-[#0d1624] border-t border-white/5 flex items-center justify-between px-8 text-[9px] font-bold text-slate-600 uppercase tracking-widest shrink-0">
          <div className="flex items-center gap-6">
            <span>Server Latency: <span className="text-emerald-500">14ms</span></span>
            <span>Uptime: 99.998%</span>
          </div>
          <div className="flex items-center gap-2">
            <span>Facility: TX-DA-092 (Lockheed Martin Cluster)</span>
          </div>
        </footer>
      </main>
    </div>
  );
}
