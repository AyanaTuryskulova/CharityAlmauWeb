import React from 'react';
import { useTranslation } from 'react-i18next';
import Button from './Button';
import styles from './ErrorState.module.css';

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

const ErrorState: React.FC<ErrorStateProps> = ({ message, onRetry }) => {
  const { t } = useTranslation();

  return (
    <div className={styles.wrapper}>
      <span className={styles.icon}>⚠️</span>
      <h3 className={styles.title}>{t('errorState.title')}</h3>
      <p className={styles.description}>{message || t('errorState.description')}</p>
      {onRetry && (
        <div className={styles.action}>
          <Button variant="secondary" onClick={onRetry}>
            {t('errorState.retry')}
          </Button>
        </div>
      )}
    </div>
  );
};

export default ErrorState;
