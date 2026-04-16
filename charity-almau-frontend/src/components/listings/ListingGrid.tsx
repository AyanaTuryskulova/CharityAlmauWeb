import type { Listing } from '../../types/listing';
import ListingCard from './ListingCard';
import styles from './ListingGrid.module.css';

interface ListingGridProps {
  listings: Listing[];
  onFavoriteToggle?: (id: string, isFavorited: boolean) => void;
  showStatus?: boolean;
  showActions?: boolean;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export default function ListingGrid({
  listings,
  onFavoriteToggle,
  showStatus,
  showActions,
  onEdit,
  onDelete,
}: ListingGridProps) {
  return (
    <div className={styles.grid}>
      {listings.map((listing) => (
        <ListingCard
          key={listing.id}
          listing={listing}
          onFavoriteToggle={onFavoriteToggle}
          showStatus={showStatus}
          showActions={showActions}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}
