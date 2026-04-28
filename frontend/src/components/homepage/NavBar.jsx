import React from 'react';
import { Layout, Menu } from 'antd';
import { Link } from 'react-router-dom'

const { Header } = Layout;

const NavBar = () => (
  <Layout className="layout">
    <Header style={{ justifyContent: 'space-between'}} className='navbar-background'>
      <Menu theme="dark" mode="horizontal" defaultSelectedKeys={['1']} className='navbar-background' style={{ display: 'block' }}>
        <Menu.Item key="1" className="bar-button">
            <Link to="/">
                Home
            </Link>
        </Menu.Item>
        <Menu.Item key="3" className="bar-button">
            <Link to="/about">
                About
            </Link>
        </Menu.Item>
        <Menu.Item key="4" className="bar-button">
            <Link to="/contact">
                Contact us
            </Link>
        </Menu.Item>
      </Menu>
    </Header>
  </Layout>
);

export default NavBar;
