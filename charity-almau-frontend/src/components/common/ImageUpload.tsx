import React, { useRef, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import styles from './ImageUpload.module.css';

interface ImageUploadProps {
  images: File[];
  existingUrls?: string[];
  onChange: (files: File[]) => void;
  onRemoveExisting?: (url: string) => void;
  onFirstImage?: (file: File) => void;
  maxImages?: number;
}

const ImageUpload: React.FC<ImageUploadProps> = ({
  images,
  existingUrls = [],
  onChange,
  onRemoveExisting,
  onFirstImage,
  maxImages = 5,
}) => {
  const { t } = useTranslation();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const totalCount = images.length + existingUrls.length;

  const addFiles = useCallback(
    (files: FileList) => {
      const arr = Array.from(files).filter((f) => f.type.startsWith('image/'));
      const available = maxImages - totalCount;
      const toAdd = arr.slice(0, available);
      if (toAdd.length === 0) return;

      const isFirst = totalCount === 0;
      const newImages = [...images, ...toAdd];
      onChange(newImages);

      if (isFirst && onFirstImage) {
        onFirstImage(toAdd[0]);
      }
    },
    [images, totalCount, maxImages, onChange, onFirstImage]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      if (e.dataTransfer.files) addFiles(e.dataTransfer.files);
    },
    [addFiles]
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) addFiles(e.target.files);
    e.target.value = '';
  };

  const removeNew = (index: number) => {
    const updated = images.filter((_, i) => i !== index);
    onChange(updated);
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.previews}>
        {existingUrls.map((url) => (
          <div key={url} className={styles.preview}>
            <img src={url} alt="" className={styles.previewImg} />
            {onRemoveExisting && (
              <button
                type="button"
                className={styles.removeBtn}
                onClick={() => onRemoveExisting(url)}
              >
                ✕
              </button>
            )}
          </div>
        ))}
        {images.map((file, i) => (
          <div key={`${file.name}-${i}`} className={styles.preview}>
            <img
              src={URL.createObjectURL(file)}
              alt=""
              className={styles.previewImg}
            />
            <button
              type="button"
              className={styles.removeBtn}
              onClick={() => removeNew(i)}
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      {totalCount < maxImages && (
        <div
          className={`${styles.dropzone} ${dragActive ? styles.dropzoneActive : ''}`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <span className={styles.dropIcon}>+</span>
          <span className={styles.dropText}>
            {t('common:imageUpload', 'Перетащите фото или нажмите')}
          </span>
          <span className={styles.dropHint}>
            {totalCount}/{maxImages}
          </span>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            multiple
            onChange={handleFileChange}
            className={styles.hiddenInput}
          />
        </div>
      )}
    </div>
  );
};

export default ImageUpload;
