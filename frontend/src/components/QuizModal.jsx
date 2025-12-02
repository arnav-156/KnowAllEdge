import React, { useState, useEffect } from 'react';
import apiClient from '../utils/apiClient';
import './QuizModal.css';

const QuizModal = ({ isOpen, onClose, topic, subtopic, educationLevel }) => {
    const [loading, setLoading] = useState(true);
    const [questions, setQuestions] = useState([]);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [selectedOption, setSelectedOption] = useState(null);
    const [score, setScore] = useState(0);
    const [showResult, setShowResult] = useState(false);
    const [masteryLevel, setMasteryLevel] = useState(0);
    const [error, setError] = useState(null);
    const [answerChecked, setAnswerChecked] = useState(false);

    useEffect(() => {
        if (isOpen && topic && subtopic) {
            fetchQuiz();
        } else {
            resetQuiz();
        }
    }, [isOpen, topic, subtopic]);

    const resetQuiz = () => {
        setLoading(true);
        setQuestions([]);
        setCurrentQuestionIndex(0);
        setSelectedOption(null);
        setScore(0);
        setShowResult(false);
        setMasteryLevel(0);
        setError(null);
        setAnswerChecked(false);
    };

    const fetchQuiz = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await apiClient.generateQuiz(topic, subtopic, educationLevel);
            if (response.success) {
                setQuestions(response.data);
            } else {
                setError('Failed to load quiz. Please try again.');
            }
        } catch (err) {
            setError('An error occurred while fetching the quiz.');
        } finally {
            setLoading(false);
        }
    };

    const handleOptionSelect = (option) => {
        if (answerChecked) return;
        setSelectedOption(option);
    };

    const checkAnswer = () => {
        setAnswerChecked(true);
        const currentQuestion = questions[currentQuestionIndex];
        if (selectedOption === currentQuestion.correct_answer) {
            setScore(score + 1);
        }
    };

    const handleNext = () => {
        if (currentQuestionIndex < questions.length - 1) {
            setCurrentQuestionIndex(currentQuestionIndex + 1);
            setSelectedOption(null);
            setAnswerChecked(false);
        } else {
            finishQuiz();
        }
    };

    const finishQuiz = async () => {
        setLoading(true);
        try {
            // Calculate final score including the last question
            let finalScore = score;
            // Note: score is already updated in checkAnswer, so we just use it.
            // Wait, checkAnswer updates state, which might not be immediate.
            // But handleNext is called after checkAnswer, so it should be fine?
            // Actually, finishQuiz is called from handleNext or directly?
            // Let's change the flow: "Check" button -> shows result -> "Next" button.

            const response = await apiClient.submitQuiz(
                topic,
                subtopic,
                score, // This might be one step behind if we don't handle it carefully
                questions.length
            );

            if (response.success) {
                setMasteryLevel(response.data.mastery_level);
                setShowResult(true);
            } else {
                setError('Failed to submit results.');
            }
        } catch (err) {
            setError('Error submitting quiz.');
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="quiz-modal-overlay">
            <div className="quiz-modal-content">
                <button className="quiz-close-btn" onClick={onClose}>&times;</button>

                {loading ? (
                    <div className="loading-container">
                        <div className="spinner"></div>
                        <p>Loading Quiz...</p>
                    </div>
                ) : error ? (
                    <div className="error-container">
                        <p>{error}</p>
                        <button className="quiz-btn" onClick={fetchQuiz}>Retry</button>
                    </div>
                ) : showResult ? (
                    <div className="quiz-result">
                        <span className="mastery-badge">
                            {masteryLevel === 3 ? '🏆' : masteryLevel === 2 ? '🥈' : '🥉'}
                        </span>
                        <h2>Quiz Completed!</h2>
                        <div className="quiz-score">
                            Score: {score} / {questions.length}
                        </div>
                        <p className="quiz-feedback">
                            {masteryLevel === 3 ? 'Excellent mastery! You are ready for the next topic.' :
                                masteryLevel === 2 ? 'Good job! You have a solid understanding.' :
                                    'Keep practicing! Review the material and try again.'}
                        </p>
                        <button className="quiz-btn" onClick={onClose}>Close</button>
                    </div>
                ) : (
                    <>
                        <div className="quiz-header">
                            <h2>{subtopic} Quiz</h2>
                            <div className="quiz-progress">
                                Question {currentQuestionIndex + 1} of {questions.length}
                            </div>
                        </div>

                        <div className="quiz-question-container">
                            <p className="quiz-question">
                                {questions[currentQuestionIndex].question}
                            </p>

                            <div className="quiz-options">
                                {questions[currentQuestionIndex].options.map((option, index) => (
                                    <button
                                        key={index}
                                        className={`quiz-option ${selectedOption === option ? 'selected' : ''
                                            } ${answerChecked && option === questions[currentQuestionIndex].correct_answer
                                                ? 'correct'
                                                : ''
                                            } ${answerChecked && selectedOption === option && option !== questions[currentQuestionIndex].correct_answer
                                                ? 'incorrect'
                                                : ''
                                            }`}
                                        onClick={() => handleOptionSelect(option)}
                                        disabled={answerChecked}
                                    >
                                        {option}
                                    </button>
                                ))}
                            </div>

                            {answerChecked && (
                                <div className="explanation-box" style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}>
                                    <strong>Explanation:</strong> {questions[currentQuestionIndex].explanation}
                                </div>
                            )}
                        </div>

                        <div className="quiz-footer">
                            {!answerChecked ? (
                                <button
                                    className="quiz-btn"
                                    onClick={checkAnswer}
                                    disabled={!selectedOption}
                                >
                                    Check Answer
                                </button>
                            ) : (
                                <button
                                    className="quiz-btn"
                                    onClick={handleNext}
                                >
                                    {currentQuestionIndex < questions.length - 1 ? 'Next Question' : 'Finish Quiz'}
                                </button>
                            )}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default QuizModal;
