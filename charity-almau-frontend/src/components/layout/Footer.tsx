import { useTranslation } from 'react-i18next';
import LanguageSwitcher from '../common/LanguageSwitcher';
import styles from './Footer.module.css';

export default function Footer() {
  const { t } = useTranslation();

  return (
    <footer className={styles.footer}>
      <span className={styles.copyright}>{t('footer.copyright')}</span>
      <div className={styles.links}>
        <a href="#" className={styles.link}>{t('footer.about')}</a>
        <a href="#" className={styles.link}>{t('footer.contact')}</a>
        <LanguageSwitcher />
      </div>
    </footer>
  );
}
