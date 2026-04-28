import React, { useState, useEffect, useRef } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import CheckEntity from '../label/CheckEntity';
import { Button } from 'antd';

const StoryBook = ({ stories, currentStoryIndex, sendEntitiesToBackend }) => {
    const [selectedPhrase, setSelectedPhrase] = useState('');
    const [userAddedWords, setUserAddedWords] = useState([]);
    const [confirmedDefaultEntities, setConfirmedDefaultEntities] = useState([]);
    const [userRemovedWords, setUserRemovedWords] = useState([]);
    const [defaultEntities, setDefaultEntities] = useState([]);
    const [slots, setSlots] = useState([]);
    const [loading, setLoading] = useState(false);
    const [customPhrase, setCustomPhrase] = useState('');
    
    // 添加节流机制
    const throttleTimer = useRef(null);
    const lastSentData = useRef(null);

    useEffect(() => {
        if (stories?.length > 0 && currentStoryIndex >= 0) {
            const currentStory = stories[currentStoryIndex];
            setUserAddedWords([...currentStory.entities_added || []]);
            setConfirmedDefaultEntities([...currentStory.entities_confirmed || []]);
            setUserRemovedWords([...currentStory.entities_removed || []]);
            setDefaultEntities([...currentStory.entities_unconfirmed || []]);
            if (currentStory.coreference && currentStory.coreference.length > 0) {
                setSlots(currentStory.coreference);
            } else {
                setSlots((currentStory.entities_unconfirmed || []).map((entity) => [entity]));
            }
        }
    }, [stories, currentStoryIndex]);

    // 节流版本的发送函数，避免频繁调用
    const throttledSendToBackend = (updatedAdded, updatedRemoved, updatedConfirmed, cleanedSlots) => {
        const currentData = JSON.stringify([updatedAdded, updatedRemoved, updatedConfirmed, cleanedSlots]);
        
        // 如果数据没有变化，不发送
        if (lastSentData.current === currentData) {
            return;
        }
        
        // 清除之前的定时器
        if (throttleTimer.current) {
            clearTimeout(throttleTimer.current);
        }
        
        // 设置新的定时器，500ms后发送请求
        throttleTimer.current = setTimeout(() => {
            lastSentData.current = currentData;
            sendEntitiesToBackend(updatedAdded, updatedRemoved, updatedConfirmed, cleanedSlots);
        }, 500);
    };

    const updateEntityStatus = (entity, action, slotIndex = null) => {
        let updatedAdded = [...userAddedWords];
        let updatedRemoved = [...userRemovedWords];
        let updatedConfirmed = [...confirmedDefaultEntities];
        let updatedSlots = [...slots];

        if (action === 'add') {
            updatedRemoved = updatedRemoved.filter((e) => e !== entity);
            updatedConfirmed = updatedConfirmed.filter((e) => e !== entity);
            updatedAdded = updatedAdded.filter((e) => e !== entity); 
        
            if (defaultEntities.includes(entity)) {
                if (!updatedConfirmed.includes(entity)) updatedConfirmed.push(entity);
            } else {
                if (!updatedAdded.includes(entity)) updatedAdded.push(entity);
            }
        
            const existsInSlots = updatedSlots.some((slot) => slot.includes(entity));
            if (!existsInSlots) updatedSlots.push([entity]);
        }
         else if (action === 'confirm') {
            updatedRemoved = updatedRemoved.filter((e) => e !== entity);
            if (!updatedConfirmed.includes(entity)) updatedConfirmed.push(entity);

        } else if (action === 'remove') {
            updatedAdded = updatedAdded.filter((e) => e !== entity);
            updatedConfirmed = updatedConfirmed.filter((e) => e !== entity);
            if (!updatedRemoved.includes(entity)) updatedRemoved.push(entity);

            if (slotIndex !== null && updatedSlots[slotIndex]) {
                updatedSlots[slotIndex] = updatedSlots[slotIndex].filter((word) => word !== entity);
            }
        }

        //console.log('✅ [Debug] Entity State Update:', {
        //    added: updatedAdded.length,
        //    removed: updatedRemoved.length,
        //    confirmed: updatedConfirmed.length,
        //    unconfirmed: defaultEntities.length
        //});

        // 去除多个连续空行，只保留一个
        const cleanedSlots = [];
        let previousEmpty = false;
        for (const slot of updatedSlots) {
            const isEmpty = slot.length === 0;
            if (isEmpty) {
                if (!previousEmpty) {
                    cleanedSlots.push(slot);
                    previousEmpty = true;
                }
            } else {
                cleanedSlots.push(slot);
                previousEmpty = false;
            }
        }

        setUserAddedWords(updatedAdded);
        setUserRemovedWords(updatedRemoved);
        setConfirmedDefaultEntities(updatedConfirmed);
        setSlots(cleanedSlots);
        throttledSendToBackend(updatedAdded, updatedRemoved, updatedConfirmed, cleanedSlots);
    };

    const handleDragEnd = (result) => {
        const { source, destination } = result;
        if (!destination) return;

        const sourceSlotIndex = parseInt(source.droppableId.split('-')[1], 10);
        const destSlotIndex = parseInt(destination.droppableId.split('-')[1], 10);

        const updatedSlots = [...slots];
        const [movedEntity] = updatedSlots[sourceSlotIndex].splice(source.index, 1);
        updatedSlots[destSlotIndex].splice(destination.index, 0, movedEntity);

        setSlots(updatedSlots);
        throttledSendToBackend(userAddedWords, userRemovedWords, confirmedDefaultEntities, updatedSlots);
    };

    const fetchCharacters = async () => {
        setLoading(true);
        try {
            const response = await fetch('/apilocal/get-character', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ storyId: currentStoryIndex }),
            });
            if (response.ok) {
                const data = await response.json();
                const characters = data.characters || [];
    
                // 清空旧的状态
                setUserAddedWords([]);
                setUserRemovedWords([]);
                setConfirmedDefaultEntities([]);
                setDefaultEntities(characters);
                setSlots(characters.map((entity) => [entity]));
    
                // 更新后端同步
                throttledSendToBackend([], [], [], characters.map((entity) => [entity]));
            } else {
                console.error('Failed to fetch character data');
            }
        } catch (error) {
            console.error('Error fetching characters:', error);
        } finally {
            setLoading(false);
        }
    };    

    const filteredEntities = defaultEntities.filter((entity) => !userRemovedWords.includes(entity));

    const renderEntityList = () => (
        <DragDropContext onDragEnd={handleDragEnd}>
            {slots.map((slot, slotIndex) => (
                <Droppable key={`slot-${slotIndex}`} droppableId={`slot-${slotIndex}`} direction="horizontal">
                    {(provided) => (
                        <div
                            ref={provided.innerRef}
                            {...provided.droppableProps}
                            style={{
                                border: '1px solid #ddd',
                                borderRadius: '5px',
                                padding: '5px',
                                marginBottom: '1px',
                                minHeight: '40px',
                                display: 'flex',
                                gap: '10px',
                                alignItems: 'center',
                            }}
                        >
                            {slot.map((entity, entityIndex) => {
                                const isConfirmed = confirmedDefaultEntities.includes(entity) || userAddedWords.includes(entity);
                                const isDefaultUnconfirmed = defaultEntities.includes(entity) && !isConfirmed;

                                return (
                                    <Draggable
                                        key={`${slotIndex}-${entity}-${entityIndex}`}
                                        draggableId={`${slotIndex}-${entity}-${entityIndex}`}
                                        index={entityIndex}
                                    >
                                        {(provided) => (
                                            <div
                                                ref={provided.innerRef}
                                                {...provided.draggableProps}
                                                {...provided.dragHandleProps}
                                                className={`draggable-item ${isConfirmed ? 'confirmed' : isDefaultUnconfirmed ? 'unconfirmed' : ''}`}
                                            >
                                                {entity}
                                                {!isConfirmed && (
                                                    <span onClick={() => updateEntityStatus(entity, 'confirm')} className="confirm-icon">✔️</span>
                                                )}
                                                <span onClick={() => updateEntityStatus(entity, 'remove', slotIndex)} className="remove-icon">❌</span>
                                            </div>
                                        )}
                                    </Draggable>
                                );
                            })}
                            {provided.placeholder}
                        </div>
                    )}
                </Droppable>
            ))}
        </DragDropContext>
    );

    return (
        <div className="story-book-container">
            <div className="story-content-container">
                <div className="story-content">
                    {stories.length > 0 && stories[currentStoryIndex] ? (
                        <>
                            <div className="story-header">
                                <h3 className="Homepage-subtitle">
                                    {stories[currentStoryIndex].primary_title} - {stories[currentStoryIndex].secondary_title}
                                </h3>
                                <button
                                    onClick={fetchCharacters}
                                    className={`orange-button ${loading ? 'loading' : ''}`}
                                    disabled={loading}
                                >
                                    {loading ? (<><span className="spinner"></span> Processing...</>) : ('Get Characters')}
                                </button>
                            </div>
                            <div className="story-body">
                                <CheckEntity
                                    key={currentStoryIndex}
                                    text={stories[currentStoryIndex].content}
                                    initialWords={userAddedWords}
                                    defaultEntities={filteredEntities}
                                    confirmedDefaultEntities={confirmedDefaultEntities}
                                    onTextSelection={setSelectedPhrase}
                                />
                            </div>
                        </>
                    ) : (
                        <div>Loading...</div>
                    )}
                </div>
                <div className="fixed-bottom">
                    <div className="selected-phrase-container">
                        <div className="selected-phrase-row">
                            <p className="selected-phrase">Selected phrase: {selectedPhrase}</p>
                            <button className="transparent-button" onClick={() => updateEntityStatus(selectedPhrase, 'add')}>Add to Entity List</button>
                        </div>
                        <div className="input-row">
                            <input
                                type="text"
                                value={customPhrase}
                                onChange={(e) => setCustomPhrase(e.target.value)}
                                className="custom-input"
                                placeholder="Enter your phrase"
                            />
                            <button className="transparent-button" onClick={() => updateEntityStatus(customPhrase.trim(), 'add')}>Add to Entity List</button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="entity-list-container">
                <h4>Entity Slots:</h4>
                <p className="entity-list-description">
                    Here are the entities in the narrative extracted by LLMs. Please confirm the entities if they are correct, or remove them if they are wrong. If there are some entities missing, you can also add them. For coreference, please drag and drop them into the same row.
                </p>
                {renderEntityList()}
            </div>
        </div>
    );
};

export default StoryBook;
