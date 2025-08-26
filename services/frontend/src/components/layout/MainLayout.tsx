import type { ReactNode } from 'react';
import React, { useState } from 'react';
import { Layout } from 'antd';
import Sidebar from './Sidebar';
import { Outlet } from 'react-router-dom';

const { Content } = Layout;

interface MainLayoutProps {
  children?: ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(true);
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar collapsed={collapsed} onCollapse={setCollapsed} />
      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'margin 0.2s' }}>
        <Content 
          style={{
            padding: '24px',
            minHeight: '100vh',
            background: '#fff',
            transition: 'margin 0.2s',
          }}
        >
          {children || <Outlet />}
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
