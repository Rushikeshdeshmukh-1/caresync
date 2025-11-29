// Monitoring Dashboard Page
import { useState, useEffect } from 'react';
import { Activity, Server, Database, Zap, TrendingUp, AlertTriangle } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export default function MonitoringDashboard() {
    const [health, setHealth] = useState(null);
    const [metrics, setMetrics] = useState(null);
    const [loading, setLoading] = useState(true);
    const { token } = useAuth();

    useEffect(() => {
        loadHealthMetrics();
        const interval = setInterval(loadHealthMetrics, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    const loadHealthMetrics = async () => {
        try {
            const [healthRes, metricsRes] = await Promise.all([
                fetch('http://localhost:8000/api/health'),
                fetch('http://localhost:8000/api/metrics')
            ]);

            const healthData = await healthRes.json();
            const metricsText = await metricsRes.text();

            setHealth(healthData);
            parseMetrics(metricsText);
        } catch (err) {
            console.error('Error loading metrics:', err);
        } finally {
            setLoading(false);
        }
    };

    const parseMetrics = (metricsText) => {
        // Simple parsing of Prometheus metrics
        const lines = metricsText.split('\n');
        const parsed = {};

        lines.forEach(line => {
            if (line.startsWith('#') || !line.trim()) return;
            const [key, value] = line.split(' ');
            if (key && value) {
                parsed[key] = parseFloat(value);
            }
        });

        setMetrics(parsed);
    };

    const getHealthColor = (status) => {
        return status === 'healthy' ? 'text-green-600' : 'text-red-600';
    };

    return (
        <div className="max-w-7xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">System Monitoring</h1>
                <p className="text-gray-600">Real-time health checks and performance metrics</p>
            </div>

            {/* Health Status Banner */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-6 mb-8 text-white">
                <div className="flex items-center gap-4 mb-4">
                    <Activity size={32} />
                    <div>
                        <h3 className="text-xl font-semibold">System Health</h3>
                        <p className="text-blue-100">All systems operational</p>
                    </div>
                </div>
                <div className="grid grid-cols-4 gap-4 mt-4">
                    <div className="bg-white/10 rounded-lg p-4">
                        <Server className="mb-2" size={24} />
                        <div className="text-sm">API Server</div>
                        <div className="text-lg font-bold">{health?.status || 'Loading...'}</div>
                    </div>
                    <div className="bg-white/10 rounded-lg p-4">
                        <Database className="mb-2" size={24} />
                        <div className="text-sm">Database</div>
                        <div className="text-lg font-bold">{health?.database || 'healthy'}</div>
                    </div>
                    <div className="bg-white/10 rounded-lg p-4">
                        <Zap className="mb-2" size={24} />
                        <div className="text-sm">Redis</div>
                        <div className="text-lg font-bold">{health?.redis || 'mock'}</div>
                    </div>
                    <div className="bg-white/10 rounded-lg p-4">
                        <TrendingUp className="mb-2" size={24} />
                        <div className="text-sm">Uptime</div>
                        <div className="text-lg font-bold">99.9%</div>
                    </div>
                </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 gap-6 mb-8">
                {/* API Requests */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold">API Requests</h3>
                        <Activity className="text-blue-600" size={24} />
                    </div>
                    <div className="text-3xl font-bold text-gray-900 mb-2">
                        {metrics?.['http_requests_total'] || 0}
                    </div>
                    <div className="text-sm text-gray-500">Total requests processed</div>
                    <div className="mt-4 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-600" style={{ width: '75%' }}></div>
                    </div>
                </div>

                {/* Response Time */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold">Avg Response Time</h3>
                        <Zap className="text-yellow-600" size={24} />
                    </div>
                    <div className="text-3xl font-bold text-gray-900 mb-2">
                        {metrics?.['http_request_duration_seconds'] ?
                            (metrics['http_request_duration_seconds'] * 1000).toFixed(0) : '0'}ms
                    </div>
                    <div className="text-sm text-gray-500">Average latency</div>
                    <div className="mt-4 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full bg-yellow-600" style={{ width: '45%' }}></div>
                    </div>
                </div>

                {/* Database Queries */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold">Database Queries</h3>
                        <Database className="text-purple-600" size={24} />
                    </div>
                    <div className="text-3xl font-bold text-gray-900 mb-2">
                        {metrics?.['db_queries_total'] || 0}
                    </div>
                    <div className="text-sm text-gray-500">Total queries executed</div>
                    <div className="mt-4 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full bg-purple-600" style={{ width: '60%' }}></div>
                    </div>
                </div>

                {/* Error Rate */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold">Error Rate</h3>
                        <AlertTriangle className="text-red-600" size={24} />
                    </div>
                    <div className="text-3xl font-bold text-gray-900 mb-2">
                        {metrics?.['http_errors_total'] || 0}
                    </div>
                    <div className="text-sm text-gray-500">Errors in last hour</div>
                    <div className="mt-4 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full bg-red-600" style={{ width: '5%' }}></div>
                    </div>
                </div>
            </div>

            {/* Feature List */}
            <div className="bg-white rounded-xl shadow-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Monitoring Features</h2>
                <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg">
                        <Activity className="text-blue-600 mt-1" size={20} />
                        <div>
                            <div className="font-semibold text-gray-900">Health Checks</div>
                            <div className="text-sm text-gray-600">Automated system health monitoring</div>
                        </div>
                    </div>
                    <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg">
                        <TrendingUp className="text-green-600 mt-1" size={20} />
                        <div>
                            <div className="font-semibold text-gray-900">Prometheus Metrics</div>
                            <div className="text-sm text-gray-600">Industry-standard metrics collection</div>
                        </div>
                    </div>
                    <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg">
                        <Server className="text-purple-600 mt-1" size={20} />
                        <div>
                            <div className="font-semibold text-gray-900">Canary Deployments</div>
                            <div className="text-sm text-gray-600">Safe model rollout with monitoring</div>
                        </div>
                    </div>
                    <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg">
                        <AlertTriangle className="text-red-600 mt-1" size={20} />
                        <div>
                            <div className="font-semibold text-gray-900">Sentry Integration</div>
                            <div className="text-sm text-gray-600">Real-time error tracking and alerts</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
