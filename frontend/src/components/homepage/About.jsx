import React from 'react'
import { Link } from 'react-router-dom'
import { Typography } from 'antd'
import logo from '../image/label-logo.png' 
import limitation from '../image/limitation.png' 
import target from '../image/target.jpg' 
import { Col, Row, Input, Button, Space, Upload, UploadProps } from 'antd';

const { Title } = Typography

export default function About() {
  return (
    <div className="Homepage">
        <div>
            <img src={logo} alt="logo" className='App-logo' style={{height: '18vmin'}}/>
        </div>
        <Title className="Homepage-title" style={{fontSize:'30px'}}>How to use SymbolicThought?</Title>
        <Row>
            <Col span={4}></Col>
            <Col span={16} className='normal-text white-background-box'>
                <Title className="Homepage-title" style={{fontSize:'25px'}}> <img src={target} alt="logo" className='App-icon1'/> Upload</Title>
                <p className='normal-text'>
                   
                    <br />
                </p>
            </Col>
            <Col span={4}></Col>
        </Row>    
        
        <Row>
            <Col span={4}></Col>
            <Col span={16} className='normal-text white-background-box'>
                <Title className="Homepage-title" style={{fontSize:'25px'}}> <img src={limitation} alt="logo" className='App-icon1'/> Customise</Title>
                <p className='normal-text'>
                    we have pre-set modules: 
                    <ul>
                        <li>
                            123
                        </li>
                        <li>
                            123
                        </li>
                    </ul>
                </p>
            </Col>
            <Col span={4}></Col>
        </Row>   
    </div>
  )
}
