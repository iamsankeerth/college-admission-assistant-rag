import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, Search, GraduationCap, Compass } from 'lucide-react';
import './Navbar.css';

export default function Navbar({ activeView, onNavigate }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="navbar">
      <div className="navbar-inner container">
        <button className="navbar-brand" onClick={() => onNavigate('home')}>
          <div className="navbar-logo">
            <GraduationCap size={20} strokeWidth={1.8} />
          </div>
          <span className="navbar-name">
            College<span className="navbar-name-accent">Compass</span>
          </span>
        </button>

        <div className="navbar-links">
          <button
            className={`navbar-link ${activeView === 'shortlist' ? 'active' : ''}`}
            onClick={() => onNavigate('shortlist')}
          >
            <Search size={15} />
            Shortlist
          </button>
          <button
            className={`navbar-link ${activeView === 'explore' ? 'active' : ''}`}
            onClick={() => onNavigate('explore')}
          >
            <Compass size={15} />
            Explore
          </button>
        </div>

        <div className="navbar-actions">
          <span className="navbar-status badge badge-official">
            <span className="status-dot" />
            Evidence-First
          </span>
        </div>

        <button className="navbar-mobile-toggle" onClick={() => setMobileOpen(!mobileOpen)}>
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            className="navbar-mobile-menu"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
          >
            <button
              className={`navbar-mobile-link ${activeView === 'shortlist' ? 'active' : ''}`}
              onClick={() => { onNavigate('shortlist'); setMobileOpen(false); }}
            >
              <Search size={16} /> Shortlist Colleges
            </button>
            <button
              className={`navbar-mobile-link ${activeView === 'explore' ? 'active' : ''}`}
              onClick={() => { onNavigate('explore'); setMobileOpen(false); }}
            >
              <Compass size={16} /> Explore a College
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
