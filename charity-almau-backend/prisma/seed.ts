import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  console.log('Seeding database...');

  // Clean existing data
  await prisma.message.deleteMany();
  await prisma.chatRoom.deleteMany();
  await prisma.rating.deleteMany();
  await prisma.request.deleteMany();
  await prisma.favorite.deleteMany();
  await prisma.listing.deleteMany();
  await prisma.user.deleteMany();

  // 1. Create admin
  const admin = await prisma.user.create({
    data: {
      email: 'admin@almau.edu.kz',
      name: 'Admin AlmaU',
      role: 'ADMIN',
    },
  });

  // 2. Create 5 students
  const students = await Promise.all(
    [
      { email: 'student1@almau.edu.kz', name: 'Айдана Серикова' },
      { email: 'student2@almau.edu.kz', name: 'Дамир Касымов' },
      { email: 'student3@almau.edu.kz', name: 'Мадина Нурланова' },
      { email: 'student4@almau.edu.kz', name: 'Арман Жумабаев' },
      { email: 'student5@almau.edu.kz', name: 'Камила Ахметова' },
    ].map((data) => prisma.user.create({ data })),
  );

  const [s1, s2, s3, s4, s5] = students;

  // 3. Create 15 listings (5 FREE, 5 EXCHANGE, 5 RENT)
  const listings = await Promise.all([
    // FREE listings
    prisma.listing.create({
      data: {
        title: 'Учебник по макроэкономике',
        description: 'Mankiw, 10th edition. В хорошем состоянии, немного подчёркнуто карандашом.',
        type: 'FREE',
        category: 'TEXTBOOKS',
        status: 'APPROVED',
        condition: 'Хорошее',
        images: ['/uploads/seed1.webp'],
        userId: s1.id,
      },
    }),
    prisma.listing.create({
      data: {
        title: 'Набор маркеров Stabilo',
        description: '12 цветов, все пишут. Просто не нужны больше.',
        type: 'FREE',
        category: 'STATIONERY',
        status: 'APPROVED',
        condition: 'Отличное',
        images: ['/uploads/seed2.webp'],
        userId: s2.id,
      },
    }),
    prisma.listing.create({
      data: {
        title: 'Футболка AlmaU Fest 2025',
        description: 'Размер M, надевали один раз на мероприятие.',
        type: 'FREE',
        category: 'CLOTHING',
        status: 'APPROVED',
        condition: 'Отличное',
        images: ['/uploads/seed3.webp'],
        userId: s3.id,
      },
    }),
    prisma.listing.create({
      data: {
        title: 'Настольная лампа IKEA',
        description: 'Белая, LED. Работает отлично, переехал в другую комнату.',
        type: 'FREE',
        category: 'FURNITURE',
        status: 'APPROVED',
        condition: 'Хорошее',
        images: ['/uploads/seed4.webp'],
        userId: s4.id,
      },
    }),
    prisma.listing.create({
      data: {
        title: 'Скакалка для фитнеса',
        description: 'Обычная скакалка, в хорошем состоянии.',
        type: 'FREE',
        category: 'SPORTS',
        status: 'APPROVED',
        condition: 'Хорошее',
        images: ['/uploads/seed5.webp'],
        userId: s5.id,
      },
    }),

    // EXCHANGE listings
    prisma.listing.create({
      data: {
        title: 'Калькулятор Casio FX-991ES',
        description: 'Научный калькулятор, полностью рабочий.',
        type: 'EXCHANGE',
        category: 'TECH',
        status: 'APPROVED',
        condition: 'Хорошее',
        exchangeWish: 'Флешка 64GB или наушники',
        images: ['/uploads/seed6.webp'],
        userId: s1.id,
      },
    }),
    prisma.listing.create({
      data: {
        title: 'Учебник Финансовый менеджмент',
        description: 'Brigham & Houston, 15th ed. Подчёркнуты ключевые моменты.',
        type: 'EXCHANGE',
        category: 'TEXTBOOKS',
        status: 'APPROVED',
        condition: 'Удовлетворительное',
        exchangeWish: 'Любой учебник по маркетингу',
        images: ['/uploads/seed7.webp'],
        userId: s2.id,
      },
    }),
    prisma.listing.create({
      data: {
        title: 'Коврик для йоги',
        description: 'Фиолетовый, 6мм толщина. Почти новый.',
        type: 'EXCHANGE',
        category: 'SPORTS',
        status: 'APPROVED',
        condition: 'Отличное',
        exchangeWish: 'Гантели или фитнес-резинки',
        images: ['/uploads/seed8.webp'],
        userId: s3.id,
      },
    }),
    prisma.listing.create({
      data: {
        title: 'Подставка для ноутбука',
        description: 'Алюминиевая, регулируемая высота. Пользовался семестр.',
        type: 'EXCHANGE',
        category: 'TECH',
        status: 'APPROVED',
        condition: 'Хорошее',
        exchangeWish: 'Беспроводная мышка',
        images: ['/uploads/seed9.webp'],
        userId: s4.id,
      },
    }),
    prisma.listing.create({
      data: {
        title: 'Толстовка Nike размер L',
        description: 'Серая, без дефектов. Просто не мой размер.',
        type: 'EXCHANGE',
        category: 'CLOTHING',
        status: 'APPROVED',
        condition: 'Отличное',
        exchangeWish: 'Толстовка размер M любая',
        images: ['/uploads/seed10.webp'],
        userId: s5.id,
      },
    }),

    // RENT listings
    prisma.listing.create({
      data: {
        title: 'Проектор Epson EB-S05',
        description: 'Для презентаций и фильмов. Сдаю на день/неделю.',
        type: 'RENT',
        category: 'TECH',
        status: 'APPROVED',
        condition: 'Хорошее',
        rentalPrice: 3000,
        images: ['/uploads/seed11.webp'],
        userId: s1.id,
      },
    }),
    prisma.listing.create({
      data: {
        title: 'Кресло офисное',
        description: 'Удобное кресло для учёбы. Сдаю на семестр.',
        type: 'RENT',
        category: 'FURNITURE',
        status: 'APPROVED',
        condition: 'Хорошее',
        rentalPrice: 1500,
        images: ['/uploads/seed12.webp'],
        userId: s2.id,
      },
    }),
    prisma.listing.create({
      data: {
        title: 'Гитара акустическая Yamaha F310',
        description: 'Отличный инструмент для начинающих. Аренда помесячно.',
        type: 'RENT',
        category: 'OTHER',
        status: 'APPROVED',
        condition: 'Хорошее',
        rentalPrice: 5000,
        images: ['/uploads/seed13.webp'],
        userId: s3.id,
      },
    }),
    prisma.listing.create({
      data: {
        title: 'Комплект учебников 1 курс Бизнес',
        description: '5 учебников по программе 1 курса. Аренда на семестр.',
        type: 'RENT',
        category: 'TEXTBOOKS',
        status: 'APPROVED',
        condition: 'Удовлетворительное',
        rentalPrice: 2000,
        images: ['/uploads/seed14.webp'],
        userId: s4.id,
      },
    }),
    prisma.listing.create({
      data: {
        title: 'Велосипед городской',
        description: 'Для передвижения по кампусу. Аренда по дням.',
        type: 'RENT',
        category: 'SPORTS',
        status: 'APPROVED',
        condition: 'Хорошее',
        rentalPrice: 2500,
        images: ['/uploads/seed15.webp'],
        userId: s5.id,
      },
    }),
  ]);

  // 4. Create some requests
  await Promise.all([
    prisma.request.create({
      data: {
        listingId: listings[0].id,
        senderId: s2.id,
        receiverId: s1.id,
        message: 'Привет! Очень нужен учебник по макре, можно забрать сегодня?',
      },
    }),
    prisma.request.create({
      data: {
        listingId: listings[1].id,
        senderId: s3.id,
        receiverId: s2.id,
        message: 'Маркеры ещё свободны?',
      },
    }),
    prisma.request.create({
      data: {
        listingId: listings[5].id,
        senderId: s4.id,
        receiverId: s1.id,
        message: 'У меня есть флешка 64GB Kingston, обменяемся?',
      },
    }),
    prisma.request.create({
      data: {
        listingId: listings[11].id,
        senderId: s5.id,
        receiverId: s2.id,
        message: 'Хочу арендовать кресло на 2 месяца, подойдёт?',
      },
    }),
  ]);

  // 5. Create chat rooms and messages
  const sortUsers = (a: string, b: string): [string, string] =>
    a < b ? [a, b] : [b, a];

  const [u1a, u2a] = sortUsers(s1.id, s2.id);
  const room1 = await prisma.chatRoom.create({
    data: { user1Id: u1a, user2Id: u2a, listingId: listings[0].id },
  });

  await prisma.message.createMany({
    data: [
      { text: 'Привет! Учебник по макре ещё доступен?', senderId: s2.id, chatRoomId: room1.id },
      { text: 'Да, можешь забрать в корпусе B', senderId: s1.id, chatRoomId: room1.id },
      { text: 'Супер, буду в 14:00!', senderId: s2.id, chatRoomId: room1.id },
    ],
  });

  const [u1b, u2b] = sortUsers(s3.id, s4.id);
  const room2 = await prisma.chatRoom.create({
    data: { user1Id: u1b, user2Id: u2b, listingId: listings[7].id },
  });

  await prisma.message.createMany({
    data: [
      { text: 'Привет! Коврик для йоги обменяешь на фитнес-резинки?', senderId: s4.id, chatRoomId: room2.id },
      { text: 'Привет, а какие резинки? Набор?', senderId: s3.id, chatRoomId: room2.id },
    ],
  });

  // 6. Create ratings
  await prisma.rating.create({
    data: {
      score: 5,
      comment: 'Отличный продавец, быстро договорились!',
      authorId: s2.id,
      targetId: s1.id,
      listingId: listings[0].id,
    },
  });

  await prisma.rating.create({
    data: {
      score: 4,
      comment: 'Всё хорошо, спасибо!',
      authorId: s4.id,
      targetId: s3.id,
      listingId: listings[7].id,
    },
  });

  await prisma.rating.create({
    data: {
      score: 5,
      comment: 'Очень приятный человек, рекомендую.',
      authorId: s1.id,
      targetId: s2.id,
    },
  });

  // Update user ratings
  for (const userId of [s1.id, s2.id, s3.id]) {
    const agg = await prisma.rating.aggregate({
      where: { targetId: userId },
      _avg: { score: true },
      _count: { score: true },
    });
    await prisma.user.update({
      where: { id: userId },
      data: {
        rating: agg._avg.score || 0,
        ratingCount: agg._count.score,
      },
    });
  }

  console.log('Seed completed!');
  console.log('  - 1 admin: admin@almau.edu.kz');
  console.log('  - 5 students: student1..5@almau.edu.kz');
  console.log('  - 15 listings (5 FREE, 5 EXCHANGE, 5 RENT)');
  console.log('  - 4 requests');
  console.log('  - 2 chat rooms with messages');
  console.log('  - 3 ratings');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
