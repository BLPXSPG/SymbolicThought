// StorySwitcher.js
import React from 'react';

const StorySwitcher = ({ stories, currentStoryIndex, onStoryClick, showStoryList, toggleStoryList }) => {
  return (
    
<div className="switch-story-container">
    <button className="toggle-button" onClick={toggleStoryList}>
        {showStoryList ? 'Hide Story List' : 'Switch Story'}
    </button>
    {showStoryList && (
        <div className="story-menu">
            <ul className="story-list">
                {stories.map((story, index) => (
                    <li
                        key={index}
                        className={`story-item ${index === currentStoryIndex ? 'active' : ''}`}
                        onClick={() => onStoryClick(index)}
                    >
                        {story.primary_title} - {story.secondary_title}
                    </li>
                ))}
            </ul>
        </div>
    )}
</div>

  );
};

export default StorySwitcher;
