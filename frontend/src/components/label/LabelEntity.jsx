import React, { useState, useEffect } from 'react';
import { Button, Row, Col } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import StoryBook from '../utils/StoryBook';

export default function LabelEntity() {
    const [stories, setStories] = useState([]);
    const [currentStoryIndex, setCurrentStoryIndex] = useState(0);
    const [showStoryList, setShowStoryList] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false); // 添加提交状态
    const navigate = useNavigate();
    const location = useLocation();
    
    useEffect(() => {
        const initialStoryIndex = location.state?.currentStoryIndex || 0;
        const initialStory = location.state?.currentStory;
        setCurrentStoryIndex(initialStoryIndex);

        fetch('/apilocal/get-books')
            .then(response => response.json())
            .then(data => {
                
                const storiesWithEntities = data.map((story, index) => ({
                    ...story,
                    defaultEntities: story.entities_updated || []
                }));
                setStories(storiesWithEntities);
                console.log("story", data)

                // If the story was passed, update the initial story view
                if (initialStory) {
                    setStories(prevStories => {
                        const updatedStories = [...prevStories];
                        updatedStories[initialStoryIndex] = initialStory;
                        return updatedStories;
                    });
                    console.log("story", data)
                }
            })
            .catch(error => console.error('Error fetching story data:', error));
    }, [location.state]);

    const handleToggleStoryList = () => {
        setShowStoryList(prev => !prev);
    };

    const handleStoryClick = (index) => {
        setCurrentStoryIndex(index);
        setShowStoryList(false); // Close the list after selection
    };

    const sendEntitiesToBackend = (addedWords, removedWords, confirmedWords, coreferenceSlots) => {
        // 防止重复提交
        if (isSubmitting) {
            console.log("Request already in progress, skipping...");
            return;
        }
        
        setIsSubmitting(true);
        console.log("check what sent back", addedWords, removedWords, confirmedWords, coreferenceSlots)
        
        fetch('/apilocal/send-entities', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                storyId: currentStoryIndex,
                addedWords,
                removedWords,
                confirmedWords,
                coreferenceSlots
            }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Entity update sent:", data);
        })
        .catch(error => {
            console.error("Error sending entity updates:", error);
        })
        .finally(() => {
            setIsSubmitting(false); // 无论成功失败都重置状态
        });
    };

    return (
        <div className="Homepage">
            {/* Top Row with Buttons */}
            <div className="full-width-container">
                <Row className="top-row">
                    <Col span={24} className="top-row-title">
                        Label Entity
                    </Col>
                    <div className="button-container">
                        <Button className="action-button left-button" onClick={handleToggleStoryList}>
                            {showStoryList ? 'Hide Story List' : 'Switch Story'}
                        </Button>
                        <Button
                            className="action-button right-button"
                            onClick={() => navigate('/labelrelation', { state: { currentStoryIndex } })}
                        >
                            Finish and Next Step
                        </Button>
                    </div>
                </Row>
            </div>

            {/* Display Story List */}
            {showStoryList && (
                <Row justify="center" style={{ marginBottom: '20px' }}>
                    <Col span={20}>
                        <ul className="story-choice" style={{ listStyleType: 'none', padding: 0, maxHeight: '80vh', overflowY: 'auto' }}>
                            {stories.map((story, index) => (
                                <li
                                    key={index}
                                    onClick={() => handleStoryClick(index)}
                                    style={{
                                        marginBottom: '5px',
                                        wordBreak: 'break-word',
                                        cursor: 'pointer',
                                        fontWeight: index === currentStoryIndex ? 'bold' : 'normal'
                                    }}
                                >
                                    <b>{story.primary_title}</b> - {story.secondary_title}
                                </li>
                            ))}
                        </ul>
                    </Col>
                </Row>
            )}

            {/* Main Story Content */}
            <Row className="background-container" style={{ minHeight: '85vh', marginTop: '20px' }}>
                <Col span={24} className="background-scroll" style={{ maxWidth: '100%', overflowY: 'auto', wordWrap: 'break-word', whiteSpace: 'pre-wrap' }}>
                    <StoryBook
                        stories={stories}
                        currentStoryIndex={currentStoryIndex}
                        sendEntitiesToBackend={sendEntitiesToBackend} // Pass the function as a prop
                    />
                </Col>
            </Row>
        </div>
    );
}
