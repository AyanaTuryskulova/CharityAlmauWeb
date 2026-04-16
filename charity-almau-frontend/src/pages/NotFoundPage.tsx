import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import EmptyState from '../components/common/EmptyState';
import Button from '../components/common/Button';

export default function NotFoundPage() {
  const { t } = useTranslation();

  return (
    <EmptyState
      icon="🔍"
      title={t('notFound.title')}
      description={t('notFound.description')}
      action={
        <Link to="/">
          <Button variant="primary">{t('notFound.goHome')}</Button>
        </Link>
      }
    />
  );
}
