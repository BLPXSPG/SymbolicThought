import React, { useState, useEffect } from 'react';

const CheckEntity = ({ text, initialWords, defaultEntities, confirmedDefaultEntities, onTextSelection }) => {
    const [selectedText, setSelectedText] = useState('');

    useEffect(() => {
        console.log('CheckEntity props:', { text, initialWords, defaultEntities, confirmedDefaultEntities });
    }, [text, initialWords, defaultEntities, confirmedDefaultEntities]);

    const handleMouseUp = () => {
        const selection = window.getSelection();
        const selectedText = selection.toString().trim();
        if (selectedText) {
            setSelectedText(selectedText);
            onTextSelection(selectedText);
        }
    };

    const highlightText = (text, words = [], defaultEntities = [], confirmedDefaultEntities = []) => {
        // Validate input types
        if (!Array.isArray(words)) {
            console.error('Expected words to be an array, but got:', words);
            words = [];
        }

        if (!Array.isArray(defaultEntities)) {
            console.error('Expected defaultEntities to be an array, but got:', defaultEntities);
            defaultEntities = [];
        }

        if (!Array.isArray(confirmedDefaultEntities)) {
            console.error('Expected confirmedDefaultEntities to be an array, but got:', confirmedDefaultEntities);
            confirmedDefaultEntities = [];
        }

        if (typeof text !== 'string') {
            console.error('Invalid text type:', typeof text);
            return '';
        }

        let result = text;
        const allEntities = [...new Set([...words, ...defaultEntities])];

        allEntities.sort((a, b) => b.length - a.length);

        allEntities.forEach(entity => {
            if (typeof entity !== 'string') {
                console.warn('Invalid entity type:', typeof entity);
                return;
            }
            const escapedEntity = escapeRegExp(entity);
            const regex = new RegExp(`${escapedEntity}`, 'g');
            let color = '#ACE1AF';
            if (defaultEntities.includes(entity) && !confirmedDefaultEntities.includes(entity)) {
                color = '#f5b7b1';
            }
            const replacement = `<span style="background-color: ${color}; display: inline;">$&</span>`;
            result = result.replace(regex, replacement);
        });

        return result;
    };

    const escapeRegExp = (string) => {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    };

    const highlightedText = highlightText(text, initialWords, defaultEntities, confirmedDefaultEntities);

    return (
        <div 
            onMouseUp={handleMouseUp}
            dangerouslySetInnerHTML={{ __html: highlightedText }}
            className="text-content"
        />
    );
};

export default CheckEntity;
