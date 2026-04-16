import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { Listing, ListingType, Category } from '../../types/listing';
import { LISTING_TYPES, CATEGORIES, getImageUrl } from '../../constants';
import { aiService } from '../../services/aiService';
import ImageUpload from '../common/ImageUpload';
import Input from '../common/Input';
import Button from '../common/Button';
import styles from './ListingForm.module.css';

interface ListingFormProps {
  initialData?: Listing;
  onSubmit: (formData: FormData) => Promise<void>;
  loading?: boolean;
}

export default function ListingForm({ initialData, onSubmit, loading }: ListingFormProps) {
  const { t } = useTranslation('listings');

  const [title, setTitle] = useState(initialData?.title ?? '');
  const [description, setDescription] = useState(initialData?.description ?? '');
  const [type, setType] = useState<ListingType>(initialData?.type ?? 'FREE');
  const [category, setCategory] = useState<Category>(initialData?.category ?? 'OTHER');
  const [exchangeWish, setExchangeWish] = useState(initialData?.exchangeWish ?? '');
  const [rentalPrice, setRentalPrice] = useState(initialData?.rentalPrice?.toString() ?? '');
  const [condition, setCondition] = useState(initialData?.condition ?? '');
  const [images, setImages] = useState<File[]>([]);
  const [existingUrls, setExistingUrls] = useState<string[]>(
    initialData?.images?.map(getImageUrl) ?? []
  );
  const [aiHint, setAiHint] = useState('');

  const handleFirstImage = async (file: File) => {
    try {
      const result = await aiService.analyzeImage(file);
      if (result.confidence > 0.5) {
        if (!title) {
          setTitle(result.suggestedTitle);
          setAiHint(t('create.aiSuggestion'));
        }
        if (CATEGORIES.includes(result.suggestedCategory as Category)) {
          setCategory(result.suggestedCategory as Category);
        }
      }
    } catch {
      // AI is optional — just ignore errors
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const formData = new FormData();
    formData.append('title', title);
    formData.append('description', description);
    formData.append('type', type);
    formData.append('category', category);
    if (condition) formData.append('condition', condition);
    if (type === 'EXCHANGE') formData.append('exchangeWish', exchangeWish);
    if (type === 'RENT') formData.append('rentalPrice', rentalPrice);

    images.forEach((file) => formData.append('images', file));

    if (initialData) {
      const kept = existingUrls.map((url) => {
        const path = url.replace(import.meta.env.VITE_API_URL, '');
        return path;
      });
      formData.append('existingImages', JSON.stringify(kept));
    }

    await onSubmit(formData);
  };

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <ImageUpload
        images={images}
        existingUrls={existingUrls}
        onChange={setImages}
        onRemoveExisting={(url) => setExistingUrls((prev) => prev.filter((u) => u !== url))}
        onFirstImage={!initialData ? handleFirstImage : undefined}
      />

      <div className={styles.field}>
        <Input
          label={`${t('create.name')}${aiHint ? ` ${aiHint}` : ''}`}
          value={title}
          onChange={(e) => { setTitle(e.target.value); setAiHint(''); }}
          required
        />
      </div>

      <div className={styles.field}>
        <label className={styles.label}>{t('create.description')}</label>
        <textarea
          className={styles.textarea}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={4}
          required
        />
      </div>

      <div className={styles.field}>
        <label className={styles.label}>{t('create.type')}</label>
        <div className={styles.radioGroup}>
          {LISTING_TYPES.map((lt) => (
            <label key={lt} className={`${styles.radio} ${type === lt ? styles.radioActive : ''}`}>
              <input
                type="radio"
                name="type"
                value={lt}
                checked={type === lt}
                onChange={() => setType(lt)}
                className={styles.radioInput}
              />
              {t(`types.${lt}`)}
            </label>
          ))}
        </div>
      </div>

      <div className={styles.field}>
        <label className={styles.label}>{t('create.category')}</label>
        <select
          className={styles.select}
          value={category}
          onChange={(e) => setCategory(e.target.value as Category)}
        >
          {CATEGORIES.map((cat) => (
            <option key={cat} value={cat}>
              {t(`categories.${cat}`)}
            </option>
          ))}
        </select>
      </div>

      {type === 'EXCHANGE' && (
        <div className={styles.field}>
          <Input
            label={t('create.exchangeWish')}
            value={exchangeWish}
            onChange={(e) => setExchangeWish(e.target.value)}
          />
        </div>
      )}

      {type === 'RENT' && (
        <div className={styles.field}>
          <Input
            label={t('create.rentalPrice')}
            type="number"
            min="0"
            value={rentalPrice}
            onChange={(e) => setRentalPrice(e.target.value)}
            required
          />
        </div>
      )}

      <div className={styles.field}>
        <Input
          label={t('create.condition')}
          value={condition}
          onChange={(e) => setCondition(e.target.value)}
        />
      </div>

      <Button type="submit" variant="primary" size="lg" loading={loading} fullWidth>
        {initialData ? t('create.saveChanges') : t('create.publish')}
      </Button>
    </form>
  );
}
