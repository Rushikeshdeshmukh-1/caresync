// PaymentWidget - Real Razorpay Integration
import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';

export default function PaymentWidget({ appointmentId, amount, onSuccess, onFailure }) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const { token, user } = useAuth();

    useEffect(() => {
        // Load Razorpay script
        const script = document.createElement('script');
        script.src = 'https://checkout.razorpay.com/v1/checkout.js';
        script.async = true;
        document.body.appendChild(script);

        return () => {
            if (document.body.contains(script)) {
                document.body.removeChild(script);
            }
        };
    }, []);

    const handlePayment = async () => {
        setLoading(true);
        setError(null);

        try {
            // Check if Razorpay is loaded
            if (!window.Razorpay) {
                throw new Error('Razorpay SDK not loaded');
            }

            // Create payment order on backend
            const orderResponse = await fetch('http://localhost:8000/api/payments/create-order', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    appointment_id: appointmentId,
                    amount: amount,
                    currency: 'INR',
                    description: 'Consultation Payment'
                })
            });

            if (!orderResponse.ok) {
                throw new Error('Failed to create payment order');
            }

            const orderData = await orderResponse.json();

            // Configure Razorpay options
            const options = {
                key: orderData.key_id,
                amount: orderData.amount * 100,
                currency: orderData.currency,
                name: 'CareSync',
                description: 'Consultation Payment',
                order_id: orderData.order_id,
                handler: async function (response) {
                    try {
                        const verifyResponse = await fetch('http://localhost:8000/api/payments/verify-payment', {
                            method: 'POST',
                            headers: {
                                'Authorization': `Bearer ${token}`,
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                razorpay_order_id: response.razorpay_order_id,
                                razorpay_payment_id: response.razorpay_payment_id,
                                razorpay_signature: response.razorpay_signature,
                                appointment_id: appointmentId
                            })
                        });

                        if (verifyResponse.ok) {
                            const verifyData = await verifyResponse.json();
                            if (onSuccess) onSuccess(verifyData);
                        } else {
                            throw new Error('Payment verification failed');
                        }
                    } catch (err) {
                        if (onFailure) onFailure(err);
                    }
                },
                prefill: {
                    name: user?.name || '',
                    email: user?.email || '',
                    contact: user?.phone || ''
                },
                theme: {
                    color: '#3B82F6'
                },
                modal: {
                    ondismiss: function () {
                        setLoading(false);
                        if (onFailure) onFailure(new Error('Payment cancelled'));
                    }
                }
            };

            const razorpay = new window.Razorpay(options);
            razorpay.open();
            setLoading(false);

        } catch (err) {
            console.error('Payment error:', err);
            setError(err.message);
            setLoading(false);
            if (onFailure) onFailure(err);
        }
    };

    return (
        <div className="bg-white rounded-lg p-6">
            <div className="mb-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Payment Details</h3>
                <div className="flex justify-between items-center py-3 border-b">
                    <span className="text-gray-600">Consultation Fee</span>
                    <span className="text-2xl font-bold text-gray-900">₹{amount}</span>
                </div>
            </div>

            {error && (
                <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-red-800 text-sm">{error}</p>
                </div>
            )}

            <button
                onClick={handlePayment}
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
                {loading ? (
                    <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        Processing...
                    </>
                ) : (
                    <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                        </svg>
                        Pay ₹{amount}
                    </>
                )}
            </button>

            <div className="mt-4 flex items-center justify-center gap-2 text-sm text-gray-500">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                </svg>
                Secured by Razorpay
            </div>
        </div>
    );
}
