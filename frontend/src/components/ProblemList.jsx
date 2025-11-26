import React, { useState } from 'react'
import { Plus, Search, AlertCircle, Check, X, Loader2 } from 'lucide-react'
import axios from 'axios'

export default function ProblemList({ patientId }) {
    const [isAdding, setIsAdding] = useState(false)
    const [searchTerm, setSearchTerm] = useState('')
    const [suggestions, setSuggestions] = useState([])
    const [loading, setLoading] = useState(false)
    const [selectedProblem, setSelectedProblem] = useState(null)
    const [problems, setProblems] = useState([
        { id: 1, term: 'Jwara', icdCode: 'MG26', icdTitle: 'Fever of other or unknown origin', status: 'Active' }
    ])

    const handleSearch = async () => {
        if (!searchTerm.trim()) return

        setLoading(true)
        try {
            const response = await axios.post('/api/suggest', {
                term: searchTerm,
                k: 3
            })
            setSuggestions(response.data.data.suggestions || [])
        } catch (error) {
            console.error('Error fetching suggestions:', error)
        } finally {
            setLoading(false)
        }
    }

    const handleAddProblem = () => {
        if (!selectedProblem) return

        const newProblem = {
            id: Date.now(),
            term: searchTerm,
            icdCode: selectedProblem.code,
            icdTitle: selectedProblem.title,
            status: 'Active'
        }

        setProblems([...problems, newProblem])
        setIsAdding(false)
        setSearchTerm('')
        setSuggestions([])
        setSelectedProblem(null)
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Problem List</h2>
                <button
                    onClick={() => setIsAdding(true)}
                    className="flex items-center gap-2 text-sm font-medium text-primary hover:text-primary/80"
                >
                    <Plus size={18} />
                    Add Problem
                </button>
            </div>

            {isAdding && (
                <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg border border-gray-200 dark:border-gray-700 space-y-4">
                    <div className="flex gap-2">
                        <div className="flex-1 relative">
                            <input
                                type="text"
                                placeholder="Enter NAMASTE term (e.g., Jwara, Kasa)..."
                                className="w-full pl-4 pr-10 py-2 rounded-lg border border-gray-300 dark:border-gray-600 focus:ring-2 focus:ring-primary/20 focus:border-primary"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                            />
                            <button
                                onClick={handleSearch}
                                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-primary"
                            >
                                {loading ? <Loader2 size={18} className="animate-spin" /> : <Search size={18} />}
                            </button>
                        </div>
                        <button
                            onClick={() => setIsAdding(false)}
                            className="px-4 py-2 text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg"
                        >
                            Cancel
                        </button>
                    </div>

                    {suggestions.length > 0 && (
                        <div className="space-y-2">
                            <p className="text-sm font-medium text-gray-500">ICD-11 Suggestions:</p>
                            <div className="grid gap-2">
                                {suggestions.map((suggestion, idx) => (
                                    <div
                                        key={idx}
                                        onClick={() => setSelectedProblem(suggestion)}
                                        className={`
                      p-3 rounded-lg border cursor-pointer transition-colors flex items-start gap-3
                      ${selectedProblem === suggestion
                                                ? 'border-primary bg-primary/5'
                                                : 'border-gray-200 dark:border-gray-700 hover:border-primary/50'}
                    `}
                                    >
                                        <div className={`mt-0.5 w-4 h-4 rounded-full border flex items-center justify-center ${selectedProblem === suggestion ? 'border-primary' : 'border-gray-400'}`}>
                                            {selectedProblem === suggestion && <div className="w-2 h-2 rounded-full bg-primary" />}
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <span className="font-mono text-sm font-bold text-primary">{suggestion.code}</span>
                                                <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 font-medium">
                                                    {(suggestion.similarity * 100).toFixed(0)}% Match
                                                </span>
                                            </div>
                                            <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">{suggestion.title}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div className="flex justify-end pt-2">
                                <button
                                    onClick={handleAddProblem}
                                    disabled={!selectedProblem}
                                    className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Add to Record
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}

            <div className="space-y-3">
                {problems.map((problem) => (
                    <div key={problem.id} className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
                        <div className="flex items-start gap-4">
                            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                                <Activity size={20} />
                            </div>
                            <div>
                                <h3 className="font-medium text-gray-900 dark:text-white">{problem.term}</h3>
                                <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                                    <span className="font-mono bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded text-xs">
                                        {problem.icdCode}
                                    </span>
                                    <span>{problem.icdTitle}</span>
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-700 rounded-full">
                                {problem.status}
                            </span>
                            <button className="text-gray-400 hover:text-red-500">
                                <X size={18} />
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
