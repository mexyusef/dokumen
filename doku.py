
import os
import random
import string
import sys

from PyQt5.Qsci import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtPrintSupport import *

from core import CoreProcessor


class EditorStandard(QsciScintilla):

	def __init__(self, filepath, parent=None, *args, **kwargs):
		super(EditorStandard, self).__init__(parent, *args, **kwargs)
		self.filepath = filepath		
		self.margin = 24
		self.init()
		self.linesChanged.connect(self.onLinesChanged)
		if self.filepath:
			self.load_file(self.filepath)

	def onLinesChanged(self):
		self.setMarginWidth(0, self.fontMetrics().width(
				str(self.lines())) + self.margin)

	def init(self):
		self.setUtf8(True)

		# lexer = QsciLexerMarkdown(self)
		lexer = QsciLexerPython(self)
		self.setLexer(lexer)

		cursor_color = QColor(0, 0, 255)
		cursor_size = 24  # cursor size in pixels

		# cursor_pixmap = QCursor(QPixmap(cursor_size, cursor_size))
		# cursor_pixmap.fill(cursor_color)

		cursor_pixmap = QPixmap(cursor_size, cursor_size)
		cursor_pixmap.fill(cursor_color)

		# self.setCursorWidth(cursor_size)
		# self.SendScintilla(QsciScintilla.SCI_SETCURSORWIDTH, cursor_size)
		self.setCursor(QCursor(cursor_pixmap))
		self.setCaretLineVisible(True)
		self.setCaretLineBackgroundColor(QColor("#e8e8e8"))
		self.setCaretForegroundColor(cursor_color)
		self.setCaretWidth(cursor_size)

		self.setAutoCompletionCaseSensitivity(False)  # ignore case
		self.setAutoCompletionSource(self.AcsAll)
		self.setAutoCompletionThreshold(1)  # One character pops up completion
		self.setAutoIndent(True)  # auto indent
		self.setBackspaceUnindents(True)
		self.setBraceMatching(self.StrictBraceMatch)
		self.setIndentationGuides(True)
		self.setIndentationsUseTabs(False)
		self.setIndentationWidth(4)
		self.setTabIndents(True)
		self.setTabWidth(4)
		self.setWhitespaceSize(1)
		self.setWhitespaceVisibility(self.WsVisible)
		self.setWhitespaceForegroundColor(Qt.gray)
		self.setWrapIndentMode(self.WrapIndentFixed)
		self.setWrapMode(self.WrapWord)

		# https://docs.huihoo.com/pyqt/QScintilla2/classQsciScintilla.html
		self.setFolding(self.BoxedTreeFoldStyle, 2)
		self.setFoldMarginColors(QColor("#676A6C"), QColor("#676A6D"))
		font = self.font() or QFont()
		font.setFamily("Consolas")
		font.setFixedPitch(True)
		font.setPointSize(10)
		self.setFont(font)
		self.setMarginsFont(font)
		self.fontmetrics = QFontMetrics(font)
		lexer.setFont(font)

		self.setMarginWidth(0, self.fontmetrics.width(
				str(self.lines())) + self.margin)
		self.setMarginLineNumbers(0, True)
		self.setMarginsBackgroundColor(QColor("gainsboro"))
		self.setMarginWidth(1, 0)
		self.setMarginWidth(2, 14)  # folded area

		# Bind autocompletion hotkey Alt+/
		completeKey = QShortcut(QKeySequence(Qt.ALT + Qt.Key_Slash), self)
		completeKey.setContext(Qt.WidgetShortcut)
		completeKey.activated.connect(self.autoCompleteFromAll)

		QShortcut(QKeySequence("Ctrl+Q"), self, activated=lambda: qApp.quit())
		QShortcut(QKeySequence("Ctrl+S"), self, activated=lambda: self.save_current_file())
		# https://docs.huihoo.com/pyqt/QScintilla2/classQsciScintilla.html
		# self.foldAll()

	def save_current_file(self):
		if self.filepath:
			file_contents = self.text()
			# file_write(self.file_path, file_contents)
			with open(self.filepath, 'w', encoding='utf8') as f:
				f.write(file_contents)


	def load_data(self, content):
		self.setText(content)

	def load_file(self, filepath):
		with open(filepath, 'r') as f:
			self.load_data(f.read())


