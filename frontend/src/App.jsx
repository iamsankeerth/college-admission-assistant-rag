import { useState, useCallback } from 'react';
import Navbar from './components/Navbar';
import IvoryTowerLanding from './components/landing/IvoryTowerLanding';
import ShortlistForm from './components/ShortlistForm';
import ShortlistResults from './components/ShortlistResults';
import LoadingState from './components/LoadingState';
import ExplorePage from './components/ExplorePage';
import { generateMockRecommendations } from './data';

export default function App() {
  const [view, setView] = useState('home'); // home | shortlist | shortlist-results | explore
  const [isLoading, setIsLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [results, setResults] = useState(null);
  const [currentProfile, setCurrentProfile] = useState(null);
  const [exploreCollege, setExploreCollege] = useState(null);

  const handleNavigate = useCallback((target) => {
    setView(target);
    if (target === 'shortlist') {
      setResults(null);
    }
    if (target === 'explore') {
      setExploreCollege(null);
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const handleShortlistSubmit = useCallback(async (profile) => {
    setCurrentProfile(profile);
    setIsLoading(true);
    setLoadingProgress(0);
    setView('shortlist-results');

    const progressInterval = setInterval(() => {
      setLoadingProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + Math.random() * 15;
      });
    }, 400);

    try {
      const { getRecommendations } = await import('./api');
      const data = await getRecommendations(profile);
      setResults(data);
    } catch (err) {
      await new Promise(r => setTimeout(r, 2000));
      const mockData = generateMockRecommendations(profile);
      setResults(mockData);
    } finally {
      clearInterval(progressInterval);
      setLoadingProgress(100);
      setTimeout(() => setIsLoading(false), 500);
    }
  }, []);

  const handleExploreFromCard = useCallback((collegeName) => {
    setExploreCollege(collegeName);
    setView('explore');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  // Home view — IvoryTower landing only
  if (view === 'home') {
    return <IvoryTowerLanding onNavigate={handleNavigate} />;
  }

  // All other views — warm cream IvoryTower background
  return (
    <div className="ivory-app-root">
      <div className="ivory-app-bg">
        <div className="ivory-vignette" />
        <div className="ivory-gold-line top" />
        <div className="ivory-pattern" />
      </div>

      <Navbar
        activeView={view === 'shortlist-results' ? 'shortlist' : view}
        onNavigate={handleNavigate}
      />

      <main className="ivory-main">
        {view === 'shortlist' && (
          <ShortlistForm
            onSubmit={handleShortlistSubmit}
            isLoading={isLoading}
          />
        )}

        {view === 'shortlist-results' && isLoading && (
          <LoadingState progress={loadingProgress} />
        )}

        {view === 'shortlist-results' && !isLoading && results && (
          <ShortlistResults
            data={results}
            profile={currentProfile}
            onBack={() => handleNavigate('shortlist')}
            onExplore={handleExploreFromCard}
          />
        )}

        {view === 'explore' && (
          <ExplorePage
            initialCollege={exploreCollege}
            onBack={() => handleNavigate(results ? 'shortlist-results' : 'home')}
          />
        )}
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
