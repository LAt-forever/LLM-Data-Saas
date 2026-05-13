import { Route, Switch } from 'wouter';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import { antdTheme } from './theme';
import { AppLayout } from './components/layout/AppLayout';
import { ToastContainer } from './components/ToastContainer';
import { HomePage } from './pages/HomePage';
import { TaskDetailPage } from './pages/TaskDetailPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <ConfigProvider theme={antdTheme}>
      <QueryClientProvider client={queryClient}>
        <AppLayout>
          <Switch>
            <Route path="/" component={HomePage} />
            <Route path="/tasks/:id" component={TaskDetailPage} />
            <Route>404: 页面不存在</Route>
          </Switch>
        </AppLayout>
        <ToastContainer />
      </QueryClientProvider>
    </ConfigProvider>
  );
}

export default App;
