import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { authService } from '../services/authService';
import styles from './LoginPage.module.css';

export default function LoginPage() {
  const { t } = useTranslation('auth');
  const { t: tc } = useTranslation('common');
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleMicrosoftLogin = () => {
    window.location.href = authService.getLoginUrl();
  };

  const handleDevLogin = async (e: FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !name.trim()) return;
    setLoading(true);
    setError('');
    try {
      const { token } = await authService.devLogin(email.trim(), name.trim());
      await login(token);
      navigate('/', { replace: true });
    } catch {
      setError(t('callback.error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <img src="/logo.svg" alt="Charity AlmaU" className={styles.logo} />

      <h1 className={styles.title}>{t('login.title')}</h1>
      <p className={styles.subtitle}>{t('login.subtitle')}</p>

      <button className={styles.microsoftBtn} onClick={handleMicrosoftLogin}>
        <svg className={styles.microsoftIcon} viewBox="0 0 21 21">
          <rect x="1" y="1" width="9" height="9" fill="#f25022" />
          <rect x="11" y="1" width="9" height="9" fill="#7fba00" />
          <rect x="1" y="11" width="9" height="9" fill="#00a4ef" />
          <rect x="11" y="11" width="9" height="9" fill="#ffb900" />
        </svg>
        {t('login.microsoft')}
      </button>

      <p className={styles.hint}>{t('login.hint')}</p>

      <div className={styles.stats}>
        <div className={styles.stat}>
          <div className={styles.statNumber}>340+</div>
          <div className={styles.statLabel}>{tc('stats.students')}</div>
        </div>
        <div className={styles.stat}>
          <div className={styles.statNumber}>1 200+</div>
          <div className={styles.statLabel}>{tc('stats.listings')}</div>
        </div>
      </div>

      {import.meta.env.DEV && (
        <div className={styles.devSection}>
          <div className={styles.devDivider}>{t('login.devLogin')}</div>
          <form className={styles.devForm} onSubmit={handleDevLogin}>
            <input
              type="email"
              className={styles.devInput}
              placeholder={t('login.email')}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <input
              type="text"
              className={styles.devInput}
              placeholder={t('login.name')}
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
            {error && <p className={styles.error}>{error}</p>}
            <button type="submit" className={styles.devBtn} disabled={loading}>
              {loading ? tc('loading') : t('login.enter')}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
