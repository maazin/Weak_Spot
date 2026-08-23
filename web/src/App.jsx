import { Component, useEffect, useState } from 'react';
import { Link, Navigate, Route, Routes } from 'react-router-dom';
import { Nav, Spinner } from './components/Chrome';
import { api } from './lib/api';
import Diagnosis from './pages/Diagnosis';
import Landing from './pages/Landing';
import Reviews from './pages/Reviews';
import Submit from './pages/Submit';
import WeakPatterns from './pages/WeakPatterns';

function ErrorScreen({ title, body, children }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 px-6 text-center">
      <h1 className="font-serif text-title font-semibold text-ink">{title}</h1>
      <p className="max-w-prose text-body text-ink-2">{body}</p>
      {children}
    </div>
  );
}

function NotFound() {
  return (
    <ErrorScreen
      title="That page does not exist"
      body="The link may be stale, or the diagnosis may belong to another account."
    >
      <Link to="/submit" className="btn-primary">
        Back to submit
      </Link>
    </ErrorScreen>
  );
}

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <ErrorScreen
          title="Something broke on this screen"
          body="The error has been logged. Reloading usually clears it."
        >
          <button type="button" onClick={() => window.location.reload()} className="btn-primary">
            Reload
          </button>
        </ErrorScreen>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  const [user, setUser] = useState(undefined); // undefined means the check is still running

  useEffect(() => {
    api
      .me()
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  if (user === undefined) return <Spinner label="Loading" />;

  if (!user) {
    return (
      <Routes>
        <Route path="/" element={<Landing onSignedIn={setUser} />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Keyboard users land here first and can jump past the nav. */}
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-brass focus:px-4 focus:py-2 focus:text-caption focus:font-medium focus:text-on-brass"
      >
        Skip to content
      </a>
      <Nav user={user} onSignOut={() => setUser(null)} />
      <div id="main">
        <Routes>
          <Route path="/" element={<Navigate to="/submit" replace />} />
          <Route path="/submit" element={<Submit />} />
          <Route path="/diagnosis/:id" element={<Diagnosis />} />
          <Route path="/reviews" element={<Reviews />} />
          <Route path="/patterns" element={<WeakPatterns />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
    </div>
  );
}
