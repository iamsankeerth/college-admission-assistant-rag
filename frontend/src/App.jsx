import { useState, useCallback, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import AppLayout from './components/AppLayout';
import AdminLayout from './components/admin/AdminLayout';
import IvoryTowerLanding from './components/landing/IvoryTowerLanding';
import ShortlistForm from './components/ShortlistForm';
import ShortlistResults from './components/ShortlistResults';
import LoadingState from './components/LoadingState';
import ExplorePage from './components/ExplorePage';
import ComparePage from './components/ComparePage';
import CollegeListPage from './components/admin/CollegeListPage';
import CollegeEditPage from './components/admin/CollegeEditPage';
import CorpusStatusPage from './components/admin/CorpusStatusPage';
import { generateMockRecommendations } from './data';
import { loadShortlist, saveProfile, encodeShortlistIds, decodeShortlistIds } from './storage';

function AppRoutes() {
  const navigate = useNavigate();
  const location = useLocation();
  const [view, setView] = useState('home');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [results, setResults] = useState(null);
  const [currentProfile, setCurrentProfile] = useState(null);
  const [exploreCollege, setExploreCollege] = useState(null);
  const [compareColleges, setCompareColleges] = useState(null);
  const [restoredShortlist, setRestoredShortlist] = useState(null);
  const [sharedIds, setSharedIds] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const encoded = params.get('s');
    if (encoded) {
      const ids = decodeShortlistIds(encoded);
      if (ids && Array.isArray(ids)) setSharedIds(ids);
    }
    const saved = loadShortlist();
    if (saved) setRestoredShortlist(saved);
  }, []);

  useEffect(() => {
    if (location.pathname === '/results' && !isLoading && restoredShortlist && !results) {
      setCurrentProfile(restoredShortlist.profile);
      setResults(restoredShortlist.results);
      setRestoredShortlist(null);
    }
  }, [location.pathname, isLoading, restoredShortlist, results]);

  const handleNavigate = useCallback((target) => {
    if (target === 'shortlist') {
      setView('shortlist');
      navigate('/shortlist');
    } else if (target === 'explore') {
      setView('explore');
      navigate('/explore');
    } else if (target === 'compare') {
      setView('compare');
      navigate('/compare');
    } else if (target === 'shortlist-results') {
      setView('shortlist-results');
      navigate('/results');
    } else {
      setView('home');
      navigate('/');
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [navigate]);

  const handleShortlistSubmit = useCallback(async (profile) => {
    setCurrentProfile(profile);
    saveProfile(profile);
    setIsLoading(true);
    setLoadingProgress(0);
    setView('shortlist-results');
    navigate('/results');

    const progressInterval = setInterval(() => {
      setLoadingProgress(prev => {
        if (prev >= 90) { clearInterval(progressInterval); return 90; }
        return prev + Math.random() * 15;
      });
    }, 400);

    try {
      const { getRecommendations } = await import('./api');
      const data = await getRecommendations(profile);
      if (sharedIds) {
        setResults({
          ...data,
          recommendations: data.recommendations.filter(c => sharedIds.includes(c.college_id)),
        });
        setSharedIds(null);
      } else {
        setResults(data);
      }
    } catch (err) {
      await new Promise(r => setTimeout(r, 2000));
      const mockData = generateMockRecommendations(profile);
      if (sharedIds) {
        setResults({
          ...mockData,
          recommendations: mockData.recommendations.filter(c => sharedIds.includes(c.college_id)),
        });
        setSharedIds(null);
      } else {
        setResults(mockData);
      }
    } finally {
      clearInterval(progressInterval);
      setLoadingProgress(100);
      setTimeout(() => setIsLoading(false), 500);
    }
  }, [navigate, sharedIds]);

  const handleExploreFromCard = useCallback((collegeName) => {
    setExploreCollege(collegeName);
    setView('explore');
    navigate(`/explore/${encodeURIComponent(collegeName)}`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [navigate]);

  const handleCompare = useCallback((colleges) => {
    setCompareColleges(colleges);
    setView('compare');
    navigate('/compare');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [navigate]);

  const getBackUrl = () => results ? '/results' : '/';

  return (
    <Routes>
      <Route element={<AppLayout location={location} />}>
        <Route path="/" element={
          <IvoryTowerLanding onNavigate={handleNavigate} restoredShortlist={restoredShortlist} hideNav={true} />
        } />
        <Route path="/shortlist" element={
          <ShortlistForm onSubmit={handleShortlistSubmit} isLoading={isLoading} initialValues={restoredShortlist?.profile} />
        } />
        <Route path="/results" element={
          <>
            {isLoading && <LoadingState progress={loadingProgress} />}
            {!isLoading && results && (
              <ShortlistResults data={results} profile={currentProfile} onBack={() => handleNavigate('shortlist')} onExplore={handleExploreFromCard} onCompare={handleCompare} />
            )}
          </>
        } />
        <Route path="/explore/:name?" element={
          <ExplorePage initialCollege={exploreCollege} onBack={() => navigate(getBackUrl())} />
        } />
        <Route path="/compare" element={
          <ComparePage colleges={compareColleges} profile={currentProfile} onBack={() => navigate(getBackUrl())} />
        } />
      </Route>
      <Route element={<AdminLayout />}>
        <Route path="/admin/colleges" element={<CollegeListPage />} />
        <Route path="/admin/colleges/:id" element={<CollegeEditPage />} />
        <Route path="/admin/corpus" element={<CorpusStatusPage />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
