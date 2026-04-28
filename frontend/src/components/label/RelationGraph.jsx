import React, { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import { Row, Button, Col, Modal, message } from 'antd';

export default function RelationGraph({ storyId, relationdata, relationdata_detail, characterdata_detail, onNodeSelect }) {
  const [highlightedNode, setHighlightedNode] = useState(null);
  const [highlightedRightNodes, setHighlightedRightNodes] = useState([]);
  const [leftTreeData, setLeftTreeData] = useState(relationdata);
  const [selectedRoot, setSelectedRoot] = useState(null);
  const [depthTwoNodes, setDepthTwoNodes] = useState([]);
  const [option, setOption] = useState({});
  const [rightTreeOption, setRightTreeOption] = useState({});
  const [deleteCandidate, setDeleteCandidate] = useState(null);
  const [chosenTask, setChosenTask] = useState("relation");
  const [showRightTree, setShowRightTree] = useState(false);
  console.log("relationdata", relationdata)

  useEffect(() => {
    setLeftTreeData(relationdata);
  }, [relationdata]);

  const updateNodeStyle = (nodes, highlightedNodeName) => {
    return nodes.map((node) => {
        // 调试信息
        if (node.value === highlightedNodeName) {
            console.log('Selected node:', {
                name: node.name,
                depth: node.depth,
                value: node.value,
                color: node.itemStyle?.color,
                confirmed: node.confirmed,
                autoSuggested: node.auto_suggested,
                check: node.check
            });

            // 如果是关系节点（depth === 4）且已确认或是用户添加的，使用绿色高亮
            const isGreenRelation = node.depth === 4 && (
                node.confirmed || // 已确认的
                (!node.auto_suggested && node.depth === 4) // 用户添加的关系
            );
            const highlightColor = isGreenRelation ? '#2E8B57' : '#E25434';
            const shadowColor = isGreenRelation ? 'rgba(46, 139, 87, 0.5)' : 'rgba(226, 84, 52, 0.5)';

            return {
                ...node,
                itemStyle: {
                    color: highlightColor,
                    boxShadow: `0 4px 8px rgba(0, 0, 0, 0.2), 0 0 10px ${shadowColor}`,
                    shadowBlur: 12,
                    shadowColor: shadowColor,
                    shadowOffsetX: 2,
                    shadowOffsetY: 2,
                },
                label: {
                    fontWeight: 'bold',
                    color: 'white',
                    backgroundColor: highlightColor,
                    padding: [5, 10],
                    borderRadius: 15,
                    borderColor: highlightColor,
                    borderWidth: 1,
                    boxShadow: `0 4px 8px rgba(0, 0, 0, 0.2), 0 0 10px ${shadowColor}`,
                    shadowBlur: 8,
                    shadowColor: shadowColor,
                    shadowOffsetX: 1,
                    shadowOffsetY: 1,
                    transform: 'scale(1.05)',
                    transition: 'all 0.3s ease',
                },
                children: node.children ? updateNodeStyle(node.children, highlightedNodeName) : [],
            };
        }

        // 根据节点的状态决定颜色
        let nodeColor;
        if (node.check) {
            // 如果节点有冲突，使用橙红色
            nodeColor = '#E25434';
        } else if (node.confirmed) {
            // 如果节点已确认，使用绿色
            nodeColor = '#2E8B57';
        } else if (node.auto_suggested) {
            // 如果是自动建议的，使用金色
            nodeColor = '#FFBF00';
        } else if (node.depth === 4) {
            // 如果是关系节点（用户添加的），使用绿色
            nodeColor = '#2E8B57';
        } else {
            // 其他情况保持原有颜色或使用默认颜色
            nodeColor = node.itemStyle?.color || '#FFBF00';
        }

        return {
            ...node,
            itemStyle: {
                ...node.itemStyle,
                color: nodeColor,
            },
            children: node.children ? updateNodeStyle(node.children, highlightedNodeName) : [],
        };
    });
};

  const updateRightTreeStyle = (nodes, highlightedRightNodeNames) => {
    return nodes.map((node) => ({
      ...node,
      symbolSize: highlightedRightNodeNames.includes(node.name) ? 10 : node.symbolSize || 7,
      itemStyle: highlightedRightNodeNames.includes(node.name) ? { color: '#ff471a' } : node.itemStyle || {},
      label: highlightedRightNodeNames.includes(node.name) 
        ? { fontSize: 15, color: '#661400' }
        : node.label || {},
      children: node.children ? updateRightTreeStyle(node.children, highlightedRightNodeNames) : [],
    }));
  };

  useEffect(() => {
    const extractDepthTwoNodes = (nodes) => {
      const seen = new Set();
      const result = [];
  
      const traverse = (node) => {
        if (node.depth === 2 && !seen.has(node.name)) {
          seen.add(node.name);
          result.push(node);
        }
        if (node.children) {
          node.children.forEach(traverse);
        }
      };
  
      nodes.forEach(traverse);
      return result;
    };
  
    const depthTwo = extractDepthTwoNodes(leftTreeData);
    console.log("Filtered depthTwoNodes", depthTwo);
    setDepthTwoNodes(depthTwo);
  }, [leftTreeData]);
  

  const buildSubTree = (rootNodeName, nodes, currentDepth = 1) => {
    for (const node of nodes) {
      if (node.name === rootNodeName && currentDepth === 2) {
        return node;
      }
      if (node.children) {
        const foundNode = buildSubTree(rootNodeName, node.children, currentDepth + 1);
        if (foundNode) return foundNode;
      }
    }
    return null; 
  };

  const findMatchingRightNodesWithAncestors = (allRightTreeNodes, childrenNames) => {
    const matchedNodes = [];
    const findInTree = (nodes) => {
      nodes.forEach((node) => {
        if (childrenNames.includes(node.name)) {
          matchedNodes.push(node.name);
        }
        if (node.children) {
          findInTree(node.children);
        }
      });
    };
    findInTree(allRightTreeNodes);
    return matchedNodes;
  };

  const handleButtonClick = (nodeName) => {
    setSelectedRoot(nodeName);
    setDeleteCandidate(null);
    setShowRightTree(false);
    //setHighlightedNode(nodeName);
    const findNodeAtDepthTwo = (nodes, targetNodeName, currentDepth = 1) => {
      for (const node of nodes) {
        if (node.name === targetNodeName && currentDepth === 2) {
          // Collect the node's name and all children's names
          const childrenNames = node.children ? node.children.map(child => child.name) : [];
          return { nodeName: node.name, childrenNames };
        }
        if (node.children) {
          const result = findNodeAtDepthTwo(node.children, targetNodeName, currentDepth + 1);
          if (result) return result;
        }
      }
      return null;
    };
    setChosenTask("character");
  };
  
  // update left tree (option) based on right tree (rightTreeOption) selection
  const updateLeftTreeChildrenHighlight = async (childrenName, isHighlighted) => {
    try {
        const response = await fetch('/apilocal/change-relation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
              childrenName, isHighlighted, highlightedNode, leftTreeData, storyId, highlightedRightNodes, selectedRoot 
            }),
        });
        const updatedTreeData = await response.json();
        console.log("updatedTreeData", updatedTreeData);
        setLeftTreeData(updatedTreeData);
    } catch (error) {
        console.error('Error updating node:', error);
    }
  };

  const updateLeftTreeChildrenHighlightCharacter = async (childrenName, isHighlighted) => {
    try {
      const response = await fetch('/apilocal/change-character', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ childrenName, isHighlighted, highlightedNode, leftTreeData, storyId }),
      });
      const updatedTreeData = await response.json();
      console.log("updatedTreeData", updatedTreeData);
      setLeftTreeData(updatedTreeData);
    } catch (error) {
      console.error('Error updating node on the server:', error);
    }
  };

  const deleteNode = async (node) => {
    try {
        const response = await fetch('/apilocal/delete-node', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
              nodeName: node.name, 
              nodeValue: node.value, 
              leftTreeData, 
              storyId 
            }),
        });
        const updatedTreeData = await response.json();
        setLeftTreeData(updatedTreeData);
        message.success(`Node "${node.name}" deleted successfully.`);
    } catch (error) {
        console.error('Error deleting node:', error);
        message.error('Failed to delete node.');
    }
  };

  // merge entities (coreference)
  const mergeCoreference = async (childrenName, isHighlighted) => {
    try {
      const response = await fetch('/apilocal/merge-coreference', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          childrenName, isHighlighted, highlightedNode, leftTreeData, storyId, highlightedRightNodes, selectedRoot 
        }),
      });

      if (response.ok) {
        const result = await response.json();
        message.success('Entities successfully merged!');
        console.log('Merge result:', result);
        return result; 
      } else {
        const error = await response.text();
        message.error(`Merge failed: ${error}`);
        throw new Error(error);
      }
    } catch (error) {
      console.error('Error merging entities:', error);
      message.error('An error occurred while merging entities.');
      throw error;
    }
  };

  const handleNodeClickLeft = (params) => {
    const childrenNames = params.data.children ? params.data.children.map(child => child.name) : [];
    setHighlightedNode(params.data.value);
    setDeleteCandidate(null);
    if (params.data.depth === 3) {
      setChosenTask("relation");
      onNodeSelect(selectedRoot, params.data.name)
      setHighlightedRightNodes(findMatchingRightNodesWithAncestors([relationdata_detail], childrenNames));
      setShowRightTree(true);
    } else if (params.data.depth === 2) {
      setChosenTask("character");
      //selectedRoot, params.data.name
      setHighlightedRightNodes(findMatchingRightNodesWithAncestors([characterdata_detail], childrenNames));
      setShowRightTree(true);
    } else if (params.data.depth === 4) {
      //setChosenTask("character");
      //selectedRoot, params.data.name
      const childrenNames = params.data.children ? params.data.children.map(child => child.name) : [];
      setHighlightedRightNodes(findMatchingRightNodesWithAncestors([characterdata_detail], childrenNames));
      setDeleteCandidate(params.data);
      setShowRightTree(false);
    }
  };

  const handleNodeClick = (params) => {
    const childrenNames = params.data.children ? params.data.children.map(child => child.name) : [];

    if (params.seriesName === 'Relation Graph') {
      setHighlightedNode(params.data.value);
      if (params.data.depth === 3) {
        setChosenTask("relation");
        setHighlightedRightNodes(findMatchingRightNodesWithAncestors([relationdata_detail], childrenNames));
      } else if (params.data.depth === 2) {
        setChosenTask("character");
        setHighlightedRightNodes(findMatchingRightNodesWithAncestors([characterdata_detail], childrenNames));
      } else if (params.data.depth === 4) {}
    } else if (params.seriesName === 'Choices') {
      const clickedNodeName = params.data.name;
      console.log("node check", clickedNodeName)
      if (clickedNodeName === 'coreference'){
        Modal.confirm({
          title: 'Merge Entities',
          content: 'Are you sure you want to merge the two entities?',
          okText: 'Confirm',
          cancelText: 'Cancel',
          onOk: async () => {
            try {
              const entities = params.data.entities; 
              await mergeCoreference(entities);
            } catch (error) {
              console.error('Merge operation failed:', error);
            }
          },
          onCancel: () => {
            message.info('Merge cancelled.');
          },
        });
      } else{
        const updater = chosenTask === 'relation' ? updateLeftTreeChildrenHighlight : updateLeftTreeChildrenHighlightCharacter;

        setHighlightedRightNodes(prev =>
          prev.includes(clickedNodeName) ? prev.filter(node => node !== clickedNodeName) : [...prev, clickedNodeName]
        );
  
        updater(clickedNodeName, !highlightedRightNodes.includes(clickedNodeName));
      }
    }
  };

  useEffect(() => {
    const rootNode = selectedRoot ? buildSubTree(selectedRoot, leftTreeData) : null;
    console.log("chart generated")

    setOption({
      tooltip: {
          trigger: 'item',
          triggerOn: 'mousemove',
          formatter: (params) => {
            const name = params.data.name;
            const check = params.data.check;
          
            let message = '';
          
            if (check && typeof check === 'object') {
              message = Object.values(check)
                .map(arr => {
                  if (Array.isArray(arr) && arr.length === 3) {
                    return `${arr[0]} - ${arr[1]} - ${arr[2]}`;
                  }
                  return '';
                })
                .filter(Boolean)
                .join('<br/>');
            } else {
              message = 'No conflicts detected';
            }
          
            return `
              <div style="font-size: 14px; line-height: 1.5;">
                <strong style="color: #E25434;">${name}</strong><br/>
                ${message}
              </div>
            `;
          },
          backgroundColor: '#ffffff',
          borderColor: '#E25434',
          borderWidth: 1,
          textStyle: {
              color: '#333',
              fontSize: 14,
          },
      },
      series: [
          {
              type: 'tree',
              name: 'Relation Graph',
              data: rootNode ? updateNodeStyle([rootNode], highlightedNode) : [],
              top: '1%',
              left: '24%',
              bottom: '15%',
              right: '25%',
              symbolSize: 10,
              expandAndCollapse: true,
              initialTreeDepth: rootNode ? 2 : 1,
              label: {
                  position: 'left',
                  verticalAlign: 'middle',
                  align: 'right',
                  fontSize: 14,
                  color: '#333',
                  backgroundColor: '#f9f9f9', 
                  padding: [5, 12], 
                  borderRadius: 16, 
                  borderWidth: 1,
                  borderColor: '#ddd', 
                  shadowColor: 'rgba(0, 0, 0, 0.1)', 
                  shadowBlur: 4, 
                  shadowOffsetX: 2, 
                  shadowOffsetY: 2, 
                  formatter: '{b}',
              },
              leaves: {
                  label: {
                      position: 'right',
                      verticalAlign: 'middle',
                      align: 'left',
                      fontSize: 14,
                      color: '#333',
                      backgroundColor: '#f9f9f9',
                      padding: [5, 12],
                      borderRadius: 16,
                      borderWidth: 1,
                      borderColor: '#ddd',
                      shadowColor: 'rgba(0, 0, 0, 0.1)',
                      shadowBlur: 4,
                      shadowOffsetX: 2,
                      shadowOffsetY: 2,
                      formatter: '{b}',
                  },
              },
              lineStyle: {
                  color: '#E25434',
                  width: 2,
              },
              animationDuration: 550,
              animationDurationUpdate: 750,
          },
      ],
    });
  
    setRightTreeOption({
      tooltip: { trigger: 'item', triggerOn: 'mousemove' },
      series: [
        {
          type: 'tree',
          name: 'Choices',
          data: updateRightTreeStyle(chosenTask === 'relation' ? [relationdata_detail] : [characterdata_detail], highlightedRightNodes),
          top: '0%', left: '15%', bottom: '20%', right: '30%',
          symbolSize: 7,
          label: { position: 'left', verticalAlign: 'middle', align: 'right' },
          leaves: { label: { position: 'right', verticalAlign: 'middle', align: 'left' } },
          expandAndCollapse: true,
          animationDuration: 550,
          animationDurationUpdate: 750,
        },
      ],
    });
  }, [selectedRoot, highlightedNode, leftTreeData, highlightedRightNodes, chosenTask]);

  // 只查找 depth=2 的 selectedRoot 节点，统计其 children 里 depth=3 的数量
  const getSelectedRootNode = (selectedRoot, treeData) => {
    if (!selectedRoot || !Array.isArray(treeData)) return null;
    let found = null;
    const traverse = (nodes) => {
      for (const node of nodes) {
        if (node.name === selectedRoot && node.depth === 2) {
          found = node;
          return;
        }
        if (node.children) traverse(node.children);
        if (found) return;
      }
    };
    traverse(treeData);
    return found;
  };

  const selectedRootNode = getSelectedRootNode(selectedRoot, leftTreeData);
  const childCount = selectedRootNode && Array.isArray(selectedRootNode.children)
    ? selectedRootNode.children.filter(child => child.depth === 3).length
    : 0;
  const baseHeight = 400;
  const height = baseHeight + Math.max(0, childCount) * 65;
  console.log('childCount (selectedRoot depth=3 children):', childCount, 'height:', height);

  return (
    <div style={{ 
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      overflow: 'auto',
      position: 'relative'
    }}>
      <div style={{ 
        paddingBottom: deleteCandidate ? '80px' : '20px'
      }}>
        <div className="label-relation-container" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 className="label-relation-title">Label Relation</h3>
              <p className="label-relation-description">
                Please select a node to display its relation tree.
              </p>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <button
                className="toggle-button"
                onClick={() => {
                  Modal.confirm({
                    title: 'Regenerate Relations',
                    content: 'Are you sure you want to regenerate all relations? This will reset all your manual changes.',
                    okText: 'Yes',
                    cancelText: 'No',
                    onOk: async () => {
                      try {
                        const response = await fetch(`/apilocal/regenerate-relations/${storyId}`, {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' }
                        });
                        if (!response.ok) {
                          throw new Error('Failed to regenerate relations');
                        }
                        const data = await response.json();
                        setLeftTreeData(data.relationdata || []);
                        message.success('Relations regenerated successfully!');
                      } catch (error) {
                        console.error('Error regenerating relations:', error);
                        message.error('Failed to regenerate relations');
                      }
                    }
                  });
                }}
              >
                Regenerate Relations
              </button>
              <button
                className="toggle-button"
                onClick={async () => {
                  try {
                    const response = await fetch('/apilocal/download-relation', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                    });
                    
                    if (!response.ok) {
                      throw new Error('Failed to download relations');
                    }
                    
                    const data = await response.json();
                    
                    // 创建Blob并下载
                    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `relations_${new Date().toISOString().split('T')[0]}.json`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    message.success('Relations downloaded successfully!');
                  } catch (error) {
                    console.error('Error downloading relations:', error);
                    message.error('Failed to download relations');
                  }
                }}
              >
                Download Relations
              </button>
            </div>
          </div>
          <Row gutter={[16, 16]} className="node-button-container">
              {depthTwoNodes.map((node) => (
                  <Col key={node.name} xs={24} sm={12} md={8} lg={6}>
                      <Button
                          className={`node-button ${node.name === selectedRoot ? 'selected' : ''}`}
                          onClick={() => handleButtonClick(node.name)}
                          block
                          style={{
                            height: 'auto',
                            whiteSpace: 'pre-wrap',
                            padding: '8px'
                          }}
                      >
                          {node.name}
                      </Button>
                  </Col>
              ))}
          </Row>
        </div>

        <div style={{ padding: '0 20px' }}>
          {selectedRoot && (
            <Row style={{ marginBottom: '20px' }}>
              <ReactECharts
                option={option}
                style={{ height: `${height}px`, minHeight: '500px', width: '45vw' }}
                onEvents={{ click: handleNodeClickLeft }}
              />
            </Row>
          )}

          {showRightTree && (
            <Row style={{ marginBottom: '20px' }}>
              <ReactECharts
                option={rightTreeOption}
                style={{ minHeight: '1000px', width: '45vw' }}
                onEvents={{ click: handleNodeClick }}
              />
            </Row>
          )}
        </div>
      </div>

      {deleteCandidate && (
        <Row justify="center" align="middle" style={{ 
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          width: '100%',
          padding: '15px',
          backgroundColor: '#fff',
          boxShadow: '0 -2px 8px rgba(0, 0, 0, 0.15)',
          zIndex: 1000
        }}>
          <Col span={12} style={{ textAlign: 'center' }}>
            <Button
              className="apple-button confirm"
              style={{
                marginRight: '10px',
                backgroundColor: '#4CAF50',
                color: 'white',
                border: 'none',
                padding: '6px 16px'
              }}
              onClick={async () => {
                try {
                  const response = await fetch('/apilocal/confirm-node', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      nodeValue: deleteCandidate.value,
                      storyId,
                      leftTreeData,
                    }),
                  });

                  if (response.ok) {
                    const updatedTreeData = await response.json();
                    setLeftTreeData(updatedTreeData);
                    message.success(`Node "${deleteCandidate.name}" confirmed.`);
                    setDeleteCandidate(null);
                  } else {
                    message.error('Failed to confirm node.');
                  }
                } catch (error) {
                  console.error('Error confirming node:', error);
                  message.error('Error occurred during confirmation.');
                }
              }}
            >
              ✅ Confirm "{deleteCandidate.name}"
            </Button>
          </Col>

          <Col span={12} style={{ textAlign: 'center' }}>
            <Button
              className="apple-button delete"
              style={{
                backgroundColor: '#ff4d4f',
                color: 'white',
                border: 'none',
                padding: '6px 16px'
              }}
              onClick={async () => {
                await deleteNode(deleteCandidate);
                setDeleteCandidate(null);
              }}
            >
              🗑 Delete "{deleteCandidate.name}"
            </Button>
          </Col>
        </Row>
      )}
    </div>
  );
}
