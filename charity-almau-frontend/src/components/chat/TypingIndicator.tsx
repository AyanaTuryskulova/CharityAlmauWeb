import { useTranslation } from 'react-i18next';
import styles from './TypingIndicator.module.css';

interface TypingIndicatorProps {
  name: string;
}

export default function TypingIndicator({ name }: TypingIndicatorProps) {
  const { t } = useTranslation('chat');

  return (
    <div className={styles.wrapper}>
      <div className={styles.dots}>
        <span className={styles.dot} />
        <span className={styles.dot} />
        <span className={styles.dot} />
      </div>
      <span className={styles.text}>{t('typing', { name })}</span>
    </div>
  );
}
