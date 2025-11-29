// Admin Audit Logs Viewer
import { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';

export default function AuditLogs() {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [filters, setFilters] = useState({
        user_id: '',
        action: '',
        limit: 100
    });
    const { token } = useAuth();

    useEffect(() => {
        loadLogs();
    }, [filters]);

    const loadLogs = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (filters.user_id) params.append('user_id', filters.user_id);
            if (filters.action) params.append('action', filters.action);
            params.append('limit', filters.limit);

            const response = await fetch(`http://localhost:8000/api/admin/audit-logs?${params}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            setLogs(data.logs || []);
        } catch (err) {
            console.error('Error loading logs:', err);
        } finally {
            setLoading(false);
        }
    };

    const getActionBadgeColor = (action) => {
        if (action.includes('create')) return 'bg-green-100 text-green-800';
        if (action.includes('update')) return 'bg-blue-100 text-blue-800';
        if (action.includes('delete')) return 'bg-red-100 text-red-800';
        if (action.includes('approve')) return 'bg-purple-100 text-purple-800';
        return 'bg-gray-100 text-gray-800';
    };

    const getStatusBadgeColor = (status) => {
        if (status === 'success') return 'bg-green-100 text-green-800';
        if (status === 'failed') return 'bg-red-100 text-red-800';
        if (status === 'blocked') return 'bg-yellow-100 text-yellow-800';
        return 'bg-gray-100 text-gray-800';
    };

    return (
        <div className="max-w-7xl mx-auto p-6">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Audit Logs</h1>
                <p className="text-gray-600">Monitor all system actions and security events</p>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-lg shadow p-6 mb-6">
                <h2 className="text-lg font-semibold mb-4">Filters</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">User ID</label>
                        <input
                            type="text"
                            value={filters.user_id}
                            onChange={(e) => setFilters({ ...filters, user_id: e.target.value })}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            placeholder="Filter by user..."
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Action</label>
                        <select
                            value={filters.action}
                            onChange={(e) => setFilters({ ...filters, action: e.target.value })}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="">All Actions</option>
                            <option value="create">Create</option>
                            <option value="update">Update</option>
                            <option value="delete">Delete</option>
                            <option value="approve">Approve</option>
                            <option value="reject">Reject</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Limit</label>
                        <select
                            value={filters.limit}
                            onChange={(e) => setFilters({ ...filters, limit: parseInt(e.target.value) })}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="50">50 logs</option>
                            <option value="100">100 logs</option>
                            <option value="500">500 logs</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Logs Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                {loading ? (
                    <div className="text-center py-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    </div>
                ) : logs.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                        No audit logs found
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Resource</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {logs.map((log) => (
                                    <tr key={log.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                            {new Date(log.timestamp).toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm font-medium text-gray-900">{log.user_id || 'System'}</div>
                                            <div className="text-xs text-gray-500">{log.actor_type}</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getActionBadgeColor(log.action)}`}>
                                                {log.action}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm text-gray-900">{log.resource}</div>
                                            {log.resource_id && (
                                                <div className="text-xs text-gray-500">{log.resource_id}</div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeColor(log.status)}`}>
                                                {log.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Stats */}
            <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white rounded-lg shadow p-4">
                    <div className="text-sm text-gray-500 mb-1">Total Logs</div>
                    <div className="text-2xl font-bold text-gray-900">{logs.length}</div>
                </div>
                <div className="bg-white rounded-lg shadow p-4">
                    <div className="text-sm text-gray-500 mb-1">Success</div>
                    <div className="text-2xl font-bold text-green-600">
                        {logs.filter(l => l.status === 'success').length}
                    </div>
                </div>
                <div className="bg-white rounded-lg shadow p-4">
                    <div className="text-sm text-gray-500 mb-1">Failed</div>
                    <div className="text-2xl font-bold text-red-600">
                        {logs.filter(l => l.status === 'failed').length}
                    </div>
                </div>
                <div className="bg-white rounded-lg shadow p-4">
                    <div className="text-sm text-gray-500 mb-1">Blocked</div>
                    <div className="text-2xl font-bold text-yellow-600">
                        {logs.filter(l => l.status === 'blocked').length}
                    </div>
                </div>
            </div>
        </div>
    );
}
