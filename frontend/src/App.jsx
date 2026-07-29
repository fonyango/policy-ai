import { useCallback, useEffect, useState } from "react";

import "./App.css";
import { getDocuments } from "./api";
import Chat from "./components/Chat";
import DocumentList from "./components/DocumentList";
import DocumentUpload from "./components/DocumentUpload";

function App() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDocuments = useCallback(async () => {
    try {
      setError("");
      setDocuments(await getDocuments());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">P</div>
          <div>
            <strong>PolicyAI</strong>
            <span>Policy assistant</span>
          </div>
        </div>

        <button className="new-chat-button" type="button">
          + New chat
        </button>

        <nav className="sidebar-nav">
          <button type="button">Search chats</button>
          <button type="button">Documents</button>
        </nav>

        <div className="sidebar-section">
          <div className="sidebar-section-heading">
            <span>Knowledge base</span>
            <span>{documents.length}</span>
          </div>

          <DocumentUpload onUpload={loadDocuments} />

          <DocumentList
            documents={documents}
            loading={loading}
            error={error}
            onDelete={loadDocuments}
          />
        </div>

        <div className="sidebar-section conversations">
          <span className="sidebar-label">Recent</span>
          <button type="button">Open tender requirements</button>
          <button type="button">Procurement thresholds</button>
          <button type="button">Preference rules</button>
        </div>

        <div className="sidebar-footer">
          <button type="button">Settings</button>
          <span>PolicyAI v0.1</span>
        </div>
      </aside>

      <main className="assistant-workspace">
        <header className="workspace-header">
          <span>PolicyAI Assistant</span>

          <div className="online-status">
            <span />
            Online
          </div>
        </header>

        <Chat documents={documents} />
      </main>
    </div>
  );
}

export default App;