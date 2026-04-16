import { Link } from 'react-router-dom';
import type { Rating } from '../../types/rating';
import Avatar from '../common/Avatar';
import StarRating from '../common/StarRating';
import styles from './ReviewCard.module.css';

interface ReviewCardProps {
  rating: Rating;
}

export default function ReviewCard({ rating }: ReviewCardProps) {
  const date = new Date(rating.createdAt).toLocaleDateString();

  return (
    <div className={styles.card}>
      <div className={styles.top}>
        <Link to={`/users/${rating.author.id}`} className={styles.author}>
          <Avatar src={rating.author.avatarUrl} name={rating.author.name} size={36} />
          <span className={styles.authorName}>{rating.author.name}</span>
        </Link>
        <span className={styles.date}>{date}</span>
      </div>

      <StarRating value={rating.score} readonly size="sm" />

      {rating.comment && <p className={styles.comment}>{rating.comment}</p>}
    </div>
  );
}
