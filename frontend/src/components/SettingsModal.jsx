import React, { useState, useEffect } from 'react';

const SettingsModal = ({ isOpen, onClose, onSave }) => {
    const [settings, setSettings] = useState({
        language: 'en',
        learningStyle: 'General',
        fontSize: 'medium',
        dailyGoal: 30
    });

    useEffect(() => {
        // Load settings from localStorage
        const savedSettings = localStorage.getItem('KNOWALLEDGE_settings');
        if (savedSettings) {
            setSettings(JSON.parse(savedSettings));
        }
    }, [isOpen]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setSettings(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSave = () => {
        localStorage.setItem('KNOWALLEDGE_settings', JSON.stringify(settings));
        if (onSave) onSave(settings);
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 10000,
            backdropFilter: 'blur(5px)'
        }}>
            <div style={{
                background: '#1a1a2e',
                color: '#fff',
                padding: '30px',
                borderRadius: '15px',
                width: '90%',
                maxWidth: '500px',
                boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
                border: '1px solid rgba(255,255,255,0.1)'
            }}>
                <h2 style={{ marginTop: 0, marginBottom: '20px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '10px' }}>
                    ⚙️ Personalization Settings
                </h2>

                <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>Preferred Language</label>
                    <select
                        name="language"
                        value={settings.language}
                        onChange={handleChange}
                        style={{ width: '100%', padding: '10px', borderRadius: '5px', border: 'none', background: 'rgba(255,255,255,0.1)', color: '#fff' }}
                    >
                        <option value="en">English</option>
                        <option value="es">Spanish (Español)</option>
                        <option value="fr">French (Français)</option>
                        <option value="de">German (Deutsch)</option>
                        <option value="zh">Chinese (中文)</option>
                        <option value="ja">Japanese (日本語)</option>
                        <option value="ar">Arabic (العربية)</option>
                    </select>
                </div>

                <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>Learning Style</label>
                    <select
                        name="learningStyle"
                        value={settings.learningStyle}
                        onChange={handleChange}
                        style={{ width: '100%', padding: '10px', borderRadius: '5px', border: 'none', background: 'rgba(255,255,255,0.1)', color: '#fff' }}
                    >
                        <option value="General">General (Balanced)</option>
                        <option value="Visual">Visual (Diagrams, Images)</option>
                        <option value="Auditory">Auditory (Conversational)</option>
                        <option value="Kinesthetic">Kinesthetic (Hands-on, Examples)</option>
                        <option value="Reading/Writing">Reading/Writing (Detailed Text)</option>
                    </select>
                </div>

                <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>Font Size</label>
                    <select
                        name="fontSize"
                        value={settings.fontSize}
                        onChange={handleChange}
                        style={{ width: '100%', padding: '10px', borderRadius: '5px', border: 'none', background: 'rgba(255,255,255,0.1)', color: '#fff' }}
                    >
                        <option value="small">Small</option>
                        <option value="medium">Medium</option>
                        <option value="large">Large</option>
                        <option value="xlarge">Extra Large</option>
                    </select>
                </div>

                <div style={{ marginBottom: '30px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>Daily Learning Goal (minutes)</label>
                    <input
                        type="number"
                        name="dailyGoal"
                        value={settings.dailyGoal}
                        onChange={handleChange}
                        min="5"
                        max="240"
                        style={{ width: '100%', padding: '10px', borderRadius: '5px', border: 'none', background: 'rgba(255,255,255,0.1)', color: '#fff' }}
                    />
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                    <button
                        onClick={onClose}
                        style={{ padding: '10px 20px', borderRadius: '5px', border: 'none', background: 'rgba(255,255,255,0.1)', color: '#fff', cursor: 'pointer' }}
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        style={{ padding: '10px 20px', borderRadius: '5px', border: 'none', background: 'linear-gradient(90deg, #4facfe, #00f2fe)', color: '#fff', fontWeight: 'bold', cursor: 'pointer' }}
                    >
                        Save Settings
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SettingsModal;
