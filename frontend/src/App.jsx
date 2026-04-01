import { useState, useCallback, useEffect } from 'react';
import Navbar from './components/Navbar';
import IvoryTowerLanding from './components/landing/IvoryTowerLanding';
import ShortlistForm from './components/ShortlistForm';
import ShortlistResults from './components/ShortlistResults';
import LoadingState from './components/LoadingState';
import ExplorePage from './components/ExplorePage';
import ComparePage from './components/ComparePage';
import { generateMockRecommendations } from './data';
import { loadShortlist, saveProfile, clearShortlist, encodeShortlistIds, decodeShortlistIds } from './storage';

export default function App() {
  const [view, setView] = useState('home');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [results, setResults] = useState(null);
  const [currentProfile, setCurrentProfile] = useState(null);
  const [exploreCollege, setExploreCollege] = useState(null);
  const [compareColleges, setCompareColleges] = useState(null);

  const [restoredShortlist, setRestoredShortlist] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sharedIds = params.get('s');
    if (sharedIds) {
      const ids = decodeShortlistIds(sharedIds);
      if (ids && Array.isArray(ids)) {
        window.__cc_shared_ids = ids;
      }
    }

    const saved = loadShortlist();
    if (saved) {
      setRestoredShortlist(saved);
    }
  }, []);

  useEffect(() => {
    if (view === 'shortlist-results' && !isLoading && restoredShortlist && !results) {
      setCurrentProfile(restoredShortlist.profile);
      setResults(restoredShortlist.results);
      setRestoredShortlist(null);
    }
  }, [view, isLoading, restoredShortlist, results]);

  const handleNavigate = useCallback((target) => {
    setView(target);
    if (target === 'shortlist') {
      setResults(null);
    }
    if (target === 'explore') {
      setExploreCollege(null);
    }
    if (target === 'compare') {
    } else {
      setCompareColleges(null);
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const handleShortlistSubmit = useCallback(async (profile) => {
    setCurrentProfile(profile);
    saveProfile(profile);
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
      if (window.__cc_shared_ids) {
        const sharedIds = window.__cc_shared_ids;
        delete window.__cc_shared_ids;
        const filtered = data.recommendations.filter(c => sharedIds.includes(c.college_id));
        setResults({ ...data, recommendations: filtered });
      }
    } catch (err) {
      await new Promise(r => setTimeout(r, 2000));
      const mockData = generateMockRecommendations(profile);
      setResults(mockData);
      if (window.__cc_shared_ids) {
        const sharedIds = window.__cc_shared_ids;
        delete window.__cc_shared_ids;
        const filtered = mockData.recommendations.filter(c => sharedIds.includes(c.college_id));
        setResults({ ...mockData, recommendations: filtered });
      }
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

  const handleCompare = useCallback((colleges) => {
    setCompareColleges(colleges);
    setView('compare');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  if (view === 'home') {
    return <IvoryTowerLanding onNavigate={handleNavigate} restoredShortlist={restoredShortlist} />;
  }

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
            initialValues={restoredShortlist?.profile}
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
            onCompare={handleCompare}
          />
        )}

        {view === 'explore' && (
          <ExplorePage
            initialCollege={exploreCollege}
            onBack={() => handleNavigate(results ? 'shortlist-results' : 'home')}
          />
        )}

        {view === 'compare' && (
          <ComparePage
            colleges={compareColleges}
            profile={currentProfile}
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
