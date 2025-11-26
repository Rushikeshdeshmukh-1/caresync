import React, { useState } from 'react'
import { Search, ArrowRight, Book, Info } from 'lucide-react'

export default function Mapping() {
    const [term, setTerm] = useState('')
    const [results, setResults] = useState([])
    const [loading, setLoading] = useState(false)

    const handleSearch = async (e) => {
        e.preventDefault()
        if (!term.trim()) return

        setLoading(true)
        try {
            // Using the suggest endpoint which uses the AI mapping engine
            const response = await fetch('/api/suggest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ term, k: 5 })
            })
            const data = await response.json()
            setResults(data.data?.results || [])
        } catch (error) {
            console.error('Error searching mapping:', error)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <div className="text-center space-y-4">
                <h1 className="text-3xl font-bold text-gray-900">NAMASTE to ICD-11 Mapping</h1>
                <p className="text-gray-600 max-w-2xl mx-auto">
                    Enter an AYUSH diagnostic term (e.g., "Jwara", "Kasa") to find the corresponding ICD-11 codes
                    using our AI-powered mapping engine.
                </p>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
                <form onSubmit={handleSearch} className="relative">
                    <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                        type="text"
                        value={term}
                        onChange={(e) => setTerm(e.target.value)}
                        placeholder="Enter diagnosis term (e.g., Jwara, Amlapitta)..."
                        className="w-full pl-12 pr-4 py-4 text-lg border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
                    />
                    <button
                        type="submit"
                        disabled={loading}
                        className="absolute right-2 top-2 bottom-2 px-6 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
                    >
                        {loading ? 'Searching...' : 'Map Code'}
                    </button>
                </form>
            </div>

            {results.length > 0 && (
                <div className="space-y-4">
                    <h2 className="text-lg font-semibold text-gray-900">Suggested ICD-11 Codes</h2>
                    <div className="grid gap-4">
                        {results.map((result, index) => (
                            <div key={index} className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 hover:border-blue-300 transition-colors group">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <span className="px-3 py-1 bg-blue-100 text-blue-700 font-bold rounded-lg font-mono">
                                                {result.icd_code}
                                            </span>
                                            {index === 0 && (
                                                <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                                                    Best Match
                                                </span>
                                            )}
                                        </div>
                                        <h3 className="text-lg font-medium text-gray-900 mb-1">{result.icd_title}</h3>
                                        <p className="text-gray-500 text-sm">{result.icd_description || 'No description available'}</p>

                                        {result.confidence && (
                                            <div className="mt-3 flex items-center gap-2 text-sm text-gray-500">
                                                <div className="w-24 h-2 bg-gray-100 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-blue-500 rounded-full"
                                                        style={{ width: `${result.confidence * 100}%` }}
                                                    />
                                                </div>
                                                <span>{Math.round(result.confidence * 100)}% Match Confidence</span>
                                            </div>
                                        )}
                                    </div>
                                    <button className="p-2 text-gray-400 hover:text-blue-600 transition-colors">
                                        <Info size={20} />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {results.length === 0 && !loading && term && (
                <div className="text-center py-12 text-gray-500">
                    <Book size={48} className="mx-auto mb-4 text-gray-300" />
                    <p>No mappings found for "{term}"</p>
                    <p className="text-sm">Try using a different term or check the spelling.</p>
                </div>
            )}
        </div>
    )
}