class BrowserWindow(QMainWindow):

	def __init__(self, *args, **kwargs):
		super(BrowserWindow, self).__init__(*args, **kwargs)
		self.tabs = QTabWidget()
		self.urls = []
		self.default_url = 'http://www.google.com'
		self.tabs.setDocumentMode(True)
		self.tabs.tabBarDoubleClicked.connect(
				self.tab_open_doubleclick)
		self.tabs.currentChanged.connect(self.current_tab_changed)
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.close_current_tab)
		self.setCentralWidget(self.tabs)
		self.status = QStatusBar()
		self.setStatusBar(self.status)
		navtb = QToolBar("Navigation")
		self.addToolBar(navtb)
		back_btn = QAction("Back", self)
		back_btn.setStatusTip("Back to previous page")

		back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
		navtb.addAction(back_btn)
		next_btn = QAction("Forward", self)
		next_btn.setStatusTip("Forward to next page")
		next_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
		navtb.addAction(next_btn)

		reload_btn = QAction("Reload", self)
		reload_btn.setStatusTip("Reload page")
		reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
		navtb.addAction(reload_btn)

		home_btn = QAction("Home", self)
		home_btn.setStatusTip("Go home")

		home_btn.triggered.connect(self.navigate_home)
		navtb.addAction(home_btn)

		navtb.addSeparator()

		self.urlbar = QLineEdit()
		self.urlbar.returnPressed.connect(self.navigate_to_url)
		navtb.addWidget(self.urlbar)
		stop_btn = QAction("Stop", self)
		stop_btn.setStatusTip("Stop loading current page")
		stop_btn.triggered.connect(lambda: self.tabs.currentWidget().stop())
		navtb.addAction(stop_btn)
		self.add_new_tab(self.default_url, 'Homepage')

		self.setWindowTitle("My Browser")
		# self.hide()

	def new_url(self, alamat):
		self.add_new_tab(alamat, alamat.removeprefix('https://'))

	def add_new_tab(self, qurl=None, label="Blank"):
		if qurl is None:
			qurl = self.default_url
		if qurl in self.urls:
			self.tabs.setCurrentIndex(self.urls.index(qurl))
			return
		self.urls.append(qurl)
		qurl = QUrl(qurl)
		browser = QWebEngineView()
		browser.setZoomFactor(1.5)
		browser.setUrl(qurl)
		i = self.tabs.addTab(browser, label)
		self.tabs.setCurrentIndex(i)
		browser.urlChanged.connect(
				lambda qurl, browser=browser: self.update_urlbar(qurl, browser))
		browser.loadFinished.connect(
				lambda _, i=i, browser=browser: self.tabs.setTabText(i, browser.page().title()))

	def tab_open_doubleclick(self, i):
		if i == -1:
			self.add_new_tab()

	def current_tab_changed(self, i):

		qurl = self.tabs.currentWidget().url()

		self.update_urlbar(qurl, self.tabs.currentWidget())

		self.update_title(self.tabs.currentWidget())

	def close_current_tab(self, i):
		if self.tabs.count() < 2:
			return

		self.tabs.removeTab(i)

	def update_title(self, browser):

		if browser != self.tabs.currentWidget():

			return

		title = self.tabs.currentWidget().page().title()

		self.setWindowTitle("% s - Geek PyQt5" % title)

	def navigate_home(self):
		self.tabs.currentWidget().setUrl(QUrl(self.default_url))

	def navigate_to_url(self):

		q = QUrl(self.urlbar.text())
		if q.scheme() == "":
			q.setScheme("http")

		self.tabs.currentWidget().setUrl(q)

	def update_urlbar(self, q, browser=None):

		if browser != self.tabs.currentWidget():
			return

		self.urlbar.setText(q.toString())
		self.urlbar.setCursorPosition(0)

	def goto_address(self, address):

		q = QUrl(address)
		if q.scheme() == "":
			q.setScheme("http")

		self.tabs.currentWidget().setUrl(q)

	def muat_ulang(self):
		self.tabs.currentWidget().reload()


