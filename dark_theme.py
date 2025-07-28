dark_theme = """
QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
}

/* QLabel styling */
QLabel {
    color: #ffffff;
}

/* Specific QLabel overrides */
QLabel#label_3 {
    background-color: #3b3b3b;  /* Darker grey background */
}

QLabel#label_4 {
    background-color: #3b3b3b;  /* Darker grey background */
}

/* QPushButton styling */
QPushButton {
    background-color: #3b3b3b;
    color: #ffffff;
    border: 1px solid #5a5a5a;
    padding: 5px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #444444;
}

/* QLineEdit styling */
QLineEdit {
    background-color: #3b3b3b;
    color: #ffffff;
    border: 1px solid #5a5a5a;
    border-radius: 4px;
    padding: 4px;
}

/* QTableWidget styling */
QTableWidget {
    background-color: #2b2b2b;
    color: #ffffff;
    gridline-color: #444444;
    selection-background-color: #444444;
    selection-color: #ffffff;
}

/* QHeaderView (row/column headers in QTableWidget) */
QHeaderView::section {
    background-color: #3b3b3b;
    color: #ffffff;
    padding: 4px;
    border: 1px solid #5a5a5a;
}

QHeaderView::section:hover {
    background-color: #444444;
}

/* Corner of QTableWidget (top-left box above row 1 and column 1) */
QTableCornerButton::section {
    background-color: #3b3b3b;
    border: 1px solid #5a5a5a;
}

/* QTabWidget styling */
QTabWidget::pane {
    border: 1px solid #5a5a5a;
    background-color: #2b2b2b;
}

QTabBar::tab {
    background-color: #3b3b3b;
    color: #ffffff;
    padding: 5px;
    border: 1px solid #5a5a5a;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #444444;
    border-bottom: 1px solid #2b2b2b;
}

QTabBar::tab:hover {
    background-color: #444444;
}

/* Scrollbars */
QScrollBar:vertical {
    background-color: #2b2b2b;
    width: 15px;
}

QScrollBar::handle:vertical {
    background-color: #5a5a5a;
    min-height: 20px;
}

QScrollBar:horizontal {
    background-color: #2b2b2b;
    height: 15px;
}

QScrollBar::handle:horizontal {
    background-color: #5a5a5a;
    min-width: 20px;
}
"""
