import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import StarRating from '../common/StarRating';
import Button from '../common/Button';
import styles from './ReviewForm.module.css';

interface ReviewFormProps {
  onSubmit: (score: number, comment: string) => Promise<void>;
}

export default function ReviewForm({ onSubmit }: ReviewFormProps) {
  const { t } = useTranslation('profile');
  const [score, setScore] = useState(0);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (score === 0) return;
    setSubmitting(true);
    try {
      await onSubmit(score, comment);
      setScore(0);
      setComment('');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <h3 className={styles.title}>{t('leaveReview')}</h3>
      <StarRating value={score} onChange={setScore} size="md" />
      <textarea
        className={styles.textarea}
        placeholder={t('reviewPlaceholder')}
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        rows={3}
      />
      <Button type="submit" loading={submitting} disabled={score === 0}>
        {t('submitReview')}
      </Button>
    </form>
  );
}
