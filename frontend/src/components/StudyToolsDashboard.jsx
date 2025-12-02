import React, { useState } from 'react';
import './StudyToolsDashboard.css';
import StudyCalendar from './StudyCalendar';
import CornellNotes from './CornellNotes';
import CitationManager from './CitationManager';
import ExportPanel from './ExportPanel';
import IntegrationSettings from './IntegrationSettings';

const StudyToolsDashboard = ({ userId, initialTab = 'calendar' }) => {
  const [activeTab, setActiveTab] = useState(initialTab);
  const [selectedTopicId, setSelectedTopicId] = useState(null);

  const tabs = [
    {
      id: 'calendar',
      name: 'Calendar',
      icon: '📅',
      description: 'Schedule study sessions and manage your learning timeline'
    },
    {
      id: 'notes',
      name: 'Cornell Notes',
      icon: '📝',
      description: 'Create structured notes with the Cornell method'
    },
    {
      id: 'citations',
      name: 'Citations',
      icon: '📚',
      description: 'Manage references and generate citations'
    },
    {
      id: 'export',
      name: 'Export',
      icon: '📥',
      description: 'Export your content in various formats'
    },
    {
      id: 'integrations',
      name: 'Integrations',
      icon: '🔗',
      description: 'Connect with external platforms and tools'
    }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'calendar':
        return <StudyCalendar userId={userId} />;
      case 'notes':
        return <CornellNotes userId={userId} topicId={selectedTopicId} />;
      case 'citations':
        return <CitationManager userId={userId} topicId={selectedTopicId} />;
      case 'export':
        return <ExportPanel userId={userId} />;
      case 'integrations':
        return <IntegrationSettings userId={userId} />;
      default:
        return <StudyCalendar userId={userId} />;
    }
  };

  const getTabStats = (tabId) => {
    // In a real implementation, these would come from API calls
    // For now, returning placeholder data
    switch (tabId) {
      case 'calendar':
        return { count: '12', label: 'Events' };
      case 'notes':
        return { count: '8', label: 'Notes' };
      case 'citations':
        return { count: '15', label: 'Citations' };
      case 'export':
        return { count: '5', label: 'Exports' };
      case 'integrations':
        return { count: '3', label: 'Connected' };
      default:
        return { count: '0', label: 'Items' };
    }
  };

  return (
    <div className="study-tools-dashboard">
      <div className="dashboard-header">
        <div className="header-content">
          <h1>Study Tools</h1>
          <p>Comprehensive tools to enhance your learning experience</p>
        </div>
        
        {selectedTopicId && (
          <div className="topic-filter">
            <span>Filtered by topic: <strong>{selectedTopicId}</strong></span>
            <button onClick={() => setSelectedTopicId(null)}>Clear Filter</button>
          </div>
        )}
      </div>

      <div className="dashboard-navigation">
        <div className="nav-tabs">
          {tabs.map(tab => {
            const stats = getTabStats(tab.id);
            return (
              <button
                key={tab.id}
                className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <div className="tab-icon">{tab.icon}</div>
                <div className="tab-info">
                  <div className="tab-name">{tab.name}</div>
                  <div className="tab-stats">
                    <span className="stat-count">{stats.count}</span>
                    <span className="stat-label">{stats.label}</span>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        <div className="nav-description">
          <p>{tabs.find(tab => tab.id === activeTab)?.description}</p>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="content-wrapper">
          {renderTabContent()}
        </div>
      </div>

      <div className="dashboard-footer">
        <div className="footer-stats">
          <div className="stat-item">
            <span className="stat-icon">📊</span>
            <span className="stat-text">All your study tools in one place</span>
          </div>
          <div className="stat-item">
            <span className="stat-icon">🔄</span>
            <span className="stat-text">Seamlessly integrated workflow</span>
          </div>
          <div className="stat-item">
            <span className="stat-icon">📱</span>
            <span className="stat-text">Access anywhere, anytime</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudyToolsDashboard;
