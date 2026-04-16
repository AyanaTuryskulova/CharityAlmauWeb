import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';

export default function AuthCallbackPage() {
  const { t } = useTranslation('auth');
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) {
      Promise.resolve().then(() => {
        setError(t('callback.error'));
        setTimeout(() => navigate('/login', { replace: true }), 2000);
      });
      return;
    }

    login(token)
      .then(() => navigate('/', { replace: true }))
      .catch(() => {
        setError(t('callback.error'));
        setTimeout(() => navigate('/login', { replace: true }), 2000);
      });
  }, [searchParams, login, navigate, t]);

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#0E0D0B',
      color: '#ffffff',
      fontSize: '1.125rem',
    }}>
      {error || t('callback.processing')}
    </div>
  );
}
