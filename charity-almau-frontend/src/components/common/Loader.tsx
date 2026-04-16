import React from 'react';
import styles from './Loader.module.css';

interface LoaderProps {
  size?: 'sm' | 'md' | 'lg';
  fullPage?: boolean;
}

const Loader: React.FC<LoaderProps> = ({ size = 'md', fullPage = false }) => {
  if (fullPage) {
    return (
      <div className={styles.fullPage}>
        <div className={`${styles.spinner} ${styles[size]}`} />
      </div>
    );
  }

  return <div className={`${styles.spinner} ${styles[size]}`} />;
};

export default Loader;
