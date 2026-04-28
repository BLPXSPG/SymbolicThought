import './App.css'
import Homepage from './components/homepage/Homepage'
import UploadStory from './components/homepage/UploadStory'
import InputCode from './components/label/InputCode'
import InitStory from './components/label/InitStory'
import LabelEntity from './components/label/LabelEntity'
import LabelRelation from './components/label/LabelRelation'
import About from './components/homepage/About'
import Contactus from './components/homepage/Contactus'
import NavBar from './components/homepage/NavBar'
import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import {
  HomeOutlined,
  BookOutlined,
} from '@ant-design/icons'
import { Layout, theme, Button, Row, Col, AutoComplete, Input } from 'antd'

const { Header, Content } = Layout

function App () {
  const [collapsed, setCollapsed] = useState(false)
  const {
    token: { colorBgContainer },
  } = theme.useToken()
  const shoelogo = (collapsed) => {
    if (collapsed) {
      return (
        <div></div>
      )
    }
  }
  //<Header style={{ display: 'flex', alignItems: 'center' }}>
  //          </Header>
  return (
    <Router>
      <Layout>
        <NavBar></NavBar>
        <Content
          style={{
            margin: '0px 0px',
            padding: 0,
            minHeight: 650,
            background: colorBgContainer,
            overflow: 'auto',
          }}>
          <div>
            <Routes>
              <Route exact path="/" element={<Homepage />} />
              <Route exact path="/upload-story" element={<UploadStory />} />
              <Route exact path="/about" element={<About />} />
              <Route exact path="/contact" element={<Contactus />} />
              <Route exact path="/set-flow" element={<InputCode />} />
              <Route exact path="/init" element={<InitStory />} />
              <Route exact path="/labelentity" element={<LabelEntity />} />
              <Route exact path="/labelrelation" element={<LabelRelation />} />
            </Routes>
          </div>
        </Content>
      </Layout>
    </Router>

  )
}

export default App
