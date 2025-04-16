# dictionary_app.py
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextBrowser, QPushButton, QListWidget, QListWidgetItem,
    QLabel, QDialog, QComboBox, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTextCodec
from database import Session, Word, Mnemonic, save_word
from spider import OnlineDictionarySpider

# 设置中文编码支持
QTextCodec.setCodecForLocale(QTextCodec.codecForName("UTF-8"))

class MnemonicItem(QWidget):
    """自定义记忆方法条目组件，包含点赞功能和内容显示"""
    vote_updated = pyqtSignal()  # 点赞更新信号，用于触发列表刷新

    def __init__(self, mnemonic, parent=None):
        """
        初始化记忆方法条目
        :param mnemonic: Mnemonic 数据库对象
        :param parent: 父组件
        """
        super().__init__(parent)
        self.mnemonic = mnemonic
        self.initUI()

    def initUI(self):
        """初始化界面布局和样式"""
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)  # 设置边距
        
        # 左侧投票区域布局
        vote_layout = QVBoxLayout()
        # 点赞按钮设置
        self.upvote_btn = QPushButton("▲")
        self.upvote_btn.setFixedSize(30, 30)
        self.upvote_btn.setStyleSheet("""
            QPushButton {
                background: #e9ecef;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #dee2e6;
            }
        """)
        self.upvote_btn.clicked.connect(self.upvote)
        
        # 点赞数显示标签
        self.vote_label = QLabel(str(self.mnemonic.votes))
        self.vote_label.setAlignment(Qt.AlignCenter)
        self.vote_label.setStyleSheet("color: #495057;")
        
        vote_layout.addWidget(self.upvote_btn)
        vote_layout.addWidget(self.vote_label)
        layout.addLayout(vote_layout)

        # 右侧内容区域布局
        content_layout = QVBoxLayout()
        # 记忆法类型标签
        self.method_label = QLabel(
            f"[{self.mnemonic.method_type}]",
            styleSheet="color: #6c757d; font-size: 12px;"  # 灰色小字样式
        )
        # 具体内容标签
        self.content_label = QLabel(self.mnemonic.content)
        self.content_label.setWordWrap(True)  # 启用自动换行
        self.content_label.setStyleSheet("font-size: 14px; color: #212529;")
        
        content_layout.addWidget(self.method_label)
        content_layout.addWidget(self.content_label)
        layout.addLayout(content_layout)
        
        self.setLayout(layout)
        self.setStyleSheet("background: #fff; border-radius: 8px;")  # 白色圆角背景

    def upvote(self):
        """处理点赞操作，更新数据库并刷新显示"""
        try:
            session = Session()
            session.add(self.mnemonic)
            self.mnemonic.votes += 1  # 点赞数+1
            session.commit()  # 提交到数据库
            self.vote_label.setText(str(self.mnemonic.votes))  # 更新显示
            self.vote_updated.emit()  # 发送刷新信号
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新失败: {str(e)}")
        finally:
            session.close()  # 确保关闭会话

