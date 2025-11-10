// 新概念英语课文数据
export const lessonsData = {
  book1: [
    {
      id: 1,
      title: 'Lesson 1 Excuse me!',
      titleCn: '第1课 对不起！',
      sentences: [
        { en: 'Excuse me!', cn: '对不起！', audio: '' },
        { en: 'Yes?', cn: '什么事？', audio: '' },
        { en: 'Is this your handbag?', cn: '这是您的手提包吗？', audio: '' },
        { en: 'Pardon?', cn: '对不起，请再说一遍。', audio: '' },
        { en: 'Is this your handbag?', cn: '这是您的手提包吗？', audio: '' },
        { en: 'Yes, it is.', cn: '是的，是我的。', audio: '' },
        { en: 'Thank you very much.', cn: '非常感谢！', audio: '' },
      ],
    },
    {
      id: 2,
      title: 'Lesson 2 Is this your...?',
      titleCn: '第2课 这是你的...吗？',
      sentences: [
        { en: 'Is this your pen?', cn: '这是你的钢笔吗？', audio: '' },
        { en: 'Yes, it is.', cn: '是的，是我的。', audio: '' },
        { en: 'Is this your pencil?', cn: '这是你的铅笔吗？', audio: '' },
        { en: 'Yes, it is.', cn: '是的，是我的。', audio: '' },
        { en: 'Is this your book?', cn: '这是你的书吗？', audio: '' },
        { en: 'Yes, it is.', cn: '是的，是我的。', audio: '' },
      ],
    },
    {
      id: 3,
      title: 'Lesson 3 Sorry, sir.',
      titleCn: '第3课 对不起，先生。',
      sentences: [
        { en: 'My coat and my umbrella please.', cn: '请把我的大衣和伞拿给我。', audio: '' },
        { en: 'Here is my ticket.', cn: '这是我（寄存东西）的牌子。', audio: '' },
        { en: 'Thank you, sir.', cn: '谢谢，先生。', audio: '' },
        { en: 'Number five.', cn: '是5号。', audio: '' },
        { en: "Here's your umbrella and your coat.", cn: '这是您的伞和大衣。', audio: '' },
        { en: 'This is not my umbrella.', cn: '这不是我的伞。', audio: '' },
        { en: 'Sorry sir.', cn: '对不起，先生。', audio: '' },
        { en: 'Is this your umbrella?', cn: '这把伞是您的吗？', audio: '' },
        { en: 'No, it is not.', cn: '不，不是！', audio: '' },
        { en: 'Is this it?', cn: '这把是吗？', audio: '' },
        { en: 'Yes, it is.', cn: '是，是这把。', audio: '' },
        { en: 'Thank you very much.', cn: '非常感谢。', audio: '' },
      ],
    },
    // 更多课文...
    ...Array.from({ length: 141 }, (_, i) => ({
      id: i + 4,
      title: `Lesson ${i + 4}`,
      titleCn: `第${i + 4}课`,
      sentences: [
        { en: 'Sample sentence 1', cn: '示例句子1', audio: '' },
        { en: 'Sample sentence 2', cn: '示例句子2', audio: '' },
      ],
    })),
  ],
  book2: [
    {
      id: 1,
      title: 'Lesson 1 A private conversation',
      titleCn: '第1课 私人谈话',
      sentences: [
        { en: 'Last week I went to the theatre.', cn: '上星期我去看戏。', audio: '' },
        { en: 'I had a very good seat.', cn: '我的座位很好。', audio: '' },
        { en: 'The play was very interesting.', cn: '戏很有意思。', audio: '' },
        { en: "I did not enjoy it.", cn: '但我却无法欣赏。', audio: '' },
      ],
    },
    ...Array.from({ length: 95 }, (_, i) => ({
      id: i + 2,
      title: `Lesson ${i + 2}`,
      titleCn: `第${i + 2}课`,
      sentences: [
        { en: 'Sample sentence 1', cn: '示例句子1', audio: '' },
        { en: 'Sample sentence 2', cn: '示例句子2', audio: '' },
      ],
    })),
  ],
  book3: [
    {
      id: 1,
      title: 'Lesson 1 A Puma at large',
      titleCn: '第1课 逃遁的美洲狮',
      sentences: [
        { en: 'Pumas are large, cat-like animals which are found in America.', cn: '美洲狮是一种体形似猫的大动物，产于美洲。', audio: '' },
        { en: 'When reports came into London Zoo that a wild puma had been spotted forty-five miles south of London, they were not taken seriously.', cn: '当伦敦动物园接到报告说，在伦敦以南45英里处发现一只美洲狮时，这些报告并没有受到重视。', audio: '' },
      ],
    },
    ...Array.from({ length: 59 }, (_, i) => ({
      id: i + 2,
      title: `Lesson ${i + 2}`,
      titleCn: `第${i + 2}课`,
      sentences: [
        { en: 'Sample sentence 1', cn: '示例句子1', audio: '' },
        { en: 'Sample sentence 2', cn: '示例句子2', audio: '' },
      ],
    })),
  ],
  book4: [
    {
      id: 1,
      title: 'Lesson 1 Finding fossil man',
      titleCn: '第1课 发现化石人',
      sentences: [
        { en: 'We can read of things that happened 5,000 years ago in the Near East, where people first learned to write.', cn: '我们从书籍中可读到5,000年前近东发生的事情，那里的人最早学会了写字。', audio: '' },
        { en: 'But there are some parts of the world where even now people cannot write.', cn: '但直到现在，世界上有些地方，人们还不会书写。', audio: '' },
      ],
    },
    ...Array.from({ length: 47 }, (_, i) => ({
      id: i + 2,
      title: `Lesson ${i + 2}`,
      titleCn: `第${i + 2}课`,
      sentences: [
        { en: 'Sample sentence 1', cn: '示例句子1', audio: '' },
        { en: 'Sample sentence 2', cn: '示例句子2', audio: '' },
      ],
    })),
  ],
};

export const booksInfo = [
  {
    id: 'book1',
    title: '新概念英语第一册',
    subtitle: 'First Things First',
    description: '英语初阶',
    lessons: 144,
  },
  {
    id: 'book2',
    title: '新概念英语第二册',
    subtitle: 'Practice and Progress',
    description: '实践与进步',
    lessons: 96,
  },
  {
    id: 'book3',
    title: '新概念英语第三册',
    subtitle: 'Developing Skills',
    description: '培养技能',
    lessons: 60,
  },
  {
    id: 'book4',
    title: '新概念英语第四册',
    subtitle: 'Fluency in English',
    description: '流利英语',
    lessons: 48,
  },
];
