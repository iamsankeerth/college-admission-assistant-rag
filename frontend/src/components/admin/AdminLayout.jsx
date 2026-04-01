import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Building2, Database, ChevronLeft, GraduationCap } from 'lucide-react';
import './AdminLayout.css';

export default function AdminLayout() {
  const navigate = useNavigate();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="admin-layout">
      <aside className={`admin-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="admin-sidebar-header">
          <button className="admin-brand" onClick={() => navigate('/')}>
            <GraduationCap size={20} strokeWidth={1.8} />
            {!sidebarCollapsed && <span>CollegeCompass</span>}
          </button>
          <button className="admin-sidebar-toggle" onClick={() => setSidebarCollapsed(!sidebarCollapsed)}>
            <ChevronLeft size={16} />
          </button>
        </div>
        
        <nav className="admin-nav">
          <NavLink to="/admin/colleges" className={({ isActive }) => `admin-nav-item ${isActive ? 'active' : ''}`}>
            <Building2 size={18} />
            {!sidebarCollapsed && <span>Colleges</span>}
          </NavLink>
          <NavLink to="/admin/corpus" className={({ isActive }) => `admin-nav-item ${isActive ? 'active' : ''}`}>
            <Database size={18} />
            {!sidebarCollapsed && <span>Corpus</span>}
          </NavLink>
        </nav>

        <div className="admin-sidebar-footer">
          <button className="admin-nav-item" onClick={() => navigate('/')}>
            <ChevronLeft size={18} />
            {!sidebarCollapsed && <span>? Back to App</span>}
          </button>
        </div>
      </aside>

      <main className="admin-main">
        <Outlet />
      </main>
    </div>
  );
}