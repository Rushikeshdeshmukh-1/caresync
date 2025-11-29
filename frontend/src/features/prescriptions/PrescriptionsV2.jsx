import React, { useState, useEffect } from 'react';
import { Plus, Search, X, Pill, User, Calendar, FileText } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

const API_BASE = 'http://localhost:8000';

export default function PrescriptionsV2() {
    const { token } = useAuth();
    const [prescriptions, setPrescriptions] = useState([]);
    const [patients, setPatients] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [formData, setFormData] = useState({
        patientId: '',
        doctorId: 'admin',
        diagnosis: '',
        notes: '',
        items: [{ medicine_name: '', form: '', dose: '', frequency: '', duration: '', instructions: '' }]
    });

    useEffect(() => {
        if (token) {
            fetchPrescriptions();
            fetchPatients();
        }
    }, [token]);

    const fetchPrescriptions = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE}/api/v2/prescriptions`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            const data = await response.json();
            setPrescriptions(data.prescriptions || []);
        } catch (error) {
            console.error('Error fetching prescriptions:', error);
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
            setPatients(data.patients || []);
        } catch (error) {
            console.error('Error fetching patients:', error);
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(`${API_BASE}/api/v2/prescriptions`, {
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
                    diagnosis: '',
                    notes: '',
                    items: [{ medicine_name: '', form: '', dose: '', frequency: '', duration: '', instructions: '' }]
                });
                fetchPrescriptions();
            }
        } catch (error) {
            console.error('Error creating prescription:', error);
        }
    };

    const addMedicineItem = () => {
        setFormData({
            ...formData,
            items: [...formData.items, { medicine_name: '', form: '', dose: '', frequency: '', duration: '', instructions: '' }]
        });
    };

    const removeMedicineItem = (index) => {
        const newItems = formData.items.filter((_, i) => i !== index);
        setFormData({ ...formData, items: newItems });
    };

    const updateMedicineItem = (index, field, value) => {
        const newItems = [...formData.items];
        newItems[index][field] = value;
        setFormData({ ...formData, items: newItems });
    };

    const formatDate = (dateString) => {
        if (!dateString) return '';
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    const filteredPrescriptions = prescriptions.filter(pres =>
        searchTerm === '' ||
        pres.patient_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        pres.diagnosis?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Prescriptions</h1>
                    <p className="text-gray-600">Manage patient prescriptions</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                    <Plus size={20} />
                    Create Prescription
                </button>
            </div>

            {/* Search */}
            <div className="bg-white rounded-lg shadow p-4">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                    <input
                        type="text"
                        placeholder="Search prescriptions..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                </div>
            </div>

            {/* Prescriptions List */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                {loading ? (
                    <div className="p-8 text-center text-gray-500">Loading prescriptions...</div>
                ) : filteredPrescriptions.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">
                        No prescriptions found. Create your first prescription!
                    </div>
                ) : (
                    <div className="divide-y divide-gray-200">
                        {filteredPrescriptions.map((prescription) => (
                            <div key={prescription.id} className="p-4 hover:bg-gray-50 transition-colors">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <User className="text-gray-400" size={20} />
                                            <h3 className="font-semibold text-gray-900">
                                                {prescription.patient_name || 'Unknown Patient'}
                                            </h3>
                                            <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                                                {prescription.item_count || 0} items
                                            </span>
                                        </div>
                                        <div className="ml-8 space-y-1 text-sm text-gray-600">
                                            <div className="flex items-center gap-2">
                                                <Calendar size={16} />
                                                <span>Issued: {formatDate(prescription.issued_at)}</span>
                                            </div>
                                            {prescription.diagnosis && (
                                                <div className="flex items-center gap-2">
                                                    <FileText size={16} />
                                                    <span className="font-medium">Diagnosis:</span>
                                                    <span>{prescription.diagnosis}</span>
                                                </div>
                                            )}
                                            {prescription.notes && (
                                                <p className="text-gray-500 italic">{prescription.notes}</p>
                                            )}
                                        </div>
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
                    <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6">
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-bold text-gray-900">Create Prescription</h2>
                                <button
                                    onClick={() => setShowCreateModal(false)}
                                    className="text-gray-400 hover:text-gray-600"
                                >
                                    <X size={24} />
                                </button>
                            </div>
                            <form onSubmit={handleCreate} className="space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                                            <option value="">Select patient</option>
                                            {patients.map((patient) => (
                                                <option key={patient.id} value={patient.id}>
                                                    {patient.name}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            Diagnosis
                                        </label>
                                        <input
                                            type="text"
                                            value={formData.diagnosis}
                                            onChange={(e) => setFormData({ ...formData, diagnosis: e.target.value })}
                                            placeholder="e.g., Common Cold"
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Notes
                                    </label>
                                    <textarea
                                        value={formData.notes}
                                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                                        rows={2}
                                        placeholder="Additional notes..."
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>

                                {/* Medicine Items */}
                                <div className="border-t pt-4">
                                    <div className="flex justify-between items-center mb-3">
                                        <h3 className="text-lg font-semibold text-gray-900">Medicines</h3>
                                        <button
                                            type="button"
                                            onClick={addMedicineItem}
                                            className="flex items-center gap-1 px-3 py-1 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700"
                                        >
                                            <Plus size={16} />
                                            Add Medicine
                                        </button>
                                    </div>

                                    {formData.items.map((item, index) => (
                                        <div key={index} className="mb-4 p-4 bg-gray-50 rounded-lg relative">
                                            {formData.items.length > 1 && (
                                                <button
                                                    type="button"
                                                    onClick={() => removeMedicineItem(index)}
                                                    className="absolute top-2 right-2 text-red-600 hover:text-red-800"
                                                >
                                                    <X size={20} />
                                                </button>
                                            )}
                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                                <div>
                                                    <label className="block text-xs font-medium text-gray-700 mb-1">
                                                        Medicine Name *
                                                    </label>
                                                    <input
                                                        type="text"
                                                        required
                                                        value={item.medicine_name}
                                                        onChange={(e) => updateMedicineItem(index, 'medicine_name', e.target.value)}
                                                        placeholder="e.g., Paracetamol"
                                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="block text-xs font-medium text-gray-700 mb-1">
                                                        Form
                                                    </label>
                                                    <input
                                                        type="text"
                                                        value={item.form}
                                                        onChange={(e) => updateMedicineItem(index, 'form', e.target.value)}
                                                        placeholder="e.g., Tablet"
                                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="block text-xs font-medium text-gray-700 mb-1">
                                                        Dose
                                                    </label>
                                                    <input
                                                        type="text"
                                                        value={item.dose}
                                                        onChange={(e) => updateMedicineItem(index, 'dose', e.target.value)}
                                                        placeholder="e.g., 500mg"
                                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="block text-xs font-medium text-gray-700 mb-1">
                                                        Frequency
                                                    </label>
                                                    <input
                                                        type="text"
                                                        value={item.frequency}
                                                        onChange={(e) => updateMedicineItem(index, 'frequency', e.target.value)}
                                                        placeholder="e.g., 3 times daily"
                                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="block text-xs font-medium text-gray-700 mb-1">
                                                        Duration
                                                    </label>
                                                    <input
                                                        type="text"
                                                        value={item.duration}
                                                        onChange={(e) => updateMedicineItem(index, 'duration', e.target.value)}
                                                        placeholder="e.g., 5 days"
                                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="block text-xs font-medium text-gray-700 mb-1">
                                                        Instructions
                                                    </label>
                                                    <input
                                                        type="text"
                                                        value={item.instructions}
                                                        onChange={(e) => updateMedicineItem(index, 'instructions', e.target.value)}
                                                        placeholder="e.g., After meals"
                                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    ))}
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
                                        Create Prescription
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
