import { useLocation } from 'wouter';
import { useAuth } from '../hooks/useAuth';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, isLoading } = useAuth();
  const [location, navigate] = useLocation();

  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: '#0f172a',
      }}>
        <span style={{ color: '#94a3b8' }}>加载中...</span>
      </div>
    );
  }

  if (!user) {
    const redirectTo = encodeURIComponent(location);
    navigate(`/login?redirectTo=${redirectTo}`);
    return null;
  }

  return <>{children}</>;
}
