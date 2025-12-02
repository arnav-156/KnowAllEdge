import React, { useState, useEffect } from 'react';
import './StudyCalendar.css';

const StudyCalendar = ({ userId }) => {
  const [events, setEvents] = useState([]);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [showEventModal, setShowEventModal] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    event_type: 'study',
    start_time: '',
    end_time: '',
    topic_id: '',
    reminder_minutes: 15,
    is_recurring: false
  });

  useEffect(() => {
    fetchEvents();
  }, [userId, currentDate]);

  const fetchEvents = async () => {
    try {
      const startOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
      const endOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
      
      const response = await fetch(
        `/api/study-tools/calendar/events?user_id=${userId}&start_date=${startOfMonth.toISOString()}&end_date=${endOfMonth.toISOString()}`
      );
      const data = await response.json();
      
      if (data.success) {
        setEvents(data.events);
      }
    } catch (error) {
      console.error('Error fetching events:', error);
    }
  };

  const handleCreateEvent = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch('/api/study-tools/calendar/events', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      
      if (data.success) {
        fetchEvents();
        setShowEventModal(false);
        resetForm();
        alert('Event created successfully!');
      }
    } catch (error) {
      console.error('Error creating event:', error);
      alert('Failed to create event');
    }
  };

  const handleDeleteEvent = async (eventId) => {
    if (!confirm('Delete this event?')) return;
    
    try {
      const response = await fetch(`/api/study-tools/calendar/events/${eventId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        fetchEvents();
        setSelectedEvent(null);
      }
    } catch (error) {
      console.error('Error deleting event:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      event_type: 'study',
      start_time: '',
      end_time: '',
      topic_id: '',
      reminder_minutes: 15,
      is_recurring: false
    });
  };

  const getDaysInMonth = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();
    
    const days = [];
    
    // Add empty cells for days before month starts
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null);
    }
    
    // Add days of month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(day);
    }
    
    return days;
  };

  const getEventsForDay = (day) => {
    if (!day) return [];
    
    const dateStr = new Date(currentDate.getFullYear(), currentDate.getMonth(), day).toISOString().split('T')[0];
    
    return events.filter(event => {
      const eventDate = new Date(event.start_time).toISOString().split('T')[0];
      return eventDate === dateStr;
    });
  };

  const previousMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1));
  };

  const nextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1));
  };

  const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];

  return (
    <div className="study-calendar">
      <div className="calendar-header">
        <button onClick={previousMonth}>←</button>
        <h2>{monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}</h2>
        <button onClick={nextMonth}>→</button>
        <button className="add-event-btn" onClick={() => setShowEventModal(true)}>
          + Add Event
        </button>
      </div>

      <div className="calendar-grid">
        <div className="calendar-day-header">Sun</div>
        <div className="calendar-day-header">Mon</div>
        <div className="calendar-day-header">Tue</div>
        <div className="calendar-day-header">Wed</div>
        <div className="calendar-day-header">Thu</div>
        <div className="calendar-day-header">Fri</div>
        <div className="calendar-day-header">Sat</div>
        
        {getDaysInMonth().map((day, index) => {
          const dayEvents = getEventsForDay(day);
          const isToday = day && 
            day === new Date().getDate() && 
            currentDate.getMonth() === new Date().getMonth() &&
            currentDate.getFullYear() === new Date().getFullYear();
          
          return (
            <div 
              key={index} 
              className={`calendar-day ${!day ? 'empty' : ''} ${isToday ? 'today' : ''}`}
            >
              {day && (
                <>
                  <div className="day-number">{day}</div>
                  <div className="day-events">
                    {dayEvents.map(event => (
                      <div 
                        key={event.id}
                        className={`event-pill ${event.event_type}`}
                        onClick={() => setSelectedEvent(event)}
                      >
                        {event.title}
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>

      {showEventModal && (
        <div className="modal-overlay" onClick={() => setShowEventModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Create Study Session</h3>
            <form onSubmit={handleCreateEvent}>
              <input
                type="text"
                placeholder="Event Title"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                required
              />
              
              <textarea
                placeholder="Description"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
              />
              
              <select
                value={formData.event_type}
                onChange={(e) => setFormData({...formData, event_type: e.target.value})}
              >
                <option value="study">Study Session</option>
                <option value="quiz">Quiz</option>
                <option value="review">Review</option>
                <option value="exam">Exam</option>
              </select>
              
              <label>Start Time</label>
              <input
                type="datetime-local"
                value={formData.start_time}
                onChange={(e) => setFormData({...formData, start_time: e.target.value})}
                required
              />
              
              <label>End Time</label>
              <input
                type="datetime-local"
                value={formData.end_time}
                onChange={(e) => setFormData({...formData, end_time: e.target.value})}
                required
              />
              
              <label>Reminder (minutes before)</label>
              <input
                type="number"
                value={formData.reminder_minutes}
                onChange={(e) => setFormData({...formData, reminder_minutes: parseInt(e.target.value)})}
              />
              
              <label>
                <input
                  type="checkbox"
                  checked={formData.is_recurring}
                  onChange={(e) => setFormData({...formData, is_recurring: e.target.checked})}
                />
                Recurring Event
              </label>
              
              <div className="modal-actions">
                <button type="submit">Create Event</button>
                <button type="button" onClick={() => setShowEventModal(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selectedEvent && (
        <div className="modal-overlay" onClick={() => setSelectedEvent(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>{selectedEvent.title}</h3>
            <p><strong>Type:</strong> {selectedEvent.event_type}</p>
            <p><strong>Start:</strong> {new Date(selectedEvent.start_time).toLocaleString()}</p>
            <p><strong>End:</strong> {new Date(selectedEvent.end_time).toLocaleString()}</p>
            {selectedEvent.description && <p>{selectedEvent.description}</p>}
            
            <div className="modal-actions">
              <button onClick={() => handleDeleteEvent(selectedEvent.id)}>Delete</button>
              <button onClick={() => setSelectedEvent(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudyCalendar;
