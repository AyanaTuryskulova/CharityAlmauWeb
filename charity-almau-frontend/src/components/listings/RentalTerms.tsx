import { useTranslation } from 'react-i18next';
import styles from './RentalTerms.module.css';

interface RentalTermsProps {
  pricePerDay: number;
}

export default function RentalTerms({ pricePerDay }: RentalTermsProps) {
  const { t } = useTranslation('listings');

  return (
    <div className={styles.wrapper}>
      <h4 className={styles.title}>{t('detail.rentalTerms')}</h4>
      <table className={styles.table}>
        <tbody>
          <tr>
            <td className={styles.period}>{t('detail.perDay')}</td>
            <td className={styles.price}>{pricePerDay} &#8376;</td>
          </tr>
          <tr>
            <td className={styles.period}>{t('detail.perWeek')}</td>
            <td className={styles.price}>{pricePerDay * 7} &#8376;</td>
          </tr>
          <tr>
            <td className={styles.period}>{t('detail.perMonth')}</td>
            <td className={styles.price}>{pricePerDay * 30} &#8376;</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