class MainWindow(QMainWindow):

	def __init__(self):
		super().__init__()
		self.disini = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')
		self.initUI()
		self.process = CoreProcessor()

	def get_inputs(self):

		output = self.html_output.text().strip()
		jars = self.jars.text().strip()
		prefixes = self.filter_package_prefixes.text().strip()
		return output, jars, prefixes

	def generate(self):
		output, jars, prefixes = self.get_inputs()
		if output and jars and prefixes:
			lokasi = f"file:///{self.disini}/{output}.html"
			self.process.run(output, [e.strip() for e in jars.split(',')], [e.strip() for e in prefixes.split(',')])
			self.browser.new_url(lokasi)

			self.browser.muat_ulang()

	def get_methods(self):
		output, jars, prefixes = self.get_inputs()
		hasil = self.process.callers_callees_lines(True, output, [e.strip() for e in jars.split(',')], [e.strip() for e in prefixes.split(',')])
		# siap tulis ke callers.txt dan calee.txt
		# print(hasil)
		self.editor1.load_file('callers.txt')
		self.editor2.load_file('callees.txt')

		# lokasi = f"file:///{self.disini}/{output}.html"
		# self.browser.new_url(lokasi)

	def initUI(self):

		self.main_layout = QHBoxLayout()
		split0 = QSplitter(Qt.Horizontal)
		split0_page_0 = QWidget(self)
		split0_pagelayout_0 = QVBoxLayout(split0_page_0)

		form0 = QFormLayout()
		self.jars = QLineEdit()
		self.html_output = QLineEdit()
		self.filter_package_prefixes = QLineEdit()
		self.jars.setText('JavaApplication1.jar')
		self.html_output.setText('callgraph3')
		self.filter_package_prefixes.setText('javaapplication1')
		
		form0.addRow('Output HTML (no ext)', self.html_output)
		form0.addRow('Jar file(s) (separated by comma)', self.jars)
		form0.addRow('Filter package prefixes (separated by comma)', self.filter_package_prefixes)

		split0_pagelayout_0.addLayout(form0)

		self.get_methods_button = QPushButton('Get Methods')
		self.get_methods_button.clicked.connect(self.get_methods)
		self.generator = QPushButton('Generate')
		self.generator.clicked.connect(self.generate)
		generate_layout = QHBoxLayout()
		generate_layout.addWidget(self.get_methods_button, 40)
		generate_layout.addWidget(self.generator, 60)

		split0_pagelayout_0.addLayout(generate_layout)

		tab0 = QTabWidget(self)
		# tab0 = QTabWidget(self, tabPosition=QTabWidget.North/South/East/West)
		tab0_page_0 = QWidget(self)
		tab0_pagelayout_0 = QVBoxLayout(tab0_page_0)
		# self.editor1 = EditorStandard('source-color.txt', self)
		self.editor1 = EditorStandard('callers.txt', self)
		# self.editor1.load_file('source-color.txt')
		tab0_pagelayout_0.addWidget(self.editor1)
		tab0.addTab(tab0_page_0, 'Callers')
		tab0_page_1 = QWidget(self)
		tab0_pagelayout_1 = QVBoxLayout(tab0_page_1)
		# self.editor2 = EditorStandard('sink-color.txt', self)
		self.editor2 = EditorStandard('callees.txt', self)
		# self.editor2.load_file('sink-color.txt')
		tab0_pagelayout_1.addWidget(self.editor2)
		tab0.addTab(tab0_page_1, 'Callees')
		split0_pagelayout_0.addWidget(tab0)

		tab0.currentChanged.connect(lambda page: print(f'tab tab0 page {page}'))

		split0.addWidget(split0_page_0)

		split0_page_1 = QWidget(self)
		split0_pagelayout_1 = QVBoxLayout(split0_page_1)

		# btn0 = QPushButton("klik untuk buka browser")
		self.browser = BrowserWindow()
		# btn0.clicked.connect(lambda: self.browser.show())
		split0_pagelayout_1.addWidget(self.browser)
		split0.addWidget(split0_page_1)

		# split0.setOrientation(Qt.Horizontal)
		# split0.setHandleWidth(8)
		# split0.setStretchFactor(0, 5)
		# split0.setStretchFactor(1, 5)
		split0.handle(1).setStyleSheet('background: 3px blue;')
		self.main_layout.addWidget(split0)
		self.main_widget = QWidget()
		self.main_widget.setLayout(self.main_layout)
		self.setCentralWidget(self.main_widget)
		self.statusBar().showMessage("Status bar here...")
		self.statusBar().setStyleSheet(
				"background-image : url(status.jpg); background-position: center; color: orange;")
		editAct = QAction("&Edit", self)
		editAct.setShortcut("Ctrl+E")
		editAct.setStatusTip("Edit own file")
		editAct.triggered.connect(lambda: os.system(f"code README.md"))
		editAct.setIcon(QApplication.style().standardIcon(
				QStyle.SP_FileDialogDetailedView))
		exitAct = QAction("E&xit", self)
		exitAct.setShortcut("Ctrl+X")
		exitAct.setStatusTip("Exit application")
		exitAct.triggered.connect(qApp.quit)
		exitAct.setIcon(QApplication.style().standardIcon(QStyle.SP_BrowserStop))
		menubar = self.menuBar()
		file_menu = menubar.addMenu("&File")
		file_misc_menu = QMenu("&Misc", self)
		about_action = QAction("About Qt", self)
		about_action.setStatusTip("Display about Qt")
		about_action.triggered.connect(QApplication.instance().aboutQt)
		file_misc_menu.addAction(about_action)
		file_menu.addAction(editAct)
		file_menu.addMenu(file_misc_menu)
		file_menu.addAction(exitAct)
		toolbar = self.addToolBar("Main Toolbar")
		toolbar.addAction(editAct)
		toolbar.addAction(exitAct)


