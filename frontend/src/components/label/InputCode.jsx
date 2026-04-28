import React, { useState, useEffect, useRef } from 'react';
import { Editor } from '@monaco-editor/react';
import axios from 'axios';
import { useNavigate, useLocation } from 'react-router-dom';
import ModelChoice from '../utils/ModelChoice';
import { Spin, Card, Button, Typography } from 'antd';
const { Title } = Typography;

const ButtonList = () => {
  const location = useLocation();
  const { taskValue } = location.state;

  const [selectedButton, setSelectedButton] = useState(null);
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const options = ['GPT', 'Claude', 'LlaMa', 'Qwen', 'Custom'];
  const [selectedOption, setSelectedOption] = useState("GPT");

  const handleOptionSelect = (option) => {
    setSelectedOption(option);
    handleButtonClick(option);
  };

  const [currentCode, setCurrentCode] = useState(null);

  const [currentModelSetting, setCurrentModelSetting]  = useState({
    GPT: { code: '', checked: false },
    Claude: { code: '', checked: false },
    LlaMa: { code: '', checked: false },
    Qwen: { code: '', checked: false },
    Custom: { code: '', checked: false },
  });

  const [currentComponentStateEntity, setCurrentComponentStateEntity] = useState({
    EntityPreProcessing: { code: '', checked: false },
    EntityExtraction: { code: '', checked: false },
    EntityPostProcessing: { code: '', checked: false }
  });

  const [currentComponentStateRelation, setCurrentComponentStateRelation] = useState({
    RelationPreProcessing: { code: '', checked: false },
    RelationExtraction: { code: '', checked: false },
    RelationPostProcessing: { code: '', checked: false }
  });

  const editorRef = useRef(null);

  useEffect(() => {
    const fetchDefaultCode = async () => {
      try {
        const Task = { task: taskValue };
        const response = await axios.post('/apilocal/send-default-flow', Task);
        setCurrentModelSetting(response.data.defaultModelSetting);
        setCurrentComponentStateEntity(response.data.defaultCodeEntity);
        setCurrentComponentStateRelation(response.data.defaultCodeRelation);
        setSelectedButton(Object.keys(response.data.defaultCodeEntity)[1]);
        setCurrentCode(response.data.defaultCodeEntity[Object.keys(response.data.defaultCodeEntity)[0]].code);
      } catch (error) {
        console.error('Error fetching default code:', error);
      }
    };
    fetchDefaultCode();
  }, [taskValue]);

  const handleButtonClick = (buttonName) => {
    setSelectedButton(buttonName);
    if (buttonName.startsWith('Entity')) {
      setCurrentCode(currentComponentStateEntity[buttonName].code);
    } else if (buttonName.startsWith('Relation')) {
      setCurrentCode(currentComponentStateRelation[buttonName].code);
    } else {
      setCurrentCode(currentModelSetting[buttonName].code);
    }
  };

  const handleSaveCode = async () => {
    try {
      const codeObject = {
        code: {
          defaultModelSetting: currentModelSetting,
          defaultCodeEntity: currentComponentStateEntity,
          defaultCodeRelation: currentComponentStateRelation
        },
        task: taskValue,
        selectedOption: selectedOption
      };
      await axios.post('/apilocal/save-setting', codeObject);
      alert('Code saved successfully!');
    } catch (error) {
      console.error('Error saving code:', error);
      alert('Error saving code. Please try again later.');
    }
  };

  const handleTestCode = async () => {
    setLoading(true);
    setResponse(null);
    try {
      const codeObject = {
        code: {
          defaultModelSetting: currentModelSetting,
          defaultCodeEntity: currentComponentStateEntity,
          defaultCodeRelation: currentComponentStateRelation
        },
        task: taskValue,
        selectedOption: selectedOption
      };
      const response = await axios.post('/apilocal/test-setting', codeObject);
      setResponse(response.data);
    } catch (error) {
      console.error('Error testing code:', error);
      alert('Error testing code. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleStartLabel = async () => {
    try {
      const codeObject = {
        code: {
          defaultModelSetting: currentModelSetting,
          defaultCodeEntity: currentComponentStateEntity,
          defaultCodeRelation: currentComponentStateRelation
        },
        task: taskValue,
        selectedOption: selectedOption
      };
      const dataToPass = {
        taskValue: { taskValue }
      };
      await axios.post('/apilocal/input-flow-character', codeObject);
      navigate('/labelentity', { state: dataToPass });
    } catch (error) {
      console.error('Error saving code:', error);
      alert('Error saving code. Please try again later.');
    }
  };

  const handleEditorChange = (newValue) => {
    setSelectedButton((prevSelectedButton) => {
      const updatedButtonName = prevSelectedButton;
      if (updatedButtonName.startsWith('Entity')) {
        setCurrentComponentStateEntity((prevState) => ({
          ...prevState,
          [updatedButtonName]: {
            ...prevState[updatedButtonName],
            checked: true,
            code: newValue,
          }
        }));
      } else if (selectedButton.startsWith('Relation')) {
        setCurrentComponentStateRelation((prevState) => ({
          ...prevState,
          [updatedButtonName]: {
            ...prevState[updatedButtonName],
            checked: true,
            code: newValue,
          }
        }));
      } else {
        setCurrentModelSetting((prevState) => ({
          ...prevState,
          [updatedButtonName]: {
            ...prevState[updatedButtonName],
            checked: true,
            code: newValue,
          }
        }));
      }
      return updatedButtonName;
    });
  };

  return (
      <div className='flowlist'>
        <div style={{ display: 'flex', gap: '20px' }}>
          <div className="flowlist-left">
            <h3 className='flowlist-subtitle'>Model Setting</h3>
            <ModelChoice
                options={options}
                selectedOption={selectedOption}
                onOptionSelect={handleOptionSelect}
            />
            <div className="flowlist-entity">
              <ul>
                <li className="flowlist-button" onClick={() => handleButtonClick(selectedOption)}>
                  Model Setting
                </li>
              </ul>
            </div>
            <h3 className='flowlist-subtitle'>Entity Extraction</h3>
            <div className="flowlist-entity">
              <ul>
                <li className="flowlist-button"
                    onClick={() => handleButtonClick('EntityPreProcessing')}>Pre-processing
                </li>
                <li className="flowlist-button" onClick={() => handleButtonClick('EntityExtraction')}>Entity
                  Extraction
                </li>
                <li className="flowlist-button"
                    onClick={() => handleButtonClick('EntityPostProcessing')}>Post-processing
                </li>
              </ul>
            </div>
            <h3 className='flowlist-subtitle'>Relation Extraction</h3>
            <div className="flowlist-entity">
              <ul>
                <li className="flowlist-button"
                    onClick={() => handleButtonClick('RelationPreProcessing')}>Pre-processing
                </li>
                <li className="flowlist-button" onClick={() => handleButtonClick('RelationExtraction')}>Relation
                  Extraction
                </li>
                <li className="flowlist-button"
                    onClick={() => handleButtonClick('RelationPostProcessing')}>Post-processing
                </li>
              </ul>
            </div>
          </div>
          {selectedButton && (
              <div>
                <h3>{selectedButton}</h3>
                <Editor
                    width="65vw"
                    height="65vh"
                    language="python"
                    theme="vs-dark"
                    value={currentCode}
                    onChange={handleEditorChange}
                    editorDidMount={(editor) => {
                      editorRef.current = editor;
                    }}
                />
              </div>
          )}
        </div>

        <div style={{marginTop: 20, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
          <Spin spinning={loading} tip="Testing...">
            <div style={{width: '65vw', display: 'flex', justifyContent: 'flex-end'}}>
              {response && (
                  <Card title="Response from Backend" style={{width: '60%'}}>
                    <pre>{JSON.stringify(response, null, 2)}</pre>
                  </Card>
              )}
            </div>
          </Spin>
        </div>

        <div style={{display: 'flex', gap: '20px'}}>
          <button className="Homepage-button" onClick={handleSaveCode}>Save Code</button>
          <button className="Homepage-button" onClick={handleTestCode}>Test Code</button>
          <button className="Homepage-button" onClick={handleStartLabel}>Start Label</button>
        </div>
      </div>
  );
};

export default ButtonList;