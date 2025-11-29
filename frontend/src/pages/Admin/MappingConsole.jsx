// Admin Mapping Console
import { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';

export default function MappingConsole() {
    const [feedbackSummary, setFeedbackSummary] = useState([]);
    const [proposals, setProposals] = useState([]);
    const [activeTab, setActiveTab] = useState('feedback');
    const [loading, setLoading] = useState(false);
    const { token } = useAuth();

    useEffect(() => {
        loadFeedbackSummary();
        loadProposals();
    }, []);

    const loadFeedbackSummary = async () => {
        setLoading(true);
        try {
            const response = await fetch('http://localhost:8000/api/mapping/feedback/summary?limit=50', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            setFeedbackSummary(data.feedback_summary || []);
        } catch (err) {
            console.error('Error loading feedback:', err);
        } finally {
            setLoading(false);
        }
    };

    const loadProposals = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/mapping/proposals', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            setProposals(data.proposals || []);
        } catch (err) {
            console.error('Error loading proposals:', err);
        }
    };

    const approveProposal = async (proposalId) => {
        try {
            await fetch(`http://localhost:8000/api/admin/mapping/proposals/${proposalId}/approve`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ notes: 'Approved via admin console' })
            });
            alert('Proposal approved! Manual migration required to apply changes.');
            loadProposals();
        } catch (err) {
            alert('Failed to approve proposal');
        }
    };

    const rejectProposal = async (proposalId) => {
        const reason = prompt('Reason for rejection:');
        if (!reason) return;

        try {
            await fetch(`http://localhost:8000/api/admin/mapping/proposals/${proposalId}/reject`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ reason })
            });
            alert('Proposal rejected');
            loadProposals();
        } catch (err) {
            alert('Failed to reject proposal');
        }
    };

    return (
        <div className="max-w-7xl mx-auto p-6">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Mapping Governance Console</h1>
                <p className="text-gray-600">Review feedback and manage mapping update proposals</p>
            </div>

            {/* Tabs */}
            <div className="border-b border-gray-200 mb-6">
                <nav className="flex space-x-8">
                    <button
                        onClick={() => setActiveTab('feedback')}
                        className={`pb-4 px-1 border-b-2 font-medium text-sm transition ${activeTab === 'feedback'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                    >
                        Feedback Summary
                    </button>
                    <button
                        onClick={() => setActiveTab('proposals')}
                        className={`pb-4 px-1 border-b-2 font-medium text-sm transition ${activeTab === 'proposals'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                    >
                        Proposals
                        {proposals.filter(p => p.status === 'pending').length > 0 && (
                            <span className="ml-2 px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                                {proposals.filter(p => p.status === 'pending').length}
                            </span>
                        )}
                    </button>
                </nav>
            </div>

            {/* Feedback Summary Tab */}
            {activeTab === 'feedback' && (
                <div className="bg-white rounded-lg shadow">
                    <div className="p-6">
                        <h2 className="text-xl font-semibold mb-4">Clinician Feedback Summary</h2>
                        {loading ? (
                            <div className="text-center py-12">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                            </div>
                        ) : feedbackSummary.length === 0 ? (
                            <div className="text-center py-12 text-gray-500">
                                No feedback collected yet
                            </div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">AYUSH Term</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">AI Suggested</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Clinician Preferred</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Count</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Confidence</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                        {feedbackSummary.map((item, idx) => (
                                            <tr key={idx} className="hover:bg-gray-50">
                                                <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{item.ayush_term}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-gray-600">{item.suggested_icd11}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-green-600 font-semibold">{item.clinician_icd11}</td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                                                        {item.correction_count}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                                                    {item.avg_confidence ? (item.avg_confidence * 100).toFixed(0) + '%' : 'N/A'}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Proposals Tab */}
            {activeTab === 'proposals' && (
                <div className="space-y-4">
                    {proposals.length === 0 ? (
                        <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">
                            No proposals yet
                        </div>
                    ) : (
                        proposals.map((proposal) => (
                            <div key={proposal.proposal_id} className="bg-white rounded-lg shadow p-6">
                                <div className="flex justify-between items-start mb-4">
                                    <div>
                                        <h3 className="text-lg font-semibold text-gray-900 mb-2">{proposal.ayush_term}</h3>
                                        <div className="flex items-center gap-4 text-sm">
                                            <div>
                                                <span className="text-gray-500">Current:</span>
                                                <span className="ml-2 text-red-600 font-medium">{proposal.current_icd11 || 'None'}</span>
                                            </div>
                                            <span className="text-gray-400">→</span>
                                            <div>
                                                <span className="text-gray-500">Proposed:</span>
                                                <span className="ml-2 text-green-600 font-medium">{proposal.proposed_icd11}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${proposal.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                                            proposal.status === 'approved' ? 'bg-green-100 text-green-800' :
                                                'bg-red-100 text-red-800'
                                        }`}>
                                        {proposal.status}
                                    </span>
                                </div>

                                <div className="mb-4 p-4 bg-gray-50 rounded">
                                    <p className="text-sm text-gray-700"><strong>Reason:</strong> {proposal.reason}</p>
                                </div>

                                {proposal.status === 'pending' && (
                                    <div className="flex gap-3">
                                        <button
                                            onClick={() => approveProposal(proposal.proposal_id)}
                                            className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition"
                                        >
                                            Approve
                                        </button>
                                        <button
                                            onClick={() => rejectProposal(proposal.proposal_id)}
                                            className="flex-1 bg-red-600 text-white py-2 rounded-lg hover:bg-red-700 transition"
                                        >
                                            Reject
                                        </button>
                                    </div>
                                )}

                                {proposal.status === 'approved' && (
                                    <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                                        <p className="text-sm text-yellow-800">
                                            ⚠️ <strong>Manual Migration Required:</strong> This proposal has been approved but mapping has NOT been updated.
                                            Follow the manual mapping update process to apply changes.
                                        </p>
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    );
}
