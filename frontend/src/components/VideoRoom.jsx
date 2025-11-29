// VideoRoom Component - Real Jitsi Meet Integration
import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../hooks/useAuth';

export default function VideoRoom({ appointmentId, isHost, onEnd }) {
    const jitsiContainerRef = useRef(null);
    const [jitsiApi, setJitsiApi] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { token, user } = useAuth();

    useEffect(() => {
        // Load Jitsi Meet External API
        const loadJitsiScript = () => {
            return new Promise((resolve, reject) => {
                if (window.JitsiMeetExternalAPI) {
                    resolve();
                    return;
                }

                const script = document.createElement('script');
                script.src = 'https://8x8.vc/external_api.js';
                script.async = true;
                script.onload = resolve;
                script.onerror = reject;
                document.body.appendChild(script);
            });
        };

        const startVideoCall = async () => {
            try {
                setLoading(true);
                setError(null);

                // Load Jitsi script
                await loadJitsiScript();

                // Start or join call based on role
                const endpoint = isHost ? '/api/teleconsult/start-call' : '/api/teleconsult/join-call';

                const response = await fetch(`http://localhost:8000${endpoint}`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        appointment_id: appointmentId,
                        room_id: appointmentId,
                        participant_name: user.name
                    })
                });

                if (!response.ok) {
                    throw new Error('Failed to start/join call');
                }

                const data = await response.json();
                const roomName = data.room_id;
                const domain = '8x8.vc';

                const options = {
                    roomName: roomName,
                    width: '100%',
                    height: '100%',
                    parentNode: jitsiContainerRef.current,
                    jwt: data.jwt_token,
                    configOverwrite: {
                        startWithAudioMuted: false,
                        startWithVideoMuted: false,
                        enableWelcomePage: false,
                        prejoinPageEnabled: false,
                        disableDeepLinking: true
                    },
                    interfaceConfigOverwrite: {
                        TOOLBAR_BUTTONS: [
                            'microphone', 'camera', 'closedcaptions', 'desktop',
                            'fullscreen', 'fodeviceselection', 'hangup', 'profile',
                            'chat', 'recording', 'livestreaming', 'etherpad',
                            'sharedvideo', 'settings', 'raisehand', 'videoquality',
                            'filmstrip', 'stats', 'shortcuts', 'tileview', 'download',
                            'help', 'mute-everyone'
                        ],
                        SHOW_JITSI_WATERMARK: false,
                        SHOW_WATERMARK_FOR_GUESTS: false,
                        DEFAULT_REMOTE_DISPLAY_NAME: 'Participant',
                        MOBILE_APP_PROMO: false
                    },
                    userInfo: {
                        displayName: user.name,
                        email: user.email
                    }
                };

                const api = new window.JitsiMeetExternalAPI(domain, options);
                setJitsiApi(api);

                api.addEventListener('videoConferenceJoined', () => {
                    console.log('Joined video conference');
                    setLoading(false);
                });

                api.addEventListener('videoConferenceLeft', async () => {
                    console.log('Left video conference');

                    if (isHost) {
                        try {
                            await fetch(`http://localhost:8000/api/teleconsult/end-call/${appointmentId}`, {
                                method: 'POST',
                                headers: {
                                    'Authorization': `Bearer ${token}`
                                }
                            });
                        } catch (err) {
                            console.error('Failed to end call:', err);
                        }
                    }

                    if (onEnd) onEnd();
                });

                api.addEventListener('readyToClose', () => {
                    api.dispose();
                    if (onEnd) onEnd();
                });

            } catch (err) {
                console.error('Error starting video call:', err);
                setError(err.message || 'Failed to start video call');
                setLoading(false);
            }
        };

        startVideoCall();

        return () => {
            if (jitsiApi) {
                jitsiApi.dispose();
            }
        };
    }, [appointmentId, isHost, token, user, onEnd]);

    if (error) {
        return (
            <div className="flex items-center justify-center h-full bg-gray-900">
                <div className="text-center text-white">
                    <div className="text-red-500 text-xl mb-4">⚠️ Error</div>
                    <div>{error}</div>
                    <button
                        onClick={onEnd}
                        className="mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg"
                    >
                        Go Back
                    </button>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full bg-gray-900">
                <div className="text-center text-white">
                    <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-white mx-auto mb-4"></div>
                    <div>Connecting to video call...</div>
                </div>
            </div>
        );
    }

    return (
        <div ref={jitsiContainerRef} className="w-full h-full" />
    );
}
