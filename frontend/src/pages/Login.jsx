import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../utils/api';
import { setAuth } from '../utils/auth';

export default function Login() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authAPI.login(formData);
      const { access_token, user } = response.data;
      setAuth(access_token, user);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <div className="inline-block p-4 rounded-full bg-card border border-primary/30 glow-effect mb-4">
            <svg
              className="w-16 h-16 text-primary"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h1 className="text-4xl font-bold text-foreground glow-text mb-2">
            Claim2Car Connect™
          </h1>
          <p className="text-muted-foreground">
            AI-Powered Total-Loss Vehicle Marketplace
          </p>
        </div>

        {/* Login Form */}
        <div className="card-glow rounded-lg p-8">
          <h2 className="text-2xl font-bold text-foreground mb-6">Sign In</h2>

          {error && (
            <div className="mb-4 p-3 rounded bg-destructive/20 border border-destructive text-destructive-foreground text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Email
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 bg-secondary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-foreground"
                placeholder="your@email.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Password
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 bg-secondary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-foreground"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary py-3 px-4 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-muted-foreground">
            Don't have an account?{' '}
            <Link to="/register" className="text-primary hover:underline font-medium">
              Register here
            </Link>
          </div>
        </div>

        {/* Demo Credentials */}
        <div className="mt-6 p-4 card-glow rounded-lg">
          <p className="text-xs text-muted-foreground text-center mb-2">Demo Credentials:</p>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div>
              <p className="text-primary font-semibold">Tow Operator</p>
              <p className="text-muted-foreground">tow@demo.com</p>
            </div>
            <div>
              <p className="text-primary font-semibold">Dealer</p>
              <p className="text-muted-foreground">dealer@demo.com</p>
            </div>
            <div>
              <p className="text-primary font-semibold">Owner</p>
              <p className="text-muted-foreground">owner@demo.com</p>
            </div>
          </div>
          <p className="text-center text-muted-foreground mt-2">Password: demo123</p>
        </div>
      </div>
    </div>
  );
}
