// Mapping Panel Component for Co-Pilot UX
import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';

export default function MappingPanel({ encounterId, notes }) {
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedMappings, setSelectedMappings] = useState([]);
    const { token } = useAuth();

    const analyzeMappings = async () => {
        setLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/api/copilot/analyze`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    encounter_id: encounterId,
                    notes: notes,
                    patient_context: {}
                })
            });

            const data = await response.json();
            setSuggestions(data.suggestions || []);
        } catch (err) {
            console.error('Analysis error:', err);
        } finally {
            setLoading(false);
        }
    };

    const acceptMappings = async () => {
        try {
            await fetch(`http://localhost:8000/api/mapping/encounters/${encounterId}/accept`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    encounter_id: encounterId,
                    selected_mappings: selectedMappings
                })
            });

            alert('Mappings accepted successfully!');
            setSelectedMappings([]);
        } catch (err) {
            alert('Failed to accept mappings');
        }
    };

    const toggleMapping = (mapping) => {
        const exists = selectedMappings.find(m => m.ayush_term === mapping.ayush_term);
        if (exists) {
            setSelectedMappings(selectedMappings.filter(m => m.ayush_term !== mapping.ayush_term));
        } else {
            setSelectedMappings([...selectedMappings, {
                ayush_term: mapping.ayush_term,
                icd_code: mapping.icd_code,
                clinician_edited: false,
                ai_suggestion_id: mapping.id,
                confidence: mapping.confidence
            }]);
        }
    };

    return (
        <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-gray-900">AI Co-Pilot Suggestions</h3>
                <button
                    onClick={analyzeMappings}
                    disabled={loading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
                >
                    {loading ? 'Analyzing...' : 'Analyze Notes'}
                </button>
            </div>

            {suggestions.length === 0 && !loading && (
                <div className="text-center py-12 text-gray-500">
                    <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                    <p>Click "Analyze Notes" to get AI mapping suggestions</p>
                </div>
            )}

            <div className="space-y-4">
                {suggestions.map((suggestion, idx) => (
                    <div
                        key={idx}
                        className={`border-2 rounded-lg p-4 transition cursor-pointer ${selectedMappings.find(m => m.ayush_term === suggestion.ayush_term)
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                        onClick={() => toggleMapping(suggestion)}
                    >
                        <div className="flex justify-between items-start mb-2">
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-semibold rounded">
                                        AYUSH
                                    </span>
                                    <span className="font-semibold text-gray-900">{suggestion.ayush_term}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">
                                        ICD-11
                                    </span>
                                    <span className="text-gray-700">{suggestion.icd_code}</span>
                                    <span className="text-gray-500 text-sm">• {suggestion.icd_title}</span>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="text-right">
                                    <div className="text-xs text-gray-500 mb-1">Confidence</div>
                                    <div className={`text-sm font-semibold ${suggestion.confidence > 0.8 ? 'text-green-600' :
                                            suggestion.confidence > 0.6 ? 'text-yellow-600' : 'text-red-600'
                                        }`}>
                                        {(suggestion.confidence * 100).toFixed(0)}%
                                    </div>
                                </div>
                            </div>
                        </div>

                        {suggestion.evidence && (
                            <div className="mt-3 p-3 bg-gray-50 rounded text-sm text-gray-600">
                                <span className="font-semibold">Evidence:</span> "{suggestion.evidence}"
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {selectedMappings.length > 0 && (
                <div className="mt-6 pt-6 border-t">
                    <button
                        onClick={acceptMappings}
                        className="w-full bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition"
                    >
                        Accept {selectedMappings.length} Selected Mapping{selectedMappings.length > 1 ? 's' : ''}
                    </button>
                </div>
            )}

            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start gap-2">
                    <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                    <div className="text-sm text-blue-800">
                        <strong>Read-Only Mapping:</strong> Accepted mappings are saved to encounter only. Original mapping database remains protected.
                    </div>
                </div>
            </div>
        </div>
    );
}
