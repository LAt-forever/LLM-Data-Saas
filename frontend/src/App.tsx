import { Route, Switch } from 'wouter';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import { antdTheme } from './theme';
import { AppLayout } from './components/layout/AppLayout';
import { ToastContainer } from './components/ToastContainer';
import { HomePage } from './pages/HomePage';
import { TaskDetailPage } from './pages/TaskDetailPage';
import { ApiConfigsPage } from './pages/ApiConfigsPage';
import { WordListsPage } from './pages/WordListsPage';
import { PromptTemplatesPage } from './pages/PromptTemplatesPage';
import { CategoriesPage } from './pages/CategoriesPage';

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
            <Route path="/settings/api-configs" component={ApiConfigsPage} />
            <Route path="/settings/wordlists" component={WordListsPage} />
            <Route path="/settings/prompt-templates" component={PromptTemplatesPage} />
            <Route path="/settings/categories" component={CategoriesPage} />
            <Route>404: 页面不存在</Route>
          </Switch>
        </AppLayout>
        <ToastContainer />
      </QueryClientProvider>
    </ConfigProvider>
  );
}

export default App;
