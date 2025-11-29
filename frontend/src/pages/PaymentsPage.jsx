// Payments Page - Payment Management Interface
import { useState, useEffect } from 'react';
import { CreditCard, CheckCircle, Clock, XCircle, DollarSign, TrendingUp } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import PaymentWidget from '../components/PaymentWidget';

export default function Payments() {
    const [payments, setPayments] = useState([]);
    const [appointments, setAppointments] = useState([]);
    const [stats, setStats] = useState({ total: 0, pending: 0, completed: 0, failed: 0 });
    const [showPaymentModal, setShowPaymentModal] = useState(false);
    const [selectedAppointment, setSelectedAppointment] = useState(null);
    const [loading, setLoading] = useState(true);
    const { token, user } = useAuth();

    useEffect(() => {
        loadPayments();
        if (user?.role === 'patient') {
            loadUnpaidAppointments();
        }
    }, [user]);

    const loadPayments = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/payments/history', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const data = await response.json();
                setPayments(data.payments || []);
                calculateStats(data.payments || []);
            }
        } catch (err) {
            console.error('Error loading payments:', err);
        } finally {
            setLoading(false);
        }
    };

    const loadUnpaidAppointments = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/appointments', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const data = await response.json();
                const unpaid = (data.appointments || []).filter(apt =>
                    apt.status === 'scheduled' || apt.status === 'confirmed'
                );
                setAppointments(unpaid);
            }
        } catch (err) {
            console.error('Error loading appointments:', err);
        }
    };

    const calculateStats = (paymentList) => {
        const stats = {
            total: paymentList.reduce((sum, p) => sum + (p.amount || 0), 0),
            pending: paymentList.filter(p => p.status === 'pending').length,
            completed: paymentList.filter(p => p.status === 'completed').length,
            failed: paymentList.filter(p => p.status === 'failed').length
        };
        setStats(stats);
    };

    const handlePayment = (appointment) => {
        setSelectedAppointment(appointment);
        setShowPaymentModal(true);
    };

    const handlePaymentSuccess = () => {
        setShowPaymentModal(false);
        setSelectedAppointment(null);
        loadPayments();
        if (user?.role === 'patient') {
            loadUnpaidAppointments();
        }
        alert('Payment successful! Your appointment is confirmed.');
    };

    const handlePaymentFailure = (error) => {
        alert(`Payment failed: ${error?.message || 'Unknown error'}`);
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed': return 'bg-green-100 text-green-800';
            case 'pending': return 'bg-yellow-100 text-yellow-800';
            case 'failed': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'completed': return <CheckCircle size={16} />;
            case 'pending': return <Clock size={16} />;
            case 'failed': return <XCircle size={16} />;
            default: return null;
        }
    };

    return (
        <div className="max-w-7xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Payments</h1>
                <p className="text-gray-600">Secure payment processing powered by Razorpay</p>
            </div>

            {/* Payment Stats */}
            <div className="grid grid-cols-4 gap-6 mb-8">
                <div className="bg-white rounded-xl shadow-lg p-6">
                    <div className="flex items-center justify-between mb-2">
                        <DollarSign className="text-blue-600" size={24} />
                        <TrendingUp className="text-green-500" size={20} />
                    </div>
                    <div className="text-2xl font-bold text-gray-900">₹{stats.total.toFixed(2)}</div>
                    <div className="text-sm text-gray-500">Total {user?.role === 'doctor' ? 'Revenue' : 'Spent'}</div>
                </div>

                <div className="bg-white rounded-xl shadow-lg p-6">
                    <div className="flex items-center justify-between mb-2">
                        <CheckCircle className="text-green-600" size={24} />
                    </div>
                    <div className="text-2xl font-bold text-gray-900">{stats.completed}</div>
                    <div className="text-sm text-gray-500">Completed</div>
                </div>

                <div className="bg-white rounded-xl shadow-lg p-6">
                    <div className="flex items-center justify-between mb-2">
                        <Clock className="text-yellow-600" size={24} />
                    </div>
                    <div className="text-2xl font-bold text-gray-900">{stats.pending}</div>
                    <div className="text-sm text-gray-500">Pending</div>
                </div>

                <div className="bg-white rounded-xl shadow-lg p-6">
                    <div className="flex items-center justify-between mb-2">
                        <XCircle className="text-red-600" size={24} />
                    </div>
                    <div className="text-2xl font-bold text-gray-900">{stats.failed}</div>
                    <div className="text-sm text-gray-500">Failed</div>
                </div>
            </div>

            {/* Razorpay Integration Banner */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-6 mb-8 text-white">
                <div className="flex items-center gap-4">
                    <CreditCard size={32} />
                    <div>
                        <h3 className="text-xl font-semibold">Razorpay Integration</h3>
                        <p className="text-blue-100">PCI DSS compliant, supports UPI, cards, wallets & more</p>
                    </div>
                </div>
                <div className="grid grid-cols-4 gap-4 mt-4">
                    <div className="bg-white/10 rounded-lg p-3 text-center">
                        <div className="text-sm">UPI</div>
                    </div>
                    <div className="bg-white/10 rounded-lg p-3 text-center">
                        <div className="text-sm">Cards</div>
                    </div>
                    <div className="bg-white/10 rounded-lg p-3 text-center">
                        <div className="text-sm">Wallets</div>
                    </div>
                    <div className="bg-white/10 rounded-lg p-3 text-center">
                        <div className="text-sm">Net Banking</div>
                    </div>
                </div>
            </div>

            {/* Unpaid Appointments (Patient Only) */}
            {user?.role === 'patient' && appointments.length > 0 && (
                <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
                    <h2 className="text-xl font-semibold mb-4">Pending Payments</h2>
                    <div className="space-y-4">
                        {appointments.map((apt) => (
                            <div key={apt.id} className="border rounded-lg p-4 flex justify-between items-center">
                                <div>
                                    <div className="font-semibold text-gray-900">Appointment with Dr. {apt.doctor_name || 'Unknown'}</div>
                                    <div className="text-sm text-gray-600">
                                        Date: {apt.date} at {apt.time}
                                    </div>
                                    <div className="text-sm text-gray-500">Consultation Fee: ₹500</div>
                                </div>
                                <button
                                    onClick={() => handlePayment({ ...apt, amount: 500 })}
                                    className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg flex items-center gap-2"
                                >
                                    <CreditCard size={16} />
                                    Pay Now
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Payment History */}
            <div className="bg-white rounded-xl shadow-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Payment History</h2>

                {loading ? (
                    <div className="text-center py-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    </div>
                ) : payments.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                        <CreditCard className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                        <p>No payment history</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Method</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {payments.map((payment) => (
                                    <tr key={payment.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                            #{payment.id?.slice(0, 8) || 'N/A'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                            {payment.created_at ? new Date(payment.created_at).toLocaleDateString() : 'N/A'}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-600">
                                            {payment.description || 'Consultation Payment'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                                            ₹{(payment.amount || 0).toFixed(2)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(payment.status)}`}>
                                                {getStatusIcon(payment.status)}
                                                {payment.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                            {payment.method || 'Razorpay'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Payment Modal */}
            {showPaymentModal && selectedAppointment && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-xl p-6 max-w-md w-full relative">
                        <button
                            onClick={() => setShowPaymentModal(false)}
                            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
                        >
                            ✕
                        </button>
                        <h3 className="text-xl font-semibold mb-4">Make Payment</h3>
                        <PaymentWidget
                            appointmentId={selectedAppointment.id}
                            amount={selectedAppointment.amount || 500}
                            onSuccess={handlePaymentSuccess}
                            onFailure={handlePaymentFailure}
                        />
                    </div>
                </div>
            )}
        </div>
    );
}
