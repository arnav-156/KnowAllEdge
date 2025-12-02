import React, { useState, useEffect } from 'react';
import apiClient from '../utils/apiClient';
import './RecommendationWidget.css';

const RecommendationWidget = ({ topic, onSelectSubtopic }) => {
    const [recommendations, setRecommendations] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (topic) {
            fetchRecommendations();
        }
    }, [topic]);

    const fetchRecommendations = async () => {
        setLoading(true);
        try {
            const response = await apiClient.getRecommendations(topic);
            if (response.success) {
                setRecommendations(response.data);
            }
        } catch (err) {
            console.error('Failed to fetch recommendations', err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="recommendation-widget">
                <div className="loading-rec">Loading personalized recommendations...</div>
            </div>
        );
    }

    if (recommendations.length === 0) return null;

    return (
        <div className="recommendation-widget">
            <div className="recommendation-header">
                <h3>🚀 Recommended Next Steps</h3>
            </div>
            <div className="recommendation-list">
                {recommendations.map((rec, index) => (
                    <div
                        key={index}
                        className="recommendation-card"
                        onClick={() => onSelectSubtopic && onSelectSubtopic(rec.subtopic)}
                    >
                        <span className="rec-title">{rec.subtopic}</span>
                        <span className="rec-reason">{rec.reason}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default RecommendationWidget;
