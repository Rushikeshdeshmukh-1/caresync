import React, { useState, useEffect } from 'react'
import { Plus, Search, Activity, Thermometer, Heart, Weight } from 'lucide-react'

export default function Encounters() {
    const [encounters, setEncounters] = useState([])
    const [patients, setPatients] = useState([])
    const [showForm, setShowForm] = useState(false)
    const [formData, setFormData] = useState({
        patient_id: '',
        chief_complaint: ''
    })

    useEffect(() => {
        fetchEncounters()
        fetchPatients()
    }, [])

    const fetchEncounters = async () => {
        try {
            const response = await fetch('/api/encounters')
            const data = await response.json()
            setEncounters(data.encounters || [])
        } catch (error) {
            console.error('Error fetching encounters:', error)
        }
    }

    const fetchPatients = async () => {
        try {
            const response = await fetch('/api/patients')
            const data = await response.json()
            setPatients(data.patients || [])
        } catch (error) {
            console.error('Error fetching patients:', error)
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            const response = await fetch('/api/encounters', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            })
            if (response.ok) {
                setShowForm(false)
                fetchEncounters()
                setFormData({ patient_id: '', chief_complaint: '' })
            }
        } catch (error) {
            console.error('Error creating encounter:', error)
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold text-gray-900">Patient Encounters</h1>
                <button
                    onClick={() => setShowForm(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                    <Plus size={20} />
                    New Encounter
                </button>
            </div>

            {showForm && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl p-6 w-full max-w-md">
                        <h2 className="text-xl font-bold mb-4">Start New Encounter</h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Patient</label>
                                <select
                                    required
                                    className="w-full p-2 border border-gray-300 rounded-lg"
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
                                    className="w-full p-2 border border-gray-300 rounded-lg"
                                    rows="3"
                                    placeholder="e.g., Fever, Cough, Headache"
                                    value={formData.chief_complaint}
                                    onChange={e => setFormData({ ...formData, chief_complaint: e.target.value })}
                                ></textarea>
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
                                    Start
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            <div className="space-y-4">
                {encounters.map((encounter) => (
                    <div key={encounter.id} className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                        <div className="flex items-start justify-between mb-4">
                            <div>
                                <h3 className="text-lg font-bold text-gray-900">
                                    {patients.find(p => p.id === encounter.patient_id)?.name || 'Unknown Patient'}
                                </h3>
                                <p className="text-sm text-gray-500">
                                    {new Date(encounter.date).toLocaleDateString()} at {new Date(encounter.date).toLocaleTimeString()}
                                </p>
                            </div>
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${encounter.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                                }`}>
                                {encounter.status}
                            </span>
                        </div>

                        <div className="bg-gray-50 p-4 rounded-lg mb-4">
                            <h4 className="text-sm font-medium text-gray-700 mb-2">Chief Complaint</h4>
                            <p className="text-gray-900">{encounter.chief_complaint}</p>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                                <Thermometer size={16} className="text-red-500" />
                                <span>Temp: --</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                                <Activity size={16} className="text-blue-500" />
                                <span>BP: --/--</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                                <Heart size={16} className="text-pink-500" />
                                <span>Pulse: --</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                                <Weight size={16} className="text-orange-500" />
                                <span>Weight: --</span>
                            </div>
                        </div>

                        <div className="flex gap-2 pt-4 border-t border-gray-100">
                            <button className="flex-1 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 font-medium text-sm">
                                View Details
                            </button>
                            <button className="flex-1 px-4 py-2 bg-gray-50 text-gray-600 rounded-lg hover:bg-gray-100 font-medium text-sm">
                                Add Vitals
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
