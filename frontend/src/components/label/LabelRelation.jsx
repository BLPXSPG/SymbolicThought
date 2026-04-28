import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Col, Row, Button } from 'antd';
import RelationGraph from './RelationGraph';
import StoryShow from '../utils/StoryShow';
import StorySwitcher from '../utils/StorySwitcher';
import { relationdata_detail } from './test_background';

export default function LabelRelation() {
    const [stories, setStories] = useState([]);
    const [currentStoryIndex, setCurrentStoryIndex] = useState(0);
    const [showStoryList, setShowStoryList] = useState(false);
    const [relationData, setRelationData] = useState([]);
    const [characterDataDetail, setCharacterDataDetail] = useState([]);
    const [highlightedNodeName, setHighlightedNodeName] = useState(null); 
    const [highlightedChildrenNames, setHighlightedChildrenNames] = useState([]);
    

    const navigate = useNavigate();
    const location = useLocation();
    
    useEffect(() => {
        const initialStoryIndex = location.state?.currentStoryIndex || 0;
        setCurrentStoryIndex(initialStoryIndex);

        fetch('/apilocal/get-books')
            .then(response => response.json())
            .then(data => {
                const storiesWithEntities = data.map(story => ({
                    ...story,
                    defaultEntities: story.entities || []
                }));
                setStories(storiesWithEntities);
                //console.log(data)
                fetchRelationData(initialStoryIndex);
            })
            .catch(error => console.error('Error fetching story data:', error));
    }, [location.state]);

    const [loading, setLoading] = useState(false);

    const fetchRelationData = (index) => {
        setLoading(true); // 开始加载
        fetch(`/apilocal/get-relation-data/${index}`)
            .then(async response => {
                const text = await response.text();
                let data;
                try {
                    data = JSON.parse(text);
                } catch (error) {
                    throw new Error(`Server returned non-JSON response (${response.status}).`);
                }
                if (!response.ok) {
                    throw new Error(data.error || `Request failed with status ${response.status}`);
                }
                return data;
            })
            .then(data => {
                console.log("relation data got", index, data);
                setRelationData(data.relationdata || []);
                setCharacterDataDetail(data.characterdata_detail || []);
                setStories(data.story_data || []);
                console.log("relation data got", relationData);
            })
            .catch(error => {
                alert(error.message);
                console.error('Error fetching relation data:', error);
            })
            .finally(() => {
                setLoading(false); // 加载完成（无论成功或失败）
            });
    };
    

    const handleStoryClick = (index) => {
        setCurrentStoryIndex(index);
        setShowStoryList(false);
        fetchRelationData(index); 
    };

    const handleNodeSelection = (nodeName, childrenNames) => {
      console.log("at label-relation", nodeName, childrenNames)
      setHighlightedNodeName(nodeName);
      
      // 安全地访问嵌套的 rag 对象
      const currentStory = stories[currentStoryIndex];
      if (currentStory && currentStory.rag && currentStory.rag[nodeName] && currentStory.rag[nodeName][childrenNames]) {
        console.log("rag", currentStory.rag[nodeName][childrenNames]);
        setHighlightedChildrenNames(currentStory.rag[nodeName][childrenNames]);
      } else {
        console.warn(`RAG data not found for: ${nodeName} -> ${childrenNames}`);
        setHighlightedChildrenNames([]);
      }
    };

    const toggleStoryList = () => {
        setShowStoryList(!showStoryList);
    };

    const navigateToLabelEntity = () => {
        const currentStory = stories[currentStoryIndex];
        navigate('/labelentity', { state: { currentStoryIndex, currentStory } });
    };

    return (
        <div className="Homepage">
            <Row className="background-container" style={{ height: '85vh', marginLeft:'20px', marginBottom: '20px' }}>
                {/* Left part - showing the story */}
                <Col span={12} className="background-scroll">
                    <Row justify="space-between" align="middle" style={{ marginBottom: '20px' }}>
                        <StorySwitcher 
                            stories={stories} 
                            currentStoryIndex={currentStoryIndex} 
                            onStoryClick={handleStoryClick} 
                            showStoryList={showStoryList}
                            toggleStoryList={toggleStoryList} 
                        />
                        <div>
                            <Button className="toggle-button" onClick={navigateToLabelEntity}>
                                Go to Label Entity
                            </Button>
                        </div>
                    </Row>
                    <StoryShow 
                        stories={stories} 
                        currentStoryIndex={currentStoryIndex} 
                        highlightedNodeName={highlightedNodeName} 
                        highlightedChildrenNames={highlightedChildrenNames} 
                    />
                </Col>

                {/* Right part - showing the relation */}
                <Col span={12} 
                    style={{ 
                        overflowY: 'auto', 
                        overflowX: 'hidden', 
                        height: '100vh' 
                    }}
                >
                    {loading ? (
                        <div className="loading-container" style={{ textAlign: 'center', paddingTop: '20px' }}>
                            <p>Generating character relations...</p>
                            <div className="spinner"></div>
                        </div>
                    ) : (
                        <RelationGraph 
                            key={currentStoryIndex}
                            storyId={currentStoryIndex}
                            relationdata={relationData} 
                            relationdata_detail={relationdata_detail} 
                            characterdata_detail={characterDataDetail} 
                            onNodeSelect={handleNodeSelection} 
                        />
                    )}
                </Col>


            </Row>
        </div>
    );
}
