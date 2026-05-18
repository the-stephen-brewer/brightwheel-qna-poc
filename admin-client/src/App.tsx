import { useState, useEffect } from 'react';
import { 
  Database, 
  BarChart3, 
  AlertTriangle, 
  MessageSquareShare, 
  X, 
  RefreshCcw,
  CheckCircle2
} from 'lucide-react';
import './App.css';

type View = 'knowledge' | 'trends' | 'alerts' | 'escalations';

interface KnowledgeItem {
  id: number;
  content: string;
  metadata: { category: string };
}

interface LogItem {
  id: string;
  question: string;
  answer: string;
  feedback: string | null;
  needs_review: boolean;
  created_at: string;
}

interface TrendData {
  total_inquiries: number;
  resolution_rate: number;
  top_categories: { name: string, count: number }[];
  sample_questions: string[];
}

const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8080/api') + '/admin';

function App() {
  const [activeView, setActiveView] = useState<View>('trends');
  const [data, setData] = useState<any[]>([]);
  const [trends, setTrends] = useState<TrendData | null>(null);
  const [selectedItem, setSelectedItem] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      if (activeView === 'trends') {
        const res = await fetch(`${API_BASE}/trends`);
        setTrends(await res.json());
      } else {
        const path = activeView === 'knowledge' ? 'knowledge' : `logs?filter_type=${activeView}`;
        const res = await fetch(`${API_BASE}/${path}`);
        setData(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    setData([]);
    fetchData();
    setSelectedItem(null);
  }, [activeView]);

  const handleResolve = async (id: string) => {
    try {
      await fetch(`${API_BASE.replace('/admin', '')}/admin/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ log_id: id, feedback: '' }) // feedback not used here but required by schema
      });
      fetchData();
      setSelectedItem(null);
    } catch (err) {
      console.error(err);
    }
  };

  const renderBadge = (item: LogItem) => {
    if (item.needs_review) return <span className="badge urgent">Escalated</span>;
    if (item.feedback === 'thumbs_down') return <span className="badge pending">Needs Review</span>;
    return <span className="badge resolved">Resolved</span>;
  };

  return (
    <div className="admin-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>Front Desk Admin</h2>
        </div>
        <nav>
          <div className={`nav-item ${activeView === 'trends' ? 'active' : ''}`} onClick={() => setActiveView('trends')}>
            <BarChart3 size={18} /> Trends
          </div>
          <div className={`nav-item ${activeView === 'knowledge' ? 'active' : ''}`} onClick={() => setActiveView('knowledge')}>
            <Database size={18} /> Knowledge Base
          </div>
          <div className={`nav-item ${activeView === 'alerts' ? 'active' : ''}`} onClick={() => setActiveView('alerts')}>
            <AlertTriangle size={18} /> Live Alerts
          </div>
          <div className={`nav-item ${activeView === 'escalations' ? 'active' : ''}`} onClick={() => setActiveView('escalations')}>
            <MessageSquareShare size={18} /> Escalation Tickets
          </div>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="main-header">
          <h1>{activeView.charAt(0).toUpperCase() + activeView.slice(1)}</h1>
          <button className="nav-item" style={{border: '1px solid #ddd', borderRadius: '4px'}} onClick={fetchData}>
            <RefreshCcw size={14} className={isLoading ? 'animate-spin' : ''} /> Refresh
          </button>
        </header>

        <div className="table-container">
          {activeView === 'trends' && trends ? (
            <div className="trends-grid" style={{gridTemplateColumns: '1fr 1fr'}}>
              <div className="metric-card">
                <div className="metric-label">Total Inquiries (24h)</div>
                <div className="metric-value">{trends.total_inquiries}</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">AI Ticket Deflection Rate</div>
                <div className="metric-value">{Math.round(trends.resolution_rate)}%</div>
              </div>
              <div className="metric-card" style={{gridColumn: 'span 2'}}>
                <div className="metric-label">Top Category: {trends.top_categories[0]?.name || 'N/A'}</div>
                <div className="metric-value">{trends.top_categories[0]?.count || 0} Questions</div>
                <div className="detail-section" style={{marginTop: '16px'}}>
                  <span className="detail-label">Sample Questions:</span>
                  <ul style={{fontSize: '13px', color: 'var(--text-secondary)', marginLeft: '20px', marginTop: '8px'}}>
                    {trends.sample_questions.map((q, i) => <li key={i}>"{q}"</li>)}
                  </ul>
                </div>
              </div>
            </div>
          ) : (
            <table>
              <thead>
                {activeView === 'knowledge' ? (
                  <tr>
                    <th>Category</th>
                    <th>Content Preview</th>
                  </tr>
                ) : (
                  <tr>
                    <th>Status</th>
                    <th>Question</th>
                    <th>Time</th>
                  </tr>
                )}
              </thead>
              <tbody>
                {data.map((item) => (
                  <tr key={item.id} onClick={() => setSelectedItem(item)}>
                    {activeView === 'knowledge' ? (
                      <>
                        <td><span className="badge resolved">{(item as KnowledgeItem).metadata?.category}</span></td>
                        <td>{(item as KnowledgeItem).content?.substring(0, 100)}...</td>
                      </>
                    ) : (
                      <>
                        <td>{renderBadge(item as LogItem)}</td>
                        <td>{(item as LogItem).question}</td>
                        <td>{(item as LogItem).created_at ? new Date((item as LogItem).created_at).toLocaleTimeString() : ''}</td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>

      {/* Right Drawer */}
      <div className={`drawer ${selectedItem ? 'open' : ''}`}>
        <div className="drawer-header">
          <h3>Details</h3>
          <button className="feedback-btn" onClick={() => setSelectedItem(null)}><X size={20} /></button>
        </div>
        <div className="drawer-content">
          {selectedItem && (
            <>
              {activeView === 'knowledge' ? (
                <div className="detail-section">
                  <span className="detail-label">Category</span>
                  <div className="detail-value">{(selectedItem as KnowledgeItem).metadata?.category}</div>
                  <div style={{marginTop: '24px'}}>
                    <span className="detail-label">Content</span>
                    <div className="detail-value">{(selectedItem as KnowledgeItem).content}</div>
                  </div>
                </div>
              ) : (
                <>
                  <div className="detail-section">
                    <span className="detail-label">Question</span>
                    <div className="detail-value">{(selectedItem as LogItem).question}</div>
                  </div>
                  <div className="detail-section">
                    <span className="detail-label">AI Answer</span>
                    <div className="detail-value">{(selectedItem as LogItem).answer}</div>
                  </div>
                  <div className="detail-section">
                    <span className="detail-label">Metadata</span>
                    <div className="detail-value">
                      ID: {selectedItem.id}<br/>
                      Feedback: {selectedItem.feedback || 'None'}<br/>
                      Needs Review: {selectedItem.needs_review ? 'Yes' : 'No'}
                    </div>
                  </div>
                  {selectedItem.needs_review && (
                    <button 
                      className="nav-item active" 
                      style={{width: '100%', justifyContent: 'center', borderRadius: '4px'}}
                      onClick={() => handleResolve(selectedItem.id)}
                    >
                      <CheckCircle2 size={16} /> Mark as Resolved
                    </button>
                  )}
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
