import React, { useState } from 'react'
import { LayoutDashboard, Users, Calendar, FileText, Pill, Receipt, Activity, Menu, X, Settings } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import Patients from './pages/Patients'
import Appointments from './pages/Appointments'
import Encounters from './pages/Encounters'
import Prescriptions from './pages/Prescriptions'
import Billing from './pages/Billing'
import Mapping from './pages/Mapping'
import OrchestratorDashboard from './pages/OrchestratorDashboard'

function App() {
    const [activeTab, setActiveTab] = useState('dashboard')
    const [isSidebarOpen, setIsSidebarOpen] = useState(true)

    const menuItems = [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { id: 'patients', label: 'Patients', icon: Users },
        { id: 'appointments', label: 'Appointments', icon: Calendar },
        { id: 'encounters', label: 'Encounters', icon: Activity },
        { id: 'prescriptions', label: 'Prescriptions', icon: Pill },
        { id: 'billing', label: 'Billing', icon: Receipt },
        { id: 'mapping', label: 'ICD-11 Mapping', icon: FileText },
        { id: 'orchestrator', label: 'Orchestrator', icon: Settings },
    ]

    const renderContent = () => {
        switch (activeTab) {
            case 'dashboard':
                return <Dashboard />
            case 'patients':
                return <Patients />
            case 'appointments':
                return <Appointments />
            case 'encounters':
                return <Encounters />
            case 'prescriptions':
                return <Prescriptions />
            case 'billing':
                return <Billing />
            case 'mapping':
                return <Mapping />
            case 'orchestrator':
                return <OrchestratorDashboard />
            default:
                return <Dashboard />
        }
    }

    return (
        <div className="min-h-screen bg-gray-50 flex">
            {/* Sidebar */}
            <aside
                className={`fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
                    } lg:relative lg:translate-x-0`}
            >
                <div className="h-16 flex items-center justify-between px-6 border-b border-gray-200">
                    <div className="flex items-center gap-2">
                        <Activity className="text-blue-600" size={24} />
                        <span className="text-xl font-bold text-gray-900">AyushCare</span>
                    </div>
                    <button
                        onClick={() => setIsSidebarOpen(false)}
                        className="lg:hidden text-gray-500 hover:text-gray-700"
                    >
                        <X size={24} />
                    </button>
                </div>

                <nav className="p-4 space-y-1">
                    {menuItems.map((item) => {
                        const Icon = item.icon
                        return (
                            <button
                                key={item.id}
                                onClick={() => {
                                    setActiveTab(item.id)
                                    if (window.innerWidth < 1024) setIsSidebarOpen(false)
                                }}
                                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${activeTab === item.id
                                    ? 'bg-blue-50 text-blue-700'
                                    : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                                    }`}
                            >
                                <Icon size={20} />
                                {item.label}
                            </button>
                        )
                    })}
                </nav>

                <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
                    <div className="flex items-center gap-3 px-4 py-3">
                        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">
                            DR
                        </div>
                        <div>
                            <p className="text-sm font-medium text-gray-900">Dr. Rushikesh</p>
                            <p className="text-xs text-gray-500">Admin</p>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                {/* Mobile Header */}
                <header className="lg:hidden h-16 bg-white border-b border-gray-200 flex items-center px-4">
                    <button
                        onClick={() => setIsSidebarOpen(true)}
                        className="text-gray-500 hover:text-gray-700"
                    >
                        <Menu size={24} />
                    </button>
                    <span className="ml-4 text-lg font-semibold text-gray-900">AyushCare</span>
                </header>

                <main className="flex-1 overflow-y-auto p-4 lg:p-8">
                    {renderContent()}
                </main>
            </div>
        </div>
    )
}

export default App
