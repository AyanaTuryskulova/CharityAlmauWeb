# ER Diagram — CharityAlmau Web

## Основные сущности

### User
- username
- email
- password

### Product
- id
- name
- description
- user_id → FK(User)
- is_approved

### Chat
- id
- participants → M2M(User)
- created_at

### Message
- id
- chat_id → FK(Chat)
- sender_id → FK(User)
- text
- timestamp
- is_read

### RentItem
- id
- product_id → FK(Product)
- renter_id → FK(User)
- status (available, rented, returned)
- start_date
- end_date
