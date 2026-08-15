import { useCallback, useEffect, useState } from "react";

import "./App.css";
import {
  logout as clearSession,
  getAccessToken,
  getCurrentUser,
  getDocuments,
} from "./api";
import Auth from "./components/Auth";
import Chat from "./components/Chat";
import DocumentList from "./components/DocumentList";
import DocumentUpload from "./components/DocumentUpload";

function App() {
  const [user, setUser] = useState(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [chatKey, setChatKey] = useState(0);

  const [selectedDocumentId, setSelectedDocumentId] = useState("");

  const loadDocuments = useCallback(async () => {
    try {
      setLoading(true);
      setError("");
      setDocuments(await getDocuments());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    async function restoreSession() {
      const token = getAccessToken();

      if (!token) {
        setCheckingAuth(false);
        return;
      }

      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
      } catch {
        clearSession();
        setUser(null);
      } finally {
        setCheckingAuth(false);
      }
    }

    restoreSession();
  }, []);

  useEffect(() => {
    if (user) {
      loadDocuments();
    }
  }, [user, loadDocuments]);

  function handleAuthenticated(authenticatedUser) {
    setUser(authenticatedUser);
  }

  function handleLogout() {
    clearSession();
    setUser(null);
    setDocuments([]);
    setError("");
  }

  function handleNewChat() {
    setSelectedDocumentId("");
    setChatKey((current) => current + 1);
  }

  if (checkingAuth) {
    return (
      <main className="auth-page">
        <p>Loading PolicyAI...</p>
      </main>
    );
  }

  if (!user) {
    return <Auth onAuthenticated={handleAuthenticated} />;
  }

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

        <button
          className="new-chat-button"
          type="button"
          onClick={handleNewChat}
        >
          + New chat
        </button>

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
            selectedDocumentId={selectedDocumentId}
            onSelect={setSelectedDocumentId}
          />
        </div>

        <div className="sidebar-footer">
          <div className="current-user">
            <strong>{user.email}</strong>
            <span>{user.role}</span>
          </div>

          <button type="button" onClick={handleLogout}>
            Sign out
          </button>

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

        <Chat
          key={chatKey}
          documents={documents}
          documentId={selectedDocumentId}
          onDocumentChange={setSelectedDocumentId}
        />
      </main>
    </div>
  );
}

export default App;