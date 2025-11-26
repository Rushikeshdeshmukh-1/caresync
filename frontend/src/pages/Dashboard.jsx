import React, { useState, useEffect } from 'react'
import { Users, Calendar, Activity, TrendingUp, DollarSign, FileText } from 'lucide-react'

const API_BASE = 'http://localhost:8000';

export default function Dashboard() {
    const [stats, setStats] = useState({
        total_patients: 0,
        today_appointments: 0,
        pending_appointments: 0,
        today_revenue: 0,
        active_prescriptions: 0,
        unpaid_bills: 0
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDashboardStats();
    }, []);

    const fetchDashboardStats = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/dashboard/stats`);
            const data = await response.json();
            setStats(data);
        } catch (error) {
            console.error('Error fetching dashboard stats:', error);
        } finally {
            setLoading(false);
        }
    };

    const statCards = [
        {
            name: 'Total Patients',
            value: stats.total_patients,
            icon: Users,
            color: 'text-blue-600 bg-blue-100',
            subtext: 'Registered patients'
        },
        {
            name: 'Today\'s Appointments',
            value: stats.today_appointments,
            icon: Calendar,
            color: 'text-purple-600 bg-purple-100',
            subtext: `${stats.pending_appointments} pending`
        },
        {
            name: 'Active Prescriptions',
            value: stats.active_prescriptions,
            icon: FileText,
            color: 'text-green-600 bg-green-100',
            subtext: 'Last 30 days'
        },
        {
            name: 'Today\'s Revenue',
            value: `₹${stats.today_revenue.toLocaleString()}`,
            icon: TrendingUp,
            color: 'text-orange-600 bg-orange-100',
            subtext: `${stats.unpaid_bills} unpaid bills`
        },
    ];

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-gray-500">Loading dashboard...</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
                    <p className="text-sm text-gray-500 mt-1">
                        Real-time data • Last updated: {new Date().toLocaleTimeString()}
                    </p>
                </div>
                <div className="text-xs bg-green-100 text-green-700 px-3 py-1 rounded-full">
                    ● Live Data (V2)
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {statCards.map((stat) => {
                    const Icon = stat.icon;
                    return (
                        <div key={stat.name} className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
                            <div className="flex items-center justify-between">
                                <div className={`p-3 rounded-lg ${stat.color}`}>
                                    <Icon size={24} />
                                </div>
                            </div>
                            <div className="mt-4">
                                <h3 className="text-sm font-medium text-gray-500">{stat.name}</h3>
                                <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
                                <p className="text-xs text-gray-400 mt-1">{stat.subtext}</p>
                            </div>
                        </div>
                    );
                })}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                    <h2 className="text-lg font-bold text-gray-900 mb-4">Quick Stats</h2>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                            <span className="text-sm text-gray-600">Pending Appointments</span>
                            <span className="font-semibold text-gray-900">{stats.pending_appointments}</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                            <span className="text-sm text-gray-600">Active Prescriptions</span>
                            <span className="font-semibold text-gray-900">{stats.active_prescriptions}</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                            <span className="text-sm text-gray-600">Unpaid Bills</span>
                            <span className="font-semibold text-gray-900">{stats.unpaid_bills}</span>
                        </div>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                    <h2 className="text-lg font-bold text-gray-900 mb-4">System Info</h2>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                            <span className="text-sm text-blue-900">Data Source</span>
                            <span className="font-semibold text-blue-900">V2 Tables (Real-time)</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                            <span className="text-sm text-green-900">Database</span>
                            <span className="font-semibold text-green-900">SQLite</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                            <span className="text-sm text-purple-900">API Version</span>
                            <span className="font-semibold text-purple-900">V2.0</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
