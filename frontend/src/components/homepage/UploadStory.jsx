import React, { useState} from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { Typography , message, Modal} from 'antd'
import logo from '../image/label-logo.png' 
import click from '../image/click.jpg' 
import upload from '../image/upload.jpg' 
import { Col, Row, Input, Button, Space, Upload, UploadProps } from 'antd';
import NavigationButton from '../utils/NavigationButton';
import { UploadOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

const { Title } = Typography


export default function UploadStory() {
  const [storyname, setStoryname] = useState('')
  const [fileList, setFileList] = useState([])
  const [storyFileUploaded, setStoryFileUploaded] = useState(false)
  const location = useLocation();
  const { taskValue } = location.state || {};
  const navigate = useNavigate();

    const handleChangeName = (e) => {
      const { value: inputValue } = e.target
      setStoryname(inputValue)
    }
      const beforeUploadJSON = (file) => {
        const isJSON = file.type === 'application/json';
        if (!isJSON) {
          message.error(`${file.name} is not a JSON file`);
        }
        const fileSize = file.size / 1024 / 1024 < 5;
        if (!fileSize) {
          message.error(`${file.name} exceeds 5MB`);
        }
        return isJSON && fileSize ? true : Upload.LIST_IGNORE;
      };
    
      const beforeUploadTXT = (file) => {
        const isTXT = file.type === 'text/plain';
        if (!isTXT) {
          message.error(`${file.name} is not a TXT file`);
        }
        const fileSize = file.size / 1024 / 1024 < 5;
        if (!fileSize) {
          message.error(`${file.name} exceeds 5MB`);
        }
        return isTXT && fileSize ? true : Upload.LIST_IGNORE;
      };
    
      const handleStoryUpload = (info) => {
        if (info.file.status === 'removed') {
          setStoryFileUploaded(false);
          return;
        }
        if (info.file.status !== 'uploading') {
          console.log(info.file, info.fileList);
          let formData = new FormData();
          formData.append("file", info.file.originFileObj);
          formData.append("fileType", "story");
          axios
          .post('/apilocal/input-narrative-file', formData)//api
          .then(function (response) {
            console.log(response)
            message.info('Story file received, thank you!')
            setStoryFileUploaded(true);
          })
          .catch(function (error) {
            console.log(error)
            setStoryFileUploaded(false);
          })
        }
      };

      const handleStartLabelling = () => {
        // 检查文件上传状态
        if (!storyFileUploaded) {
          message.warning('Please upload a story file before starting labelling.');
          return;
        }

        // 显示确认对话框
        Modal.confirm({
          title: 'Confirm File Format',
          content: (
            <div>
              <p>Please confirm that your uploaded story file is in the correct format:</p>
              <ul>
                <li><strong>Story file:</strong> JSON format with proper story structure</li>
              </ul>
              
              <p><strong>Story file format example:</strong></p>
              <pre style={{ 
                backgroundColor: '#f5f5f5', 
                padding: '10px', 
                borderRadius: '4px', 
                fontSize: '12px',
                overflow: 'auto',
                maxHeight: '150px'
              }}>
{`[
  {
    "number": 1,
    "primary_title": "Historical record",
    "secondary_title": "Crimean War",
    "content": "In the autumn of 1853..."
  },
  {
    "number": 2,
    "primary_title": "Historical record", 
    "secondary_title": "Mongol invasion",
    "content": "In the mid-19th century..."
  }
]`}
              </pre>
              
              <p>Proceeding with incorrectly formatted files may cause errors in the labelling process.</p>
              <p>Do you want to continue with the current file?</p>
            </div>
          ),
          okText: 'Yes, Continue',
          cancelText: 'Cancel',
          width: 600,
          onOk() {
            // 用户确认后导航到标注页面
            navigate('/labelentity');
          },
          onCancel() {
            console.log('User cancelled');
          },
        });
      };

      const showFormatDetails = () => {
        Modal.info({
          title: 'Story File Format Requirements',
          content: (
            <div>
              <p><strong>Required format:</strong> JSON file containing an array of story objects</p>
              
              <p><strong>Required fields for each story object:</strong></p>
              <ul>
                <li><strong>number:</strong> Integer - Story sequence number</li>
                <li><strong>primary_title:</strong> String - Main category or type</li>
                <li><strong>secondary_title:</strong> String - Specific title or subtitle</li>
                <li><strong>content:</strong> String - The actual story content</li>
              </ul>
              
              <p><strong>Example format:</strong></p>
              <pre style={{ 
                backgroundColor: '#f5f5f5', 
                padding: '10px', 
                borderRadius: '4px', 
                fontSize: '12px',
                overflow: 'auto',
                maxHeight: '200px'
              }}>
{`[
  {
    "number": 1,
    "primary_title": "Historical record",
    "secondary_title": "Crimean War",
    "content": "In the autumn of 1853, tensions between Russia and the Ottoman Empire escalated..."
  },
  {
    "number": 2,
    "primary_title": "Historical record", 
    "secondary_title": "Mongol invasion",
    "content": "In the mid-19th century, the Mongol forces advanced across the steppes..."
  }
]`}
              </pre>
            </div>
          ),
          width: 700,
          okText: 'Got it',
        });
      };

  return (
    <div className="Homepage">
      <div>
        <img src={logo} alt="logo" className='App-logo'/>
      </div>
      <Title className="Homepage-title"> SymbolicThought</Title>

      <Row>
        <Col span={8}></Col>
        <Col span={16} className='normal-text no-wrap'>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <b>Upload your story file: </b> 
            {storyFileUploaded && <span style={{ color: 'green' }}>✓ Uploaded</span>}
            <Upload beforeUpload={beforeUploadJSON} onChange={handleStoryUpload}>
              <Button ghost className='uploadbutton'>
                <img src={upload} alt="logo" className='App-icon2'/> 
              </Button>
            </Upload>
          </div>
          <div style={{ marginTop: '5px', textAlign: 'center' }}>
            <Button 
              type="link" 
              size="small" 
              onClick={showFormatDetails}
              style={{ 
                padding: '0', 
                height: 'auto', 
                fontSize: '12px', 
                color: '#666',
                textDecoration: 'underline'
              }}
            >
              View format requirements
            </Button>
          </div>
        </Col>
        <Col span={8}></Col>
      </Row> 
      <div style={{ marginTop: '50px' }}></div>
      <div style={{ marginTop: '30px', textAlign: 'center' }}>
        <Button 
          type="primary"
          size="large"
          className='Homepage-button'
          onClick={handleStartLabelling}
        >
          Start Labelling
        </Button>
      </div>

    </div>
  )
}
