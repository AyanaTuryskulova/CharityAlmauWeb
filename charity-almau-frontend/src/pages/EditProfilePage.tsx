import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { userService } from '../services/userService';
import { authService } from '../services/authService';
import { getAvatarUrl } from '../constants';
import Avatar from '../components/common/Avatar';
import Button from '../components/common/Button';
import Loader from '../components/common/Loader';
import styles from './EditProfilePage.module.css';

export default function EditProfilePage() {
  const { t } = useTranslation('profile');
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [name, setName] = useState(user?.name ?? '');
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!user) return <Loader fullPage />;

  const currentAvatarUrl = avatarPreview || getAvatarUrl(user.avatarUrl);

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAvatarFile(file);
      setAvatarPreview(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('name', name.trim());
      if (avatarFile) {
        formData.append('avatar', avatarFile);
      }
      await userService.updateMe(formData);
      // Refresh auth user data
      const token = localStorage.getItem('token');
      if (token) {
        await authService.getMe();
        // Force re-render by re-login
        await login(token);
      }
      navigate('/profile');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('common:error'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={styles.page}>
      <h2 className={styles.title}>{t('editTitle')}</h2>

      <form className={styles.form} onSubmit={handleSubmit}>
        <div className={styles.avatarSection}>
          <label className={styles.label}>{t('avatar')}</label>
          <div className={styles.avatarRow}>
            {currentAvatarUrl ? (
              <img
                src={currentAvatarUrl}
                alt={user.name}
                className={styles.avatarPreview}
              />
            ) : (
              <Avatar src={null} name={user.name} size={80} />
            )}
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
            >
              {t('common:change', 'Change')}
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleAvatarChange}
              className={styles.hiddenInput}
            />
          </div>
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="name">{t('name')}</label>
          <input
            id="name"
            type="text"
            className={styles.input}
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>

        {error && <p className={styles.error}>{error}</p>}

        <div className={styles.actions}>
          <Button type="submit" loading={saving}>
            {t('common:save', 'Save')}
          </Button>
          <Button type="button" variant="ghost" onClick={() => navigate('/profile')}>
            {t('common:cancel', 'Cancel')}
          </Button>
        </div>
      </form>
    </div>
  );
}
