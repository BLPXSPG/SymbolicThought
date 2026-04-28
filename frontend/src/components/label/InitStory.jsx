import React, { useState, useEffect }from 'react'
import { Link,useLocation,useParams } from 'react-router-dom'
import { Spin, Button, Row  } from 'antd';
import axios from 'axios'

export default function InitStory() {

  const [initstate, setInitstate] = useState(0)
  const [charactername, setCharactername] = useState('')
  const [background, setBackground] = useState('')
  const [backgroundindex, setBackgroundindex] = useState([])
  // all characters in the given background story
  const [agents, setAgents] = useState([])
  const [relations, setRelations] = useState([])
  const [relationcategory, setRelationcategory] = useState([])
 
  useEffect(() => {
    var datain = {
      story: charactername,
    }
    axios
      .post('/apilocal/background', datain)
      .then(function (response) {
        setCharactername(response.data.filename)
        setBackground(response.data.background)
        setBackgroundindex(response.data.background_index)
        setAgents(response.data.agents)
        setRelations(response.data.relations)
        setRelationcategory(response.data.relationcategory)
        setInitstate(1)

      })
      .catch(function (error) {
        console.log(error)
        setBackground(error)
      })
  }, [])
  
  if (initstate == 0){
  return (
    <div className='Cacf'>
      <Row>
      <Spin tip="Loading" size="large">
      </Spin> 
      </Row>
      <Row className='spincontent'>
      Loading...
      </Row>         
    </div>
  )
}else if (initstate==1){
  return(
    <div className='Cacf'>
      <Link to={"/story/" + `${charactername}` } state={{ charactername:charactername,background:background,backgroundindex:backgroundindex,relations:relations,relationcategory:relationcategory}}>
        <Button  shape="round" size={'large'} className='initebutton'> 
          Let's Go!
        </Button>
      </Link> 
    </div>
  )
}
}
