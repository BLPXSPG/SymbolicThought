import React, { useState} from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { Typography , message} from 'antd'
import logo from '../image/label-logo.png' 
import click from '../image/click.jpg' 
import upload from '../image/upload.jpg' 
import { Col, Row, Input, Button, Space, Upload, UploadProps } from 'antd';
import NavigationButton from '../utils/NavigationButton';
import { useNavigate } from 'react-router-dom';

const { Title } = Typography

export default function Homepage() {
  const [storyname, setStoryname] = useState('')
  const [fileList, setFileList] = useState([])

  const navigate = useNavigate();

  const handleCharacterRelation = async () => {
    try {
      // Send message to backend
      //await axios.post('/apilocal/input-flow-character', 1);
      const dataToPass = {
        taskValue: 'Character'
      };
      // Navigate to the upload page
      navigate('/upload-story', { state: dataToPass });
    } catch (error) {
      console.error('Error sending message:', error);
      // Optionally, you can show an error message to the user here
    }
  };

  const handleSalientEvent = async () => {
    try {
      // Send message to backend
      //await axios.post('/apilocal/input-flow-event', 1);
      const dataToPass = {
        taskValue: 'Event'
      };
      // Navigate to the upload page
      navigate('/upload-story', { state: dataToPass });
    } catch (error) {
      console.error('Error sending message:', error);
      // Optionally, you can show an error message to the user here
    }
  };

  const handleCustom = async () => {
    try {
      const dataToPass = {
        taskValue: 'Custom'
      };
      // Navigate to the upload page
      navigate('/upload-story', { state: dataToPass });
    } catch (error) {
      console.error('Error sending message:', error);
      // Optionally, you can show an error message to the user here
    }
  };

  return (
    <div className="Homepage">
      <div>
        <img src={logo} alt="logo" className='App-logo'/>
      </div>
      <Title className="Homepage-title"> SymbolicThought</Title>
      <Col className='normal-text no-wrap Homepage-subtitle' span={24}>
        <b>The AI-powered tool for labeling complex narrative relationships </b> 
      </Col>
      <NavigationButton path="/labelentity" name="Try SymbolicThought"> </NavigationButton>
      <NavigationButton path="/upload-story" name="Upload Your Narrative"> </NavigationButton>
    </div>
  )
}
