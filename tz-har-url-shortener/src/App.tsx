import { useState, useEffect } from 'react';
import { 
  Link2, 
  LogOut, 
  BarChart3, 
  Tag, 
  Star, 
  Trash2, 
  Copy, 
  ExternalLink, 
  Plus, 
  X,  
  RefreshCw, 
  Check, 
  AlertTriangle, 
  QrCode, 
  Download, 
  Search, 
  SlidersHorizontal 
} from 'lucide-react';
import { api } from './services/TzHarApi';
import { Constants } from './util/Constants';
import type { User } from './types/user';
import type { UrlTag, URLResponse, UrlStats } from './types/URL';
import type { Dashboard } from './types/dashboard';
import { generateQrOnCanvas } from './util/qr';
import type { QrCodeModal } from './types/QrCodeModal';
import { useUser } from './context/AuthContext';


const App = () => {

  const { user, setUser, session, setSession, logout} = useUser()
  const [view, setView] = useState<string>('login');
  const [loading, setLoading] = useState(false);
  
  // Auth states
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  // URL states
  const [urls, setUrls] = useState<URLResponse[]>([]);
  const [newUrl, setNewUrl] = useState('');
  const [newUrlTitle, setNewUrlTitle] = useState('');
  const [newUrlDescription, setNewUrlDescription] = useState('');
  const [newUrlFavorite, setNewUrlFavorite] = useState(false);
  const [showUrlModal, setShowUrlModal] = useState(false);
  
  // Tag states
  const [tags, setTags] = useState<UrlTag[]>([]);
  const [showTagModal, setShowTagModal] = useState(false);
  const [newTagName, setNewTagName] = useState('');
  const [newTagDescription, setNewTagDescription] = useState('');
  const [newTagColor, setNewTagColor] = useState('#3B82F6');
  

  // Dashboard states
  const [dashboardData, setDashboardData] = useState<Dashboard | null>(null);
  
  // Tag assignment
  const [selectedUrlForTag, setSelectedUrlForTag] = useState<number | null>(null);
  
  // Stats modal
  const [selectedUrlForStats, setSelectedUrlForStats] = useState<URLResponse | null>(null);
  const [urlStats, setUrlStats] = useState<UrlStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(false);
  
  // Notifications
  const [notification, setNotification] = useState<{type: string, message: string, icon: string} | null>(null);
  
  // Redirect warning
  const [redirectWarning, setRedirectWarning] = useState<{url: string, title: string | null, short_url: string} | null>(null);
  
  // QR Code modal
  const [qrCodeModal, setQrCodeModal] = useState<QrCodeModal | null>(null);
  
  // Search and filters
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filterFavorites, setFilterFavorites] = useState(false);
  const [filterTags, setFilterTags] = useState<number[]>([]);
  const [sortBy, setSortBy] = useState('date-desc'); // date-desc, date-asc, clicks-desc, clicks-asc, alpha-asc, alpha-desc

  useEffect(() => {
    if (user) { loadData(); }
  }, [user, view]);

  // Generate QR Code when modal opens

  const fillQrCodeCanvas = async (url: string) => {
    const canvas = document.getElementById('qr-canvas');
    if (canvas) {
      await generateQrOnCanvas(canvas as any, url)
    }
  }

  useEffect(() => {
    if (qrCodeModal) {
      fillQrCodeCanvas(qrCodeModal.url)
    }
  }, [qrCodeModal]);

  const loadData = async () => {
    try {
      if (view === 'urls') {
        const data = await api.url.getUserUrls();
        setUrls(data.results);
      } else if (view === 'tags') {
        const data = await api.tag.getUserTags();
        setTags(data.results);
      } else if (view === 'dashboard') {
        const data = await api.dashboard.getDashboard();
        setDashboardData(data);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const handleLogin = async () => {
    setLoading(true);
    try {
      const userData = await api.auth.login(email, password);
      const tags = await api.tag.getUserTags()
      setTags(tags.results)
      setUser(userData);
      setView('urls');
    } catch (error: any) {
      alert('Login failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async () => {
    setLoading(true);
    try {
      await api.auth.signup(email, password);
      const userData = await api.auth.login(email, password);
      setUser(userData);
      setView('urls');
    } catch (error: any) {
      alert('Signup failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await api.auth.logout();
      setUser(null);
      setView('login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const handleShortenUrl = async () => {
    if (!newUrl) return;
    
    setLoading(true);
    try {
      await api.url.shortenUrl({ 
        url: newUrl,
        title: newUrlTitle || undefined,
        descr: newUrlDescription || undefined,
        is_favorite: newUrlFavorite
      });
      setNewUrl('');
      setNewUrlTitle('');
      setNewUrlDescription('');
      setNewUrlFavorite(false);
      setShowUrlModal(false);
      loadData();
    } catch (error: any) {
      alert('Error shortening URL: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUrl = async (id: number) => {
    if (!confirm('Delete this URL?')) return;
    try {
      await api.url.deleteUserUrl(id);
      loadData();
    } catch (error: any) {
      alert('Error deleting URL: ' + error.message);
    }
  };

  const handleToggleFavorite = async (urlId: number, isFavorite: boolean) => {
    try {
      await api.url.setFavoriteUrl(urlId, !isFavorite);
      loadData();
    } catch (error: any) {
      alert('Error updating favorite: ' + error.message);
    }
  };

  const handleCreateTag = async () => {
    if (!newTagName) return;
    
    try {
      await api.tag.createTag({ 
        name: newTagName, 
        color: newTagColor,
        descr: newTagDescription || undefined
      });
      setNewTagName('');
      setNewTagDescription('');
      setNewTagColor('#3B82F6');
      setShowTagModal(false);
      loadData();
    } catch (error: any) {
      alert('Error creating tag: ' + error.message);
    }
  };

  const handleDeleteTag = async (id: number) => {
    if (!confirm('Delete this tag?')) return;
    try {
      await api.tag.deleteTag(id);
      loadData();
    } catch (error: any) {
      alert('Error deleting tag: ' + error.message);
    }
  };

  const handleAddTagToUrl = async (urlId: number, tagId: number) => {
    try {
      await api.tag.createUrlTagRelation(urlId, tagId);
      loadData();
      setSelectedUrlForTag(null);
    } catch (error: any) {
      alert('Error adding tag: ' + error.message);
    }
  };

  const handleRemoveTagFromUrl = async (urlId: number, tagId: number) => {
    try {
      await api.tag.deleteUrlTagRelation(urlId, tagId);
      loadData();
    } catch (error: any) {
      alert('Error removing tag: ' + error.message);
    }
  };

  const handleViewStats = async (url: any) => {
    setSelectedUrlForStats(url);
    setLoadingStats(true);
    try {
      const stats = await api.url.getUrlStats(url.short_code);
      console.log(stats)
      setUrlStats(stats);
    } catch (error: any) {
      setUrlStats(null);
    } finally {
      setLoadingStats(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setNotification({
      type: 'success',
      message: 'Link copied to clipboard!',
      icon: 'copy'
    });
    setTimeout(() => setNotification(null), 3000);
  };

  const handleUrlClick = (e: any, url: URLResponse) => {
    e.preventDefault();
    setRedirectWarning({
      url: url.original_url,
      short_url: url.short_url,
      title: url.title
    });
  };

  const confirmRedirect = () => {
    if (redirectWarning) {
      window.open(redirectWarning.short_url, '_blank', 'noopener,noreferrer');
      setRedirectWarning(null);
    }
  };

  const generateQRCode = (url: URLResponse) => {
    const shortUrl = `http://short.url/${url.short_code}`;
    setQrCodeModal({
      url: shortUrl,
      originalUrl: url.original_url,
      title: url.title ?? '',
      shortCode: url.short_code
    });
  };

  const downloadQRCode = () => {
    if (!qrCodeModal) return;
    
    const canvas: any = document.getElementById('qr-canvas');
    if (canvas) {
      const link = document.createElement('a');
      link.download = `qrcode-${qrCodeModal.shortCode}.png`;
      link.href = canvas.toDataURL();
      link.click();
      
      setNotification({
        type: 'success',
        message: 'QR Code downloaded successfully!',
        icon: 'download'
      });
      setTimeout(() => setNotification(null), 3000);
    }
  };

  const toggleFilterTag = (tagId: number) => {
    setFilterTags(prev => 
      prev.includes(tagId) 
        ? prev.filter(id => id !== tagId)
        : [...prev, tagId]
    );
  };

  const clearFilters = () => {
    setSearchQuery('');
    setFilterFavorites(false);
    setFilterTags([]);
    setSortBy('date-desc');
  };

  const getFilteredAndSortedUrls = () => {
    let filtered = [...urls];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(url => 
        (url.title && url.title.toLowerCase().includes(query)) ||
        url.original_url.toLowerCase().includes(query) ||
        url.short_code.toLowerCase().includes(query) ||
        (url.descr && url.descr.toLowerCase().includes(query))
      );
    }

    // Favorites filter
    if (filterFavorites) {
      filtered = filtered.filter(url => url.is_favorite);
    }

    // Tags filter
    if (filterTags.length > 0) {
      filtered = filtered.filter(url => 
        url.tags && url.tags.some(tag => filterTags.includes(tag.id))
      );
    }

    // Sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'date-desc':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'date-asc':
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        case 'clicks-desc':
          return (b.clicks ?? 0) - (a.clicks ?? 0);
        case 'clicks-asc':
          return (a.clicks ?? 0) - (b.clicks ?? 0);
        case 'alpha-asc':
          return (a.title || a.original_url).localeCompare(b.title || b.original_url);
        case 'alpha-desc':
          return (b.title || b.original_url).localeCompare(a.title || a.original_url);
        default:
          return 0;
      }
    });

    return filtered;
  };

  const filteredUrls = getFilteredAndSortedUrls();
  const hasActiveFilters = searchQuery || filterFavorites || filterTags.length > 0 || sortBy !== 'date-desc';

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-md p-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-600 rounded-2xl mb-4">
              <Link2 className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-slate-900">TzHar URL</h1>
            <p className="text-slate-600 mt-2">Shorten and manage your links</p>
          </div>

          <div className="flex gap-2 mb-6">
            <button
              onClick={() => setView('login')}
              className={`flex-1 py-2.5 rounded-lg font-medium transition-all duration-200 ${
                view === 'login'
                  ? 'bg-indigo-600 text-white shadow-md hover:shadow-lg hover:bg-indigo-700 active:scale-95'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:shadow-sm active:scale-98'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setView('signup')}
              className={`flex-1 py-2.5 rounded-lg font-medium transition-all duration-200 ${
                view === 'signup'
                  ? 'bg-indigo-600 text-white shadow-md hover:shadow-lg hover:bg-indigo-700 active:scale-95'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:shadow-sm active:scale-98'
              }`}
            >
              Sign Up
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (view === 'login' ? handleLogin() : handleSignup())}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (view === 'login' ? handleLogin() : handleSignup())}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                placeholder="••••••••"
              />
            </div>
            <button
              onClick={view === 'login' ? handleLogin : handleSignup}
              disabled={loading}
              className="w-full bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-700 hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-md active:scale-98"
            >
              {loading ? 'Loading...' : view === 'login' ? 'Login' : 'Create Account'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center">
                <Link2 className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-xl font-bold text-slate-900">TzHar URL</h1>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-slate-600 hidden sm:inline">{user.email}</span>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 text-slate-700 hover:bg-slate-100 rounded-lg transition-all duration-200 hover:shadow-sm active:scale-95"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row gap-6">
          {/* Sidebar */}
          <aside className="w-full md:w-64 flex-shrink-0">
            <nav className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 space-y-2">
              <button
                onClick={() => setView('urls')}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                  view === 'urls'
                    ? 'bg-indigo-50 text-indigo-600 font-medium shadow-sm'
                    : 'text-slate-700 hover:bg-slate-50 hover:shadow-sm active:scale-98'
                }`}
              >
                <Link2 className="w-5 h-5" />
                My URLs
              </button>
              <button
                onClick={() => setView('tags')}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                  view === 'tags'
                    ? 'bg-indigo-50 text-indigo-600 font-medium shadow-sm'
                    : 'text-slate-700 hover:bg-slate-50 hover:shadow-sm active:scale-98'
                }`}
              >
                <Tag className="w-5 h-5" />
                Tags
              </button>
              <button
                onClick={() => setView('dashboard')}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                  view === 'dashboard'
                    ? 'bg-indigo-50 text-indigo-600 font-medium shadow-sm'
                    : 'text-slate-700 hover:bg-slate-50 hover:shadow-sm active:scale-98'
                }`}
              >
                <BarChart3 className="w-5 h-5" />
                Dashboard
              </button>
            </nav>
          </aside>

          {/* Main Content */}
          <main className="flex-1">
            {view === 'dashboard' && dashboardData && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-slate-900">Dashboard</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center">
                        <Link2 className="w-6 h-6 text-indigo-600" />
                      </div>
                      <div>
                        <p className="text-sm text-slate-600">Total URLs</p>
                        <p className="text-2xl font-bold text-slate-900">{dashboardData.total_urls}</p>
                      </div>
                    </div>
                  </div>
                  
                </div>
              </div>
            )}

            {view === 'urls' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold text-slate-900">My URLs</h2>
                  <button
                    onClick={() => setShowUrlModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 hover:shadow-lg transition-all duration-200 shadow-md active:scale-95"
                  >
                    <Plus className="w-5 h-5" />
                    New URL
                  </button>
                </div>

                {/* Search and Filters */}
                <div className="space-y-4">
                  {/* Search Bar */}
                  <div className="flex gap-3">
                    <div className="flex-1 relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                        placeholder="Search by title, URL, or short code..."
                      />
                    </div>
                    <button
                      onClick={() => setShowFilters(!showFilters)}
                      className={`flex items-center gap-2 px-4 py-3 rounded-lg font-medium transition-all duration-200 ${
                        showFilters || hasActiveFilters
                          ? 'bg-indigo-600 text-white shadow-md hover:bg-indigo-700'
                          : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      <SlidersHorizontal className="w-5 h-5" />
                      Filters
                      {hasActiveFilters && !showFilters && (
                        <span className="w-2 h-2 bg-white rounded-full" />
                      )}
                    </button>
                  </div>

                  {/* Filters Panel */}
                  {showFilters && (
                    <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-5 animate-in slide-in-from-top duration-300">
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-slate-900">Filters & Sorting</h3>
                        {hasActiveFilters && (
                          <button
                            onClick={clearFilters}
                            className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
                          >
                            Clear All
                          </button>
                        )}
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Sort By */}
                        <div>
                          <label className="block text-sm font-medium text-slate-700 mb-3">
                            Sort By
                          </label>
                          <div className="space-y-2">
                            {[
                              { value: 'date-desc', label: 'Newest First' },
                              { value: 'date-asc', label: 'Oldest First' },
                              { value: 'clicks-desc', label: 'Most Clicks' },
                              { value: 'clicks-asc', label: 'Least Clicks' },
                              { value: 'alpha-asc', label: 'A to Z' },
                              { value: 'alpha-desc', label: 'Z to A' }
                            ].map(option => (
                              <button
                                key={option.value}
                                onClick={() => setSortBy(option.value)}
                                className={`w-full text-left px-3 py-2 rounded-lg transition-all duration-200 ${
                                  sortBy === option.value
                                    ? 'bg-indigo-50 text-indigo-600 font-medium'
                                    : 'text-slate-700 hover:bg-slate-50'
                                }`}
                              >
                                {option.label}
                              </button>
                            ))}
                          </div>
                        </div>

                        {/* Filter Options */}
                        <div className="space-y-4">
                          {/* Favorites */}
                          <div>
                            <label className="block text-sm font-medium text-slate-700 mb-3">
                              Quick Filters
                            </label>
                            <button
                              onClick={() => setFilterFavorites(!filterFavorites)}
                              className={`w-full flex items-center justify-between px-4 py-3 rounded-lg border transition-all duration-200 ${
                                filterFavorites
                                  ? 'bg-amber-50 border-amber-200 text-amber-700'
                                  : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                              }`}
                            >
                              <div className="flex items-center gap-2">
                                <Star className={`w-4 h-4 ${filterFavorites ? 'fill-current' : ''}`} />
                                <span className="font-medium">Favorites Only</span>
                              </div>
                              {filterFavorites && (
                                <Check className="w-4 h-4" />
                              )}
                            </button>
                          </div>

                          {/* Tags Filter */}
                          {tags.length > 0 && (
                            <div>
                              <label className="block text-sm font-medium text-slate-700 mb-3">
                                Filter by Tags
                              </label>
                              <div className="space-y-2 max-h-48 overflow-y-auto">
                                {tags.map(tag => (
                                  <button
                                    key={tag.id}
                                    onClick={() => toggleFilterTag(tag.id)}
                                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition-all duration-200 ${
                                      filterTags.includes(tag.id)
                                        ? 'bg-slate-100 border border-slate-300'
                                        : 'hover:bg-slate-50'
                                    }`}
                                  >
                                    <div className="flex items-center gap-2">
                                      <div
                                        className="w-4 h-4 rounded"
                                        style={{ backgroundColor: tag.color }}
                                      />
                                      <span className="text-sm text-slate-700">{tag.name}</span>
                                    </div>
                                    {filterTags.includes(tag.id) && (
                                      <Check className="w-4 h-4 text-indigo-600" />
                                    )}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Results Count */}
                  <div className="flex items-center justify-between text-sm">
                    <p className="text-slate-600">
                      Showing <span className="font-medium text-slate-900">{filteredUrls.length}</span> of <span className="font-medium text-slate-900">{urls.length}</span> URLs
                    </p>
                    {hasActiveFilters && (
                      <div className="flex items-center gap-2">
                        <span className="text-slate-600">Active filters:</span>
                        <div className="flex gap-2">
                          {searchQuery && (
                            <span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded-md text-xs font-medium">
                              Search: "{searchQuery}"
                            </span>
                          )}
                          {filterFavorites && (
                            <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded-md text-xs font-medium">
                              Favorites
                            </span>
                          )}
                          {filterTags.length > 0 && (
                            <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-md text-xs font-medium">
                              {filterTags.length} Tag{filterTags.length > 1 ? 's' : ''}
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div className="space-y-3">
                  {filteredUrls.map((url) => (
                    <div key={url.id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md hover:border-slate-300 transition">
                      <div className="flex flex-col sm:flex-row items-start justify-between gap-4">
                        <div className="flex-1 min-w-0 w-full">
                          {/* Title if exists */}
                          {url.title && (
                            <h3 className="text-lg font-semibold text-slate-900 mb-1">{url.title}</h3>
                          )}
                          
                          <div className="flex items-center gap-2 mb-2">
                            <button
                              onClick={(e) => handleUrlClick(e, url)}
                              className="text-slate-700 hover:text-indigo-600 truncate text-sm transition-colors"
                            >
                              {url.original_url}
                            </button>
                            <ExternalLink className="w-4 h-4 text-slate-400 flex-shrink-0" />
                          </div>
                          
                          {/* Description if exists */}
                          {url.descr && (
                            <p className="text-sm text-slate-600 mb-2 line-clamp-2">{url.descr}</p>
                          )}
                          
                          <div className="flex items-center gap-3 text-sm">
                            <span className="text-indigo-600 font-mono font-medium">{url.short_code}</span>
                            <span className="text-slate-400">•</span>
                            <span className="text-slate-600">{url.clicks || 0} clicks</span>
                          </div>

                          {url.tags && url.tags.length > 0 && (
                            <div className="flex flex-wrap gap-2 mt-3">
                              {url.tags.map((tag) => (
                                <span
                                  key={tag.id}
                                  className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium"
                                  style={{ backgroundColor: tag.color + '20', color: tag.color }}
                                >
                                  {tag.name}
                                  <button
                                    onClick={() => handleRemoveTagFromUrl(url.id, tag.id)}
                                    className="hover:opacity-70 hover:scale-110 transition-all duration-150"
                                  >
                                    <X className="w-3 h-3" />
                                  </button>
                                </span>
                              ))}
                            </div>
                          )}
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleToggleFavorite(url.id, url.is_favorite === true)}
                            className={`p-2 rounded-lg transition-all duration-200 ${
                              url.is_favorite
                                ? 'text-amber-500 hover:bg-amber-50 hover:shadow-sm active:scale-90'
                                : 'text-slate-400 hover:bg-slate-50 hover:text-slate-600 hover:shadow-sm active:scale-90'
                            }`}
                          >
                            <Star className={`w-5 h-5 ${url.is_favorite ? 'fill-current' : ''}`} />
                          </button>
                          <button
                            onClick={() => handleViewStats(url)}
                            className="p-2 text-slate-600 hover:bg-blue-50 hover:text-blue-600 rounded-lg transition-all duration-200 hover:shadow-sm active:scale-90"
                          >
                            <BarChart3 className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => generateQRCode(url)}
                            className="p-2 text-slate-600 hover:bg-purple-50 hover:text-purple-600 rounded-lg transition-all duration-200 hover:shadow-sm active:scale-90"
                          >
                            <QrCode className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => setSelectedUrlForTag(url.id)}
                            className="p-2 text-slate-600 hover:bg-indigo-50 hover:text-indigo-600 rounded-lg transition-all duration-200 hover:shadow-sm active:scale-90"
                          >
                            <Tag className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => copyToClipboard(`http://short.url/${url.short_code}`)}
                            className="p-2 text-slate-600 hover:bg-emerald-50 hover:text-emerald-600 rounded-lg transition-all duration-200 hover:shadow-sm active:scale-90"
                          >
                            <Copy className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => handleDeleteUrl(url.id)}
                            className="p-2 text-rose-600 hover:bg-rose-50 rounded-lg transition-all duration-200 hover:shadow-sm active:scale-90"
                          >
                            <Trash2 className="w-5 h-5" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {view === 'tags' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold text-slate-900">Tags</h2>
                  <button
                    onClick={() => setShowTagModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 hover:shadow-lg transition-all duration-200 shadow-md active:scale-95"
                  >
                    <Plus className="w-5 h-5" />
                    New Tag
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {tags.map((tag) => (
                    <div
                      key={tag.id}
                      className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md hover:border-slate-300 transition"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div
                            className="w-10 h-10 rounded-lg flex-shrink-0"
                            style={{ backgroundColor: tag.color }}
                          />
                          <div className="min-w-0">
                            <h3 className="font-medium text-slate-900 truncate">{tag.name}</h3>
                            <p className="text-xs text-slate-500">{tag.color}</p>
                          </div>
                        </div>
                        <button
                          onClick={() => handleDeleteTag(tag.id)}
                          className="p-2 text-rose-600 hover:bg-rose-50 rounded-lg transition-all duration-200 hover:shadow-sm active:scale-90 flex-shrink-0"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                      
                      {tag.descr && (
                        <p className="text-sm text-slate-600 line-clamp-2 mt-2">{tag.descr}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </main>
        </div>
      </div>

      {/* QR Code Modal */}
      {qrCodeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-md p-6 animate-in fade-in duration-200">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                  <QrCode className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="text-xl font-bold text-slate-900">QR Code</h3>
              </div>
              <button
                onClick={() => setQrCodeModal(null)}
                className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all duration-200 active:scale-90"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* QR Code Display */}
            <div className="bg-white rounded-xl border-2 border-slate-200 p-6 mb-6 flex items-center justify-center">
              <canvas id="qr-canvas" className="max-w-full h-auto" />
            </div>

            {/* URL Info */}
            <div className="bg-slate-50 rounded-lg p-4 border border-slate-200 mb-6">
              {qrCodeModal.title && (
                <p className="text-sm font-medium text-slate-900 mb-2">{qrCodeModal.title}</p>
              )}
              <div className="flex items-center gap-2 mb-3">
                <Link2 className="w-4 h-4 text-indigo-600 flex-shrink-0" />
                <p className="text-sm font-mono font-medium text-indigo-600">{qrCodeModal.url}</p>
              </div>
              <div className="flex items-start gap-2">
                <ExternalLink className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-slate-600 break-all">{qrCodeModal.originalUrl}</p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={() => setQrCodeModal(null)}
                className="flex-1 px-4 py-3 bg-slate-100 text-slate-700 rounded-lg font-medium hover:bg-slate-200 transition-all duration-200 active:scale-98"
              >
                Close
              </button>
              <button
                onClick={downloadQRCode}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 hover:shadow-lg transition-all duration-200 shadow-md active:scale-98"
              >
                <Download className="w-4 h-4" />
                Download
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Redirect Warning Modal */}
      {redirectWarning && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-md p-6 animate-in fade-in duration-200">
            <div className="flex items-start gap-4 mb-6">
              <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center flex-shrink-0">
                <AlertTriangle className="w-6 h-6 text-amber-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-slate-900 mb-2">Redirect Warning</h3>
                <p className="text-sm text-slate-600">You are about to be redirected to an external website.</p>
              </div>
            </div>

            <div className="bg-slate-50 rounded-lg p-4 border border-slate-200 mb-6">
              {redirectWarning.title && (
                <p className="text-sm font-medium text-slate-900 mb-2">{redirectWarning.title}</p>
              )}
              <div className="flex items-start gap-2">
                <ExternalLink className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-slate-700 break-all">{redirectWarning.url}</p>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setRedirectWarning(null)}
                className="flex-1 px-4 py-3 bg-slate-100 text-slate-700 rounded-lg font-medium hover:bg-slate-200 transition-all duration-200 active:scale-98"
              >
                Cancel
              </button>
              <button
                onClick={confirmRedirect}
                className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 hover:shadow-lg transition-all duration-200 shadow-md active:scale-98"
              >
                Continue
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Notification Toast */}
      {notification && (
        <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-top duration-300">
          <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-4 flex items-center gap-3 min-w-[300px]">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
              notification.type === 'success' ? 'bg-emerald-100' : 'bg-blue-100'
            }`}>
              {notification.icon === 'copy' ? (
                <Check className={`w-5 h-5 ${
                  notification.type === 'success' ? 'text-emerald-600' : 'text-blue-600'
                }`} />
              ) : notification.icon === 'download' ? (
                <Download className={`w-5 h-5 ${
                  notification.type === 'success' ? 'text-emerald-600' : 'text-blue-600'
                }`} />
              ) : (
                <Copy className={`w-5 h-5 ${
                  notification.type === 'success' ? 'text-emerald-600' : 'text-blue-600'
                }`} />
              )}
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-900">{notification.message}</p>
            </div>
            <button
              onClick={() => setNotification(null)}
              className="p-1 text-slate-400 hover:text-slate-600 rounded transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Create URL Modal */}
      {showUrlModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center">
                  <Link2 className="w-6 h-6 text-indigo-600" />
                </div>
                <h3 className="text-xl font-bold text-slate-900">Create Short URL</h3>
              </div>
              <button
                onClick={() => {
                  setShowUrlModal(false);
                  setNewUrl('');
                  setNewUrlTitle('');
                  setNewUrlDescription('');
                  setNewUrlFavorite(false);
                }}
                className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all duration-200 active:scale-90"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-5">
              {/* URL Input */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  URL <span className="text-rose-500">*</span>
                </label>
                <input
                  type="url"
                  value={newUrl}
                  onChange={(e) => setNewUrl(e.target.value)}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                  placeholder="https://example.com/very-long-url"
                  required
                />
              </div>

              {/* Title Input */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Title <span className="text-slate-400 text-xs">(optional)</span>
                </label>
                <input
                  type="text"
                  value={newUrlTitle}
                  onChange={(e) => setNewUrlTitle(e.target.value)}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                  placeholder="My awesome link"
                  maxLength={100}
                />
                <p className="text-xs text-slate-500 mt-1">{newUrlTitle.length}/100 characters</p>
              </div>

              {/* Description Input */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Description <span className="text-slate-400 text-xs">(optional)</span>
                </label>
                <textarea
                  value={newUrlDescription}
                  onChange={(e) => setNewUrlDescription(e.target.value)}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none"
                  placeholder="Add a description for this URL..."
                  rows={3}
                  maxLength={500}
                />
                <p className="text-xs text-slate-500 mt-1">{newUrlDescription.length}/500 characters</p>
              </div>

              {/* Favorite Toggle */}
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
                    <Star className={`w-5 h-5 ${newUrlFavorite ? 'fill-amber-500 text-amber-500' : 'text-amber-500'}`} />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">Mark as Favorite</p>
                    <p className="text-xs text-slate-600">Add this URL to your favorites</p>
                  </div>
                </div>
                <button
                  onClick={() => setNewUrlFavorite(!newUrlFavorite)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 focus:outline-none ${
                    newUrlFavorite ? 'bg-indigo-600' : 'bg-slate-300'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200 ${
                      newUrlFavorite ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => {
                    setShowUrlModal(false);
                    setNewUrl('');
                    setNewUrlTitle('');
                    setNewUrlDescription('');
                    setNewUrlFavorite(false);
                  }}
                  className="flex-1 px-4 py-3 bg-slate-100 text-slate-700 rounded-lg font-medium hover:bg-slate-200 transition-all duration-200 active:scale-98"
                >
                  Cancel
                </button>
                <button
                  onClick={handleShortenUrl}
                  disabled={loading || !newUrl}
                  className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-md active:scale-98"
                >
                  {loading ? 'Creating...' : 'Create Short URL'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tag Modal */}
      {showTagModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-violet-100 rounded-xl flex items-center justify-center">
                  <Tag className="w-6 h-6 text-violet-600" />
                </div>
                <h3 className="text-xl font-bold text-slate-900">Create New Tag</h3>
              </div>
              <button
                onClick={() => {
                  setShowTagModal(false);
                  setNewTagName('');
                  setNewTagDescription('');
                  setNewTagColor('#3B82F6');
                }}
                className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all duration-200 active:scale-90"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Tag Name <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={newTagName}
                  onChange={(e) => setNewTagName(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleCreateTag()}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                  placeholder="e.g., Work, Personal, Important"
                  maxLength={50}
                />
                <p className="text-xs text-slate-500 mt-1">{newTagName.length}/50 characters</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Description <span className="text-slate-400 text-xs">(optional)</span>
                </label>
                <textarea
                  value={newTagDescription}
                  onChange={(e) => setNewTagDescription(e.target.value)}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none"
                  placeholder="Add a description for this tag..."
                  rows={3}
                  maxLength={200}
                />
                <p className="text-xs text-slate-500 mt-1">{newTagDescription.length}/200 characters</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-3">Tag Color</label>
                
                {/* Color Preview */}
                <div className="mb-4">
                  <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <div 
                      className="w-12 h-12 rounded-lg shadow-sm border-2 border-white"
                      style={{ backgroundColor: newTagColor }}
                    />
                    <div className="flex-1">
                      <p className="text-sm text-slate-600 mb-1">Selected Color</p>
                      <p className="text-sm font-mono font-medium text-slate-900">{newTagColor.toUpperCase()}</p>
                    </div>
                  </div>
                </div>

                {/* Color Presets */}
                <div className="mb-4">
                  <p className="text-xs font-medium text-slate-600 mb-2">Quick Select</p>
                  <div className="grid grid-cols-9 gap-2">
                    {Constants.COLOR_PRESSETS.map((color) => (
                      <button
                        key={color}
                        onClick={() => setNewTagColor(color)}
                        className={`w-8 h-8 rounded-lg transition-all duration-200 hover:scale-110 ${
                          newTagColor === color 
                            ? 'ring-2 ring-offset-2 ring-indigo-500 scale-110' 
                            : 'hover:shadow-md'
                        }`}
                        style={{ backgroundColor: color }}
                        title={color}
                      />
                    ))}
                  </div>
                </div>

                {/* Custom Color Picker */}
                <div>
                  <p className="text-xs font-medium text-slate-600 mb-2">Custom Color</p>
                  <div className="flex gap-3">
                    <input
                      type="color"
                      value={newTagColor}
                      onChange={(e) => setNewTagColor(e.target.value)}
                      className="h-12 w-20 rounded-lg border-2 border-slate-300 cursor-pointer hover:border-indigo-400 transition-colors"
                    />
                    <input
                      type="text"
                      value={newTagColor}
                      onChange={(e) => {
                        const value = e.target.value;
                        if (/^#[0-9A-Fa-f]{0,6}$/.test(value)) {
                          setNewTagColor(value);
                        }
                      }}
                      className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none font-mono text-sm"
                      placeholder="#3B82F6"
                      maxLength={7}
                    />
                  </div>
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => {
                    setShowTagModal(false);
                    setNewTagName('');
                    setNewTagDescription('');
                    setNewTagColor('#3B82F6');
                  }}
                  className="flex-1 px-4 py-3 bg-slate-100 text-slate-700 rounded-lg font-medium hover:bg-slate-200 transition-all duration-200 active:scale-98"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateTag}
                  disabled={!newTagName}
                  className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 hover:shadow-lg transition-all duration-200 shadow-md active:scale-98 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Tag
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Tag to URL Modal */}
      {selectedUrlForTag && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-slate-900">Add Tag</h3>
              <button
                onClick={() => setSelectedUrlForTag(null)}
                className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all duration-200 active:scale-90"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2">
              {tags.map((tag) => (
                <button
                  key={tag.id}
                  onClick={() => handleAddTagToUrl(selectedUrlForTag, tag.id)}
                  className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 transition-all duration-200 border border-transparent hover:border-slate-200 hover:shadow-sm active:scale-98"
                >
                  <div
                    className="w-8 h-8 rounded-lg"
                    style={{ backgroundColor: tag.color }}
                  />
                  <span className="font-medium text-slate-900">{tag.name}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Stats Modal */}
      {selectedUrlForStats && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-2xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                  <BarChart3 className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="text-xl font-bold text-slate-900">URL Statistics</h3>
              </div>
              <button
                onClick={() => {
                  setSelectedUrlForStats(null);
                  setUrlStats(null);
                }}
                className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all duration-200 active:scale-90"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              {/* URL Info */}
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                <div className="flex items-center gap-2 mb-2">
                  <Link2 className="w-4 h-4 text-slate-500" />
                  <span className="text-sm font-medium text-slate-700">Original URL</span>
                </div>
                <p className="text-slate-900 break-all">{selectedUrlForStats.original_url}</p>
                <div className="mt-3 flex items-center gap-2">
                  <span className="text-sm text-slate-600">Short code:</span>
                  <span className="text-sm font-mono font-medium text-indigo-600">{selectedUrlForStats.short_code}</span>
                </div>
              </div>

              {/* Stats Content */}
              {loadingStats ? (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto mb-3" />
                    <p className="text-slate-600">Loading statistics...</p>
                  </div>
                </div>
              ) : urlStats ? (
                <div className="space-y-4">
                  {/* Stats Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                          <BarChart3 className="w-6 h-6 text-emerald-600" />
                        </div>
                        <div>
                          <p className="text-sm text-slate-600">Total Clicks</p>
                          <p className="text-2xl font-bold text-slate-900">{urlStats.total_clicks}</p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-violet-100 rounded-xl flex items-center justify-center">
                          <ExternalLink className="w-6 h-6 text-violet-600" />
                        </div>
                        <div>
                          <p className="text-sm text-slate-600">Last Click</p>
                          <p className="text-sm font-medium text-slate-900">
                            {urlStats.last_click 
                              ? new Date(urlStats.last_click).toLocaleDateString() 
                              : 'Never'}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Referrers */}
                  {urlStats.countries && urlStats.countries.length > 0 && (
                    <div className="bg-white rounded-xl p-5 border border-slate-200">
                      <h4 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
                        <ExternalLink className="w-4 h-4" />
                        Top Countries
                      </h4>
                      <div className="space-y-2">
                        {urlStats.countries.map((country, index) => (
                          <div 
                            key={index}
                            className="flex items-center justify-between py-2 px-3 bg-slate-50 rounded-lg"
                          >
                            <span className="text-sm text-slate-700">{country}</span>
                            <span className="text-xs font-medium text-slate-500">#{index + 1}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Created Date */}
                  <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-600">Created</span>
                      <span className="text-slate-900 font-medium">
                        {new Date(selectedUrlForStats.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              ) : <p>This url has not statistics yet!</p>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;