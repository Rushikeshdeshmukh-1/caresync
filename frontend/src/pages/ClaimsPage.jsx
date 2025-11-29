// Claims Management Page
import { useState, useEffect } from 'react';
import { FileText, Send, CheckCircle, Clock, AlertCircle, Download } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export default function Claims() {
    const [claims, setClaims] = useState([]);
    const [encounters, setEncounters] = useState([]);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const { token } = useAuth();

    useEffect(() => {
        loadClaims();
        loadEncounters();
    }, []);

    const loadClaims = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/admin/claims', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            setClaims(data.claims || []);
        } catch (err) {
            console.error('Error loading claims:', err);
        } finally {
            setLoading(false);
        }
    };

    const loadEncounters = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/encounters', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            setEncounters(data.encounters || []);
        } catch (err) {
            console.error('Error loading encounters:', err);
        }
    };

    const generateClaim = async (encounterId) => {
        setGenerating(true);
        try {
            const response = await fetch('http://localhost:8000/api/claims/generate', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ encounter_id: encounterId })
            });

            if (response.ok) {
                alert('Claim generated successfully!');
                loadClaims();
            }
        } catch (err) {
            alert('Failed to generate claim');
        } finally {
            setGenerating(false);
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'approved': return 'bg-green-100 text-green-800';
            case 'pending': return 'bg-yellow-100 text-yellow-800';
            case 'rejected': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    return (
        <div className="max-w-7xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Claims Management</h1>
                <p className="text-gray-600">Generate and manage insurance claim packets</p>
            </div>

            {/* Feature Banner */}
            <div className="bg-gradient-to-r from-green-600 to-teal-600 rounded-xl p-6 mb-8 text-white">
                <div className="flex items-center gap-4 mb-4">
                    <FileText size={32} />
                    <div>
                        <h3 className="text-xl font-semibold">Automated Claim Generation</h3>
                        <p className="text-green-100">ICD-11 coded claims ready for insurer submission</p>
                    </div>
                </div>
                <div className="grid grid-cols-3 gap-4 mt-4">
                    <div className="bg-white/10 rounded-lg p-4">
                        <div className="text-2xl font-bold">{claims.length}</div>
                        <div className="text-sm text-green-100">Total Claims</div>
                    </div>
                    <div className="bg-white/10 rounded-lg p-4">
                        <div className="text-2xl font-bold">
                            {claims.filter(c => c.status === 'approved').length}
                        </div>
                        <div className="text-sm text-green-100">Approved</div>
                    </div>
                    <div className="bg-white/10 rounded-lg p-4">
                        <div className="text-2xl font-bold">
                            {claims.filter(c => c.status === 'pending').length}
                        </div>
                        <div className="text-sm text-green-100">Pending</div>
                    </div>
                </div>
            </div>

            {/* Generate Claims Section */}
            <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
                <h2 className="text-xl font-semibold mb-4">Generate New Claim</h2>
                <p className="text-gray-600 mb-4">Select an encounter to generate an insurance claim packet</p>

                <div className="space-y-3">
                    {encounters.slice(0, 5).map((encounter) => (
                        <div key={encounter.id} className="border rounded-lg p-4 flex justify-between items-center">
                            <div>
                                <div className="font-semibold text-gray-900">Encounter #{encounter.id.slice(0, 8)}</div>
                                <div className="text-sm text-gray-600">
                                    Patient: {encounter.patient_name} | Date: {new Date(encounter.date).toLocaleDateString()}
                                </div>
                                {encounter.diagnosis && (
                                    <div className="text-sm text-gray-500 mt-1">Diagnosis: {encounter.diagnosis}</div>
                                )}
                            </div>
                            <button
                                onClick={() => generateClaim(encounter.id)}
                                disabled={generating}
                                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50"
                            >
                                <Send size={16} />
                                Generate Claim
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Claims List */}
            <div className="bg-white rounded-xl shadow-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Claim History</h2>

                {loading ? (
                    <div className="text-center py-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
                    </div>
                ) : claims.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                        <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                        <p>No claims generated yet</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Claim ID</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Patient</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {claims.map((claim) => (
                                    <tr key={claim.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                            #{claim.id.slice(0, 8)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                            {claim.patient_name}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                            {new Date(claim.created_at).toLocaleDateString()}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                                            ₹{claim.amount?.toFixed(2) || '0.00'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(claim.status)}`}>
                                                {claim.status === 'approved' && <CheckCircle size={14} />}
                                                {claim.status === 'pending' && <Clock size={14} />}
                                                {claim.status === 'rejected' && <AlertCircle size={14} />}
                                                {claim.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                                            <button className="text-blue-600 hover:text-blue-800 flex items-center gap-1">
                                                <Download size={16} />
                                                Download
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
