import { createBrowserRouter } from 'react-router-dom';
import Layout from './components/layout/Layout';
import ProtectedRoute from './components/common/ProtectedRoute';
import AdminRoute from './components/common/AdminRoute';
import LoginPage from './pages/LoginPage';
import AuthCallbackPage from './pages/AuthCallbackPage';
import HomePage from './pages/HomePage';
import ListingDetailPage from './pages/ListingDetailPage';
import CreateListingPage from './pages/CreateListingPage';
import EditListingPage from './pages/EditListingPage';
import MyListingsPage from './pages/MyListingsPage';
import FavoritesPage from './pages/FavoritesPage';
import RequestsPage from './pages/RequestsPage';
import ChatsPage from './pages/ChatsPage';
import ProfilePage from './pages/ProfilePage';
import EditProfilePage from './pages/EditProfilePage';
import UserProfilePage from './pages/UserProfilePage';
import AdminPage from './pages/AdminPage';
import NotFoundPage from './pages/NotFoundPage';

const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/auth/callback', element: <AuthCallbackPage /> },
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <ProtectedRoute><HomePage /></ProtectedRoute> },
      { path: 'listings/:id', element: <ProtectedRoute><ListingDetailPage /></ProtectedRoute> },
      { path: 'listings/new', element: <ProtectedRoute><CreateListingPage /></ProtectedRoute> },
      { path: 'listings/:id/edit', element: <ProtectedRoute><EditListingPage /></ProtectedRoute> },
      { path: 'my-listings', element: <ProtectedRoute><MyListingsPage /></ProtectedRoute> },
      { path: 'favorites', element: <ProtectedRoute><FavoritesPage /></ProtectedRoute> },
      { path: 'requests', element: <ProtectedRoute><RequestsPage /></ProtectedRoute> },
      { path: 'chats', element: <ProtectedRoute><ChatsPage /></ProtectedRoute> },
      { path: 'chats/:chatId', element: <ProtectedRoute><ChatsPage /></ProtectedRoute> },
      { path: 'profile', element: <ProtectedRoute><ProfilePage /></ProtectedRoute> },
      { path: 'profile/edit', element: <ProtectedRoute><EditProfilePage /></ProtectedRoute> },
      { path: 'users/:userId', element: <ProtectedRoute><UserProfilePage /></ProtectedRoute> },
      { path: 'admin', element: <AdminRoute><AdminPage /></AdminRoute> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);

export default router;
