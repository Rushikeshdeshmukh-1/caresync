import React, { useState, useEffect } from 'react';
import { PlayCircle, PauseCircle, Activity, Shield, Database, AlertTriangle, RefreshCw } from 'lucide-react';

const OrchestratorDashboard = () => {
    const [status, setStatus] = useState(null);
    const [auditLogs, setAuditLogs] = useState([]);
    const [reviewQueue, setReviewQueue] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('audit');

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000); // Refresh every 5 seconds
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        try {
            // Fetch orchestrator status
            const statusRes = await fetch('http://localhost:8000/api/orchestrator/status');
            const statusData = await statusRes.json();
            setStatus(statusData);

            // Fetch audit logs
            const auditRes = await fetch('http://localhost:8000/api/orchestrator/audit?limit=10');
            const auditData = await auditRes.json();
            setAuditLogs(auditData.logs || []);

            // Fetch review queue
            const queueRes = await fetch('http://localhost:8000/api/orchestrator/review_queue?status=open');
            const queueData = await queueRes.json();
            setReviewQueue(queueData.tasks || []);

            setLoading(false);
        } catch (error) {
            console.error('Error fetching data:', error);
            setLoading(false);
        }
    };

    const handlePause = async () => {
        try {
            await fetch('http://localhost:8000/api/orchestrator/pause', { method: 'POST' });
            fetchData();
        } catch (error) {
            console.error('Error pausing orchestrator:', error);
        }
    };

    const handleResume = async () => {
        try {
            await fetch('http://localhost:8000/api/orchestrator/resume', { method: 'POST' });
            fetchData();
        } catch (error) {
            console.error('Error resuming orchestrator:', error);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <RefreshCw className="animate-spin h-8 w-8 text-blue-500" />
            </div>
        );
    }

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Orchestrator Dashboard</h1>
                    <p className="text-gray-600 mt-1">Monitor AI orchestration system</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={fetchData}
                        className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg flex items-center gap-2 transition-colors"
                    >
                        <RefreshCw className="h-4 w-4" />
                        Refresh
                    </button>
                    {status?.status === 'active' ? (
                        <button
                            onClick={handlePause}
                            className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg flex items-center gap-2 transition-colors"
                        >
                            <PauseCircle className="h-4 w-4" />
                            Pause Orchestrator
                        </button>
                    ) : (
                        <button
                            onClick={handleResume}
                            className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg flex items-center gap-2 transition-colors"
                        >
                            <PlayCircle className="h-4 w-4" />
                            Resume Orchestrator
                        </button>
                    )}
                </div>
            </div>

            {/* Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Status Card */}
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-medium text-gray-600">Status</h3>
                        <Activity className="h-4 w-4 text-gray-400" />
                    </div>
                    <div className="flex items-center gap-2">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${status?.status === 'active'
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}>
                            {status?.status || 'Unknown'}
                        </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">Mode: {status?.mode || 'N/A'}</p>
                </div>

                {/* Blocked Writes Card */}
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-medium text-gray-600">Blocked Writes</h3>
                        <Shield className="h-4 w-4 text-gray-400" />
                    </div>
                    <div className="text-3xl font-bold text-gray-900">{status?.blocked_write_count || 0}</div>
                    <p className="text-xs text-gray-500 mt-2">Safeguards active</p>
                </div>

                {/* Review Queue Card */}
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-medium text-gray-600">Review Queue</h3>
                        <AlertTriangle className="h-4 w-4 text-gray-400" />
                    </div>
                    <div className="text-3xl font-bold text-gray-900">{reviewQueue.length}</div>
                    <p className="text-xs text-gray-500 mt-2">Pending reviews</p>
                </div>

                {/* Audit Logs Card */}
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-medium text-gray-600">Audit Logs</h3>
                        <Database className="h-4 w-4 text-gray-400" />
                    </div>
                    <div className="text-3xl font-bold text-gray-900">{auditLogs.length}</div>
                    <p className="text-xs text-gray-500 mt-2">Recent actions</p>
                </div>
            </div>

            {/* Tabs */}
            <div className="bg-white rounded-lg shadow">
                <div className="border-b border-gray-200">
                    <div className="flex">
                        <button
                            onClick={() => setActiveTab('audit')}
                            className={`px-6 py-3 font-medium transition-colors ${activeTab === 'audit'
                                    ? 'border-b-2 border-blue-500 text-blue-600'
                                    : 'text-gray-600 hover:text-gray-900'
                                }`}
                        >
                            Audit Log
                        </button>
                        <button
                            onClick={() => setActiveTab('queue')}
                            className={`px-6 py-3 font-medium transition-colors ${activeTab === 'queue'
                                    ? 'border-b-2 border-blue-500 text-blue-600'
                                    : 'text-gray-600 hover:text-gray-900'
                                }`}
                        >
                            Review Queue
                        </button>
                    </div>
                </div>

                <div className="p-6">
                    {/* Audit Log Tab */}
                    {activeTab === 'audit' && (
                        <div>
                            <h2 className="text-lg font-semibold mb-4">Recent Audit Logs</h2>
                            <p className="text-gray-600 mb-4">All orchestrator actions are logged here</p>
                            <div className="space-y-2">
                                {auditLogs.length === 0 ? (
                                    <p className="text-gray-500 text-center py-8">No audit logs yet</p>
                                ) : (
                                    auditLogs.map((log) => (
                                        <div key={log.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <span className={`px-2 py-1 rounded text-xs font-medium ${log.status === 'success'
                                                            ? 'bg-green-100 text-green-800'
                                                            : log.status === 'blocked'
                                                                ? 'bg-red-100 text-red-800'
                                                                : 'bg-gray-100 text-gray-800'
                                                        }`}>
                                                        {log.status}
                                                    </span>
                                                    <span className="font-medium text-gray-900">{log.action}</span>
                                                </div>
                                                <p className="text-sm text-gray-600">
                                                    Actor: {log.actor}
                                                    {log.attempted_write && ' • ⚠️ Write attempt blocked'}
                                                </p>
                                            </div>
                                            <div className="text-sm text-gray-500">
                                                {new Date(log.timestamp).toLocaleString()}
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    )}

                    {/* Review Queue Tab */}
                    {activeTab === 'queue' && (
                        <div>
                            <h2 className="text-lg font-semibold mb-4">Review Queue</h2>
                            <p className="text-gray-600 mb-4">Items requiring human review</p>
                            <div className="space-y-2">
                                {reviewQueue.length === 0 ? (
                                    <p className="text-gray-500 text-center py-8">No pending reviews</p>
                                ) : (
                                    reviewQueue.map((task) => (
                                        <div key={task.id} className="p-4 border border-yellow-200 bg-yellow-50 rounded-lg">
                                            <div className="flex items-center justify-between">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <AlertTriangle className="h-4 w-4 text-yellow-600" />
                                                        <p className="font-medium text-gray-900">Task #{task.id}: {task.reason}</p>
                                                    </div>
                                                    <p className="text-sm text-gray-600">
                                                        Priority: {task.priority} • Created: {new Date(task.created_at).toLocaleString()}
                                                    </p>
                                                </div>
                                                <button className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm transition-colors">
                                                    Review
                                                </button>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default OrchestratorDashboard;
