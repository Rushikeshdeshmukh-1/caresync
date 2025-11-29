// Teleconsult Page - Full Video Consultation Interface
import { useState, useEffect } from 'react';
import { Video, Phone, PhoneOff, Mic, MicOff, Camera, CameraOff, Users } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import VideoRoom from '../components/VideoRoom';

export default function Teleconsult() {
    const [appointments, setAppointments] = useState([]);
    const [activeCall, setActiveCall] = useState(null);
    const [loading, setLoading] = useState(true);
    const { token, user } = useAuth();

    useEffect(() => {
        loadAppointments();
    }, []);

    const loadAppointments = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/appointments', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            setAppointments(data.appointments || []);
        } catch (err) {
            console.error('Error loading appointments:', err);
        } finally {
            setLoading(false);
        }
    };

    const startCall = (appointment) => {
        setActiveCall(appointment);
    };

    const endCall = () => {
        setActiveCall(null);
        loadAppointments();
    };

    if (activeCall) {
        return (
            <div className="h-screen flex flex-col">
                <div className="bg-gray-900 text-white px-6 py-4 flex justify-between items-center">
                    <div>
                        <h2 className="text-xl font-semibold">Video Consultation</h2>
                        <p className="text-sm text-gray-300">Appointment #{activeCall.id}</p>
                    </div>
                    <button
                        onClick={endCall}
                        className="bg-red-600 hover:bg-red-700 px-6 py-2 rounded-lg flex items-center gap-2"
                    >
                        <PhoneOff size={20} />
                        End Call
                    </button>
                </div>
                <div className="flex-1">
                    <VideoRoom
                        appointmentId={activeCall.id}
                        isHost={user.role === 'doctor'}
                        onEnd={endCall}
                    />
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Teleconsultation</h1>
                <p className="text-gray-600">Secure video consultations powered by Jitsi</p>
            </div>

            {/* Feature Banner */}
            <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl p-6 mb-8 text-white">
                <div className="flex items-center gap-4 mb-4">
                    <Video size={32} />
                    <div>
                        <h3 className="text-xl font-semibold">HD Video Consultations</h3>
                        <p className="text-purple-100">End-to-end encrypted, HIPAA compliant</p>
                    </div>
                </div>
                <div className="grid grid-cols-3 gap-4 mt-4">
                    <div className="bg-white/10 rounded-lg p-4">
                        <div className="text-2xl font-bold">256-bit</div>
                        <div className="text-sm text-purple-100">Encryption</div>
                    </div>
                    <div className="bg-white/10 rounded-lg p-4">
                        <div className="text-2xl font-bold">1080p</div>
                        <div className="text-sm text-purple-100">Video Quality</div>
                    </div>
                    <div className="bg-white/10 rounded-lg p-4">
                        <div className="text-2xl font-bold">Unlimited</div>
                        <div className="text-sm text-purple-100">Duration</div>
                    </div>
                </div>
            </div>

            {/* Upcoming Appointments */}
            <div className="bg-white rounded-xl shadow-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Scheduled Consultations</h2>

                {loading ? (
                    <div className="text-center py-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    </div>
                ) : appointments.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                        <Video className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                        <p>No scheduled consultations</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {appointments.map((apt) => (
                            <div key={apt.id} className="border rounded-lg p-4 hover:border-blue-500 transition">
                                <div className="flex justify-between items-start">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <Users className="text-blue-600" size={20} />
                                            <h3 className="font-semibold text-gray-900">
                                                {user.role === 'doctor' ? apt.patient_name : apt.doctor_name}
                                            </h3>
                                        </div>
                                        <div className="text-sm text-gray-600">
                                            <p>Date: {new Date(apt.date).toLocaleDateString()}</p>
                                            <p>Time: {apt.time}</p>
                                            {apt.notes && <p className="mt-2 text-gray-500">Notes: {apt.notes}</p>}
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => startCall(apt)}
                                        className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg flex items-center gap-2 transition"
                                    >
                                        <Video size={20} />
                                        Join Call
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Features List */}
            <div className="grid grid-cols-2 gap-6 mt-8">
                <div className="bg-white rounded-lg p-6 shadow">
                    <Camera className="text-blue-600 mb-3" size={32} />
                    <h3 className="font-semibold text-lg mb-2">HD Video & Audio</h3>
                    <p className="text-gray-600 text-sm">Crystal clear 1080p video with noise cancellation</p>
                </div>
                <div className="bg-white rounded-lg p-6 shadow">
                    <Users className="text-purple-600 mb-3" size={32} />
                    <h3 className="font-semibold text-lg mb-2">Screen Sharing</h3>
                    <p className="text-gray-600 text-sm">Share medical records and reports in real-time</p>
                </div>
            </div>
        </div>
    );
}
