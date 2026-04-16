import { getAvatarUrl } from '../../constants';
import styles from './Avatar.module.css';

interface AvatarProps {
  src: string | null;
  name: string;
  size?: number;
  className?: string;
}

export default function Avatar({ src, name, size = 36, className }: AvatarProps) {
  const url = getAvatarUrl(src);
  const fontSize = Math.round(size * 0.4);

  if (url) {
    return (
      <img
        src={url}
        alt={name}
        width={size}
        height={size}
        className={`${styles.avatar} ${className ?? ''}`}
      />
    );
  }

  return (
    <div
      className={`${styles.placeholder} ${className ?? ''}`}
      style={{ width: size, height: size, fontSize }}
    >
      {(name ?? '?').charAt(0)}
    </div>
  );
}