class AddMnemonicDialog(QDialog):
    """添加记忆方法对话框，包含类型选择和内容输入"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加记忆方法")
        self.setFixedSize(400, 300)  # 固定对话框尺寸
        self.initUI()

    def initUI(self):
        """初始化对话框布局"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)  # 统一边距
        
        # 方法类型选择区域
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("方法类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["词根词缀", "谐音法", "联想法", "其他"])  # 预置分类
        self.type_combo.setStyleSheet("padding: 5px;")
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # 内容输入区域
        layout.addWidget(QLabel("具体内容:"))
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("请输入记忆方法...")
        self.content_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                min-height: 100px;  # 设置最小高度
            }
        """)
        layout.addWidget(self.content_input)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)  # 按钮间距
        # 提交按钮
        submit_btn = QPushButton("提交")
        submit_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)
        submit_btn.clicked.connect(self.validate_input)
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #5a6268;
            }
        """)
        cancel_btn.clicked.connect(self.reject)  # 直接关闭对话框
        
        btn_layout.addStretch()  # 添加弹性空间
        btn_layout.addWidget(submit_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def validate_input(self):
        """验证用户输入是否符合要求"""
        content = self.content_input.toPlainText().strip()
        if len(content) < 3:
            QMessageBox.warning(self, "警告", "内容至少需要3个字符！")
            return
        self.accept()  # 通过验证关闭对话框

    def get_data(self):
        """获取用户输入的标准化数据"""
        return {
            "method_type": self.type_combo.currentText(),
            "content": self.content_input.toPlainText().strip()
        }

class DictionaryApp(QMainWindow):
    """主应用程序窗口，包含核心功能逻辑"""
    def __init__(self):
        super().__init__()
        # 初始化数据库会话和爬虫
        self.session = Session()
        self.spider = OnlineDictionarySpider()
        self.current_word = None  # 当前显示的单词对象
        
        # 初始化界面和功能
        self.initUI()
        self.connect_signals()
        self.load_style()

    def initUI(self):
        """初始化主界面布局"""
        self.setWindowTitle('智能单词词典')
        self.setGeometry(300, 300, 800, 600)  # 初始位置和尺寸
        
        # 主部件容器
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主垂直布局
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # 搜索区域布局
        search_layout = QHBoxLayout()
        # 搜索输入框
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("输入要查询的单词...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ced4da;
                border-radius: 6px;
                font-size: 16px;
            }
        """)
        # 搜索按钮
        self.search_btn = QPushButton("搜索")
        self.search_btn.setStyleSheet("""
            QPushButton {
                background: #007bff;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #0069d9;
            }
        """)
        search_layout.addWidget(self.search_box, 4)  # 4:1 的比例分配空间
        search_layout.addWidget(self.search_btn, 1)
        main_layout.addLayout(search_layout)

        # 单词释义显示区域
        self.definition_display = QTextBrowser()
        self.definition_display.setStyleSheet("""
            QTextBrowser {
                background: #f8f9fa;
                padding: 15px;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        main_layout.addWidget(self.definition_display)

        # 记忆方法区域
        mnemonics_layout = QVBoxLayout()
        mnemonics_layout.addWidget(QLabel("🏅 记忆方法排行榜"))  # 装饰性标题
        
        # 记忆方法列表
        self.mnemonic_list = QListWidget()
        self.mnemonic_list.setStyleSheet("""
            QListWidget {
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
            QListWidget::item { 
                margin: 5px;
            }
        """)
        mnemonics_layout.addWidget(self.mnemonic_list)
        
        # 上传按钮
        self.upload_btn = QPushButton("✨ 上传记忆方法")
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background: #17a2b8;
                color: white;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #138496;
            }
        """)
        mnemonics_layout.addWidget(self.upload_btn)
        
        main_layout.addLayout(mnemonics_layout)

    def connect_signals(self):
        """连接所有信号与槽函数"""
        self.search_btn.clicked.connect(self.on_search)
        self.search_box.returnPressed.connect(self.on_search)  # 回车触发搜索
        self.upload_btn.clicked.connect(self.show_add_mnemonic_dialog)

    def load_style(self):
        """加载全局样式表"""
        self.setStyleSheet("""
            QMainWindow {
                background: #f8f9fa;
            }
            QLabel {
                color: #495057;
                font-size: 14px;
            }
        """)

    def on_search(self):
        """处理搜索功能的核心逻辑"""
        word = self.search_box.text().strip().lower()
        if not word:
            return

        # 显示加载状态
        self.definition_display.setText("⏳ 正在查询，请稍候...")
        QApplication.processEvents()  # 强制刷新UI

        try:
            # 优先查询本地数据库
            local_word = self.session.query(Word).filter_by(word=word).first()
            if local_word:
                self.current_word = local_word
                self.display_word(local_word)
                return

            # 在线查询（本地不存在时）
            result = self.spider.fetch_definition(word)
            if "error" in result:
                self.definition_display.setText(f"⚠️ {result['error']}")
                return

            # 保存新单词到数据库
            new_word = save_word(self.session, word, result)
            self.current_word = new_word
            self.display_word(new_word, examples=result.get("examples", []))
            
        except Exception as e:
            self.definition_display.setText(f"❌ 发生错误: {str(e)}")
        finally:
            self.load_mnemonics()  # 无论结果如何都加载记忆方法

    def display_word(self, word, examples=None):
        """格式化显示单词信息"""
        text = f"📖 【{word.word.upper()}】\n\n"  # 大写显示单词
        text += word.definition.replace("\n", "\n\n")  # 处理换行
        
        if examples:
            text += "\n\n🌟 精选例句：\n" + "\n\n".join(examples)
        
        self.definition_display.setText(text)

    def show_add_mnemonic_dialog(self):
        """显示添加记忆方法对话框"""
        if not self.current_word:
            QMessageBox.warning(self, "提示", "请先查询一个单词！")
            return
        
        dialog = AddMnemonicDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.save_mnemonic(dialog.get_data())

    def save_mnemonic(self, data):
        """保存记忆方法到数据库"""
        try:
            session = Session()
            new_mnemonic = Mnemonic(
                word_id=self.current_word.id,
                method_type=data["method_type"],
                content=data["content"]
            )
            session.add(new_mnemonic)
            session.commit()
            self.load_mnemonics()  # 刷新列表
            QMessageBox.information(self, "成功", "记忆方法已添加！")
        except Exception as e:
            session.rollback()  # 回滚事务
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
        finally:
            session.close()

    def load_mnemonics(self):
        """加载并显示当前单词的记忆方法"""
        self.mnemonic_list.clear()
        if not self.current_word:
            return

        session = Session()
        try:
            # 获取最新数据（避免缓存问题）
            word = session.query(Word).get(self.current_word.id)
            # 按点赞数降序排序
            mnemonics = sorted(word.mnemonics, key=lambda x: x.votes, reverse=True)
            
            for m in mnemonics:
                item = QListWidgetItem()
                widget = MnemonicItem(m)
                widget.vote_updated.connect(self.load_mnemonics)  # 绑定刷新信号
                self.mnemonic_list.addItem(item)
                self.mnemonic_list.setItemWidget(item, widget)
                item.setSizeHint(widget.sizeHint())  # 设置合适的高度
        finally:
            session.close()

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        self.session.close()  # 关闭数据库会话
        super().closeEvent(event)

if __name__ == '__main__':
    # 处理Qt平台插件路径（Windows系统可能需要）
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.dirname(sys.argv[0])
    
    app = QApplication(sys.argv)
    window = DictionaryApp()
    window.show()
    sys.exit(app.exec_())