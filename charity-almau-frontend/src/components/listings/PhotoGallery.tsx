import { useState } from 'react';
import { getImageUrl } from '../../constants';
import styles from './PhotoGallery.module.css';

interface PhotoGalleryProps {
  images: string[];
}

export default function PhotoGallery({ images }: PhotoGalleryProps) {
  const [active, setActive] = useState(0);

  if (images.length === 0) {
    return <div className={styles.placeholder} />;
  }

  return (
    <div className={styles.gallery}>
      <div className={styles.main}>
        <img
          src={getImageUrl(images[active])}
          alt=""
          className={styles.mainImage}
        />
      </div>
      {images.length > 1 && (
        <div className={styles.thumbs}>
          {images.map((img, i) => (
            <button
              key={i}
              className={`${styles.thumb} ${i === active ? styles.thumbActive : ''}`}
              onClick={() => setActive(i)}
            >
              <img src={getImageUrl(img)} alt="" className={styles.thumbImg} />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
