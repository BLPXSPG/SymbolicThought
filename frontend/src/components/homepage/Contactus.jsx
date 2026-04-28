import React, { useState} from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { Typography , message} from 'antd'
import logo from '../image/label-logo.png' 
import click from '../image/click.jpg' 
import upload from '../image/upload.jpg' 
import { Col, Row, Input, Button, Space, Upload, UploadProps } from 'antd';

const { Title } = Typography

export default function Contactus() {
  const [storyname, setStoryname] = useState('')
    const SubmitStoryName = () => {
      let datain = {
        input:storyname,
      }
      axios
        .post('/apilocal/input-narrative-name', datain)//api
        .then(function (response) {
          console.log(response)
          message.info('Received, thank you!')
        })
        .catch(function (error) {
          console.log(error)
        })
    }

    const handleChangeName = (e) => {
      const { value: inputValue } = e.target
      setStoryname(inputValue)
    }
    
  return (
    <div className="Homepage">
      <div>
        <img src={logo} alt="logo" className='App-logo '/>
      </div>
      <Title className="Homepage-title">Contact us</Title>
      <Input placeholder='Name' onChange={handleChangeName} style={{width:"200pt", margin:"2pt"}}></Input>
      <Input placeholder='Eamil' onChange={handleChangeName} style={{width:"200pt", margin:"2pt"}}></Input>
      <Input placeholder='Message' onChange={handleChangeName} style={{width:"200pt", margin:"2pt"}}></Input>
      <Button className='Homepage-button' onClick={SubmitStoryName} style={{margin:"10pt"}}>Submit</Button>

      <Row>
        <Col span={10}></Col>
        <Col span={4} className='normal-text no-wrap'>
           
        </Col>
        <Col span={10} className='normal-text'>
        </Col>
      </Row> 
    </div>
  )
}
