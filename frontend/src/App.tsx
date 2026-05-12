import { Route, Switch } from 'wouter';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout';
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
    <QueryClientProvider client={queryClient}>
      <Layout>
        <Switch>
          <Route path="/" component={HomePage} />
          <Route path="/tasks/:id" component={TaskDetailPage} />
          <Route>404: 页面不存在</Route>
        </Switch>
      </Layout>
      <ToastContainer />
    </QueryClientProvider>
  );
}

export default App;
