import React, { useState } from 'react';
import { Bot, AlertTriangle, CheckCircle, MessageSquare, Send, Loader, ChevronRight, ChevronDown } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export default function CoPilotPanel({ encounterId, notes, patientContext }) {
    const { token } = useAuth();
    const [activeTab, setActiveTab] = useState('analysis'); // 'analysis' or 'chat'
    const [loading, setLoading] = useState(false);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [chatMessage, setChatMessage] = useState('');
    const [chatHistory, setChatHistory] = useState([]);
    const [chatLoading, setChatLoading] = useState(false);
    const [expandedSuggestions, setExpandedSuggestions] = useState({});

    const handleAnalyze = async () => {
        if (!notes || !encounterId) return;

        setLoading(true);
        try {
            const response = await fetch('/api/copilot/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    encounter_id: encounterId,
                    notes: notes,
                    patient_context: patientContext || {},
                    actor: 'clinician'
                })
            });

            if (!response.ok) throw new Error('Analysis failed');
            const data = await response.json();
            setAnalysisResult(data);
        } catch (error) {
            console.error('Error analyzing notes:', error);
            // Handle error (maybe show toast)
        } finally {
            setLoading(false);
        }
    };

    const handleChatSubmit = async (e) => {
        e.preventDefault();
        if (!chatMessage.trim() || !encounterId) return;

        const userMsg = { role: 'user', content: chatMessage };
        setChatHistory(prev => [...prev, userMsg]);
        setChatMessage('');
        setChatLoading(true);

        try {
            const response = await fetch('/api/copilot/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    encounter_id: encounterId,
                    message: userMsg.content,
                    context: { notes, ...patientContext }
                })
            });

            if (!response.ok) throw new Error('Chat failed');
            const data = await response.json();

            setChatHistory(prev => [...prev, { role: 'assistant', content: data.response }]);
        } catch (error) {
            console.error('Error in chat:', error);
            setChatHistory(prev => [...prev, { role: 'system', content: 'Failed to get response. Please try again.' }]);
        } finally {
            setChatLoading(false);
        }
    };

    const toggleSuggestion = (index) => {
        setExpandedSuggestions(prev => ({
            ...prev,
            [index]: !prev[index]
        }));
    };

    return (
        <div className="flex flex-col h-full bg-white border-l border-gray-200 w-96 shadow-lg">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
                <div className="flex items-center gap-2 text-blue-700 font-bold">
                    <Bot size={24} />
                    <span>AYUSH Co-Pilot</span>
                </div>
                <div className="flex bg-gray-200 rounded-lg p-1 text-xs font-medium">
                    <button
                        onClick={() => setActiveTab('analysis')}
                        className={`px-3 py-1 rounded-md transition-colors ${activeTab === 'analysis' ? 'bg-white shadow-sm text-blue-700' : 'text-gray-600 hover:text-gray-900'}`}
                    >
                        Analysis
                    </button>
                    <button
                        onClick={() => setActiveTab('chat')}
                        className={`px-3 py-1 rounded-md transition-colors ${activeTab === 'chat' ? 'bg-white shadow-sm text-blue-700' : 'text-gray-600 hover:text-gray-900'}`}
                    >
                        Chat
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
                {activeTab === 'analysis' ? (
                    <div className="space-y-6">
                        {/* Analyze Button */}
                        <div className="bg-blue-50 p-4 rounded-xl border border-blue-100">
                            <p className="text-sm text-blue-800 mb-3">
                                Analyze clinical notes for AYUSH terms, ICD-11 mappings, and safety checks.
                            </p>
                            <button
                                onClick={handleAnalyze}
                                disabled={loading || !notes}
                                className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                            >
                                {loading ? <Loader className="animate-spin" size={18} /> : <Activity size={18} />}
                                {loading ? 'Analyzing...' : 'Analyze Notes'}
                            </button>
                        </div>

                        {analysisResult && (
                            <>
                                {/* Warnings */}
                                {analysisResult.warnings && analysisResult.warnings.length > 0 && (
                                    <div className="space-y-2">
                                        <h3 className="text-sm font-bold text-gray-700 flex items-center gap-2">
                                            <AlertTriangle size={16} className="text-amber-500" />
                                            Safety Warnings
                                        </h3>
                                        {analysisResult.warnings.map((warning, idx) => (
                                            <div key={idx} className={`p-3 rounded-lg border text-sm ${warning.severity === 'high'
                                                ? 'bg-red-50 border-red-200 text-red-800'
                                                : 'bg-amber-50 border-amber-200 text-amber-800'
                                                }`}>
                                                <div className="font-bold mb-1 flex items-center justify-between">
                                                    {warning.code}
                                                    <span className="text-xs uppercase px-2 py-0.5 rounded-full bg-white bg-opacity-50">
                                                        {warning.severity}
                                                    </span>
                                                </div>
                                                {warning.message}
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* Suggestions */}
                                {analysisResult.suggestions && analysisResult.suggestions.length > 0 && (
                                    <div className="space-y-2">
                                        <h3 className="text-sm font-bold text-gray-700 flex items-center gap-2">
                                            <CheckCircle size={16} className="text-green-600" />
                                            Suggestions
                                        </h3>
                                        <div className="space-y-2">
                                            {analysisResult.suggestions.map((suggestion, idx) => (
                                                <div key={idx} className="border border-gray-200 rounded-lg overflow-hidden">
                                                    <button
                                                        onClick={() => toggleSuggestion(idx)}
                                                        className="w-full flex items-center justify-between p-3 bg-white hover:bg-gray-50 text-left"
                                                    >
                                                        <div>
                                                            <div className="text-sm font-bold text-gray-900">
                                                                {suggestion.ayush_term} <span className="text-gray-400">→</span> {suggestion.icd11_code}
                                                            </div>
                                                            <div className="text-xs text-gray-500 truncate max-w-[200px]">
                                                                {suggestion.icd11_title}
                                                            </div>
                                                        </div>
                                                        {expandedSuggestions[idx] ? <ChevronDown size={16} className="text-gray-400" /> : <ChevronRight size={16} className="text-gray-400" />}
                                                    </button>

                                                    {expandedSuggestions[idx] && (
                                                        <div className="p-3 bg-gray-50 border-t border-gray-200 text-xs text-gray-600 space-y-2">
                                                            <p><strong>Full Title:</strong> {suggestion.icd11_title}</p>
                                                            <p><strong>Confidence:</strong> {(suggestion.confidence * 100).toFixed(1)}%</p>
                                                            <p><strong>Explanation:</strong> {suggestion.explanation}</p>
                                                            <button className="w-full mt-2 py-1.5 bg-green-600 text-white rounded hover:bg-green-700 transition-colors">
                                                                Accept Mapping
                                                            </button>
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Follow-ups */}
                                {analysisResult.followups && analysisResult.followups.length > 0 && (
                                    <div className="space-y-2">
                                        <h3 className="text-sm font-bold text-gray-700 flex items-center gap-2">
                                            <MessageSquare size={16} className="text-blue-500" />
                                            Recommendations
                                        </h3>
                                        <ul className="list-disc list-inside text-sm text-gray-600 space-y-1 bg-gray-50 p-3 rounded-lg border border-gray-200">
                                            {analysisResult.followups.map((item, idx) => (
                                                <li key={idx}>{item}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                ) : (
                    <div className="flex flex-col h-full">
                        <div className="flex-1 space-y-4 overflow-y-auto mb-4">
                            {chatHistory.length === 0 && (
                                <div className="text-center text-gray-400 mt-10 text-sm">
                                    <Bot size={40} className="mx-auto mb-2 opacity-20" />
                                    <p>Ask me anything about this encounter.</p>
                                </div>
                            )}
                            {chatHistory.map((msg, idx) => (
                                <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`max-w-[85%] rounded-lg p-3 text-sm ${msg.role === 'user'
                                        ? 'bg-blue-600 text-white rounded-br-none'
                                        : 'bg-gray-100 text-gray-800 rounded-bl-none'
                                        }`}>
                                        {msg.content}
                                    </div>
                                </div>
                            ))}
                            {chatLoading && (
                                <div className="flex justify-start">
                                    <div className="bg-gray-100 rounded-lg p-3 rounded-bl-none">
                                        <Loader className="animate-spin text-gray-400" size={16} />
                                    </div>
                                </div>
                            )}
                        </div>
                        <form onSubmit={handleChatSubmit} className="relative">
                            <input
                                type="text"
                                value={chatMessage}
                                onChange={(e) => setChatMessage(e.target.value)}
                                placeholder="Type a message..."
                                className="w-full pr-10 pl-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                                disabled={chatLoading}
                            />
                            <button
                                type="submit"
                                disabled={!chatMessage.trim() || chatLoading}
                                className="absolute right-1 top-1 p-1.5 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50 transition-colors"
                            >
                                <Send size={14} />
                            </button>
                        </form>
                    </div>
                )}
            </div>
        </div>
    );
}

function Activity({ size = 24, className = "" }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
        >
            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
        </svg>
    );
}
