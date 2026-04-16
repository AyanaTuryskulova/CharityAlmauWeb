import { useState, useRef, useEffect } from 'react';
import { Link, NavLink, useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext';
import { useChat } from '../../contexts/ChatContext';
import Avatar from '../common/Avatar';
import styles from './Header.module.css';

export default function Header() {
  const { t } = useTranslation();
  const { user, isAdmin, logout } = useAuth();
  const { totalUnread } = useChat();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [search, setSearch] = useState(searchParams.get('search') ?? '');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && search.trim()) {
      navigate(`/?search=${encodeURIComponent(search.trim())}`);
    }
  };

  const handleLogout = () => {
    setDropdownOpen(false);
    logout();
    navigate('/login');
  };

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `${styles.navLink} ${isActive ? styles.navLinkActive : ''}`;

  return (
    <header className={styles.header}>
      <Link to="/" className={styles.logo}>
        <img src="/logo-horizontal.svg" alt="Charity AlmaU" className={styles.logoHorizontal} />
        <img src="/logo-icon.svg" alt="Charity AlmaU" className={styles.logoIcon} />
      </Link>

      <nav className={styles.nav}>
        <NavLink to="/" end className={navLinkClass}>
          {t('nav.catalog')}
        </NavLink>
        <NavLink to="/my-listings" className={navLinkClass}>
          {t('nav.myListings')}
        </NavLink>
        <NavLink to="/requests" className={navLinkClass}>
          {t('nav.requests')}
        </NavLink>
        <NavLink to="/chats" className={navLinkClass}>
          {t('nav.chats')}
          {totalUnread > 0 && <span className={styles.chatBadge}>{totalUnread}</span>}
        </NavLink>
      </nav>

      <div className={styles.searchWrap}>
        <input
          type="text"
          className={styles.searchInput}
          placeholder={t('search.placeholder')}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={handleSearch}
        />
      </div>

      <button className={styles.addBtn} onClick={() => navigate('/listings/new')}>
        {t('nav.addListing')}
      </button>

      {user && (
        <div className={styles.userMenu} ref={dropdownRef}>
          <button
            className={styles.userMenuBtn}
            onClick={() => setDropdownOpen(!dropdownOpen)}
          >
            <Avatar src={user.avatarUrl} name={user.name} size={34} />
          </button>

          {dropdownOpen && (
            <div className={styles.dropdown}>
              <Link
                to="/profile"
                className={styles.dropdownLink}
                onClick={() => setDropdownOpen(false)}
              >
                {t('nav.profile')}
              </Link>
              <Link
                to="/favorites"
                className={styles.dropdownLink}
                onClick={() => setDropdownOpen(false)}
              >
                {t('nav.favorites')}
              </Link>
              {isAdmin && (
                <Link
                  to="/admin"
                  className={styles.dropdownLink}
                  onClick={() => setDropdownOpen(false)}
                >
                  {t('nav.admin')}
                </Link>
              )}
              <div className={styles.dropdownDivider} />
              <button className={styles.logoutBtn} onClick={handleLogout}>
                {t('nav.logout')}
              </button>
            </div>
          )}
        </div>
      )}
    </header>
  );
}
