import { Sidebar } from './Sidebar';
import { colors } from '../../theme/tokens';

export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: colors.bg }}>
      <Sidebar />
      <main
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
          background: colors.bg,
        }}
      >
        {children}
      </main>
    </div>
  );
}
