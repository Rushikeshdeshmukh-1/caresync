import React, { useState, useEffect } from 'react'
import { Plus, Search, ArrowLeft, Save } from 'lucide-react'
import CoPilotPanel from '../components/CoPilotPanel'

export default function Encounters() {
    const [encounters, setEncounters] = useState([])
    const [patients, setPatients] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [showForm, setShowForm] = useState(false)
    const [submitting, setSubmitting] = useState(false)
    const [selectedEncounter, setSelectedEncounter] = useState(null)

    // Form data for new encounter
    const [formData, setFormData] = useState({
        patient_id: '',
        chief_complaint: ''
    })

    // Detailed view state
    const [encounterDetails, setEncounterDetails] = useState(null)
    const [detailsLoading, setDetailsLoading] = useState(false)

    useEffect(() => {
        fetchData()
    }, [])

    const fetchData = async () => {
        setLoading(true)
        setError(null)
        try {
            await Promise.all([fetchEncounters(), fetchPatients()])
        } catch (err) {
            console.error("Error fetching data:", err)
            setError("Failed to load data. Please try again.")
        } finally {
            setLoading(false)
        }
    }

    const fetchEncounters = async () => {
        const response = await fetch('/api/encounters')
        if (!response.ok) throw new Error('Failed to fetch encounters')
        const data = await response.json()
        setEncounters(data.encounters || [])
    }

    const fetchPatients = async () => {
        const response = await fetch('/api/patients')
        if (!response.ok) throw new Error('Failed to fetch patients')
        const data = await response.json()
        setPatients(data.patients || [])
    }

    const handleCreateEncounter = async (e) => {
        e.preventDefault()
        setSubmitting(true)
        setError(null)

        try {
            const response = await fetch('/api/encounters', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Failed to create encounter')
            }

            // Success
            setShowForm(false)
            setFormData({ patient_id: '', chief_complaint: '' })
            fetchEncounters() // Refresh list
        } catch (err) {
            console.error('Error creating encounter:', err)
            setError(err.message)
        } finally {
            setSubmitting(false)
        }
    }

    const handleViewEncounter = async (encounterId) => {
        setDetailsLoading(true)
        try {
            const response = await fetch(`/api/encounters/${encounterId}`)
            if (!response.ok) throw new Error('Failed to fetch encounter details')
            const data = await response.json()
            setEncounterDetails(data)
            setSelectedEncounter(encounterId)
        } catch (err) {
            console.error('Error fetching details:', err)
            setError("Failed to load encounter details.")
        } finally {
            setDetailsLoading(false)
        }
    }

    const handleUpdateNotes = (field, value) => {
        setEncounterDetails(prev => ({
            ...prev,
            [field]: value
        }))
    }

    // Combine all notes for Co-Pilot analysis
    const getCombinedNotes = () => {
        if (!encounterDetails) return '';
        return `
Chief Complaint: ${encounterDetails.chief_complaint || ''}
History of Present Illness: ${encounterDetails.history_of_present_illness || ''}
Examination: ${encounterDetails.examination || ''}
Assessment: ${encounterDetails.assessment || ''}
Plan: ${encounterDetails.plan || ''}
        `.trim();
    }

    if (selectedEncounter && encounterDetails) {
        return (
            <div className="flex h-[calc(100vh-64px)] overflow-hidden bg-gray-50">
                {/* Main Content - Clinical Notes */}
                <div className="flex-1 flex flex-col overflow-hidden">
                    {/* Header */}
                    <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between shadow-sm z-10">
                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => setSelectedEncounter(null)}
                                className="p-2 hover:bg-gray-100 rounded-full text-gray-600 transition-colors"
                            >
                                <ArrowLeft size={20} />
                            </button>
                            <div>
                                <h1 className="text-xl font-bold text-gray-900">{encounterDetails.patient_name}</h1>
                                <p className="text-sm text-gray-500">
                                    {new Date(encounterDetails.visit_date).toLocaleDateString()} • {encounterDetails.status}
                                </p>
                            </div>
                        </div>
                        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm">
                            <Save size={18} />
                            Save Changes
                        </button>
                    </div>

                    {/* Scrollable Content */}
                    <div className="flex-1 overflow-y-auto p-6 space-y-6">
                        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                            <label className="block text-sm font-bold text-gray-700 mb-2 uppercase tracking-wide">Chief Complaint</label>
                            <textarea
                                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                                rows="2"
                                value={encounterDetails.chief_complaint || ''}
                                onChange={e => handleUpdateNotes('chief_complaint', e.target.value)}
                                placeholder="Patient's primary complaint..."
                            />
                        </div>

                        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                            <label className="block text-sm font-bold text-gray-700 mb-2 uppercase tracking-wide">History of Present Illness</label>
                            <textarea
                                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                                rows="4"
                                value={encounterDetails.history_of_present_illness || ''}
                                onChange={e => handleUpdateNotes('history_of_present_illness', e.target.value)}
                                placeholder="Detailed history..."
                            />
                        </div>

                        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                            <label className="block text-sm font-bold text-gray-700 mb-2 uppercase tracking-wide">Examination</label>
                            <textarea
                                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                                rows="4"
                                value={encounterDetails.examination || ''}
                                onChange={e => handleUpdateNotes('examination', e.target.value)}
                                placeholder="Physical examination findings..."
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-6">
                            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                                <label className="block text-sm font-bold text-gray-700 mb-2 uppercase tracking-wide">Assessment</label>
                                <textarea
                                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                                    rows="4"
                                    value={encounterDetails.assessment || ''}
                                    onChange={e => handleUpdateNotes('assessment', e.target.value)}
                                    placeholder="Clinical assessment..."
                                />
                            </div>
                            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                                <label className="block text-sm font-bold text-gray-700 mb-2 uppercase tracking-wide">Plan</label>
                                <textarea
                                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                                    rows="4"
                                    value={encounterDetails.plan || ''}
                                    onChange={e => handleUpdateNotes('plan', e.target.value)}
                                    placeholder="Treatment plan..."
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Sidebar - Co-Pilot */}
                <CoPilotPanel
                    encounterId={selectedEncounter}
                    notes={getCombinedNotes()}
                    patientContext={{
                        // Mock context for now, ideally fetch from patient record
                        medications: [],
                        conditions: []
                    }}
                />
            </div>
        )
    }

    return (
        <div className="space-y-6 p-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold text-gray-900">Patient Encounters</h1>
                <button
                    onClick={() => setShowForm(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
                >
                    <Plus size={20} />
                    New Encounter
                </button>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg relative shadow-sm" role="alert">
                    <strong className="font-bold">Error: </strong>
                    <span className="block sm:inline">{error}</span>
                </div>
            )}

            {loading ? (
                <div className="text-center py-20">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-500 font-medium">Loading encounters...</p>
                </div>
            ) : (
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <table className="w-full text-left">
                        <thead className="bg-gray-50 border-b border-gray-200">
                            <tr>
                                <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider">Date</th>
                                <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider">Patient</th>
                                <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider">Chief Complaint</th>
                                <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {encounters.length === 0 ? (
                                <tr>
                                    <td colSpan="5" className="px-6 py-16 text-center text-gray-500">
                                        <div className="flex flex-col items-center justify-center">
                                            <div className="bg-gray-100 p-4 rounded-full mb-4">
                                                <Search size={24} className="text-gray-400" />
                                            </div>
                                            <p className="text-lg font-medium text-gray-900">No encounters found</p>
                                            <p className="text-sm text-gray-500 mt-1">Get started by creating a new encounter.</p>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                encounters.map(encounter => (
                                    <tr key={encounter.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4 text-sm text-gray-500 whitespace-nowrap">
                                            {new Date(encounter.visit_date).toLocaleDateString()}
                                        </td>
                                        <td className="px-6 py-4 text-sm font-medium text-gray-900">
                                            {encounter.patient_name || encounter.patient_id}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-500 truncate max-w-xs">
                                            {encounter.chief_complaint}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2.5 py-0.5 text-xs font-medium rounded-full ${encounter.status === 'completed'
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-blue-100 text-blue-800'
                                                }`}>
                                                {encounter.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-sm whitespace-nowrap">
                                            <button
                                                onClick={() => handleViewEncounter(encounter.id)}
                                                className="text-blue-600 hover:text-blue-800 font-medium hover:underline"
                                            >
                                                View / Edit
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            )}

            {showForm && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
                    <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-2xl transform transition-all">
                        <h2 className="text-xl font-bold mb-4 text-gray-900">Start New Encounter</h2>

                        {error && (
                            <div className="mb-4 bg-red-50 text-red-700 p-3 rounded-lg text-sm border border-red-100">
                                {error}
                            </div>
                        )}

                        <form onSubmit={handleCreateEncounter} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Patient</label>
                                <select
                                    required
                                    className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-gray-50"
                                    value={formData.patient_id}
                                    onChange={e => setFormData({ ...formData, patient_id: e.target.value })}
                                >
                                    <option value="">Select Patient</option>
                                    {patients.map(p => (
                                        <option key={p.id} value={p.id}>{p.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Chief Complaint</label>
                                <textarea
                                    required
                                    className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-gray-50"
                                    rows="3"
                                    placeholder="e.g., Fever, Cough, Headache"
                                    value={formData.chief_complaint}
                                    onChange={e => setFormData({ ...formData, chief_complaint: e.target.value })}
                                ></textarea>
                            </div>
                            <div className="flex gap-3 mt-6 justify-end">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setShowForm(false)
                                        setError(null)
                                    }}
                                    className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors font-medium"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={submitting}
                                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium shadow-sm"
                                >
                                    {submitting ? (
                                        <>
                                            <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                            Starting...
                                        </>
                                    ) : (
                                        'Start Encounter'
                                    )}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}
