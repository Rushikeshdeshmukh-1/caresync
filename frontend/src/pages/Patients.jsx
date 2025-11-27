import React, { useState, useEffect } from 'react'
import { Plus, Search, Phone, Mail, User } from 'lucide-react'

export default function Patients() {
    const [patients, setPatients] = useState([])
    const [loading, setLoading] = useState(true)
    const [showForm, setShowForm] = useState(false)
    const [formData, setFormData] = useState({
        name: '',
        age: '',
        gender: '',
        phone: '',
        email: '',
        abha_id: ''
    })

    useEffect(() => {
        fetchPatients()
    }, [])

    const fetchPatients = async () => {
        try {
            const response = await fetch('/api/patients')
            const data = await response.json()
            setPatients(data.patients || [])
            setLoading(false)
        } catch (error) {
            console.error('Error fetching patients:', error)
            setLoading(false)
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            const response = await fetch('/api/patients', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            })
            if (response.ok) {
                setShowForm(false)
                fetchPatients()
                setFormData({ name: '', age: '', gender: '', phone: '', email: '', abha_id: '' })
            }
        } catch (error) {
            console.error('Error creating patient:', error)
        }
    }

    const [historyModalOpen, setHistoryModalOpen] = useState(false)
    const [selectedPatient, setSelectedPatient] = useState(null)
    const [patientHistory, setPatientHistory] = useState([])
    const [historyLoading, setHistoryLoading] = useState(false)

    const handleViewHistory = async (patient) => {
        setSelectedPatient(patient)
        setHistoryModalOpen(true)
        setHistoryLoading(true)
        try {
            const response = await fetch(`/api/encounters?patient_id=${patient.id}`)
            if (response.ok) {
                const data = await response.json()
                setPatientHistory(data.encounters || [])
            } else {
                console.error('Failed to fetch history')
            }
        } catch (error) {
            console.error('Error fetching history:', error)
        } finally {
            setHistoryLoading(false)
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold text-gray-900">Patients</h1>
                <button
                    onClick={() => setShowForm(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                    <Plus size={20} />
                    Add Patient
                </button>
            </div>

            {showForm && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl p-6 w-full max-w-md">
                        <h2 className="text-xl font-bold mb-4">Register New Patient</h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                                <input
                                    type="text"
                                    required
                                    className="w-full p-2 border border-gray-300 rounded-lg"
                                    value={formData.name}
                                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Age</label>
                                    <input
                                        type="number"
                                        className="w-full p-2 border border-gray-300 rounded-lg"
                                        value={formData.age}
                                        onChange={e => setFormData({ ...formData, age: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
                                    <select
                                        className="w-full p-2 border border-gray-300 rounded-lg"
                                        value={formData.gender}
                                        onChange={e => setFormData({ ...formData, gender: e.target.value })}
                                    >
                                        <option value="">Select</option>
                                        <option value="M">Male</option>
                                        <option value="F">Female</option>
                                        <option value="O">Other</option>
                                    </select>
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                                <input
                                    type="tel"
                                    className="w-full p-2 border border-gray-300 rounded-lg"
                                    value={formData.phone}
                                    onChange={e => setFormData({ ...formData, phone: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">ABHA ID</label>
                                <input
                                    type="text"
                                    className="w-full p-2 border border-gray-300 rounded-lg"
                                    value={formData.abha_id}
                                    onChange={e => setFormData({ ...formData, abha_id: e.target.value })}
                                />
                            </div>
                            <div className="flex gap-3 mt-6">
                                <button
                                    type="button"
                                    onClick={() => setShowForm(false)}
                                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                                >
                                    Register
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {historyModalOpen && selectedPatient && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
                    <div className="bg-white rounded-xl p-6 w-full max-w-2xl shadow-2xl max-h-[80vh] flex flex-col">
                        <div className="flex justify-between items-center mb-6">
                            <div>
                                <h2 className="text-xl font-bold text-gray-900">Patient History</h2>
                                <p className="text-sm text-gray-500">{selectedPatient.name} (Age: {selectedPatient.age})</p>
                            </div>
                            <button
                                onClick={() => setHistoryModalOpen(false)}
                                className="text-gray-400 hover:text-gray-600"
                            >
                                <span className="text-2xl">&times;</span>
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto">
                            {historyLoading ? (
                                <div className="text-center py-10">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                                    <p className="mt-2 text-gray-500">Loading history...</p>
                                </div>
                            ) : patientHistory.length === 0 ? (
                                <div className="text-center py-10 bg-gray-50 rounded-lg border border-gray-100">
                                    <p className="text-gray-500">No previous encounters found for this patient.</p>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {patientHistory.map(encounter => (
                                        <div key={encounter.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                                            <div className="flex justify-between items-start mb-2">
                                                <div>
                                                    <span className="text-sm font-bold text-blue-600">
                                                        {new Date(encounter.visit_date).toLocaleDateString()}
                                                    </span>
                                                    <span className="mx-2 text-gray-300">|</span>
                                                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${encounter.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
                                                        }`}>
                                                        {encounter.status}
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="space-y-1">
                                                <p className="text-sm text-gray-900"><span className="font-medium">Chief Complaint:</span> {encounter.chief_complaint}</p>
                                                {encounter.diagnosis && (
                                                    <p className="text-sm text-gray-600"><span className="font-medium">Diagnosis:</span> {encounter.diagnosis}</p>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className="mt-6 flex justify-end">
                            <button
                                onClick={() => setHistoryModalOpen(false)}
                                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="p-4 border-b border-gray-200">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                        <input
                            type="text"
                            placeholder="Search patients..."
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase">Patient</th>
                                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase">Contact</th>
                                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase">Age/Gender</th>
                                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase">ABHA ID</th>
                                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {loading ? (
                                <tr><td colSpan="5" className="px-6 py-4 text-center">Loading...</td></tr>
                            ) : patients.length === 0 ? (
                                <tr><td colSpan="5" className="px-6 py-4 text-center text-gray-500">No patients found</td></tr>
                            ) : (
                                patients.map((patient) => (
                                    <tr key={patient.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium">
                                                    {patient.name.charAt(0)}
                                                </div>
                                                <span className="font-medium text-gray-900">{patient.name}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col text-sm text-gray-500">
                                                <span className="flex items-center gap-1"><Phone size={14} /> {patient.phone || '-'}</span>
                                                {patient.email && <span className="flex items-center gap-1"><Mail size={14} /> {patient.email}</span>}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-500">
                                            {patient.age} / {patient.gender}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-500">
                                            {patient.abha_id || '-'}
                                        </td>
                                        <td className="px-6 py-4">
                                            <button
                                                onClick={() => handleViewHistory(patient)}
                                                className="text-blue-600 hover:text-blue-800 text-sm font-medium hover:underline"
                                            >
                                                View History
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}
