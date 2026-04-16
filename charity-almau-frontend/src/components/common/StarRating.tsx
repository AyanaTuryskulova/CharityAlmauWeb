import React, { useState } from 'react';
import styles from './StarRating.module.css';

interface StarRatingProps {
  value: number;
  onChange?: (value: number) => void;
  size?: 'sm' | 'md' | 'lg';
  readonly?: boolean;
}

const StarRating: React.FC<StarRatingProps> = ({
  value,
  onChange,
  size = 'md',
  readonly = false,
}) => {
  const [hovered, setHovered] = useState(0);

  const stars = [1, 2, 3, 4, 5];

  return (
    <div className={`${styles.wrapper} ${styles[size]}`}>
      {stars.map((star) => (
        <span
          key={star}
          className={`${styles.star} ${
            star <= (hovered || value) ? styles.filled : styles.empty
          } ${readonly ? styles.readonly : styles.interactive}`}
          onClick={() => !readonly && onChange?.(star)}
          onMouseEnter={() => !readonly && setHovered(star)}
          onMouseLeave={() => !readonly && setHovered(0)}
        >
          ★
        </span>
      ))}
    </div>
  );
};

export default StarRating;
