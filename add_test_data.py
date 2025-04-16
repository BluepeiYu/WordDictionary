from database import Session, Word, Mnemonic

def add_sample_data():
    session = Session()
    
    # 清除旧数据
    session.query(Mnemonic).delete()
    session.query(Word).delete()
    
    # 添加测试单词
    ambition = Word(
        word="ambition",
        definition="n. 雄心，抱负",
        mnemonics=[
            Mnemonic(
                method_type="homonym",
                content="谐音：俺必胜 → 有雄心",
                votes=5
            ),
            Mnemonic(
                method_type="sentence",
                content="am(上午) + bit(一点) + ion(离子) → 上午一点离子实验激发雄心",
                votes=3
            )
        ]
    )
    
    session.add(ambition)
    session.commit()
    print("测试数据添加成功！")

if __name__ == '__main__':
    add_sample_data()