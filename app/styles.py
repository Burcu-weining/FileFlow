
# FileFlow desktop application stylesheet

APP_STYLE = """
QWidget {
    background-color: #F7F8FC;
    color: #23263B;
    font-family: Arial;
    font-size: 14px;
}

/* Main application window */
QWidget#mainWindow {
    background-color: #F7F8FC;
}

/* Application title */
QLabel#appTitle {
    font-size: 28px;
    font-weight: bold;
    color: #635BDB;
    background: transparent;
}

/* Application subtitle */
QLabel#appSubtitle {
    font-size: 13px;
    color: #84889C;
    background: transparent;
}

/* Section headings */
QLabel#sectionTitle {
    font-size: 15px;
    font-weight: bold;
    color: #23263B;
    background: transparent;
}

/* Status text */
QLabel#statusLabel {
    color: #696E86;
    font-size: 13px;
    background: transparent;
}

/* All buttons */
QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #DCE0EE;
    border-radius: 10px;
    color: #343852;
    padding: 12px 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #F0EEFF;
    border-color: #A9A1EF;
}

QPushButton:disabled {
    background-color: #ECEEF4;
    color: #9A9EB0;
    border-color: #E1E3EB;
}

/* Main conversion button */
QPushButton#convertButton {
    background-color: #635BDB;
    border: none;
    color: #FFFFFF;
    font-size: 15px;
    padding: 15px;
}

QPushButton#convertButton:hover {
    background-color: #5148BD;
}

QPushButton#convertButton:disabled {
    background-color: #BBB7E8;
    color: #FFFFFF;
}

/* File queue */
QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #E1E4EF;
    border-radius: 12px;
    padding: 8px;
    outline: none;
}

QListWidget::item {
    padding: 11px;
    border-radius: 7px;
}

QListWidget::item:hover {
    background-color: #F4F2FF;
}

QListWidget::item:selected {
    background-color: #E9E6FF;
    color: #37308D;
}

/* Output format dropdown */
QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #DCE0EE;
    border-radius: 10px;
    padding: 11px;
    min-height: 18px;
}

QComboBox:hover {
    border-color: #958BEA;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #23263B;
    selection-background-color: #E9E6FF;
}

/* Progress bar */
QProgressBar {
    background-color: #E8EAF2;
    border: none;
    border-radius: 7px;
    height: 14px;
    text-align: center;
    color: #37308D;
    font-size: 10px;
}

QProgressBar::chunk {
    background-color: #635BDB;
    border-radius: 7px;
}
"""
