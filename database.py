# database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# 声明性基类
Base = declarative_base()

class Word(Base):
    """ 单词数据表模型 """
    __tablename__ = 'words'
    
    id = Column(Integer, primary_key=True)
    word = Column(String(50), unique=True, nullable=False, comment="单词文本")
    definition = Column(Text, comment="词典释义")
    
    # 与记忆方法建立一对多关系
    mnemonics = relationship(
        'Mnemonic', 
        backref='word', 
        cascade='all, delete-orphan',
        order_by="desc(Mnemonic.votes)"
    )

class Mnemonic(Base):
    """ 记忆方法数据表模型 """
    __tablename__ = 'mnemonics'
    
    id = Column(Integer, primary_key=True)
    word_id = Column(
        Integer, 
        ForeignKey('words.id', ondelete='CASCADE'), 
        nullable=False,
        comment="关联的单词ID"
    )
    method_type = Column(
        String(20), 
        comment="记忆法类型", 
        default='general'
    )
    content = Column(Text, nullable=False, comment="具体内容")
    votes = Column(
        Integer, 
        default=0, 
        nullable=False, 
        comment="点赞数量"
    )

# 数据库连接配置
engine = create_engine(
    'sqlite:///dictionary.db', 
    echo=False,  # 设为True可查看SQL日志
    connect_args={'check_same_thread': False}  # 允许多线程
)

# 会话工厂
Session = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

def initialize_db():
    """ 初始化数据库表结构 """
    Base.metadata.create_all(engine)

def save_word(session, word_str, definition_data):
    """
    保存单词到数据库
    :param session: 数据库会话
    :param word_str: 要保存的单词
    :param definition_data: 包含释义的字典（来自爬虫）
    :return: Word对象
    """
    try:
        # 检查是否已存在
        existing_word = session.query(Word).filter_by(word=word_str).first()
        if existing_word:
            return existing_word

        # 创建新单词条目
        new_word = Word(
            word=word_str,
            definition="\n".join(definition_data.get('definitions', []))
        )

        # 添加关联的例句（如果需要可以扩展）
        # for ex in definition_data.get('examples', []):
        #     new_mnemonic = Mnemonic(
        #         method_type='example',
        #         content=ex
        #     )
        #     new_word.mnemonics.append(new_mnemonic)

        session.add(new_word)
        session.commit()
        return new_word

    except Exception as e:
        session.rollback()
        raise RuntimeError(f"保存单词失败: {str(e)}")

if __name__ == '__main__':
    # 初始化数据库（仅首次运行）
    print("正在初始化数据库...")
    initialize_db()
    print("数据库表已创建")