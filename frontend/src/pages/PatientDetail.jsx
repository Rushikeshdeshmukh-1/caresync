import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import { User, FileText, Activity, Pill, Clock } from 'lucide-react'
import ProblemList from '../components/ProblemList'

export default function PatientDetail() {
    const { id } = useParams()
    const [activeTab, setActiveTab] = useState('problems')

    const tabs = [
        { id: 'overview', label: 'Overview', icon: User },
        { id: 'problems', label: 'Problems', icon: Activity },
        { id: 'encounters', label: 'Encounters', icon: FileText },
        { id: 'medications', label: 'Medications', icon: Pill },
        { id: 'history', label: 'History', icon: Clock },
    ]

    return (
        <div className="space-y-6">
            {/* Patient Header */}
            <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
                <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                        <div className="w-16 h-16 rounded-full bg-primary/10 text-primary flex items-center justify-center text-2xl font-bold">
                            R
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Rahul Sharma</h1>
                            <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
                                <span>32 Years</span>
                                <span>•</span>
                                <span>Male</span>
                                <span>•</span>
                                <span>ID: P-{id}</span>
                            </div>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button className="px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                            Edit Profile
                        </button>
                        <button className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90">
                            Start Visit
                        </button>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="border-b border-gray-200 dark:border-gray-700">
                <nav className="flex space-x-8" aria-label="Tabs">
                    {tabs.map((tab) => {
                        const Icon = tab.icon
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`
                  flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm
                  ${activeTab === tab.id
                                        ? 'border-primary text-primary'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                `}
                            >
                                <Icon size={18} />
                                {tab.label}
                            </button>
                        )
                    })}
                </nav>
            </div>

            {/* Tab Content */}
            <div className="min-h-[400px]">
                {activeTab === 'problems' && <ProblemList patientId={id} />}
                {activeTab === 'overview' && (
                    <div className="text-center py-12 text-gray-500">
                        Overview content placeholder
                    </div>
                )}
                {activeTab === 'encounters' && (
                    <div className="text-center py-12 text-gray-500">
                        Encounters content placeholder
                    </div>
                )}
                {/* Add other tabs as needed */}
            </div>
        </div>
    )
}
