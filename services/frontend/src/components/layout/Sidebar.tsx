import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import { ProjectOutlined, EditOutlined } from '@ant-design/icons';

interface SidebarProps {
  onCollapse?: (collapsed: boolean) => void;
  collapsed?: boolean;
}

const { Sider } = Layout;

const Sidebar: React.FC<SidebarProps> = ({ onCollapse, collapsed: propCollapsed }) => {
  const [internalCollapsed, setInternalCollapsed] = useState(true);
  const isControlled = propCollapsed !== undefined;
  const collapsed = isControlled ? propCollapsed : internalCollapsed;
  const location = useLocation();

  return (
    <Sider 
      collapsible 
      collapsed={collapsed} 
      onCollapse={() => {
        if (onCollapse) {
          onCollapse(!collapsed);
        } else {
          setInternalCollapsed(!internalCollapsed);
        }
      }}
      width={200}
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
      }}
    >
      <div className="logo" style={{ 
        height: '32px',
        margin: '16px',
        background: 'rgba(255, 255, 255, 0.2)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
        fontSize: collapsed ? '16px' : '18px',
        fontWeight: 'bold'
      }}>
        {collapsed ? 'AF' : 'AgentFlow'}
      </div>
      <Menu
        theme="dark"
        mode="inline"
        defaultSelectedKeys={['/graphs']}
        selectedKeys={[location.pathname]}
        items={[
          {
            key: '/graphs',
            icon: <ProjectOutlined />,
            label: <Link to="/graphs">Graph Management</Link>,
          },
          {
            key: '/editor',
            icon: <EditOutlined />,
            label: <Link to="/editor">Graph Editor</Link>,
          },
        ]}
      />
    </Sider>
  );
};

export default Sidebar;
