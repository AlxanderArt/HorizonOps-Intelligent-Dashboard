import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, Play, User, Lock, ArrowRight, Sparkles } from 'lucide-react';

export function Login() {
  const navigate = useNavigate();
  const { login, enterDemoMode } = useAuth();
  const [showLogin, setShowLogin] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleDemo = () => {
    enterDemoMode();
    navigate('/');
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const success = await login(email, password);
    if (success) {
      navigate('/');
    } else {
      setError('Invalid credentials');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#0a0f1a] flex items-center justify-center p-8">
      <div className="w-full max-w-4xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-[#4fa3d1] to-[#3FB950] rounded-lg flex items-center justify-center">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-white tracking-tight">HorizonOps</h1>
          </div>
          <p className="text-slate-400 text-lg">AI-Driven Operational Intelligence for Aerospace Manufacturing</p>
        </div>

        {!showLogin ? (
          /* Main Options - Demo and Sign In */
          <div className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto">
            {/* Demo Mode Card */}
            <button
              onClick={handleDemo}
              className="group bg-gradient-to-br from-[#4fa3d1]/20 to-[#4fa3d1]/5 border border-[#4fa3d1]/30 rounded-xl p-8 text-left hover:border-[#4fa3d1]/60 hover:from-[#4fa3d1]/30 hover:to-[#4fa3d1]/10 transition-all duration-300"
            >
              <div className="w-16 h-16 bg-[#4fa3d1]/20 rounded-lg flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Play className="w-8 h-8 text-[#4fa3d1]" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-3">Demo Mode</h3>
              <p className="text-slate-400 text-sm mb-6 leading-relaxed">
                Explore the full platform with simulated aerospace manufacturing data. Perfect for seeing all features in action.
              </p>
              <div className="flex items-center gap-2 text-[#4fa3d1] text-sm font-semibold mb-4">
                <Sparkles className="w-4 h-4" />
                <span>Recommended for recruiters & reviewers</span>
              </div>
              <div className="flex items-center gap-2 text-[#4fa3d1] opacity-0 group-hover:opacity-100 transition-opacity">
                <span className="text-sm font-medium">Launch Demo</span>
                <ArrowRight className="w-4 h-4" />
              </div>
            </button>

            {/* Sign In Card */}
            <button
              onClick={() => setShowLogin(true)}
              className="group bg-[#3FB950]/10 border border-[#3FB950]/30 rounded-xl p-8 text-left hover:border-[#3FB950]/60 hover:bg-[#3FB950]/20 transition-all duration-300"
            >
              <div className="w-16 h-16 bg-[#3FB950]/20 rounded-lg flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Lock className="w-8 h-8 text-[#3FB950]" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-3">Sign In</h3>
              <p className="text-slate-400 text-sm mb-6 leading-relaxed">
                Access your personalized dashboard with saved preferences, custom alerts, and real operational data.
              </p>
              <div className="flex items-center gap-2 text-[#3FB950]/80 text-sm font-semibold mb-4">
                <User className="w-4 h-4" />
                <span>For registered operators</span>
              </div>
              <div className="flex items-center gap-2 text-[#3FB950] opacity-0 group-hover:opacity-100 transition-opacity">
                <span className="text-sm font-medium">Sign In</span>
                <ArrowRight className="w-4 h-4" />
              </div>
            </button>
          </div>
        ) : (
          /* Login Form */
          <div className="max-w-md mx-auto">
            <div className="bg-white/5 border border-white/10 rounded-xl p-8">
              <h2 className="text-2xl font-bold text-white mb-6">Sign In</h2>

              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-[#4fa3d1]/50"
                    placeholder="operator@horizonops.io"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">Password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-[#4fa3d1]/50"
                    placeholder="Enter your password"
                    required
                  />
                </div>

                {error && (
                  <p className="text-red-400 text-sm">{error}</p>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 bg-[#3FB950] hover:bg-[#3FB950]/80 text-white font-semibold rounded-lg transition-colors disabled:opacity-50"
                >
                  {loading ? 'Signing in...' : 'Sign In'}
                </button>
              </form>

              <div className="mt-6 pt-6 border-t border-white/10 flex items-center justify-between">
                <button
                  onClick={() => setShowLogin(false)}
                  className="text-slate-400 hover:text-white text-sm transition-colors"
                >
                  Back to options
                </button>
                <button
                  onClick={handleDemo}
                  className="text-[#4fa3d1] hover:underline text-sm"
                >
                  Try Demo Instead
                </button>
              </div>

            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-12">
          <p className="text-slate-600 text-sm">
            Built for scientific study and technical craftsmanship
          </p>
          <p className="text-slate-700 text-xs mt-1">
            Applicable to real-world aerospace manufacturing operations
          </p>
        </div>
      </div>
    </div>
  );
}
