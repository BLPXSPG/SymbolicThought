import React, { useState, useEffect } from 'react';

const StoryShow = ({ stories, currentStoryIndex, highlightedNodeName, highlightedChildrenNames }) => {
    const [userAddedWordsMap, setUserAddedWordsMap] = useState({});
    const [userRemovedWordsMap, setUserRemovedWordsMap] = useState({});
    const [confirmedDefaultEntities, setConfirmedDefaultEntities] = useState({});
    //console.log(highlightedNodeName, highlightedChildrenNames)

    useEffect(() => {
        if (stories?.length > 0) {
            const initialWordsMap = {};
            const initialConfirmedEntities = {};
            const initialRemovedWordsMap = {};
            stories.forEach((story, index) => {
                initialWordsMap[index] = [];
                initialConfirmedEntities[index] = [];
                initialRemovedWordsMap[index] = [];
            });
            setUserAddedWordsMap(initialWordsMap);
            setConfirmedDefaultEntities(initialConfirmedEntities);
            setUserRemovedWordsMap(initialRemovedWordsMap);
        }
    }, [stories, highlightedNodeName, highlightedChildrenNames]);

    const currentStory = stories[currentStoryIndex];
    const currentUserAddedWords = userAddedWordsMap[currentStoryIndex] || [];
    const currentConfirmedDefaultEntities = confirmedDefaultEntities[currentStoryIndex] || [];
    const currentDefaultEntities = Array.isArray(currentStory?.defaultEntities) 
        ? currentStory.defaultEntities.filter(entity => !userRemovedWordsMap[currentStoryIndex]?.includes(entity))
        : [];

        const getHighlightedContent = (text, highlight, highlightedChildrenNames = []) => {
            if (typeof text !== 'string') return null;
            const highlightList = Array.from(new Set([highlight, ...(highlightedChildrenNames || [])].filter(Boolean)))
                .sort((a, b) => b.length - a.length); 
            if (highlightList.length === 0) return text;
            const escapeRegex = (str) => str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const pattern = highlightList.map(escapeRegex).join('|');
            const regex = new RegExp(`(${pattern})`, 'gi');
            const parts = text.split(regex).filter(part => part !== undefined);
            return parts.map((part, index) => {
                const isMatch = highlightList.some(h => h.toLowerCase() === part.toLowerCase());
                return isMatch ? (
                    <span key={index} className="highlighted-text">{part}</span>
                ) : (
                    part
                );
            });
        };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '80%', maxWidth: '100%', overflow: 'hidden' }}>
            {stories.length > 0 && currentStory ? (
                <>
                    <h3 className="Homepage-subtitle">
                        {stories[currentStoryIndex].primary_title} -{' '}
                        {stories[currentStoryIndex].secondary_title}
                    </h3>
                    <div style={{ flex: 1, overflowY: 'auto', marginBottom: '20px' }}>
                        <div className="text-content" >{getHighlightedContent(currentStory.content, highlightedNodeName, highlightedChildrenNames)}</div>
                    </div>
                </>
            ) : (
                <div>Loading...</div>
            )}
        </div>
    );    
};

export default StoryShow;
