import React, { useState, useEffect } from 'react';
import { Plus, Search, X, DollarSign, User, Calendar, CreditCard, Check } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function BillingV2() {
    const [bills, setBills] = useState([]);
    const [patients, setPatients] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showPaymentModal, setShowPaymentModal] = useState(false);
    const [selectedBill, setSelectedBill] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState('all');
    const [formData, setFormData] = useState({
        patientId: '',
        notes: '',
        items: [{ description: '', quantity: 1, unit_price: 0, amount: 0 }]
    });
    const [paymentData, setPaymentData] = useState({
        paidAmount: 0,
        paymentMethod: 'cash'
    });

    useEffect(() => {
        fetchBills();
        fetchPatients();
    }, [filterStatus]);

    const fetchBills = async () => {
        try {
            setLoading(true);
            const params = new URLSearchParams();
            if (filterStatus !== 'all') params.append('payment_status', filterStatus);

            const response = await fetch(`${API_BASE}/api/v2/billing?${params}`);
            const data = await response.json();
            setBills(data.bills || []);
        } catch (error) {
            console.error('Error fetching bills:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchPatients = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/patients?limit=100`);
            const data = await response.json();
            setPatients(data.patients || []);
        } catch (error) {
            console.error('Error fetching patients:', error);
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        console.log('Creating bill with data:', formData);

        try {
            const response = await fetch(`${API_BASE}/api/v2/billing`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            console.log('Response status:', response.status);
            const responseData = await response.json();
            console.log('Response data:', responseData);

            if (response.ok) {
                alert('Invoice created successfully!');
                setShowCreateModal(false);
                setFormData({
                    patientId: '',
                    notes: '',
                    items: [{ description: '', quantity: 1, unit_price: 0, amount: 0 }]
                });
                fetchBills();
            } else {
                alert(`Error creating invoice: ${responseData.detail || 'Unknown error'}`);
                console.error('Error response:', responseData);
            }
        } catch (error) {
            console.error('Error creating bill:', error);
            alert(`Failed to create invoice: ${error.message}`);
        }
    };

    const handlePayment = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(`${API_BASE}/api/v2/billing/${selectedBill.id}/payment`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(paymentData)
            });

            if (response.ok) {
                setShowPaymentModal(false);
                setSelectedBill(null);
                setPaymentData({ paidAmount: 0, paymentMethod: 'cash' });
                fetchBills();
            }
        } catch (error) {
            console.error('Error updating payment:', error);
        }
    };

    const addBillItem = () => {
        setFormData({
            ...formData,
            items: [...formData.items, { description: '', quantity: 1, unit_price: 0, amount: 0 }]
        });
    };

    const removeBillItem = (index) => {
        const newItems = formData.items.filter((_, i) => i !== index);
        setFormData({ ...formData, items: newItems });
    };

    const updateBillItem = (index, field, value) => {
        const newItems = [...formData.items];
        newItems[index][field] = value;

        // Auto-calculate amount
        if (field === 'quantity' || field === 'unit_price') {
            newItems[index].amount = newItems[index].quantity * newItems[index].unit_price;
        }

        setFormData({ ...formData, items: newItems });
    };

    const getTotalAmount = () => {
        return formData.items.reduce((sum, item) => sum + (item.amount || 0), 0);
    };

    const formatCurrency = (amount) => {
        return `₹${amount.toFixed(2)}`;
    };

    const formatDate = (dateString) => {
        if (!dateString) return '';
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    const getStatusColor = (status) => {
        const colors = {
            paid: 'bg-green-100 text-green-800',
            partial: 'bg-yellow-100 text-yellow-800',
            unpaid: 'bg-red-100 text-red-800'
        };
        return colors[status] || 'bg-gray-100 text-gray-800';
    };

    const filteredBills = bills.filter(bill =>
        searchTerm === '' ||
        bill.patient_name?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Billing</h1>
                    <p className="text-gray-600">Manage invoices and payments</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                    <Plus size={20} />
                    Create Invoice
                </button>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-lg shadow p-4 flex gap-4 flex-wrap">
                <div className="flex-1 min-w-[200px]">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                        <input
                            type="text"
                            placeholder="Search bills..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>
                </div>
                <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                    <option value="all">All Status</option>
                    <option value="paid">Paid</option>
                    <option value="partial">Partially Paid</option>
                    <option value="unpaid">Unpaid</option>
                </select>
            </div>

            {/* Bills List */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                {loading ? (
                    <div className="p-8 text-center text-gray-500">Loading bills...</div>
                ) : filteredBills.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">
                        No bills found. Create your first invoice!
                    </div>
                ) : (
                    <div className="divide-y divide-gray-200">
                        {filteredBills.map((bill) => (
                            <div key={bill.id} className="p-4 hover:bg-gray-50 transition-colors">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <User className="text-gray-400" size={20} />
                                            <h3 className="font-semibold text-gray-900">
                                                {bill.patient_name || 'Unknown Patient'}
                                            </h3>
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(bill.payment_status)}`}>
                                                {bill.payment_status}
                                            </span>
                                        </div>
                                        <div className="ml-8 space-y-1 text-sm text-gray-600">
                                            <div className="flex items-center gap-2">
                                                <Calendar size={16} />
                                                <span>Created: {formatDate(bill.created_at)}</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <DollarSign size={16} />
                                                <span className="font-semibold">Total: {formatCurrency(bill.total_amount)}</span>
                                                <span className="text-gray-400">|</span>
                                                <span>Paid: {formatCurrency(bill.paid_amount)}</span>
                                                <span className="text-gray-400">|</span>
                                                <span className="text-red-600">Due: {formatCurrency(bill.total_amount - bill.paid_amount)}</span>
                                            </div>
                                            {bill.payment_method && (
                                                <div className="flex items-center gap-2">
                                                    <CreditCard size={16} />
                                                    <span>Method: {bill.payment_method}</span>
                                                </div>
                                            )}
                                            {bill.notes && (
                                                <p className="text-gray-500 italic">{bill.notes}</p>
                                            )}
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        {bill.payment_status !== 'paid' && (
                                            <button
                                                onClick={() => {
                                                    setSelectedBill(bill);
                                                    setPaymentData({
                                                        paidAmount: bill.total_amount - bill.paid_amount,
                                                        paymentMethod: 'cash'
                                                    });
                                                    setShowPaymentModal(true);
                                                }}
                                                className="px-3 py-1 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                                            >
                                                Record Payment
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Create Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6">
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-bold text-gray-900">Create Invoice</h2>
                                <button
                                    onClick={() => setShowCreateModal(false)}
                                    className="text-gray-400 hover:text-gray-600"
                                >
                                    <X size={24} />
                                </button>
                            </div>
                            <form onSubmit={handleCreate} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Patient * {patients.length > 0 && <span className="text-gray-500">({patients.length} available)</span>}
                                    </label>
                                    <select
                                        required
                                        value={formData.patientId}
                                        onChange={(e) => setFormData({ ...formData, patientId: e.target.value })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    >
                                        <option value="">Select patient</option>
                                        {patients.map((patient) => (
                                            <option key={patient.id} value={patient.id}>
                                                {patient.name}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Notes
                                    </label>
                                    <textarea
                                        value={formData.notes}
                                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                                        rows={2}
                                        placeholder="Additional notes..."
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>

                                {/* Bill Items */}
                                <div className="border-t pt-4">
                                    <div className="flex justify-between items-center mb-3">
                                        <h3 className="text-lg font-semibold text-gray-900">Items</h3>
                                        <button
                                            type="button"
                                            onClick={addBillItem}
                                            className="flex items-center gap-1 px-3 py-1 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700"
                                        >
                                            <Plus size={16} />
                                            Add Item
                                        </button>
                                    </div>

                                    {formData.items.map((item, index) => (
                                        <div key={index} className="mb-4 p-4 bg-gray-50 rounded-lg relative">
                                            {formData.items.length > 1 && (
                                                <button
                                                    type="button"
                                                    onClick={() => removeBillItem(index)}
                                                    className="absolute top-2 right-2 text-red-600 hover:text-red-800"
                                                >
                                                    <X size={20} />
                                                </button>
                                            )}
                                            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                                                <div className="md:col-span-2">
                                                    <label className="block text-xs font-medium text-gray-700 mb-1">
                                                        Description *
                                                    </label>
                                                    <input
                                                        type="text"
                                                        required
                                                        value={item.description}
                                                        onChange={(e) => updateBillItem(index, 'description', e.target.value)}
                                                        placeholder="e.g., Consultation Fee"
                                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="block text-xs font-medium text-gray-700 mb-1">
                                                        Quantity *
                                                    </label>
                                                    <input
                                                        type="number"
                                                        required
                                                        min="1"
                                                        value={item.quantity}
                                                        onChange={(e) => updateBillItem(index, 'quantity', parseInt(e.target.value) || 1)}
                                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="block text-xs font-medium text-gray-700 mb-1">
                                                        Unit Price *
                                                    </label>
                                                    <input
                                                        type="number"
                                                        required
                                                        min="0"
                                                        step="0.01"
                                                        value={item.unit_price}
                                                        onChange={(e) => updateBillItem(index, 'unit_price', parseFloat(e.target.value) || 0)}
                                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                                    />
                                                </div>
                                            </div>
                                            <div className="mt-2 text-right">
                                                <span className="text-sm font-semibold text-gray-700">
                                                    Amount: {formatCurrency(item.amount)}
                                                </span>
                                            </div>
                                        </div>
                                    ))}

                                    <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                                        <div className="flex justify-between items-center">
                                            <span className="text-lg font-bold text-gray-900">Total Amount:</span>
                                            <span className="text-2xl font-bold text-blue-600">{formatCurrency(getTotalAmount())}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex gap-3 pt-4">
                                    <button
                                        type="button"
                                        onClick={() => setShowCreateModal(false)}
                                        className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                                    >
                                        Create Invoice
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}

            {/* Payment Modal */}
            {showPaymentModal && selectedBill && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg max-w-md w-full">
                        <div className="p-6">
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-bold text-gray-900">Record Payment</h2>
                                <button
                                    onClick={() => setShowPaymentModal(false)}
                                    className="text-gray-400 hover:text-gray-600"
                                >
                                    <X size={24} />
                                </button>
                            </div>
                            <form onSubmit={handlePayment} className="space-y-4">
                                <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Total Amount:</span>
                                        <span className="font-semibold">{formatCurrency(selectedBill.total_amount)}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Already Paid:</span>
                                        <span className="font-semibold">{formatCurrency(selectedBill.paid_amount)}</span>
                                    </div>
                                    <div className="flex justify-between border-t pt-2">
                                        <span className="text-gray-900 font-bold">Amount Due:</span>
                                        <span className="font-bold text-red-600">{formatCurrency(selectedBill.total_amount - selectedBill.paid_amount)}</span>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Payment Amount *
                                    </label>
                                    <input
                                        type="number"
                                        required
                                        min="0"
                                        step="0.01"
                                        max={selectedBill.total_amount - selectedBill.paid_amount}
                                        value={paymentData.paidAmount}
                                        onChange={(e) => setPaymentData({ ...paymentData, paidAmount: parseFloat(e.target.value) || 0 })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Payment Method *
                                    </label>
                                    <select
                                        required
                                        value={paymentData.paymentMethod}
                                        onChange={(e) => setPaymentData({ ...paymentData, paymentMethod: e.target.value })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    >
                                        <option value="cash">Cash</option>
                                        <option value="card">Card</option>
                                        <option value="upi">UPI</option>
                                        <option value="bank_transfer">Bank Transfer</option>
                                        <option value="cheque">Cheque</option>
                                    </select>
                                </div>

                                <div className="flex gap-3 pt-4">
                                    <button
                                        type="button"
                                        onClick={() => setShowPaymentModal(false)}
                                        className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
                                    >
                                        <Check size={20} />
                                        Record Payment
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
