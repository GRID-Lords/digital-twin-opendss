import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import {
  Home,
  Cpu,
  Activity,
  BarChart3,
  Monitor,
  Menu,
  X
} from 'lucide-react';

const SidebarContainer = styled.aside`
  position: fixed;
  top: 0;
  left: 0;
  width: 250px;
  height: 100vh;
  background: #1e293b;
  border-right: 1px solid #334155;
  transform: ${props => props.isOpen ? 'translateX(0)' : 'translateX(-100%)'};
  transition: transform 0.3s ease;
  z-index: 1000;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);

  @media (max-width: 768px) {
    width: 100%;
    transform: ${props => props.isOpen ? 'translateX(0)' : 'translateX(-100%)'};
  }
`;

const SidebarHeader = styled.div`
  padding: 1.5rem;
  border-bottom: 1px solid #334155;
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const Logo = styled.div`
  color: #f1f5f9;
  font-size: 1.25rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const ToggleButton = styled.button`
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  transition: all 0.2s;

  &:hover {
    background: #334155;
    color: #f1f5f9;
  }

  @media (min-width: 769px) {
    display: none;
  }
`;

const Nav = styled.nav`
  padding: 1rem 0;
`;

const NavItem = styled(Link)`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  color: ${props => props.active ? '#f1f5f9' : '#94a3b8'};
  text-decoration: none;
  font-weight: ${props => props.active ? '600' : '400'};
  font-size: 0.875rem;
  background: ${props => props.active ? '#334155' : 'transparent'};
  border-left: ${props => props.active ? '3px solid #3b82f6' : '3px solid transparent'};
  transition: all 0.2s ease;

  &:hover {
    color: #f1f5f9;
    background: #334155;
  }
`;

const NavIcon = styled.div`
  font-size: 1.125rem;
  display: flex;
  align-items: center;
  color: #94a3b8;
`;

const NavText = styled.span`
  font-size: 0.875rem;
`;

const Sidebar = ({ isOpen, onToggle }) => {
  const location = useLocation();

  const navItems = [
    { path: '/', icon: Home, label: 'Dashboard' },
    { path: '/assets', icon: Cpu, label: 'Assets' },
    { path: '/scada', icon: Activity, label: 'SCADA' },
    { path: '/analytics', icon: BarChart3, label: 'Analytics' },
    { path: '/visualization', icon: Monitor, label: 'Visualization' },
  ];

  return (
    <SidebarContainer isOpen={isOpen}>
      <SidebarHeader>
        <Logo>
          Digital Twin
        </Logo>
        <ToggleButton onClick={onToggle}>
          {isOpen ? <X /> : <Menu />}
        </ToggleButton>
      </SidebarHeader>
      <Nav>
        {navItems.map((item) => (
          <NavItem
            key={item.path}
            to={item.path}
            active={location.pathname === item.path ? 1 : 0}
          >
            <NavIcon>
              <item.icon />
            </NavIcon>
            <NavText>{item.label}</NavText>
          </NavItem>
        ))}
      </Nav>
    </SidebarContainer>
  );
};

export default Sidebar;