def get_icon():
	pixmap = QPixmap(16, 16)
	pixmap.fill(Qt.transparent)
	painter = QPainter()
	painter.begin(pixmap)
	painter.setFont(QFont('Webdings', 11))
	painter.setPen(Qt.GlobalColor(random.randint(4, 18)))
	painter.drawText(0, 0, 16, 16, Qt.AlignCenter,
									random.choice(string.ascii_letters))
	painter.end()
	return QIcon(pixmap)


def set_theme(app):
	app.setStyle("Fusion")
	palette = QPalette()
	palette.setColor(QPalette.Window, QColor(53, 53, 53))
	palette.setColor(QPalette.WindowText, Qt.white)
	palette.setColor(QPalette.Base, QColor(25, 25, 25))
	palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
	palette.setColor(QPalette.ToolTipBase, Qt.black)
	palette.setColor(QPalette.ToolTipText, Qt.white)
	palette.setColor(QPalette.Text, Qt.white)
	palette.setColor(QPalette.Button, QColor(53, 53, 53))
	palette.setColor(QPalette.ButtonText, Qt.white)
	palette.setColor(QPalette.BrightText, Qt.red)
	palette.setColor(QPalette.Link, QColor(42, 130, 218))
	palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
	palette.setColor(QPalette.HighlightedText, Qt.black)
	app.setPalette(palette)


background_image_stylesheet = '''
MainWindow {
	border-image: url("bg.jpg");
	background-repeat: no-repeat; 
	background-position: center;
}
'''


def main():
	app = QApplication([])
	set_theme(app)
	wnd = MainWindow()
	wnd.setStyleSheet(background_image_stylesheet)
	wnd.show()
	wnd.resize(1200, 800)
	wnd.setWindowTitle('Automatic Java Document Generator')
	QShortcut(QKeySequence("Ctrl+Q"), wnd, activated=lambda: qApp.quit())
	sys.exit(app.exec_())


if __name__ == '__main__':
	main()
