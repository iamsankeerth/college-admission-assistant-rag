import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';

export default function AppLayout() {
  return (
    <div className="ivory-app-root">
      <div className="ivory-app-bg">
        <div className="ivory-vignette" />
        <div className="ivory-gold-line top" />
        <div className="ivory-pattern" />
      </div>
      <Navbar />
      <main className="ivory-main">
        <Outlet />
      </main>
      <footer className="ivory-footer">
        <div className="ivory-container">
          <div className="ivory-footer-line" />
          <p className="ivory-footer-brand">CollegeCompass</p>
          <p className="ivory-footer-note">
            Data sourced from official college websites. Cutoff ranks are indicative and may vary.
            Always verify with official counselling portals before making decisions.
          </p>
        </div>
      </footer>
    </div>
  );
}