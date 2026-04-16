import { useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { useChat } from '../contexts/ChatContext';
import { useListing } from '../hooks/useListing';
import { chatService } from '../services/chatService';
import { requestsService } from '../services/requestsService';
import PhotoGallery from '../components/listings/PhotoGallery';
import SellerCard from '../components/listings/SellerCard';
import RentalTerms from '../components/listings/RentalTerms';
import SimilarItems from '../components/listings/SimilarItems';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import Loader from '../components/common/Loader';
import EmptyState from '../components/common/EmptyState';
import styles from './ListingDetailPage.module.css';

export default function ListingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation('listings');
  const { t: tc } = useTranslation();
  const { user } = useAuth();
  const { sendMessage, refreshRooms } = useChat();
  const { listing, loading, error } = useListing(id);

  const [actionLoading, setActionLoading] = useState<'respond' | 'write' | null>(null);
  const [actionMsg, setActionMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Chat popup state
  const [chatOpen, setChatOpen] = useState(false);
  const [chatRoomId, setChatRoomId] = useState<string | null>(null);
  const [chatText, setChatText] = useState('');
  const [chatSending, setChatSending] = useState(false);
  const [chatSent, setChatSent] = useState(false);

  const handleWrite = async () => {
    if (!listing) return;
    setActionLoading('write');
    setActionMsg(null);
    try {
      const room = await chatService.createRoom(listing.userId, listing.id);
      setChatRoomId(room.id);
      setChatOpen(true);
      setChatSent(false);
      setChatText('');
    } catch {
      setActionMsg({ type: 'error', text: 'Не удалось открыть чат' });
    } finally {
      setActionLoading(null);
    }
  };

  const handleSendChat = useCallback(async () => {
    if (!chatRoomId || !chatText.trim()) return;
    setChatSending(true);
    try {
      sendMessage(chatRoomId, chatText.trim());
      setChatSent(true);
      setChatText('');
      await refreshRooms();
    } catch {
      // silent
    } finally {
      setChatSending(false);
    }
  }, [chatRoomId, chatText, sendMessage, refreshRooms]);

  const handleRespond = async () => {
    if (!listing) return;
    setActionLoading('respond');
    setActionMsg(null);
    try {
      await requestsService.createRequest(listing.id);
      setActionMsg({ type: 'success', text: 'Отклик отправлен!' });
    } catch (err: unknown) {
      const code = (err as { code?: string })?.code;
      let text = 'Не удалось отправить отклик';
      if (code === 'REQUEST_ALREADY_EXISTS') text = 'Вы уже откликались на это объявление';
      if (code === 'REQUEST_OWN_LISTING') text = 'Нельзя откликнуться на своё объявление';
      setActionMsg({ type: 'error', text });
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) return <Loader fullPage />;
  if (error || !listing) {
    return (
      <EmptyState
        icon="📦"
        title={t('detail.notFound')}
        description={t('detail.notFoundDesc')}
        action={<Button onClick={() => navigate('/')}>{tc('back')}</Button>}
      />
    );
  }

  const isOwner = user?.id === listing.userId;
  const typeVariant = listing.type === 'FREE' ? 'accent' : 'primary';

  return (
    <div className={styles.page}>
      <button className={styles.backBtn} onClick={() => navigate(-1)}>
        &larr; {tc('back')}
      </button>

      <div className={styles.layout}>
        <div className={styles.left}>
          <PhotoGallery images={listing.images} />
        </div>

        <div className={styles.right}>
          <div className={styles.badges}>
            <Badge variant={typeVariant}>{t(`types.${listing.type}`)}</Badge>
            <span className={styles.categoryLabel}>{t(`categories.${listing.category}`)}</span>
          </div>

          <h1 className={styles.title}>{listing.title}</h1>

          {listing.type === 'RENT' && listing.rentalPrice != null && (
            <div className={styles.price}>{listing.rentalPrice} &#8376; / {t('detail.perDay')}</div>
          )}
          {listing.type === 'FREE' && (
            <div className={styles.priceAccent}>{t('detail.free')}</div>
          )}
          {listing.type === 'EXCHANGE' && listing.exchangeWish && (
            <div className={styles.exchangeWish}>
              <span className={styles.exchangeLabel}>{t('detail.exchangeWish')}:</span> {listing.exchangeWish}
            </div>
          )}

          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>{t('detail.description')}</h3>
            <p className={styles.desc}>{listing.description}</p>
          </div>

          {listing.condition && (
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>{t('detail.condition')}</h3>
              <p className={styles.desc}>{listing.condition}</p>
            </div>
          )}

          {listing.type === 'RENT' && listing.rentalPrice != null && (
            <RentalTerms pricePerDay={listing.rentalPrice} />
          )}

          {listing.status === 'REJECTED' && listing.rejectReason && (
            <div className={styles.rejectBox}>
              <strong>{t('detail.rejectReason')}:</strong> {listing.rejectReason}
            </div>
          )}

          {!isOwner && (
            <div className={styles.actionBtns}>
              <Button variant="primary" size="lg" onClick={handleRespond} loading={actionLoading === 'respond'}>
                {t('detail.respond')}
              </Button>
              <Button variant="secondary" size="lg" onClick={handleWrite} loading={actionLoading === 'write'}>
                {t('detail.write')}
              </Button>
              {actionMsg && (
                <p className={actionMsg.type === 'success' ? styles.successMsg : styles.errorMsg}>
                  {actionMsg.text}
                </p>
              )}
            </div>
          )}

          {isOwner && (
            <div className={styles.actionBtns}>
              <Button variant="secondary" onClick={() => navigate(`/listings/${listing.id}/edit`)}>
                {tc('edit')}
              </Button>
            </div>
          )}

          <SellerCard user={listing.user} />
        </div>
      </div>

      <SimilarItems listingId={listing.id} />

      {/* Chat popup */}
      <Modal isOpen={chatOpen} onClose={() => setChatOpen(false)} title={`Сообщение — ${listing.user.name}`}>
        <div className={styles.chatPopup}>
          <div className={styles.chatListingInfo}>
            {listing.images[0] && (
              <img src={`${import.meta.env.VITE_API_URL}${listing.images[0]}`} alt="" className={styles.chatListingImg} />
            )}
            <span className={styles.chatListingTitle}>{listing.title}</span>
          </div>

          {chatSent ? (
            <div className={styles.chatSentBox}>
              <p className={styles.chatSentText}>Сообщение отправлено!</p>
              <div className={styles.chatSentActions}>
                <Button variant="secondary" onClick={() => navigate(`/chats/${chatRoomId}`)}>
                  Перейти в чат
                </Button>
                <Button variant="primary" onClick={() => { setChatSent(false); setChatText(''); }}>
                  Написать ещё
                </Button>
              </div>
            </div>
          ) : (
            <>
              <textarea
                className={styles.chatTextarea}
                rows={3}
                placeholder="Напишите сообщение..."
                value={chatText}
                onChange={(e) => setChatText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendChat();
                  }
                }}
              />
              <Button
                variant="primary"
                onClick={handleSendChat}
                loading={chatSending}
                disabled={!chatText.trim()}
              >
                Отправить
              </Button>
            </>
          )}
        </div>
      </Modal>
    </div>
  );
}
