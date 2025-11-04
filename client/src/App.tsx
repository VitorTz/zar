import { useUser } from './context/AuthContext';
import AuthPage from './pages/AuthPage';
import { useView } from './context/ViewContext';
import Header from './components/Header';
import SideBar from './components/SideBar';
import DashboardPage from './pages/Dashboard';
import UrlsPage from './pages/UrlsPage';
import TagsPage from './pages/TagsPage';
import { useDialog } from './hooks/useDialog';
import ERDiagram from './pages/ErDiagram';
import APIRoutesExplorer from './pages/ApiPage';


const App = () => {
  
  const { AlertRenderer, ConfirmRenderer } = useDialog()
  const { user } = useUser()
  const { view } = useView()

  if (!user) {
    return <AuthPage/>
    
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Header/>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row gap-6">
          <SideBar/>
          <main className="flex-1">
            {view === 'dashboard' && <DashboardPage/> }
            {view === 'urls' && <UrlsPage/>}
            {view === 'tags' && <TagsPage/> }
            {view === 'db' && <ERDiagram/> }
            {view === 'api' && <APIRoutesExplorer/> }
            {ConfirmRenderer}
            {AlertRenderer}
          </main>
        </div>
      </div>
    </div>
  );
};

export default App;