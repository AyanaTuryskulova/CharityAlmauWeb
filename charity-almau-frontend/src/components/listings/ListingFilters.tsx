import { useTranslation } from 'react-i18next';
import type { ListingType, Category } from '../../types/listing';
import styles from './ListingFilters.module.css';

interface ListingFiltersProps {
  activeType: string;
  onTypeChange: (type: string) => void;
  activeCategory?: string;
  onCategoryChange?: (category: string) => void;
}

const TYPES: ('' | ListingType)[] = ['', 'FREE', 'EXCHANGE', 'RENT'];
const CATEGORIES: ('' | Category)[] = ['', 'TEXTBOOKS', 'TECH', 'FURNITURE', 'CLOTHING', 'SPORTS', 'STATIONERY', 'OTHER'];

export default function ListingFilters({ activeType, onTypeChange, activeCategory = '', onCategoryChange }: ListingFiltersProps) {
  const { t } = useTranslation('listings');

  return (
    <div className={styles.wrapper}>
      <div className={styles.filters}>
        {TYPES.map((type) => (
          <button
            key={type}
            className={`${styles.filterBtn} ${activeType === type ? styles.active : ''}`}
            onClick={() => onTypeChange(type)}
          >
            {type === '' ? t('types.all') : t(`types.${type}`)}
          </button>
        ))}
      </div>

      {onCategoryChange && (
        <div className={styles.filters}>
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              className={`${styles.filterBtn} ${styles.categoryBtn} ${activeCategory === cat ? styles.activeCategory : ''}`}
              onClick={() => onCategoryChange(cat)}
            >
              {cat === '' ? t('types.all') : t(`categories.${cat}`)}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
