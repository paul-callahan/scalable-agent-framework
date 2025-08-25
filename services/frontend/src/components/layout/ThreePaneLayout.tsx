import React from 'react';
import type { ReactNode } from 'react';
import './ThreePaneLayout.css';

interface ThreePaneLayoutProps {
  leftPane: ReactNode;
  centerTopPane: ReactNode;
  centerBottomPane: ReactNode;
  header?: ReactNode;
}

const ThreePaneLayout: React.FC<ThreePaneLayoutProps> = ({
  leftPane,
  centerTopPane,
  centerBottomPane,
  header,
}) => {
  return (
    <div className="three-pane-layout">
      {header && <div className="layout-header">{header}</div>}
      <div className="layout-content">
        <div className="left-pane">{leftPane}</div>
        <div className="right-panes">
          <div className="center-top-pane">{centerTopPane}</div>
          <div className="center-bottom-pane">{centerBottomPane}</div>
        </div>
      </div>
    </div>
  );
};

export default ThreePaneLayout;