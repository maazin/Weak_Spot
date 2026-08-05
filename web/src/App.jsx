import { Component, useEffect, useState } from 'react';
import { Link, Navigate, Route, Routes } from 'react-router-dom';
import { Nav, Spinner } from './components/Chrome';
import { api } from './lib/api';
import Diagnosis from './pages/Diagnosis';
import Landing from './pages/Landing';
import Reviews from './pages/Reviews';
import Submit from './pages/Submit';
import WeakPatterns from './pages/WeakPatterns';

/** 404 and the unhandled-error boundary share error-state.png, per spec section 10. */
function ErrorScreen({ title, body, children }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-5 px-4 text-center">
      <img src="/assets/error-state.png" alt="" className="w-56 max-w-full" />
      <h1 className="text-lg font-semibold text-zinc-100">{title}</h1>
      <p className="max-w-md text-sm text-muted">{body}</p>
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
        Back to Submit
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
          <button onClick={() => window.location.reload()} className="btn-primary">
            Reload
          </button>
        </ErrorScreen>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  const [user, setUser] = useState(undefined); // undefined = still checking

  useEffect(() => {
    api
      .me()
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  if (user === undefined) return <Spinner label="Loading…" />;

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
      <Nav user={user} onSignOut={() => setUser(null)} />
      <Routes>
        <Route path="/" element={<Navigate to="/submit" replace />} />
        <Route path="/submit" element={<Submit />} />
        <Route path="/diagnosis/:id" element={<Diagnosis />} />
        <Route path="/reviews" element={<Reviews />} />
        <Route path="/patterns" element={<WeakPatterns />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </div>
  );
}
