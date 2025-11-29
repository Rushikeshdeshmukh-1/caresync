import React, { useState, useEffect } from 'react';
import { Calendar, Clock, User, Plus, Search, X } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

const API_BASE = 'http://localhost:8000';

export default function AppointmentsV2() {
    const { token } = useAuth();
    const [appointments, setAppointments] = useState([]);
    const [patients, setPatients] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [filter, setFilter] = useState({ status: 'all', search: '' });
    const [formData, setFormData] = useState({
        patientId: '',
        doctorId: 'admin',
        startTime: '',
        endTime: '',
        reason: '',
        notes: ''
    });

    useEffect(() => {
        if (token) {
            fetchAppointments();
            fetchPatients();
        }
    }, [filter, token]);

    const fetchAppointments = async () => {
        try {
            setLoading(true);
            const params = new URLSearchParams();
            if (filter.status !== 'all') params.append('status', filter.status);

            const response = await fetch(`${API_BASE}/api/v2/appointments?${params}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            const data = await response.json();
            setAppointments(data.appointments || []);
        } catch (error) {
            console.error('Error fetching appointments:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchPatients = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/patients?limit=100`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            const data = await response.json();
            console.log('Fetched patients:', data);
            setPatients(data.patients || []);
        } catch (error) {
            console.error('Error fetching patients:', error);
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(`${API_BASE}/api/v2/appointments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                setShowCreateModal(false);
                setFormData({
                    patientId: '',
                    doctorId: 'admin',
                    startTime: '',
                    endTime: '',
                    reason: '',
                    notes: ''
                });
                fetchAppointments();
            }
        } catch (error) {
            console.error('Error creating appointment:', error);
        }
    };

    const handleCancel = async (id) => {
        if (!confirm('Cancel this appointment?')) return;

        try {
            const response = await fetch(`${API_BASE}/api/v2/appointments/${id}/cancel`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                fetchAppointments();
            }
        } catch (error) {
            console.error('Error cancelling appointment:', error);
        }
    };

    const formatDateTime = (datetime) => {
        if (!datetime) return '';
        const date = new Date(datetime);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getStatusColor = (status) => {
        const colors = {
            scheduled: 'bg-blue-100 text-blue-800',
            confirmed: 'bg-green-100 text-green-800',
            in_progress: 'bg-yellow-100 text-yellow-800',
            completed: 'bg-gray-100 text-gray-800',
            cancelled: 'bg-red-100 text-red-800',
            no_show: 'bg-orange-100 text-orange-800'
        };
        return colors[status] || 'bg-gray-100 text-gray-800';
    };

    const filteredAppointments = appointments.filter(apt =>
        filter.search === '' ||
        apt.patient_name?.toLowerCase().includes(filter.search.toLowerCase()) ||
        apt.reason?.toLowerCase().includes(filter.search.toLowerCase())
    );

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Appointments</h1>
                    <p className="text-gray-600">Manage patient appointments</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                    <Plus size={20} />
                    Book Appointment
                </button>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-lg shadow p-4 flex gap-4 flex-wrap">
                <div className="flex-1 min-w-[200px]">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                        <input
                            type="text"
                            placeholder="Search appointments..."
                            value={filter.search}
                            onChange={(e) => setFilter({ ...filter, search: e.target.value })}
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>
                </div>
                <select
                    value={filter.status}
                    onChange={(e) => setFilter({ ...filter, status: e.target.value })}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                    <option value="all">All Status</option>
                    <option value="scheduled">Scheduled</option>
                    <option value="confirmed">Confirmed</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                </select>
            </div>

            {/* Appointments List */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                {loading ? (
                    <div className="p-8 text-center text-gray-500">Loading appointments...</div>
                ) : filteredAppointments.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">
                        No appointments found. Book your first appointment!
                    </div>
                ) : (
                    <div className="divide-y divide-gray-200">
                        {filteredAppointments.map((appointment) => (
                            <div key={appointment.id} className="p-4 hover:bg-gray-50 transition-colors">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <User className="text-gray-400" size={20} />
                                            <h3 className="font-semibold text-gray-900">
                                                {appointment.patient_name || 'Unknown Patient'}
                                            </h3>
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(appointment.status)}`}>
                                                {appointment.status}
                                            </span>
                                        </div>
                                        <div className="ml-8 space-y-1 text-sm text-gray-600">
                                            <div className="flex items-center gap-2">
                                                <Calendar size={16} />
                                                <span>{formatDateTime(appointment.start_time)}</span>
                                                <span>-</span>
                                                <span>{formatDateTime(appointment.end_time)}</span>
                                            </div>
                                            {appointment.reason && (
                                                <div className="flex items-center gap-2">
                                                    <Clock size={16} />
                                                    <span>{appointment.reason}</span>
                                                </div>
                                            )}
                                            {appointment.notes && (
                                                <p className="text-gray-500 italic">{appointment.notes}</p>
                                            )}
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        {appointment.status === 'scheduled' && (
                                            <button
                                                onClick={() => handleCancel(appointment.id)}
                                                className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                            >
                                                Cancel
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Create Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6">
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-bold text-gray-900">Book Appointment</h2>
                                <button
                                    onClick={() => setShowCreateModal(false)}
                                    className="text-gray-400 hover:text-gray-600"
                                >
                                    <X size={24} />
                                </button>
                            </div>
                            <form onSubmit={handleCreate} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Patient * {patients.length > 0 && <span className="text-gray-500">({patients.length} available)</span>}
                                    </label>
                                    <select
                                        required
                                        value={formData.patientId}
                                        onChange={(e) => setFormData({ ...formData, patientId: e.target.value })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    >
                                        <option value="">
                                            {patients.length === 0 ? 'No patients found - Please register a patient first' : 'Select patient'}
                                        </option>
                                        {patients.map((patient) => (
                                            <option key={patient.id} value={patient.id}>
                                                {patient.name}
                                            </option>
                                        ))}
                                    </select>
                                    {patients.length === 0 && (
                                        <p className="mt-1 text-sm text-red-600">
                                            Please go to Patients tab and register a patient first
                                        </p>
                                    )}
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Start Time *
                                    </label>
                                    <input
                                        type="datetime-local"
                                        required
                                        value={formData.startTime}
                                        onChange={(e) => {
                                            const start = e.target.value;
                                            const endTime = start ? new Date(new Date(start).getTime() + 30 * 60000).toISOString().slice(0, 16) : '';
                                            setFormData({ ...formData, startTime: start, endTime });
                                        }}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        End Time *
                                    </label>
                                    <input
                                        type="datetime-local"
                                        required
                                        value={formData.endTime}
                                        onChange={(e) => setFormData({ ...formData, endTime: e.target.value })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Reason
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.reason}
                                        onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                                        placeholder="e.g., Regular checkup"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Notes
                                    </label>
                                    <textarea
                                        value={formData.notes}
                                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                                        rows={3}
                                        placeholder="Additional notes..."
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>
                                <div className="flex gap-3 pt-4">
                                    <button
                                        type="button"
                                        onClick={() => setShowCreateModal(false)}
                                        className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                                    >
                                        Book Appointment
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
