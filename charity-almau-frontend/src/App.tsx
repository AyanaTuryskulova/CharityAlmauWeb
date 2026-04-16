import { RouterProvider } from 'react-router-dom';
import { Suspense } from 'react';
import { AuthProvider } from './contexts/AuthContext';
import { ChatProvider } from './contexts/ChatContext';
import { NotificationProvider } from './contexts/NotificationContext';
import router from './router';
import './config/i18n';
import './global.css';

export default function App() {
  return (
    <Suspense fallback={<div style={{ padding: '2rem', textAlign: 'center' }}>Загрузка...</div>}>
      <NotificationProvider>
        <AuthProvider>
          <ChatProvider>
            <RouterProvider router={router} />
          </ChatProvider>
        </AuthProvider>
      </NotificationProvider>
    </Suspense>
  );
}
