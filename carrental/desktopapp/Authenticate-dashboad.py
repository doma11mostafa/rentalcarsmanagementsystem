import sys
import os
import requests
import json
import webbrowser # <-- ADDED IMPORT
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QDate, QTimer
from PyQt5.QtGui import *

# API Base URL - Make sure your backend server is running at this address
API_BASE = "http://127.0.0.1:8000"

# --- Custom Widgets ---

class GradientWidget(QWidget):
    """A custom widget with a vertical gradient background."""
    def __init__(self, colors=['#f6ad55', '#dd6b20']):
        super().__init__()
        self.colors = colors
        # This is necessary to ensure the widget can be styled with stylesheets
        self.setAttribute(Qt.WA_StyledBackground, True)

    def paintEvent(self, event):
        """Overrides the paint event to draw the gradient."""
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(self.colors[0]))
        gradient.setColorAt(1, QColor(self.colors[1]))
        painter.fillRect(self.rect(), gradient)
        super().paintEvent(event)

class ModernCard(QFrame):
    """A modern-looking card widget to display stats."""
    def __init__(self, title="", value="", icon="📊"):
        super().__init__()
        self.setFixedSize(200, 120)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d3748, stop:1 #4a5568);
                border-radius: 15px;
                border: 1px solid #4a5568;
            }
            QFrame:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4a5568, stop:1 #2d3748);
                border: 1px solid #f59e0b;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Icon and Title Row
        top_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px; color: #f59e0b; background: transparent;")
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #e2e8f0; font-size: 12px; font-weight: bold; background: transparent;")
        
        top_layout.addWidget(icon_label)
        top_layout.addStretch()
        top_layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold; background: transparent;")
        value_label.setAlignment(Qt.AlignCenter)
        
        layout.addLayout(top_layout)
        layout.addWidget(value_label)
        layout.addStretch()

class ModernButton(QPushButton):
    """A custom button with a gradient and hover effects."""
    def __init__(self, text, color="#f6ad55"):
        super().__init__(text)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color}, stop:1 #dd6b20);
                color: white;
                border: none;
                border-radius: 20px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #dd6b20, stop:1 {color});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #c05621, stop:1 #9c4221);
            }}
        """)
        self.setMinimumHeight(40)

class ModernInput(QLineEdit):
    """A custom line edit with a modern, translucent style."""
    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                padding: 15px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #f59e0b;
                background: rgba(255, 255, 255, 0.15);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.6);
            }
        """)
        self.setMinimumHeight(50)

# --- Customer Profile Widgets ---

class CustomerProfileCard(QFrame):
    """A card widget to display customer profile with photo and basic info."""
    profile_clicked = pyqtSignal(dict)
    
    def __init__(self, customer_data):
        super().__init__()
        self.customer_data = customer_data
        self.setFixedSize(280, 180)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d3748, stop:1 #4a5568);
                border-radius: 15px;
                border: 2px solid #4a5568;
            }
            QFrame:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4a5568, stop:1 #2d3748);
                border: 2px solid #f59e0b;
            }
        """)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Profile photo section
        photo_layout = QHBoxLayout()
        self.photo_label = QLabel()
        self.photo_label.setFixedSize(60, 60)
        self.photo_label.setStyleSheet("""
            QLabel {
                border: 2px solid #f59e0b;
                border-radius: 30px;
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        self.photo_label.setAlignment(Qt.AlignCenter)
        
        # Load profile image or show default
        if self.customer_data.get('profile_image'):
            self.load_profile_image()
        else:
            self.photo_label.setText("👤")
            self.photo_label.setStyleSheet(self.photo_label.styleSheet() + """
                font-size: 24px;
                color: #f59e0b;
            """)
        
        photo_layout.addWidget(self.photo_label)
        photo_layout.addStretch()
        
        # Customer info
        name_label = QLabel(self.customer_data.get('full_name', 'N/A'))
        name_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
            background: transparent;
        """)
        name_label.setWordWrap(True)
        
        email_label = QLabel(self.customer_data.get('email', 'N/A'))
        email_label.setStyleSheet("""
            color: #cbd5e0;
            font-size: 12px;
            background: transparent;
        """)
        email_label.setWordWrap(True)
        
        phone_label = QLabel(f"📞 {self.customer_data.get('phone_number', 'N/A')}")
        phone_label.setStyleSheet("""
            color: #a0aec0;
            font-size: 11px;
            background: transparent;
        """)
        
        national_id_label = QLabel(f"🆔 {self.customer_data.get('National_ID', 'N/A')}")
        national_id_label.setStyleSheet("""
            color: #a0aec0;
            font-size: 11px;
            background: transparent;
        """)
        
        layout.addLayout(photo_layout)
        layout.addWidget(name_label)
        layout.addWidget(email_label)
        layout.addWidget(phone_label)
        layout.addWidget(national_id_label)
        layout.addStretch()
        
    def load_profile_image(self):
        """Load customer profile image from URL or file path."""
        try:
            profile_image = self.customer_data.get('profile_image')
            if profile_image:
                # Handle both URL and local file paths
                if profile_image.startswith('http'):
                    # For web URLs, you'd need to download the image
                    # For now, we'll handle local media files
                    pass
                else:
                    # Local file path
                    full_path = os.path.join(os.path.dirname(__file__), '..', '..', 'media', profile_image)
                    if os.path.exists(full_path):
                        pixmap = QPixmap(full_path)
                        scaled_pixmap = pixmap.scaled(
                            self.photo_label.size(),
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                        self.photo_label.setPixmap(scaled_pixmap)
                        return
            
            # Fallback to default icon
            self.photo_label.setText("👤")
            self.photo_label.setStyleSheet(self.photo_label.styleSheet() + """
                font-size: 24px;
                color: #f59e0b;
            """)
        except Exception as e:
            print(f"Error loading profile image: {e}")
            self.photo_label.setText("👤")
            self.photo_label.setStyleSheet(self.photo_label.styleSheet() + """
                font-size: 24px;
                color: #667eea;
            """)
    
    def mousePressEvent(self, event):
        """Handle click on customer profile card."""
        if event.button() == Qt.LeftButton:
            self.profile_clicked.emit(self.customer_data)
        super().mousePressEvent(event)

class CustomerProfileDialog(QDialog):
    """Dialog showing detailed customer profile with rental history and summary."""
    
    def __init__(self, customer_data, parent=None):
        super().__init__(parent)
        self.customer_data = customer_data
        self.setWindowTitle(f"Customer Profile - {customer_data.get('full_name', 'Unknown')}")
        self.setFixedSize(900, 700)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c);
            }
            QLabel {
                color: #e2e8f0;
                background: transparent;
            }
        """)
        self.setup_ui()
        self.load_rental_history()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Header with customer info and photo
        header_layout = QHBoxLayout()
        
        # Customer photo
        self.photo_label = QLabel()
        self.photo_label.setFixedSize(120, 120)
        self.photo_label.setStyleSheet("""
            QLabel {
                border: 3px solid #f59e0b;
                border-radius: 60px;
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        self.photo_label.setAlignment(Qt.AlignCenter)
        
        # Load profile image
        if self.customer_data.get('profile_image'):
            self.load_profile_image()
        else:
            self.photo_label.setText("👤")
            self.photo_label.setStyleSheet(self.photo_label.styleSheet() + """
                font-size: 48px;
                color: #f59e0b;
            """)
        
        # Customer details
        details_layout = QVBoxLayout()
        
        name_label = QLabel(self.customer_data.get('full_name', 'N/A'))
        name_label.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        
        email_label = QLabel(f"📧 {self.customer_data.get('email', 'N/A')}")
        email_label.setStyleSheet("color: #cbd5e0; font-size: 14px; margin-bottom: 5px;")
        
        phone_label = QLabel(f"📞 {self.customer_data.get('phone_number', 'N/A')}")
        phone_label.setStyleSheet("color: #cbd5e0; font-size: 14px; margin-bottom: 5px;")
        
        national_id_label = QLabel(f"🆔 National ID: {self.customer_data.get('National_ID', 'N/A')}")
        national_id_label.setStyleSheet("color: #a0aec0; font-size: 12px; margin-bottom: 5px;")
        
        nationality_label = QLabel(f"🌍 Nationality: {self.customer_data.get('Nationality', 'N/A')}")
        nationality_label.setStyleSheet("color: #a0aec0; font-size: 12px; margin-bottom: 5px;")
        
        license_label = QLabel(f"🚗 License: {self.customer_data.get('License_Number', 'N/A')}")
        license_label.setStyleSheet("color: #a0aec0; font-size: 12px;")
        
        details_layout.addWidget(name_label)
        details_layout.addWidget(email_label)
        details_layout.addWidget(phone_label)
        details_layout.addWidget(national_id_label)
        details_layout.addWidget(nationality_label)
        details_layout.addWidget(license_label)
        details_layout.addStretch()
        
        header_layout.addWidget(self.photo_label)
        header_layout.addLayout(details_layout)
        header_layout.addStretch()
        
        # Summary cards
        summary_layout = QHBoxLayout()
        self.total_rentals_card = ModernCard("Total Rentals", "0", "📝")
        self.total_spent_card = ModernCard("Total Spent", "0 AED", "💰")
        self.active_rentals_card = ModernCard("Active Rentals", "0", "🚗")
        
        summary_layout.addWidget(self.total_rentals_card)
        summary_layout.addWidget(self.total_spent_card)
        summary_layout.addWidget(self.active_rentals_card)
        summary_layout.addStretch()
        
        # Rental history table
        history_label = QLabel("📋 Rental History")
        history_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-top: 20px;")
        
        self.history_table = QTableWidget()
        self.setup_history_table()
        
        # Close button
        close_btn = ModernButton("❌ Close", "#6c757d")
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(150)
        
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        
        main_layout.addLayout(header_layout)
        main_layout.addLayout(summary_layout)
        main_layout.addWidget(history_label)
        main_layout.addWidget(self.history_table)
        main_layout.addLayout(close_layout)
        
    def setup_history_table(self):
        """Setup the rental history table."""
        self.history_table.setStyleSheet("""
            QTableWidget {
                background: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 10px;
                color: white;
                gridline-color: #4a5568;
            }
            QTableWidget::item {
                background: #2d3748;
                padding: 8px;
                border-bottom: 1px solid #4a5568;
            }
            QTableWidget::item:selected {
                background: rgba(102, 126, 234, 0.4);
            }
            QHeaderView::section {
                background: rgba(102, 126, 234, 0.8);
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        self.history_table.setAlternatingRowColors(False)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
    def load_profile_image(self):
        """Load customer profile image."""
        try:
            profile_image = self.customer_data.get('profile_image')
            if profile_image:
                full_path = os.path.join(os.path.dirname(__file__), '..', '..', 'media', profile_image)
                if os.path.exists(full_path):
                    pixmap = QPixmap(full_path)
                    scaled_pixmap = pixmap.scaled(
                        self.photo_label.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.photo_label.setPixmap(scaled_pixmap)
                    return
            
            # Fallback
            self.photo_label.setText("👤")
            self.photo_label.setStyleSheet(self.photo_label.styleSheet() + """
                font-size: 48px;
                color: #f59e0b;
            """)
        except Exception as e:
            print(f"Error loading profile image: {e}")
            self.photo_label.setText("👤")
            self.photo_label.setStyleSheet(self.photo_label.styleSheet() + """
                font-size: 48px;
                color: #667eea;
            """)
    
    def load_rental_history(self):
        """Load customer rental history from API."""
        try:
            customer_id = self.customer_data.get('id')
            if not customer_id:
                return
                
            # Get all rentals and filter by customer
            response = requests.get(f"{API_BASE}/api/rentals/history/", timeout=5)
            if response.status_code == 200:
                all_rentals = response.json().get('data', [])
                # Filter by customer name (API returns customer names as strings)
                customer_name = self.customer_data.get('full_name', '').strip()
                rentals = []
                for rental in all_rentals:
                    rental_customer = rental.get('customer', '').strip()
                    if rental_customer.lower() == customer_name.lower():
                        rentals.append(rental)
            else:
                rentals = []
                print(f"Failed to load rental data: {response.status_code}")
            
            # Update summary cards
            total_rentals = len(rentals)
            total_spent = sum(float(rental.get('total_price', 0)) for rental in rentals)
            active_rentals = sum(1 for rental in rentals if rental.get('status') == 'active')
            
            # print(f"Debug: Found {total_rentals} rentals, {active_rentals} active, total spent: {total_spent}")
            # print(f"Debug: API response status: {response.status_code}")
            # print(f"Debug: Raw response data: {response.json() if response.status_code == 200 else 'No data'}")
            # print(f"Debug: Customer name being filtered: '{customer_name}'")
            
            # Find and update the value labels in each card
            for label in self.total_rentals_card.findChildren(QLabel):
                if label.objectName() == "value_label":
                    label.setText(str(total_rentals))
                    break
            else:
                # Fallback: update the last label (usually the value)
                labels = self.total_rentals_card.findChildren(QLabel)
                if labels:
                    labels[-1].setText(str(total_rentals))
            
            for label in self.total_spent_card.findChildren(QLabel):
                if label.objectName() == "value_label":
                    label.setText(f"{total_spent:.2f} AED")
                    break
            else:
                labels = self.total_spent_card.findChildren(QLabel)
                if labels:
                    labels[-1].setText(f"{total_spent:.2f} AED")
            
            for label in self.active_rentals_card.findChildren(QLabel):
                if label.objectName() == "value_label":
                    label.setText(str(active_rentals))
                    break
            else:
                labels = self.active_rentals_card.findChildren(QLabel)
                if labels:
                    labels[-1].setText(str(active_rentals))
            
            # Populate table
            self.history_table.setRowCount(len(rentals))
            self.history_table.setColumnCount(6)
            self.history_table.setHorizontalHeaderLabels([
                "Car", "Start Date", "End Date", "Total Price", "Status", "Car Photos"
            ])
            
            for row, rental in enumerate(rentals):
                car_info = rental.get('car', '')
                if isinstance(car_info, str):
                    # Car is a string like "Hyundai Optrasee 2017 (ASR-5555)"
                    car_text = car_info
                else:
                    # Car is an object with separate fields
                    car_text = f"{car_info.get('brand', '')} {car_info.get('model', '')} ({car_info.get('license_plate', '')})"
                
                self.history_table.setItem(row, 0, QTableWidgetItem(car_text))
                self.history_table.setItem(row, 1, QTableWidgetItem(rental.get('start_date', 'N/A')))
                self.history_table.setItem(row, 2, QTableWidgetItem(rental.get('end_date', 'N/A')))
                self.history_table.setItem(row, 3, QTableWidgetItem(f"{rental.get('total_price', 0)} AED"))
                
                # Status with color
                status = rental.get('status', 'unknown')
                status_item = QTableWidgetItem(status.title())
                if status == 'active':
                    status_item.setForeground(QColor("#28a745"))
                elif status == 'completed':
                    status_item.setForeground(QColor("#17a2b8"))
                else:
                    status_item.setForeground(QColor("#dc3545"))
                self.history_table.setItem(row, 4, status_item)
                
                # Action buttons layout
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(5, 2, 5, 2)
                action_layout.setSpacing(5)
                
                # Car photos button
                photos_btn = QPushButton("📷")
                photos_btn.setFixedSize(30, 25)
                photos_btn.setStyleSheet("""
                    QPushButton {
                        background: #f6ad55;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background: #dd6b20;
                    }
                """)
                photos_btn.clicked.connect(lambda checked, car=car_text: self.show_car_photos_from_string(car))
                action_layout.addWidget(photos_btn)
                
                # Complete rental button (only for active rentals)
                if status == 'active':
                    complete_btn = QPushButton("✅")
                    complete_btn.setFixedSize(30, 25)
                    complete_btn.setStyleSheet("""
                        QPushButton {
                            background: #28a745;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            font-size: 12px;
                        }
                        QPushButton:hover {
                            background: #218838;
                        }
                    """)
                    complete_btn.clicked.connect(lambda checked, r=rental: self.complete_rental(r))
                    action_layout.addWidget(complete_btn)
                
                action_layout.addStretch()
                self.history_table.setCellWidget(row, 5, action_widget)
            
            self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                
        except requests.exceptions.RequestException as e:
            print(f"Could not load rental history: {e}")
    
    def complete_rental(self, rental):
        """Complete an active rental."""
        reply = QMessageBox.question(
            self, 
            "Complete Rental", 
            f"Are you sure you want to complete this rental?\n\nCar: {rental.get('car', {}).get('brand', '')} {rental.get('car', {}).get('model', '')}\nCustomer will be charged final amount including any violations.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                response = requests.post(f"{API_BASE}/api/rentals/complete/", 
                                       json={'rental_id': rental['id']}, 
                                       timeout=5)
                if response.status_code == 200:
                    QMessageBox.information(self, "Success", "Rental completed successfully!\nInvoice has been generated.")
                    self.load_rental_history()  # Refresh the table
                else:
                    QMessageBox.warning(self, "Error", f"Failed to complete rental: {response.status_code}")
            except requests.exceptions.RequestException as e:
                QMessageBox.warning(self, "Error", f"Network error: {str(e)}")

    def show_car_photos_from_string(self, car_text):
        """Show car photos in a popup dialog from car string."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Car Photos - {car_text}")
        dialog.setFixedSize(600, 400)
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c);
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        # Create a scroll area for photos
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        # Photos container
        photos_widget = QWidget()
        photos_layout = QGridLayout(photos_widget)
        
        # Add placeholder for now since we don't have car object
        placeholder_label = QLabel("📷 Car photos would be displayed here")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("""
            QLabel {
                color: #a0aec0;
                font-size: 16px;
                padding: 50px;
            }
        """)
        photos_layout.addWidget(placeholder_label, 0, 0)
        
        scroll.setWidget(photos_widget)
        layout.addWidget(scroll)
        
        dialog.exec_()

    def show_car_photos(self, car_info):
        """Show car photos in a popup dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Car Photos - {car_info.get('brand', '')} {car_info.get('model', '')}")
        dialog.setFixedSize(600, 400)
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c);
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        # Car info
        info_label = QLabel(f"{car_info.get('brand', '')} {car_info.get('model', '')} - {car_info.get('license_plate', '')}")
        info_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        info_label.setAlignment(Qt.AlignCenter)
        
        # Photos layout
        photos_layout = QHBoxLayout()
        
        # Main image
        if car_info.get('main_image'):
            main_photo = QLabel()
            main_photo.setFixedSize(180, 120)
            main_photo.setStyleSheet("border: 2px solid #f59e0b; border-radius: 10px;")
            main_photo.setAlignment(Qt.AlignCenter)
            
            try:
                full_path = os.path.join(os.path.dirname(__file__), '..', '..', 'media', car_info['main_image'])
                if os.path.exists(full_path):
                    pixmap = QPixmap(full_path)
                    scaled_pixmap = pixmap.scaled(main_photo.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    main_photo.setPixmap(scaled_pixmap)
                else:
                    main_photo.setText("🚗\nMain Photo")
                    main_photo.setStyleSheet(main_photo.styleSheet() + "color: #f59e0b; font-size: 14px;")
            except:
                main_photo.setText("🚗\nMain Photo")
                main_photo.setStyleSheet(main_photo.styleSheet() + "color: #f59e0b; font-size: 14px;")
            
            photos_layout.addWidget(main_photo)
        
        # Interior image
        if car_info.get('interior_image'):
            interior_photo = QLabel()
            interior_photo.setFixedSize(180, 120)
            interior_photo.setStyleSheet("border: 2px solid #f59e0b; border-radius: 10px;")
            interior_photo.setAlignment(Qt.AlignCenter)
            
            try:
                full_path = os.path.join(os.path.dirname(__file__), '..', '..', 'media', car_info['interior_image'])
                if os.path.exists(full_path):
                    pixmap = QPixmap(full_path)
                    scaled_pixmap = pixmap.scaled(interior_photo.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    interior_photo.setPixmap(scaled_pixmap)
                else:
                    interior_photo.setText("🏠\nInterior")
                    interior_photo.setStyleSheet(interior_photo.styleSheet() + "color: #f59e0b; font-size: 14px;")
            except:
                interior_photo.setText("🏠\nInterior")
                interior_photo.setStyleSheet(interior_photo.styleSheet() + "color: #f59e0b; font-size: 14px;")
            
            photos_layout.addWidget(interior_photo)
        
        # Exterior image
        if car_info.get('exterior_image'):
            exterior_photo = QLabel()
            exterior_photo.setFixedSize(180, 120)
            exterior_photo.setStyleSheet("border: 2px solid #f59e0b; border-radius: 10px;")
            exterior_photo.setAlignment(Qt.AlignCenter)
            
            try:
                full_path = os.path.join(os.path.dirname(__file__), '..', '..', 'media', car_info['exterior_image'])
                if os.path.exists(full_path):
                    pixmap = QPixmap(full_path)
                    scaled_pixmap = pixmap.scaled(exterior_photo.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    exterior_photo.setPixmap(scaled_pixmap)
                else:
                    exterior_photo.setText("🌟\nExterior")
                    exterior_photo.setStyleSheet(exterior_photo.styleSheet() + "color: #f59e0b; font-size: 14px;")
            except:
                exterior_photo.setText("🌟\nExterior")
                exterior_photo.setStyleSheet(exterior_photo.styleSheet() + "color: #f59e0b; font-size: 14px;")
            
            photos_layout.addWidget(exterior_photo)
        
        close_btn = ModernButton("Close", "#6c757d")
        close_btn.clicked.connect(dialog.accept)
        
        layout.addWidget(info_label)
        layout.addLayout(photos_layout)
        layout.addStretch()
        layout.addWidget(close_btn)
        
        dialog.exec_()

# --- Dialogs for Adding Data ---

class AddCarDialog(QDialog):
    """Dialog for adding a new car to the system."""
    car_added = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Car")
        self.setFixedSize(450, 700)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c);
            }
            QLabel {
                color: #e2e8f0; 
                font-weight: bold; 
                margin-top: 10px;
                background: transparent;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QWidget {
                background: transparent;
            }
        """)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Create scroll area for the form
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background: transparent; 
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
        """)
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(scroll_widget)
        
        title = QLabel("🚗 Add New Car")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        
        # Form fields
        self.brand_combo = QComboBox()
        self.brand_combo.addItems([
            "Audi", "BMW", "Chevrolet", "Ford", "Honda", "Hyundai",
            "Infiniti", "Jaguar", "Kia", "Land Rover", "Lexus", "Mazda",
            "Mercedes", "Mitsubishi", "Nissan", "Peugeot", "Porsche",
            "Renault", "Subaru", "Tesla", "Toyota", "Volkswagen", "Volvo"
        ])
        self.brand_combo.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 12px;
                color: white;
                font-size: 14px;
            }
        """)
        
        self.model_input = ModernInput("Car Model (e.g., Camry, Civic)")
        self.year_input = ModernInput("Year (e.g., 2023)")
        self.year_input.setValidator(QIntValidator(1990, 2099))
        self.license_input = ModernInput("License Plate")
        self.color_input = ModernInput("Color")
        self.price_input = ModernInput("Price per Day (AED)")
        self.price_input.setValidator(QDoubleValidator(0.0, 9999.99, 2))
        
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Description (optional)")
        self.description_input.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                padding: 15px;
                color: white;
                font-size: 14px;
            }
        """)
        self.description_input.setMaximumHeight(80)
        
        # Image upload sections
        self.main_image_path = None
        self.interior_image_path = None
        self.exterior_image_path = None
        
        # Main Image
        main_image_layout = QHBoxLayout()
        self.main_image_btn = ModernButton("📷 Select Main Image", "#17a2b8")
        self.main_image_btn.clicked.connect(lambda: self.select_image('main'))
        self.main_image_label = QLabel("No image selected")
        self.main_image_label.setStyleSheet("color: #cbd5e0; font-size: 12px; background: transparent;")
        main_image_layout.addWidget(self.main_image_btn)
        main_image_layout.addWidget(self.main_image_label)
        
        # Interior Image
        interior_image_layout = QHBoxLayout()
        self.interior_image_btn = ModernButton("🏠 Select Interior Image", "#17a2b8")
        self.interior_image_btn.clicked.connect(lambda: self.select_image('interior'))
        self.interior_image_label = QLabel("No image selected")
        self.interior_image_label.setStyleSheet("color: #cbd5e0; font-size: 12px; background: transparent;")
        interior_image_layout.addWidget(self.interior_image_btn)
        interior_image_layout.addWidget(self.interior_image_label)
        
        # Exterior Image
        exterior_image_layout = QHBoxLayout()
        self.exterior_image_btn = ModernButton("🌟 Select Exterior Image", "#17a2b8")
        self.exterior_image_btn.clicked.connect(lambda: self.select_image('exterior'))
        self.exterior_image_label = QLabel("No image selected")
        self.exterior_image_label.setStyleSheet("color: #cbd5e0; font-size: 12px; background: transparent;")
        exterior_image_layout.addWidget(self.exterior_image_btn)
        exterior_image_layout.addWidget(self.exterior_image_label)
        
        # Image preview labels
        self.main_image_preview = QLabel()
        self.main_image_preview.setFixedSize(150, 100)
        self.main_image_preview.setStyleSheet("border: 2px solid #4a5568; border-radius: 8px; background: rgba(255,255,255,0.1);")
        self.main_image_preview.setAlignment(Qt.AlignCenter)
        self.main_image_preview.setText("Main Image\nPreview")
        
        self.interior_image_preview = QLabel()
        self.interior_image_preview.setFixedSize(150, 100)
        self.interior_image_preview.setStyleSheet("border: 2px solid #4a5568; border-radius: 8px; background: rgba(255,255,255,0.1);")
        self.interior_image_preview.setAlignment(Qt.AlignCenter)
        self.interior_image_preview.setText("Interior Image\nPreview")
        
        self.exterior_image_preview = QLabel()
        self.exterior_image_preview.setFixedSize(150, 100)
        self.exterior_image_preview.setStyleSheet("border: 2px solid #4a5568; border-radius: 8px; background: rgba(255,255,255,0.1);")
        self.exterior_image_preview.setAlignment(Qt.AlignCenter)
        self.exterior_image_preview.setText("Exterior Image\nPreview")
        
        # Image previews layout
        previews_layout = QHBoxLayout()
        previews_layout.addWidget(self.main_image_preview)
        previews_layout.addWidget(self.interior_image_preview)
        previews_layout.addWidget(self.exterior_image_preview)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        save_btn = ModernButton("💾 Save Car", "#28a745")
        save_btn.clicked.connect(self.save_car)
        cancel_btn = ModernButton("❌ Cancel", "#dc3545")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        # Add widgets to layout
        layout.addWidget(title)
        layout.addWidget(QLabel("Brand:"))
        layout.addWidget(self.brand_combo)
        layout.addWidget(self.model_input)
        layout.addWidget(self.year_input)
        layout.addWidget(self.license_input)
        layout.addWidget(self.color_input)
        layout.addWidget(self.price_input)
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.description_input)
        
        # Image upload sections
        layout.addWidget(QLabel("Car Images (Optional):"))
        layout.addLayout(main_image_layout)
        layout.addLayout(interior_image_layout)
        layout.addLayout(exterior_image_layout)
        layout.addLayout(previews_layout)
        
        layout.addStretch()
        layout.addLayout(buttons_layout)
        
        scroll.setWidget(scroll_widget)
        
        # Main layout for the dialog
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

    def select_image(self, image_type):
        """Open file dialog to select an image"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, 
            f"Select {image_type.title()} Image", 
            "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            if image_type == 'main':
                self.main_image_path = file_path
                self.main_image_label.setText(f"Selected: {os.path.basename(file_path)}")
                self.show_image_preview(file_path, self.main_image_preview)
            elif image_type == 'interior':
                self.interior_image_path = file_path
                self.interior_image_label.setText(f"Selected: {os.path.basename(file_path)}")
                self.show_image_preview(file_path, self.interior_image_preview)
            elif image_type == 'exterior':
                self.exterior_image_path = file_path
                self.exterior_image_label.setText(f"Selected: {os.path.basename(file_path)}")
                self.show_image_preview(file_path, self.exterior_image_preview)

    def show_image_preview(self, file_path, preview_label):
        """Show image preview in the label"""
        try:
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(
                preview_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            preview_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Error loading image preview: {e}")

    def save_car(self):
        """Validates input and sends data to the API to save the car."""
        try:
            # Basic validation
            if not all([self.model_input.text(), self.license_input.text(), self.color_input.text()]):
                self.show_message("Please fill all required fields.", "error")
                return

            # Prepare form data
            form_data = {
                'brand': self.brand_combo.currentText(),
                'model': self.model_input.text(),
                'year': self.year_input.text(),
                'license_plate': self.license_input.text(),
                'color': self.color_input.text(),
                'price_per_day': self.price_input.text(),
                'description': self.description_input.toPlainText()
            }
            
            files = {}
            
            # Add images if selected
            if self.main_image_path:
                files['main_image'] = open(self.main_image_path, 'rb')
            if self.interior_image_path:
                files['interior_image'] = open(self.interior_image_path, 'rb')
            if self.exterior_image_path:
                files['exterior_image'] = open(self.exterior_image_path, 'rb')
            
            try:
                # Send multipart form data if images are present, otherwise JSON
                if files:
                    response = requests.post(f"{API_BASE}/api/cars/add/", data=form_data, files=files)
                else:
                    # Convert to proper types for JSON
                    json_data = {
                        'brand': form_data['brand'],
                        'model': form_data['model'],
                        'year': int(form_data['year']),
                        'license_plate': form_data['license_plate'],
                        'color': form_data['color'],
                        'price_per_day': float(form_data['price_per_day']),
                        'description': form_data['description']
                    }
                    response = requests.post(f"{API_BASE}/api/cars/add/", json=json_data)
                
                if response.status_code == 200:
                    self.show_message("Car added successfully!", "success")
                    self.car_added.emit()
                    self.accept()
                else:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('message', 'Failed to add car.')
                    except:
                        error_msg = f"Failed to add car. Status: {response.status_code}"
                    self.show_message(f"Error: {error_msg}", "error")
            
            finally:
                # Close file handles
                for file_handle in files.values():
                    file_handle.close()

        except ValueError:
            self.show_message("Invalid number format for Year or Price.", "error")
        except Exception as e:
            self.show_message(f"An unexpected error occurred: {e}", "error")

    def show_message(self, message, msg_type="info"):
        msg = QMessageBox(self)
        msg.setWindowTitle("Car Information")
        msg.setText(message)
        msg.setIcon(QMessageBox.Information if msg_type == "success" else QMessageBox.Critical)
        msg.exec_()

class BulkAddCarsDialog(QDialog):
    """Dialog for adding multiple sample cars to the database."""
    cars_added = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Sample Cars to Database")
        self.setFixedSize(600, 500)
        self.setStyleSheet("""
            QDialog { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2d3748, stop:1 #1a202c); 
            }
            QLabel {
                color: #e2e8f0; 
                font-weight: bold; 
                background: transparent;
            }
        """)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("🚗 Add Sample Cars to Database")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold; background: transparent;")
        title.setAlignment(Qt.AlignCenter)

        info_label = QLabel("This will add a variety of sample cars with different brands to your database.")
        info_label.setStyleSheet("color: #cbd5e0; font-size: 14px; margin-bottom: 20px; background: transparent;")
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignCenter)

        # Sample cars list display
        self.cars_list = QTextEdit()
        self.cars_list.setReadOnly(True)
        self.cars_list.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                padding: 15px;
                color: white;
                font-size: 12px;
                font-family: 'Courier New', monospace;
            }
        """)
        
        # Populate the list with sample cars
        sample_cars_text = self.get_sample_cars_text()
        self.cars_list.setPlainText(sample_cars_text)

        add_btn = ModernButton("✅ Add All Cars", "#28a745")
        add_btn.clicked.connect(self.add_sample_cars)
        
        cancel_btn = ModernButton("❌ Cancel", "#dc3545")
        cancel_btn.clicked.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addWidget(title)
        layout.addWidget(info_label)
        layout.addWidget(QLabel("Cars to be added:"))
        layout.addWidget(self.cars_list)
        layout.addLayout(btn_layout)

    def get_sample_cars_text(self):
        """Get formatted text of sample cars to be added."""
        sample_cars = self.get_sample_cars_data()
        text_lines = []
        for car in sample_cars:
            text_lines.append(f"• {car['brand']} {car['model']} {car['year']} - {car['license_plate']} - {car['price_per_day']} AED/day")
        return "\n".join(text_lines)

    def get_sample_cars_data(self):
        """Get sample cars data to add to database."""
        return [
            {"brand": "Toyota", "model": "Camry", "year": 2023, "license_plate": "TOY-001", "color": "White", "price_per_day": 150, "description": "Reliable sedan with excellent fuel economy"},
            {"brand": "Honda", "model": "Civic", "year": 2022, "license_plate": "HON-002", "color": "Silver", "price_per_day": 140, "description": "Compact car perfect for city driving"},
            {"brand": "BMW", "model": "X5", "year": 2023, "license_plate": "BMW-003", "color": "Black", "price_per_day": 350, "description": "Luxury SUV with premium features"},
            {"brand": "Mercedes", "model": "C-Class", "year": 2022, "license_plate": "MER-004", "color": "Blue", "price_per_day": 300, "description": "Elegant luxury sedan"},
            {"brand": "Audi", "model": "A4", "year": 2023, "license_plate": "AUD-005", "color": "Gray", "price_per_day": 280, "description": "Sporty luxury sedan with advanced technology"},
            {"brand": "Ford", "model": "Mustang", "year": 2022, "license_plate": "FOR-006", "color": "Red", "price_per_day": 250, "description": "Iconic American sports car"},
            {"brand": "Chevrolet", "model": "Tahoe", "year": 2023, "license_plate": "CHE-007", "color": "Black", "price_per_day": 320, "description": "Full-size SUV perfect for families"},
            {"brand": "Nissan", "model": "Altima", "year": 2022, "license_plate": "NIS-008", "color": "White", "price_per_day": 145, "description": "Comfortable midsize sedan"},
            {"brand": "Hyundai", "model": "Tucson", "year": 2023, "license_plate": "HYU-009", "color": "Silver", "price_per_day": 180, "description": "Compact SUV with modern features"},
            {"brand": "Tesla", "model": "Model 3", "year": 2023, "license_plate": "TES-010", "color": "White", "price_per_day": 400, "description": "Electric luxury sedan with autopilot"},
            {"brand": "Lexus", "model": "RX", "year": 2022, "license_plate": "LEX-011", "color": "Pearl", "price_per_day": 380, "description": "Premium luxury SUV"},
            {"brand": "Porsche", "model": "911", "year": 2023, "license_plate": "POR-012", "color": "Yellow", "price_per_day": 800, "description": "High-performance sports car"},
            {"brand": "Volkswagen", "model": "Jetta", "year": 2022, "license_plate": "VOL-013", "color": "Blue", "price_per_day": 160, "description": "German engineering compact sedan"},
            {"brand": "Mazda", "model": "CX-5", "year": 2023, "license_plate": "MAZ-014", "color": "Red", "price_per_day": 190, "description": "Stylish crossover SUV"},
            {"brand": "Kia", "model": "Sorento", "year": 2022, "license_plate": "KIA-015", "color": "Gray", "price_per_day": 200, "description": "Family-friendly SUV with warranty"},
        ]

    def add_sample_cars(self):
        """Add all sample cars to the database."""
        sample_cars = self.get_sample_cars_data()
        added_count = 0
        failed_count = 0
        
        progress_dialog = QProgressDialog("Adding cars to database...", "Cancel", 0, len(sample_cars), self)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.show()
        
        for i, car_data in enumerate(sample_cars):
            if progress_dialog.wasCanceled():
                break
                
            try:
                response = requests.post(f"{API_BASE}/api/cars/add/", json=car_data, timeout=10)
                if response.status_code == 200:
                    added_count += 1
                else:
                    failed_count += 1
                    print(f"Failed to add {car_data['brand']} {car_data['model']}: {response.status_code}")
            except Exception as e:
                failed_count += 1
                print(f"Error adding {car_data['brand']} {car_data['model']}: {str(e)}")
            
            progress_dialog.setValue(i + 1)
            QApplication.processEvents()
        
        progress_dialog.close()
        
        # Show results
        if added_count > 0:
            QMessageBox.information(
                self, 
                "Cars Added Successfully", 
                f"Successfully added {added_count} cars to the database.\n"
                f"Failed to add {failed_count} cars."
            )
            self.cars_added.emit()
            self.accept()
        else:
            QMessageBox.warning(
                self, 
                "No Cars Added", 
                f"Failed to add any cars to the database.\n"
                f"Please check your server connection and try again."
            )

class AddCustomerDialog(QDialog):
    """Dialog for adding a new customer to the system."""
    customer_added = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Customer")
        self.setFixedSize(500, 800)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c);
            }
            QLabel {
                color: #e2e8f0; 
                font-weight: bold; 
                margin-top: 10px;
                background: transparent;
            }
        """)
        
        # Initialize image paths
        self.profile_image_path = None
        self.license_image_path = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout for the dialog
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area for the content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c);
                border: none;
            }
        """)

        # Content widget inside the scroll area
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c);
            }
        """)
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("👥 Add New Customer")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        
        self.name_input = ModernInput("Full Name")
        self.email_input = ModernInput("Email")
        self.phone_input = ModernInput("Phone Number")
        self.national_id_input = ModernInput("National ID")
        self.nationality_input = ModernInput("Nationality")
        
        # --- Use QDateEdit for date fields ---
        self.dob_input = QDateEdit()
        self.dob_input.setCalendarPopup(True)
        self.dob_input.setDisplayFormat("yyyy-MM-dd")
        self.dob_input.setDate(QDate.currentDate().addYears(-18))  # Default to 18 years ago
        self.dob_input.setStyleSheet("""
            QDateEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                padding: 15px;
                color: white;
                font-size: 14px;
            }
        """)
        
        self.license_input = ModernInput("License Number")
        
        self.license_expiry_input = QDateEdit()
        self.license_expiry_input.setCalendarPopup(True)
        self.license_expiry_input.setDisplayFormat("yyyy-MM-dd")
        self.license_expiry_input.setDate(QDate.currentDate().addYears(1))  # Default to 1 year from now
        self.license_expiry_input.setStyleSheet("""
            QDateEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                padding: 15px;
                color: white;
                font-size: 14px;
            }
        """)
        
        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Address")
        self.address_input.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px; padding: 15px; color: white; font-size: 14px;
            }
        """)
        self.address_input.setMaximumHeight(60)
        
        # Image upload sections
        images_layout = QHBoxLayout()
        
        # Profile Image Section
        profile_section = QVBoxLayout()
        profile_label = QLabel("📷 Profile Image:")
        profile_label.setStyleSheet("color: #e2e8f0; font-weight: bold; background: transparent;")
        
        self.profile_image_label = QLabel("No image selected")
        self.profile_image_label.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.1);
                border: 2px dashed rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 20px;
                color: rgba(255, 255, 255, 0.7);
                text-align: center;
                min-height: 100px;
            }
        """)
        self.profile_image_label.setAlignment(Qt.AlignCenter)
        
        profile_btn = ModernButton("📁 Select Profile Image", "#17a2b8")
        profile_btn.clicked.connect(self.select_profile_image)
        
        profile_section.addWidget(profile_label)
        profile_section.addWidget(self.profile_image_label)
        profile_section.addWidget(profile_btn)
        
        # License Image Section
        license_section = QVBoxLayout()
        license_label = QLabel("🆔 License Image:")
        license_label.setStyleSheet("color: #e2e8f0; font-weight: bold; background: transparent;")
        
        self.license_image_label = QLabel("No image selected")
        self.license_image_label.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.1);
                border: 2px dashed rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 20px;
                color: rgba(255, 255, 255, 0.7);
                text-align: center;
                min-height: 100px;
            }
        """)
        self.license_image_label.setAlignment(Qt.AlignCenter)
        
        license_btn = ModernButton("📁 Select License Image", "#17a2b8")
        license_btn.clicked.connect(self.select_license_image)
        
        license_section.addWidget(license_label)
        license_section.addWidget(self.license_image_label)
        license_section.addWidget(license_btn)
        
        images_layout.addLayout(profile_section)
        images_layout.addLayout(license_section)
        
        buttons_layout = QHBoxLayout()
        save_btn = ModernButton("💾 Save Customer", "#28a745")
        save_btn.clicked.connect(self.save_customer)
        cancel_btn = ModernButton("❌ Cancel", "#dc3545")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addWidget(title)
        layout.addWidget(self.name_input)
        layout.addWidget(self.email_input)
        layout.addWidget(self.phone_input)
        layout.addWidget(QLabel("Address:"))
        layout.addWidget(self.address_input)
        layout.addWidget(self.national_id_input)
        layout.addWidget(self.nationality_input)
        layout.addWidget(QLabel("Date of Birth:"))
        layout.addWidget(self.dob_input)
        layout.addWidget(self.license_input)
        layout.addWidget(QLabel("License Expiry:"))
        layout.addWidget(self.license_expiry_input)
        layout.addLayout(images_layout)
        layout.addStretch()
        layout.addLayout(buttons_layout)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def select_profile_image(self):
        """Open file dialog to select profile image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Profile Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.profile_image_path = file_path
            # Show preview
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.profile_image_label.setPixmap(scaled_pixmap)
            self.profile_image_label.setText("")

    def select_license_image(self):
        """Open file dialog to select license image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select License Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.license_image_path = file_path
            # Show preview
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.license_image_label.setPixmap(scaled_pixmap)
            self.license_image_label.setText("")

    def save_customer(self):
        """Validates and sends customer data with images to the API."""
        try:
            # Prepare form data for multipart upload
            import requests
            
            # Basic customer data
            data = {
                'full_name': self.name_input.text(),
                'email': self.email_input.text(),
                'phone_number': self.phone_input.text(),
                'address': self.address_input.toPlainText(),
                'National_ID': self.national_id_input.text(),
                'Nationality': self.nationality_input.text(),
                'date_of_birth': self.dob_input.date().toString("yyyy-MM-dd"),
                'License_Number': self.license_input.text(),
                'License_Expiry_Date': self.license_expiry_input.date().toString("yyyy-MM-dd")
            }

            if not all([data['full_name'], data['email'], data['National_ID']]):
                self.show_message("Please fill Name, Email, and National ID.", "error")
                return

            # Prepare files for upload
            files = {}
            if self.profile_image_path:
                files['profile_image'] = open(self.profile_image_path, 'rb')
            if self.license_image_path:
                files['license_image'] = open(self.license_image_path, 'rb')

            try:
                # Send multipart form data
                response = requests.post(f"{API_BASE}/api/customers/register/", data=data, files=files)
                
                if response.status_code == 200:
                    self.show_message("Customer added successfully!", "success")
                    self.customer_added.emit()
                    self.accept()
                else:
                    error_msg = response.json().get('error', 'Failed to add customer.')
                    self.show_message(f"Error: {error_msg}", "error")
            finally:
                # Close file handles
                for file_handle in files.values():
                    file_handle.close()
                    
        except Exception as e:
            self.show_message(f"An error occurred: {str(e)}", "error")

    def show_message(self, message, msg_type="info"):
        msg = QMessageBox(self)
        msg.setWindowTitle("Customer Information")
        msg.setText(message)
        msg.setIcon(QMessageBox.Information if msg_type == "success" else QMessageBox.Critical)
        msg.exec_()

# =============================================================================
# NEW DIALOG WINDOWS FOR RENTALS AND VIOLATIONS (INTEGRATED)
# =============================================================================

class CreateRentalDialog(QDialog):
    """Dialog for creating a new rental."""
    rental_created = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Rental")
        self.setFixedSize(500, 550)  # Increased height for tax and discount fields
        self.setStyleSheet("""
            QDialog { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2d3748, stop:1 #1a202c); 
            }
            QLabel {
                color: #e2e8f0; 
                font-weight: bold; 
                margin-top: 10px;
                background: transparent;
            }
        """)
        self.setup_ui()
        self.load_customers_and_cars()
        
    def setup_ui(self):
        # Main layout for the dialog
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area for the content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; }")

        # Content widget inside the scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("📝 Create New Rental")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold; margin-bottom: 10px; background: transparent;")
        title.setAlignment(Qt.AlignCenter)

        combo_style = """
            QComboBox {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px; padding: 12px; color: white;
                font-size: 14px; min-height: 25px;
            }
        """
        date_style = """
            QDateEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px; padding: 12px; color: white;
                font-size: 14px; min-height: 25px;
            }
        """

        self.customer_combo = QComboBox()
        self.customer_combo.setStyleSheet(combo_style)

        self.car_combo = QComboBox()
        self.car_combo.setStyleSheet(combo_style)

        self.start_date = QDateEdit(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        self.start_date.setStyleSheet(date_style)

        self.end_date = QDateEdit(QDate.currentDate().addDays(1))
        self.end_date.setCalendarPopup(True)
        self.end_date.setStyleSheet(date_style)

        # Tax and Discount fields
        input_style = """
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                padding: 12px;
                color: white;
                font-size: 14px;
                min-height: 25px;
            }
            QLineEdit:focus {
                border: 2px solid #f59e0b;
                background: rgba(255, 255, 255, 0.15);
            }
        """
        
        self.tax_input = QLineEdit()
        self.tax_input.setPlaceholderText("Tax amount (AED) - Optional")
        self.tax_input.setStyleSheet(input_style)
        
        self.discount_input = QLineEdit()
        self.discount_input.setPlaceholderText("Discount amount (AED) - Optional")
        self.discount_input.setStyleSheet(input_style)

        create_btn = ModernButton("✅ Create Rental", "#28a745")
        create_btn.clicked.connect(self.create_rental)
        
        cancel_btn = ModernButton("❌ Cancel", "#dc3545")
        cancel_btn.clicked.connect(self.reject)

        content_layout.addWidget(title)
        content_layout.addWidget(QLabel("Select Customer:"))
        content_layout.addWidget(self.customer_combo)
        content_layout.addWidget(QLabel("Select Car:"))
        content_layout.addWidget(self.car_combo)
        
        date_layout = QHBoxLayout()
        start_group = QVBoxLayout()
        start_group.addWidget(QLabel("Start Date:"))
        start_group.addWidget(self.start_date)
        
        end_group = QVBoxLayout()
        end_group.addWidget(QLabel("End Date:"))
        end_group.addWidget(self.end_date)
        
        date_layout.addLayout(start_group)
        date_layout.addLayout(end_group)
        
        content_layout.addLayout(date_layout)
        
        # Add tax and discount fields to the layout
        content_layout.addWidget(QLabel("Tax Amount (AED):"))
        content_layout.addWidget(self.tax_input)
        content_layout.addWidget(QLabel("Discount Amount (AED):"))
        content_layout.addWidget(self.discount_input)
        
        content_layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        content_layout.addLayout(btn_layout)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def load_customers_and_cars(self):
        try:
            # Load customers
            response_cust = requests.get(f"{API_BASE}/api/customers/")
            if response_cust.status_code == 200:
                customers = response_cust.json().get('data', [])
                for customer in customers:
                    self.customer_combo.addItem(f"{customer['full_name']} ({customer['National_ID']})", customer['id'])

            # Load available cars
            response_cars = requests.get(f"{API_BASE}/api/cars/available/")
            if response_cars.status_code == 200:
                cars = response_cars.json().get('data', [])
                for car in cars:
                    self.car_combo.addItem(f"{car['brand']} {car['model']} ({car['license_plate']})", car['id'])
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Network Error", f"Could not load data from server:\n{e}")

    def create_rental(self):
        # Validate tax and discount inputs
        tax_amount = 0.0
        discount_amount = 0.0
        
        if self.tax_input.text().strip():
            try:
                tax_amount = float(self.tax_input.text().strip())
                if tax_amount < 0:
                    QMessageBox.warning(self, "Error", "Tax amount cannot be negative.")
                    return
            except ValueError:
                QMessageBox.warning(self, "Error", "Please enter a valid tax amount.")
                return
        
        if self.discount_input.text().strip():
            try:
                discount_amount = float(self.discount_input.text().strip())
                if discount_amount < 0:
                    QMessageBox.warning(self, "Error", "Discount amount cannot be negative.")
                    return
            except ValueError:
                QMessageBox.warning(self, "Error", "Please enter a valid discount amount.")
                return
        
        rental_data = {
            'customer_id': self.customer_combo.currentData(),
            'car_id': self.car_combo.currentData(),
            'start_date': self.start_date.date().toString('yyyy-MM-dd'),
            'end_date': self.end_date.date().toString('yyyy-MM-dd'),
            'tax_amount': tax_amount,
            'discount_amount': discount_amount
        }
        
        if not rental_data['customer_id'] or not rental_data['car_id']:
            QMessageBox.warning(self, "Error", "Please select a customer and a car.")
            return

        response = requests.post(f"{API_BASE}/api/rentals/create/", json=rental_data)
        
        if response.status_code == 200:
            response_data = response.json()
            rental_id = response_data.get('rental_id')
            
            # Show success message with contract option
            msg = QMessageBox()
            msg.setWindowTitle("Success")
            msg.setText("Rental created successfully!")
            msg.setInformativeText("Would you like to view and download the rental contract?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.Yes)
            
            result = msg.exec_()
            
            if result == QMessageBox.Yes and rental_id:
                # Open contract in browser
                import webbrowser
                contract_url = f"{API_BASE}/api/rentals/{rental_id}/contract/"
                webbrowser.open(contract_url)
            
            self.rental_created.emit()
            self.accept()
        else:
            # Improved error handling
            try:
                error_detail = response.json().get('message') or response.json().get('error') or str(response.json())
            except Exception:
                error_detail = response.text
            QMessageBox.warning(self, "Error", f"Failed to create rental: {error_detail}")

class AddViolationDialog(QDialog):
    """Dialog for adding violation to a rental."""
    violation_added = pyqtSignal()
    
    def __init__(self, rental_id, parent=None):
        super().__init__(parent)
        self.rental_id = rental_id
        self.setWindowTitle("Add Violation")
        self.setFixedSize(450, 450)
        self.setStyleSheet("""
            QDialog { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2d3748, stop:1 #1a202c); 
            }
            QLabel {
                color: #e2e8f0; 
                font-weight: bold; 
                margin-top: 10px;
                background: transparent;
            }
        """)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("⚠️ Add Violation")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold; background:transparent;")
        title.setAlignment(Qt.AlignCenter)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Speeding", "Illegal Parking", "Running Red Light", "Accident", "Other"])
        self.type_combo.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.1); border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px; padding: 12px; color: white;
                font-size: 14px; min-height: 25px;
            }
        """)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Description of violation...")
        self.description_input.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.1); border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px; padding: 15px; color: white;
                font-size: 14px; min-height: 80px;
            }
        """)

        self.fine_input = ModernInput("Fine Amount (AED)")
        self.fine_input.setValidator(QDoubleValidator(0.0, 99999.99, 2))


        add_btn = ModernButton("➕ Add Violation", "#dc3545")
        add_btn.clicked.connect(self.add_violation)
        
        cancel_btn = ModernButton("❌ Cancel", "#6c757d")
        cancel_btn.clicked.connect(self.reject)

        layout.addWidget(title)
        layout.addWidget(QLabel("Violation Type:"))
        layout.addWidget(self.type_combo)
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.description_input)
        layout.addWidget(self.fine_input)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)


    def add_violation(self):
        try:
            violation_data = {
                'rental_id': self.rental_id,
                'violation_type': self.type_combo.currentText().lower().replace(' ', '_'),
                'description': self.description_input.toPlainText(),
                'fine_amount': float(self.fine_input.text()) if self.fine_input.text() else 0
            }
            
            response = requests.post(f"{API_BASE}/api/violations/add/", json=violation_data)
            
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Violation added successfully!")
                self.violation_added.emit()
                self.accept()
            else:
                error_detail = response.json().get('error', 'Unknown error')
                QMessageBox.warning(self, "Error", f"Failed to add violation: {error_detail}")
        except ValueError:
             QMessageBox.warning(self, "Input Error", "Please enter a valid fine amount.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")


# --- Authentication Windows ---

# --- Authentication Windows ---

class LoginWindow(GradientWidget):
    """Login window for user authentication."""
    login_success = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__(['#f6ad55', '#dd6b20'])
        self.setWindowTitle("Renty - Car Rental System")
        self.setFixedSize(400, 600)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet("background: transparent; color: white; font-size: 16px; font-weight: bold;")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.close)
        
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        top_layout.addWidget(close_btn)
        
        # Logo image
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "renty.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # Scale the logo to a reasonable size while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(200, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setStyleSheet("background: transparent; margin-bottom: 10px;")
        else:
            # Fallback to text if logo not found
            logo_label.setText("🚗 Renty")
            logo_label.setStyleSheet("color: white; font-size: 32px; font-weight: bold; margin-bottom: 20px; background: transparent;")
            logo_label.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("Car Rental Management System")
        subtitle.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 16px; background: transparent;")
        subtitle.setAlignment(Qt.AlignCenter)
        
        self.username_input = ModernInput("Username")
        self.password_input = ModernInput("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        login_btn = ModernButton("Login")
        login_btn.clicked.connect(self.handle_login)
        
        signup_btn = ModernButton("Sign Up", "#28a745")
        signup_btn.clicked.connect(self.show_signup)
        
        main_layout.addLayout(top_layout)
        main_layout.addStretch(1)
        main_layout.addWidget(logo_label)
        main_layout.addWidget(subtitle)
        main_layout.addSpacing(40)
        main_layout.addWidget(self.username_input)
        main_layout.addWidget(self.password_input)
        main_layout.addSpacing(20)
        main_layout.addWidget(login_btn)
        main_layout.addWidget(signup_btn)
        main_layout.addStretch(2)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            self.show_message("Please fill all fields", "error")
            return
        
        try:
            response = requests.post(f"{API_BASE}/api/auth/login/", 
                                     json={'username': username, 'password': password}, timeout=5)
            
            if response.status_code == 200:
                payload = response.json()
                user_data = payload.get('user', payload)
                self.login_success.emit(user_data)
                self.close()
            else:
                self.show_message("Invalid credentials. Please try again.", "error")
        except requests.exceptions.RequestException as e:
            self.show_message(f"Network error: Could not connect to the server.\n{e}", "error")

    def show_signup(self):
        self.signup_window = SignupWindow()
        self.signup_window.signup_success.connect(self.on_signup_success)
        self.signup_window.show()

    def on_signup_success(self):
        self.show_message("Account created successfully! Please login.", "success")

    def show_message(self, message, msg_type):
        msg = QMessageBox(self)
        msg.setWindowTitle("Login")
        msg.setText(message)
        msg.setIcon(QMessageBox.Critical if msg_type == "error" else QMessageBox.Information)
        msg.exec_()

class SignupWindow(GradientWidget):
    """Signup window for new user registration."""
    signup_success = pyqtSignal()
    
    def __init__(self):
        super().__init__(['#28a745', '#20c997'])
        self.setWindowTitle("Sign Up")
        self.setFixedSize(400, 700)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        close_btn = QPushButton("✕")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet("background: transparent; color: white; font-size: 16px; font-weight: bold;")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.close)
        
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        top_layout.addWidget(close_btn)
        
        title = QLabel("Create Account")
        title.setStyleSheet("color: white; font-size: 28px; font-weight: bold; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        
        self.username_input = ModernInput("Username")
        self.email_input = ModernInput("Email")
        self.password_input = ModernInput("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input = ModernInput("Confirm Password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        
        signup_btn = ModernButton("Create Account", "#17a2b8")
        signup_btn.clicked.connect(self.handle_signup)
        
        back_btn = ModernButton("Back to Login", "#6c757d")
        back_btn.clicked.connect(self.close)
        
        main_layout.addLayout(top_layout)
        main_layout.addWidget(title)
        main_layout.addSpacing(30)
        main_layout.addWidget(self.username_input)
        main_layout.addWidget(self.email_input)
        main_layout.addWidget(self.password_input)
        main_layout.addWidget(self.confirm_password_input)
        main_layout.addSpacing(20)
        main_layout.addWidget(signup_btn)
        main_layout.addWidget(back_btn)
        main_layout.addStretch()

    def handle_signup(self):
        username = self.username_input.text()
        email = self.email_input.text()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        if not all([username, email, password, confirm_password]):
            self.show_message("Please fill all fields", "error")
            return
            
        if password != confirm_password:
            self.show_message("Passwords do not match", "error")
            return
            
        try:
            response = requests.post(f"{API_BASE}/api/auth/signup/",
                                     json={'username': username, 'email': email, 'password': password}, timeout=5)
            
            if response.status_code == 200:
                self.signup_success.emit()
                self.close()
            else:
                error_msg = response.json().get('error', 'Signup failed.')
                self.show_message(f"Error: {error_msg}", "error")
        except requests.exceptions.RequestException as e:
            self.show_message(f"Network error: Could not connect to the server.\n{e}", "error")

    def show_message(self, message, msg_type):
        msg = QMessageBox(self)
        msg.setWindowTitle("Sign Up")
        msg.setText(message)
        msg.setIcon(QMessageBox.Critical if msg_type == "error" else QMessageBox.Information)
        msg.exec_()




# =============================================================================
# NEW MANAGEMENT PAGE WIDGETS (INTEGRATED)
# =============================================================================

class RentalsManagementPage(QWidget):
    """Widget to manage rentals."""
    data_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; color: white;")
        self.setup_ui()
        self.load_rentals_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        header_layout = QHBoxLayout()
        title = QLabel("📝 Rentals Management")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        
        create_rental_btn = ModernButton("+ Create Rental", "#007bff")
        create_rental_btn.setFixedWidth(200)
        create_rental_btn.clicked.connect(self.show_create_rental_dialog)
        
        refresh_btn = ModernButton("🔄 Refresh", "#17a2b8")
        refresh_btn.setFixedWidth(150)
        refresh_btn.clicked.connect(self.load_rentals_data)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        header_layout.addWidget(create_rental_btn)
        
        self.rentals_table = QTableWidget()
        # Using a shared setup method from the main window would be ideal
        # but for simplicity, we define it here.
        self.setup_table_style(self.rentals_table, "rgba(0, 123, 255, 0.8)")
        
        buttons_layout = QHBoxLayout()
        
        self.add_violation_btn = ModernButton("⚠️ Add Violation", "#ffc107")
        self.add_violation_btn.clicked.connect(self.add_violation_to_rental)
        
        self.complete_rental_btn = ModernButton("✅ Complete Rental", "#28a745")
        self.complete_rental_btn.clicked.connect(self.complete_rental)
        
        self.generate_invoice_btn = ModernButton("📄 View Invoice PDF", "#17a2b8")
        self.generate_invoice_btn.clicked.connect(self.generate_invoice)
        
        self.edit_rental_btn = ModernButton("✏️ Edit Rental", "#ffc107")
        self.edit_rental_btn.clicked.connect(self.edit_selected_rental)
        
        self.delete_rental_btn = ModernButton("🗑️ Delete Rental", "#dc3545")
        self.delete_rental_btn.clicked.connect(self.delete_selected_rental)
        
        buttons_layout.addWidget(self.add_violation_btn)
        buttons_layout.addWidget(self.complete_rental_btn)
        buttons_layout.addWidget(self.generate_invoice_btn)
        buttons_layout.addWidget(self.edit_rental_btn)
        buttons_layout.addWidget(self.delete_rental_btn)
        buttons_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.rentals_table)
        main_layout.addLayout(buttons_layout)

    def setup_table_style(self, table, header_color):
        table.setAlternatingRowColors(False)  # Disable alternating row colors
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Allow multi-select
        
        # Enable smooth scrolling
        table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        
        # Set scroll bar policies to show when needed
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        table.setStyleSheet(f"""
            QTableWidget {{
                background: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 10px;
                color: white;
                gridline-color: #4a5568;
            }}
            QTableWidget::item {{
                background: #2d3748;  /* Set all rows to dark background */
                padding: 10px;
                border-bottom: 1px solid #4a5568;
            }}
            QTableWidget::item:selected {{
                background: rgba(102, 126, 234, 0.4);
            }}
            QHeaderView::section {{
                background: {header_color};
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }}
            /* Vertical Scrollbar */
            QTableWidget QScrollBar:vertical {{
                border: none;
                background: #1a202c;
                width: 14px;
                border-radius: 7px;
            }}
            QTableWidget QScrollBar::handle:vertical {{
                background: #4a5568;
                min-height: 20px;
                border-radius: 7px;
                margin: 2px;
            }}
            QTableWidget QScrollBar::handle:vertical:hover {{
                background: #f59e0b;
            }}
            QTableWidget QScrollBar::handle:vertical:pressed {{
                background: #9c4221;
            }}
            QTableWidget QScrollBar::add-line:vertical,
            QTableWidget QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            QTableWidget QScrollBar::add-page:vertical,
            QTableWidget QScrollBar::sub-page:vertical {{
                background: none;
            }}
            /* Horizontal Scrollbar */
            QTableWidget QScrollBar:horizontal {{
                border: none;
                background: #1a202c;
                height: 14px;
                border-radius: 7px;
            }}
            QTableWidget QScrollBar::handle:horizontal {{
                background: #4a5568;
                min-width: 20px;
                border-radius: 7px;
                margin: 2px;
            }}
            QTableWidget QScrollBar::handle:horizontal:hover {{
                background: #f59e0b;
            }}
            QTableWidget QScrollBar::handle:horizontal:pressed {{
                background: #9c4221;
            }}
            QTableWidget QScrollBar::add-line:horizontal,
            QTableWidget QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
            }}
            QTableWidget QScrollBar::add-page:horizontal,
            QTableWidget QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """)

    def load_rentals_data(self):
        try:
            response = requests.get(f"{API_BASE}/api/rentals/history/")
            if response.status_code == 200:
                rentals = response.json().get('data', [])
                self.display_rentals(rentals)
        except requests.exceptions.RequestException as e:
            print(f"Could not load rentals data: {e}")

    def display_rentals(self, rentals):
        self.rentals_table.setRowCount(0) # Clear table
        self.rentals_table.setRowCount(len(rentals))
        self.rentals_table.setColumnCount(12)
        headers = ["ID", "Customer", "Car", "Start Date", "End Date", "Total Price", "Tax", "Discount", "Status", "Violations", "Invoice ID", "Contract"]
        self.rentals_table.setHorizontalHeaderLabels(headers)
        
        for row, rental in enumerate(rentals):
            # Store rental data in the first item of each row for easy access
            item_id = QTableWidgetItem(str(rental['id']))
            item_id.setData(Qt.UserRole, rental) # Store the whole dictionary
            self.rentals_table.setItem(row, 0, item_id)
            
            self.rentals_table.setItem(row, 1, QTableWidgetItem(rental.get('customer', 'N/A')))
            self.rentals_table.setItem(row, 2, QTableWidgetItem(rental.get('car', 'N/A')))
            self.rentals_table.setItem(row, 3, QTableWidgetItem(rental.get('start_date', 'N/A')))
            self.rentals_table.setItem(row, 4, QTableWidgetItem(rental.get('end_date', 'N/A')))
            self.rentals_table.setItem(row, 5, QTableWidgetItem(f"{rental.get('total_price', 0)} AED"))
            
            # Add tax and discount columns
            tax_amount = rental.get('tax_amount', 0)
            discount_amount = rental.get('discount_amount', 0)
            self.rentals_table.setItem(row, 6, QTableWidgetItem(f"{tax_amount} AED" if tax_amount > 0 else "N/A"))
            self.rentals_table.setItem(row, 7, QTableWidgetItem(f"{discount_amount} AED" if discount_amount > 0 else "N/A"))
            
            status_item = QTableWidgetItem(rental['status'].title())
            if rental['status'] == 'active':
                status_item.setForeground(QColor("#28a745")) # Green
            elif rental['status'] == 'completed':
                status_item.setForeground(QColor("#17a2b8")) # Blue
            self.rentals_table.setItem(row, 8, status_item)
            
            violations_text = f"{rental.get('violations_count', 0)} ({rental.get('violations_amount', 0)} AED)"
            self.rentals_table.setItem(row, 9, QTableWidgetItem(violations_text))
            
            invoice_text = str(rental.get('invoice_id', 'N/A'))
            self.rentals_table.setItem(row, 10, QTableWidgetItem(invoice_text))
            
            # Add contract button
            contract_btn = QPushButton("📄 View Contract")
            contract_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4a9b8e;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #3d8275;
                }
            """)
            contract_btn.clicked.connect(lambda checked, r_id=rental['id']: self.view_rental_contract(r_id))
            self.rentals_table.setCellWidget(row, 11, contract_btn)
            
        self.rentals_table.resizeColumnsToContents()
        self.rentals_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.rentals_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)


    def view_rental_contract(self, rental_id):
        """Open rental contract in browser"""
        try:
            import webbrowser
            contract_url = f"{API_BASE}/api/rentals/{rental_id}/contract/"
            webbrowser.open(contract_url)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open contract: {str(e)}")

    def show_create_rental_dialog(self):
        dialog = CreateRentalDialog(self)
        dialog.rental_created.connect(self.load_rentals_data)
        dialog.rental_created.connect(self.data_changed.emit) # Notify main window
        dialog.exec_()

    def get_selected_rental(self):
        current_row = self.rentals_table.currentRow()
        if current_row >= 0:
            return self.rentals_table.item(current_row, 0).data(Qt.UserRole)
        return None

    def add_violation_to_rental(self):
        rental = self.get_selected_rental()
        if rental:
            if rental['status'] != 'active':
                QMessageBox.warning(self, "Action Denied", "Cannot add violations to a completed rental.")
                return
            dialog = AddViolationDialog(rental['id'], self)
            dialog.violation_added.connect(self.load_rentals_data)
            dialog.violation_added.connect(self.data_changed.emit)
            dialog.exec_()
        else:
            QMessageBox.warning(self, "Selection Required", "Please select a rental from the table.")

    def complete_rental(self):
        rental = self.get_selected_rental()
        if rental:
            response = requests.post(f"{API_BASE}/api/rentals/complete/", json={'rental_id': rental['id']})
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Rental completed and invoice generated!")
                self.load_rentals_data()
                self.data_changed.emit()
            else:
                error = response.json().get('error', 'Failed to complete rental.')
                QMessageBox.warning(self, "Error", error)
        else:
            QMessageBox.warning(self, "Selection Required", "Please select a rental from the table.")

    def generate_invoice(self):
        rental = self.get_selected_rental()
        if rental:
            invoice_id = rental.get('invoice_id')
            if invoice_id:
                try:
                    webbrowser.open(f"{API_BASE}/api/invoices/{invoice_id}/pdf/")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not open invoice PDF: {e}")
            else:
                QMessageBox.warning(self, "No Invoice", "No invoice found for this rental. Please complete the rental first.")
        else:
            QMessageBox.warning(self, "Selection Required", "Please select a rental from the table.")
    
    def edit_selected_rental(self):
        rental = self.get_selected_rental()
        if not rental:
            QMessageBox.warning(self, "No Selection", "Please select a rental to edit.")
            return
        
        if rental['status'] == 'completed':
            QMessageBox.warning(self, "Action Denied", "Cannot edit a completed rental.")
            return
        
        # For simplicity, we'll open a blank dialog. In a full implementation,
        # you would fetch the rental data and pre-fill the dialog.
        dialog = CreateRentalDialog(self)
        # This dialog should be modified to handle updates instead of just creations.
        # This would involve changing the API endpoint and request method (e.g., PUT or PATCH).
        if dialog.exec_() == QDialog.Accepted:
            self.load_rentals_data()
            self.data_changed.emit()

    def delete_selected_rental(self):
        rental = self.get_selected_rental()
        if not rental:
            QMessageBox.warning(self, "No Selection", "Please select a rental to delete.")
            return
            
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete rental #{rental['id']}?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return
            
        try:
            response = requests.delete(f"{API_BASE}/api/rentals/{rental['id']}/delete/")
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Rental deleted successfully!")
                self.load_rentals_data()
                self.data_changed.emit()
            else:
                error_msg = response.json().get('message', 'Unknown error')
                QMessageBox.warning(self, "Delete Failed", f"Failed to delete rental: {error_msg}")
        except Exception as e:
            QMessageBox.warning(self, "Delete Failed", f"Failed to delete rental: {e}")


class InvoicesManagementPage(QWidget):
    """Widget to manage invoices. (Placeholder)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel(f"🧾 Invoices Management - Coming Soon!")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        layout.addWidget(label)
        
class ViolationsManagementPage(QWidget):
    """Widget to manage violations. (Placeholder)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel(f"⚠️ Violations Management - Coming Soon!")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        layout.addWidget(label)

class CreateUserDialog(QDialog):
    """Dialog for creating a new user."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New User")
        self.setFixedSize(450, 600)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c);
            }
            QLabel {
                color: #e2e8f0; 
                font-weight: bold; 
                margin-top: 10px;
                background: transparent;
            }
        """)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        title = QLabel("👤 Create New User")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Username
        layout.addWidget(QLabel("Username:"))
        self.username_input = ModernInput("Enter username")
        layout.addWidget(self.username_input)
        
        # Email
        layout.addWidget(QLabel("Email:"))
        self.email_input = ModernInput("Enter email address")
        layout.addWidget(self.email_input)
        
        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_input = ModernInput("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        
        # First Name
        layout.addWidget(QLabel("First Name:"))
        self.first_name_input = ModernInput("Enter first name")
        layout.addWidget(self.first_name_input)
        
        # Last Name
        layout.addWidget(QLabel("Last Name:"))
        self.last_name_input = ModernInput("Enter last name")
        layout.addWidget(self.last_name_input)
        
        # Role checkboxes
        roles_layout = QHBoxLayout()
        
        self.admin_checkbox = QCheckBox("Admin")
        self.admin_checkbox.setStyleSheet("""
            QCheckBox {
                color: white;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background: #f6ad55;
                border: 2px solid #f59e0b;
                border-radius: 3px;
            }
        """)
        
        self.agent_checkbox = QCheckBox("Agent")
        self.agent_checkbox.setStyleSheet(self.admin_checkbox.styleSheet())
        
        self.active_checkbox = QCheckBox("Active")
        self.active_checkbox.setChecked(True)  # Default to active
        self.active_checkbox.setStyleSheet(self.admin_checkbox.styleSheet())
        
        roles_layout.addWidget(self.admin_checkbox)
        roles_layout.addWidget(self.agent_checkbox)
        roles_layout.addWidget(self.active_checkbox)
        roles_layout.addStretch()
        
        layout.addWidget(QLabel("Roles:"))
        layout.addLayout(roles_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        cancel_btn = ModernButton("Cancel", "#6c757d")
        cancel_btn.clicked.connect(self.reject)
        
        create_btn = ModernButton("Create User", "#28a745")
        create_btn.clicked.connect(self.create_user)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(create_btn)
        
        layout.addLayout(buttons_layout)
    
    def create_user(self):
        # Validate input
        if not all([self.username_input.text().strip(), self.password_input.text().strip()]):
            QMessageBox.warning(self, "Validation Error", "Username and password are required.")
            return
        
        user_data = {
            'username': self.username_input.text().strip(),
            'email': self.email_input.text().strip(),
            'password': self.password_input.text().strip(),
            'first_name': self.first_name_input.text().strip(),
            'last_name': self.last_name_input.text().strip(),
            'is_admin': self.admin_checkbox.isChecked(),
            'is_agent': self.agent_checkbox.isChecked(),
            'is_active': self.active_checkbox.isChecked()
        }
        
        try:
            response = requests.post(f"{API_BASE}/api/users/create/", 
                                   json=user_data, timeout=5)
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "User created successfully!")
                self.accept()
            else:
                error_msg = response.json().get('message', 'Unknown error occurred')
                QMessageBox.warning(self, "Error", f"Failed to create user: {error_msg}")
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Network Error", f"Could not create user: {e}")

class EditUserDialog(QDialog):
    """Dialog for editing an existing user."""
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Edit User")
        self.setFixedSize(450, 600)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c);
            }
            QLabel {
                color: #e2e8f0; 
                font-weight: bold; 
                margin-top: 10px;
                background: transparent;
            }
        """)
        self.setup_ui()
        self.load_user_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        title = QLabel("✏️ Edit User")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Username
        layout.addWidget(QLabel("Username:"))
        self.username_input = ModernInput("Enter username")
        layout.addWidget(self.username_input)
        
        # Email
        layout.addWidget(QLabel("Email:"))
        self.email_input = ModernInput("Enter email address")
        layout.addWidget(self.email_input)
        
        # Password (optional for editing)
        layout.addWidget(QLabel("New Password (leave blank to keep current):"))
        self.password_input = ModernInput("Enter new password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        
        # First Name
        layout.addWidget(QLabel("First Name:"))
        self.first_name_input = ModernInput("Enter first name")
        layout.addWidget(self.first_name_input)
        
        # Last Name
        layout.addWidget(QLabel("Last Name:"))
        self.last_name_input = ModernInput("Enter last name")
        layout.addWidget(self.last_name_input)
        
        # Role checkboxes
        roles_layout = QHBoxLayout()
        
        self.admin_checkbox = QCheckBox("Admin")
        self.admin_checkbox.setStyleSheet("""
            QCheckBox {
                color: white;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background: #667eea;
                border: 2px solid #667eea;
                border-radius: 3px;
            }
        """)
        
        self.agent_checkbox = QCheckBox("Agent")
        self.agent_checkbox.setStyleSheet(self.admin_checkbox.styleSheet())
        
        self.active_checkbox = QCheckBox("Active")
        self.active_checkbox.setStyleSheet(self.admin_checkbox.styleSheet())
        
        roles_layout.addWidget(self.admin_checkbox)
        roles_layout.addWidget(self.agent_checkbox)
        roles_layout.addWidget(self.active_checkbox)
        roles_layout.addStretch()
        
        layout.addWidget(QLabel("Roles:"))
        layout.addLayout(roles_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        cancel_btn = ModernButton("Cancel", "#6c757d")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = ModernButton("Save Changes", "#28a745")
        save_btn.clicked.connect(self.save_user)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_user_data(self):
        try:
            response = requests.get(f"{API_BASE}/api/users/", timeout=5)
            if response.status_code == 200:
                users = response.json().get('data', [])
                user = next((u for u in users if u['id'] == self.user_id), None)
                if user:
                    self.username_input.setText(user.get('username', ''))
                    self.email_input.setText(user.get('email', ''))
                    self.first_name_input.setText(user.get('first_name', ''))
                    self.last_name_input.setText(user.get('last_name', ''))
                    self.admin_checkbox.setChecked(user.get('is_admin', False))
                    self.agent_checkbox.setChecked(user.get('is_agent', False))
                    self.active_checkbox.setChecked(user.get('is_active', True))
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Network Error", f"Could not load user data: {e}")
    
    def save_user(self):
        # Validate input
        if not self.username_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Username is required.")
            return
        
        user_data = {
            'username': self.username_input.text().strip(),
            'email': self.email_input.text().strip(),
            'first_name': self.first_name_input.text().strip(),
            'last_name': self.last_name_input.text().strip(),
            'is_admin': self.admin_checkbox.isChecked(),
            'is_agent': self.agent_checkbox.isChecked(),
            'is_active': self.active_checkbox.isChecked()
        }
        
        # Only include password if it's provided
        if self.password_input.text().strip():
            user_data['password'] = self.password_input.text().strip()
        
        try:
            response = requests.put(f"{API_BASE}/api/users/{self.user_id}/update/", 
                                  json=user_data, timeout=5)
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "User updated successfully!")
                self.accept()
            else:
                error_msg = response.json().get('message', 'Unknown error occurred')
                QMessageBox.warning(self, "Error", f"Failed to update user: {error_msg}")
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Network Error", f"Could not update user: {e}")

class UsersManagementPage(QWidget):
    """Widget to manage users (Admin only)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_users_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        header_layout = QHBoxLayout()
        title = QLabel("👤 Users Management")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")

        create_user_btn = ModernButton("+ Add User", "#007bff")
        create_user_btn.setFixedWidth(150)
        create_user_btn.clicked.connect(self.show_create_user_dialog)

        refresh_btn = ModernButton("🔄 Refresh", "#17a2b8")
        refresh_btn.setFixedWidth(120)
        refresh_btn.clicked.connect(self.load_users_data)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        header_layout.addWidget(create_user_btn)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(8)
        self.users_table.setHorizontalHeaderLabels(["ID", "Username", "Email", "Full Name", "Admin", "Agent", "Active", "Date Joined"])
        self.setup_table_style(self.users_table, "rgba(0, 123, 255, 0.8)")

        buttons_layout = QHBoxLayout()
        self.edit_user_btn = ModernButton("✏️ Edit User", "#ffc107")
        self.edit_user_btn.clicked.connect(self.edit_selected_user)
        self.delete_user_btn = ModernButton("🗑️ Delete User", "#dc3545")
        self.delete_user_btn.clicked.connect(self.delete_selected_user)
        buttons_layout.addWidget(self.edit_user_btn)
        buttons_layout.addWidget(self.delete_user_btn)
        buttons_layout.addStretch()

        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.users_table)
        main_layout.addLayout(buttons_layout)

    def setup_table_style(self, table, header_color):
        table.setAlternatingRowColors(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table.setStyleSheet(f"""
            QTableWidget {{ background: #2d3748; border: 1px solid #4a5568; border-radius: 10px; color: white; gridline-color: #4a5568; }}
            QTableWidget::item {{ background: #2d3748; padding: 10px; border-bottom: 1px solid #4a5568; }}
            QTableWidget::item:selected {{ background: rgba(102, 126, 234, 0.4); }}
            QHeaderView::section {{ background: {header_color}; color: white; padding: 12px; border: none; font-weight: bold; font-size: 14px; }}
        """)

    def load_users_data(self):
        try:
            response = requests.get(f"{API_BASE}/api/users/", timeout=5)
            if response.status_code == 200:
                response_data = response.json()
                # Backend returns {'status': 'success', 'data': [...]}
                if isinstance(response_data, dict) and response_data.get('status') == 'success':
                    users = response_data.get('data', [])
                elif isinstance(response_data, list):
                    users = response_data
                else:
                    users = []
                
                self.users_table.setRowCount(len(users))
                for row, user in enumerate(users):
                    # ID column
                    id_item = QTableWidgetItem(str(user.get('id', '')))
                    id_item.setData(Qt.UserRole, user.get('id'))
                    self.users_table.setItem(row, 0, id_item)
                    
                    # Username
                    self.users_table.setItem(row, 1, QTableWidgetItem(user.get('username', '')))
                    
                    # Email
                    self.users_table.setItem(row, 2, QTableWidgetItem(user.get('email', '')))
                    
                    # Full Name (combine first_name and last_name from backend)
                    first_name = user.get('first_name', '')
                    last_name = user.get('last_name', '')
                    full_name = f"{first_name} {last_name}".strip() or 'N/A'
                    self.users_table.setItem(row, 3, QTableWidgetItem(full_name))
                    
                    # Admin status with color coding
                    admin_item = QTableWidgetItem("✅ Yes" if user.get('is_admin', False) else "❌ No")
                    if user.get('is_admin', False):
                        admin_item.setForeground(QColor("#28a745"))
                    else:
                        admin_item.setForeground(QColor("#dc3545"))
                    self.users_table.setItem(row, 4, admin_item)
                    
                    # Agent status with color coding
                    agent_item = QTableWidgetItem("✅ Yes" if user.get('is_agent', False) else "❌ No")
                    if user.get('is_agent', False):
                        agent_item.setForeground(QColor("#28a745"))
                    else:
                        agent_item.setForeground(QColor("#dc3545"))
                    self.users_table.setItem(row, 5, agent_item)
                    
                    # Active status with color coding
                    active_item = QTableWidgetItem("✅ Active" if user.get('is_active', True) else "❌ Inactive")
                    if user.get('is_active', True):
                        active_item.setForeground(QColor("#28a745"))
                    else:
                        active_item.setForeground(QColor("#dc3545"))
                    self.users_table.setItem(row, 6, active_item)
                    
                    # Date joined
                    date_joined = user.get('date_joined', 'N/A')
                    if date_joined and date_joined != 'N/A':
                        # Format the date if it's a datetime string
                        try:
                            from datetime import datetime
                            dt = datetime.strptime(date_joined, '%Y-%m-%d %H:%M:%S')
                            date_joined = dt.strftime('%Y-%m-%d')
                        except:
                            pass  # Keep original format if parsing fails
                    self.users_table.setItem(row, 7, QTableWidgetItem(str(date_joined)))
                
                self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                
                if len(users) == 0:
                    QMessageBox.information(self, "Info", "No users found in the system.")
                    
            else:
                QMessageBox.warning(self, "API Error", f"Failed to load users. Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Network Error", f"Could not load users data: {e}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"An error occurred while loading users: {e}")

    def show_create_user_dialog(self):
        dialog = CreateUserDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_users_data()

    def edit_selected_user(self):
        selected_rows = self.users_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a user to edit.")
            return
        user_id = self.users_table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        dialog = EditUserDialog(user_id, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_users_data()

    def delete_selected_user(self):
        selected_rows = self.users_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a user to delete.")
            return
        user_id = self.users_table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        username = self.users_table.item(selected_rows[0].row(), 0).text()
        reply = QMessageBox.question(self, "Confirm Deletion", f"Are you sure you want to delete user '{username}'?\n\nThis action cannot be undone.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                response = requests.delete(f"{API_BASE}/api/users/{user_id}/delete/", timeout=5)
                if response.status_code == 200:
                    QMessageBox.information(self, "Success", "User deleted successfully!")
                    self.load_users_data()
                else:
                    error_msg = response.json().get('message', 'Unknown error occurred')
                    QMessageBox.warning(self, "Error", f"Failed to delete user: {error_msg}")
            except requests.exceptions.RequestException as e:
                QMessageBox.warning(self, "Network Error", f"Could not delete user: {e}")

class MaintenanceReportPage(QWidget):
    """Page for adding maintenance records and viewing daily reports."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; color: white;")
        self.setup_ui()
        # Load cars after UI is fully initialized - use direct call since UI is now properly set up
        self.load_cars()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        header_layout = QHBoxLayout()
        title = QLabel("🛠️ Maintenance & Daily Report")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        container = QHBoxLayout()

        maint_group = QFrame()
        maint_group.setStyleSheet("QFrame { background: #2d3748; border-radius: 10px; padding: 16px; }")
        maint_layout = QVBoxLayout(maint_group)
        maint_title = QLabel("Add Maintenance Record")
        maint_title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        maint_layout.addWidget(maint_title)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        self.car_combo = QComboBox()
        self.car_combo.setStyleSheet("QComboBox { background: rgba(255,255,255,0.1); border: 2px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 10px; color: white; }")
        self.amount_input = ModernInput("Amount (e.g., 150.00)")
        self.amount_input.setValidator(QDoubleValidator(0.0, 9999999.99, 2))
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Description (optional)")
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setStyleSheet("QTextEdit { background: rgba(255,255,255,0.1); border: 2px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 10px; color: white; }")
        self.maint_date = QDateEdit(QDate.currentDate())
        self.maint_date.setCalendarPopup(True)
        self.maint_date.setDisplayFormat("yyyy-MM-dd")
        self.maint_date.setStyleSheet("QDateEdit { background: rgba(255,255,255,0.1); border: 2px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 10px; color: white; }")
        form.addRow("Car:", self.car_combo)
        form.addRow("Amount:", self.amount_input)
        form.addRow("Description:", self.desc_input)
        form.addRow("Date:", self.maint_date)
        maint_layout.addLayout(form)
        submit_btn = ModernButton("➕ Add Maintenance", "#28a745")
        submit_btn.clicked.connect(self.submit_maintenance)
        maint_layout.addWidget(submit_btn)

        report_group = QFrame()
        report_group.setStyleSheet("QFrame { background: #2d3748; border-radius: 10px; padding: 16px; }")
        report_layout = QVBoxLayout(report_group)
        report_title = QLabel("Daily Financial Report")
        report_title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        report_layout.addWidget(report_title)
        filter_layout = QHBoxLayout()
        
        # Single date selection
        single_date_layout = QVBoxLayout()
        single_label = QLabel("Single Date Report:")
        single_label.setStyleSheet("color: #e2e8f0; font-weight: bold;")
        single_date_layout.addWidget(single_label)
        
        single_row = QHBoxLayout()
        self.report_date = QDateEdit(QDate.currentDate())
        self.report_date.setCalendarPopup(True)
        self.report_date.setDisplayFormat("yyyy-MM-dd")
        self.report_date.setStyleSheet("QDateEdit { background: rgba(255,255,255,0.1); border: 2px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 10px; color: white; }")
        fetch_btn = ModernButton("📅 Fetch Report", "#17a2b8")
        fetch_btn.clicked.connect(self.fetch_report)
        single_row.addWidget(QLabel("Date:"))
        single_row.addWidget(self.report_date)
        single_row.addWidget(fetch_btn)
        single_date_layout.addLayout(single_row)
        
        # Date range selection
        range_date_layout = QVBoxLayout()
        range_label = QLabel("Date Range Report:")
        range_label.setStyleSheet("color: #e2e8f0; font-weight: bold;")
        range_date_layout.addWidget(range_label)
        
        range_row = QHBoxLayout()
        self.from_date = QDateEdit(QDate.currentDate().addDays(-7))
        self.from_date.setCalendarPopup(True)
        self.from_date.setDisplayFormat("yyyy-MM-dd")
        self.from_date.setStyleSheet("QDateEdit { background: rgba(255,255,255,0.1); border: 2px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 10px; color: white; }")
        
        self.to_date = QDateEdit(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        self.to_date.setDisplayFormat("yyyy-MM-dd")
        self.to_date.setStyleSheet("QDateEdit { background: rgba(255,255,255,0.1); border: 2px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 10px; color: white; }")
        
        fetch_range_btn = ModernButton("📊 Fetch Range Report", "#28a745")
        fetch_range_btn.clicked.connect(self.fetch_range_report)
        
        range_row.addWidget(QLabel("From:"))
        range_row.addWidget(self.from_date)
        range_row.addWidget(QLabel("To:"))
        range_row.addWidget(self.to_date)
        range_row.addWidget(fetch_range_btn)
        range_date_layout.addLayout(range_row)
        
        filter_layout.addLayout(single_date_layout)
        filter_layout.addWidget(QLabel("  |  "))  # Separator
        filter_layout.addLayout(range_date_layout)
        report_layout.addLayout(filter_layout)
        self.rentals_count_label = QLabel("Rentals: 0")
        self.rental_revenue_label = QLabel("Rental Revenue: 0.00")
        self.maintenance_expenses_label = QLabel("Maintenance Expenses: 0.00")
        self.net_income_label = QLabel("Net Income: 0.00")
        for lbl in [self.rentals_count_label, self.rental_revenue_label, self.maintenance_expenses_label, self.net_income_label]:
            lbl.setStyleSheet("color: #e2e8f0; font-size: 16px; font-weight: bold;")
            report_layout.addWidget(lbl)
        self.report_message = QLabel("")
        self.report_message.setStyleSheet("color: #cbd5e0;")
        report_layout.addWidget(self.report_message)

        container.addWidget(maint_group, 1)
        container.addWidget(report_group, 1)
        main_layout.addLayout(container)

    def fetch_range_report(self):
        from_date_str = self.from_date.date().toString("yyyy-MM-dd")
        to_date_str = self.to_date.date().toString("yyyy-MM-dd")
        
        if self.from_date.date() > self.to_date.date():
            QMessageBox.warning(self, "Invalid Range", "From date must be before or equal to To date.")
            return
            
        try:
            # Fetch data for each day in the range
            current_date = self.from_date.date()
            end_date = self.to_date.date()
            
            total_rentals = 0
            total_revenue = 0.0
            total_maintenance = 0.0
            
            while current_date <= end_date:
                date_str = current_date.toString("yyyy-MM-dd")
                resp = requests.get(f"{API_BASE}/api/reports/daily/", params={"date": date_str}, timeout=8)
                
                if resp.status_code == 200:
                    data = resp.json()
                    total_rentals += int(data.get('rentals_count', 0))
                    total_revenue += float(data.get('rentals_revenue', 0) or 0)
                    total_maintenance += float(data.get('maintenance_total', 0) or 0)
                
                current_date = current_date.addDays(1)
            
            net_income = total_revenue - total_maintenance
            
            self.rentals_count_label.setText(f"Total Rentals: {total_rentals}")
            self.rental_revenue_label.setText(f"Total Revenue: {total_revenue:.2f}")
            self.maintenance_expenses_label.setText(f"Total Maintenance: {total_maintenance:.2f}")
            self.net_income_label.setText(f"Net Income: {net_income:.2f}")
            
            if total_rentals == 0 and total_revenue == 0 and total_maintenance == 0:
                self.report_message.setText(f"No data for range {from_date_str} to {to_date_str}. Showing zeros.")
            else:
                days_count = self.from_date.date().daysTo(self.to_date.date()) + 1
                self.report_message.setText(f"Range report: {from_date_str} to {to_date_str} ({days_count} days)")
                
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Network Error", f"Could not fetch range report: {e}")

    def load_cars(self):
        try:
            resp = requests.get(f"{API_BASE}/api/cars/available/", timeout=5)
            if resp.status_code == 200:
                cars = resp.json().get('data', [])
                self.car_combo.clear()
                for car in cars:
                    self.car_combo.addItem(f"{car.get('brand','')} {car.get('model','')} ({car.get('license_plate','')})", car.get('id'))
            else:
                QMessageBox.warning(self, "Error", f"Failed to load cars: {resp.status_code}")
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Network Error", f"Could not load cars: {e}")

    def submit_maintenance(self):
        car_id = self.car_combo.currentData()
        amount_text = self.amount_input.text().strip()
        desc = self.desc_input.toPlainText().strip()
        date_str = self.maint_date.date().toString("yyyy-MM-dd")
        if not car_id or not amount_text:
            QMessageBox.warning(self, "Validation Error", "Car and Amount are required.")
            return
        try:
            amount = float(amount_text)
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Amount must be a number.")
            return
        payload = {"car_id": car_id, "amount": amount, "description": desc, "date": date_str}
        try:
            resp = requests.post(f"{API_BASE}/api/maintenance/add/", json=payload, timeout=8)
            if resp.status_code == 200:
                QMessageBox.information(self, "Success", "Maintenance record added.")
                self.amount_input.clear()
                self.desc_input.clear()
            else:
                try:
                    msg = resp.json().get('message', resp.text)
                except Exception:
                    msg = resp.text
                QMessageBox.warning(self, "Error", f"Failed to add maintenance: {msg}")
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Network Error", f"Could not add maintenance: {e}")

    def fetch_report(self):
        date_str = self.report_date.date().toString("yyyy-MM-dd")
        try:
            resp = requests.get(f"{API_BASE}/api/reports/daily/", params={"date": date_str}, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                # Backend returns data directly, not nested in 'data' key
                rentals_count = int(data.get('rentals_count', 0))
                rental_revenue = float(data.get('rentals_revenue', 0) or 0)  # Note: backend uses 'rentals_revenue'
                maintenance_expenses = float(data.get('maintenance_total', 0) or 0)  # Note: backend uses 'maintenance_total'
                net_income = rental_revenue - maintenance_expenses
                
                self.rentals_count_label.setText(f"Rentals: {rentals_count}")
                self.rental_revenue_label.setText(f"Rental Revenue: {rental_revenue:.2f}")
                self.maintenance_expenses_label.setText(f"Maintenance Expenses: {maintenance_expenses:.2f}")
                self.net_income_label.setText(f"Net Income: {net_income:.2f}")
                
                if rentals_count == 0 and rental_revenue == 0 and maintenance_expenses == 0:
                    self.report_message.setText("No data for the selected date. Showing zeros.")
                else:
                    self.report_message.setText(f"Report for {data.get('date', date_str)}")
            else:
                QMessageBox.warning(self, "Error", f"Failed to fetch report: {resp.status_code}")
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Network Error", f"Could not fetch report: {e}")


class DashboardWindow(QMainWindow):
    """The main dashboard window after a successful login."""
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.setWindowTitle("Car Rental Dashboard")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)
        
        # Set a dark theme for the main window
        self.setStyleSheet("QMainWindow { background: #1a202c; }")
        
        self.setup_ui()
        self.load_dashboard_data()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = self.create_sidebar()
        
        # Main Content Area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 10, 20, 20)
        
        # Header
        header = self.create_header()
        
        # Stats Cards Container
        self.stats_container = QHBoxLayout()
        self.stats_container.setSpacing(20)
        
        # Content Stack for different pages
        self.content_stack = QStackedWidget()
        self.setup_content_pages()
        
        content_layout.addWidget(header)
        content_layout.addLayout(self.stats_container)
        content_layout.addWidget(self.content_stack, 1) # Give stack more stretch factor
        
        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_area, 1)

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            QFrame {
                background: #2d3748;
                border-right: 1px solid #4a5568;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        logo = QLabel("Renty")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("""
            color: white; font-size: 20px; font-weight: bold;
            padding: 20px; background: rgba(255, 153, 0, 0.2);
            border-radius: 10px; margin: 10px;
        """)
        
        logo_path = os.path.join(os.path.dirname(__file__), "renty.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # Make logo more prominent in header with better shape
            scaled_pixmap = pixmap.scaled(100, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label = QLabel()
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setStyleSheet("""
                background: transparent; 
                margin-right: 20px;
                border: 2px solid rgba(255, 153, 0, 0.3);
                border-radius: 8px;
                padding: 5px;
            """)
            layout.addWidget(logo_label)
        else:
            layout.addWidget(logo)
        
        nav_buttons = [
            ("📊 Dashboard", 0), ("🚗 Cars", 1), ("👥 Customers", 2),
            ("📝 Rentals", 3)
        ]
        
        # Add Users Management for admin users only
        # Insert Maintenance & Report at index 4, so Users page shifts to 5 if present
        nav_buttons.append(("🛠️ Maintenance & Report", 4))
        if self.user_data.get('is_admin', False):
            nav_buttons.append(("👤 Users Management", 5))
        
        layout.addWidget(logo)
        layout.addSpacing(20)
        
        for text, index in nav_buttons:
            btn = QPushButton(text)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #e2e8f0; border: none;
                    padding: 15px; font-size: 14px; text-align: left;
                    border-radius: 8px;
                }
                QPushButton:hover { background: rgba(102, 126, 234, 0.3); color: white; }
                QPushButton:pressed { background: rgba(102, 126, 234, 0.5); }
            """)
            btn.clicked.connect(lambda checked, i=index: self.content_stack.setCurrentIndex(i))
            layout.addWidget(btn)
        
        layout.addStretch()
        
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.setCursor(QCursor(Qt.PointingHandCursor))
        logout_btn.setStyleSheet("""
            QPushButton {
                background: rgba(220, 53, 69, 0.8); color: white; border: none;
                padding: 15px; border-radius: 8px; margin: 10px; font-size: 14px;
            }
            QPushButton:hover { background: rgba(220, 53, 69, 1); }
        """)
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)
        
        return sidebar

    def create_header(self):
        header = QFrame()
        header.setFixedHeight(100)
        header.setStyleSheet("""
            QFrame { background: #2d3748; border-radius: 10px; padding: 15px; }
        """)
        
        layout = QHBoxLayout(header)
        
        # Logo and company info section
        logo_section = QHBoxLayout()
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "renty.png")
        
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # Make logo more prominent in header with better shape
            scaled_pixmap = pixmap.scaled(100, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setStyleSheet("""
                background: transparent; 
                margin-right: 20px;
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 8px;
                padding: 5px;
            """)
            
            # Company name and subtitle
            company_info = QVBoxLayout()
            company_name = QLabel("")
            company_name.setStyleSheet("""
                color: white; 
                font-size: 24px; 
                font-weight: bold; 
                background: transparent; 
                margin: 0px;
            """)
            
            company_subtitle = QLabel("")
            company_subtitle.setStyleSheet("""
                color: rgba(255,255,255,0.9); 
                font-size: 13px; 
                background: transparent; 
                margin: 0px;
            """)
            
            company_info.addWidget(company_name)
            company_info.addWidget(company_subtitle)
            company_info.setSpacing(2)
            
            logo_section.addWidget(logo_label)
            logo_section.addLayout(company_info)
        else:
            # Fallback text logo
            fallback_logo = QLabel("🚗 Renty")
            fallback_logo.setStyleSheet("color: white; font-size: 24px; font-weight: bold; background: transparent;")
            logo_section.addWidget(fallback_logo)
        
        # Welcome message
        welcome = QLabel(f"Welcome back, {self.user_data['username']}!")
        welcome.setStyleSheet("color: white; font-size: 16px; font-weight: bold; background: transparent;")
        
        # Determine role badge based on user privileges
        if self.user_data.get('is_admin', False):
            role_badge = QLabel("🔑 Admin")
        elif self.user_data.get('is_agent', False):
            role_badge = QLabel("👨‍💼 Agent")
        else:
            role_badge = QLabel("👤 User")
        role_badge.setAlignment(Qt.AlignCenter)
        role_badge.setStyleSheet("""
            background: rgba(102, 126, 234, 0.8); color: white;
            padding: 8px 16px; border-radius: 15px;
            font-size: 12px; font-weight: bold;
        """)
        
        layout.addLayout(logo_section)
        layout.addStretch()
        layout.addWidget(welcome)
        layout.addWidget(role_badge)
        return header

    def setup_content_pages(self):
        self.dashboard_page = self.create_dashboard_page()
        self.cars_page = self.create_cars_page()
        self.customers_page = self.create_customers_page()
        self.rentals_page = RentalsManagementPage()
        self.maintenance_report_page = MaintenanceReportPage()

        self.content_stack.addWidget(self.dashboard_page)
        self.content_stack.addWidget(self.cars_page)
        self.content_stack.addWidget(self.customers_page)
        self.content_stack.addWidget(self.rentals_page)
        self.content_stack.addWidget(self.maintenance_report_page)
        
        # Add Users Management page for admin users only
        if self.user_data.get('is_admin', False):
            self.users_page = UsersManagementPage()
            self.content_stack.addWidget(self.users_page)

    def create_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("📊 Dashboard Overview")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold; margin: 10px;")
        
        refresh_btn = ModernButton("🔄 Refresh All Data", "#17a2b8")
        refresh_btn.clicked.connect(self.refresh_all_data)
        refresh_btn.setFixedWidth(200)

        header_layout = QHBoxLayout()
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)
        layout.addStretch()
        return page
    
    def refresh_all_data(self):
        self.load_dashboard_data()
        self.load_cars_data()
        self.load_customers_data()
        self.rentals_page.load_rentals_data() # Refresh rentals page too

    def create_cars_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        header_layout = QHBoxLayout()
        title = QLabel("🚗 Cars Management")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        
        add_car_btn = ModernButton("+ Add Car", "#28a745")
        add_car_btn.setFixedWidth(150)
        add_car_btn.clicked.connect(self.show_add_car_dialog)
        
        bulk_add_btn = ModernButton("📦 Add Sample Cars", "#6f42c1")
        bulk_add_btn.setFixedWidth(180)
        bulk_add_btn.clicked.connect(self.show_bulk_add_cars_dialog)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(add_car_btn)
        header_layout.addWidget(bulk_add_btn)

        refresh_btn = ModernButton("🔄 Refresh", "#17a2b8")
        refresh_btn.setFixedWidth(120)
        refresh_btn.clicked.connect(self.load_cars_data)
        header_layout.addWidget(refresh_btn)
        
        edit_car_btn = ModernButton("✏️ Edit Car", "#ffc107")
        edit_car_btn.setFixedWidth(120)
        edit_car_btn.clicked.connect(self.edit_selected_car)
        header_layout.addWidget(edit_car_btn)
        
        delete_car_btn = ModernButton("🗑️ Delete Car", "#dc3545")
        delete_car_btn.setFixedWidth(130)
        delete_car_btn.clicked.connect(self.delete_selected_cars)
        header_layout.addWidget(delete_car_btn)

        self.cars_table = QTableWidget()
        self.setup_table_style(self.cars_table)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.cars_table)
        self.load_cars_data()
        return page

    def create_customers_page(self):
        page = QWidget()
        main_layout = QVBoxLayout(page)
        main_layout.setSpacing(20)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        title = QLabel("👥 Customer Profiles Dashboard")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        
        add_customer_btn = ModernButton("+ Add Customer", "#28a745")
        add_customer_btn.setFixedWidth(180)
        add_customer_btn.clicked.connect(self.show_add_customer_dialog)
        
        refresh_btn = ModernButton("🔄 Refresh", "#17a2b8")
        refresh_btn.setFixedWidth(120)
        refresh_btn.clicked.connect(self.load_customer_profiles)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        header_layout.addWidget(add_customer_btn)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 Search Customers:")
        search_label.setStyleSheet("color: #e2e8f0; font-size: 14px; font-weight: bold;")
        
        self.customer_search_input = ModernInput("Search by name, email, or National ID...")
        self.customer_search_input.textChanged.connect(self.filter_customer_profiles)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.customer_search_input)
        
        # Customer profiles scroll area
        self.profiles_scroll = QScrollArea()
        self.profiles_scroll.setWidgetResizable(True)
        self.profiles_scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
        """)
        
        # Container widget for customer profile cards
        self.profiles_container = QWidget()
        self.profiles_container.setStyleSheet("background: transparent;")
        self.profiles_layout = QGridLayout(self.profiles_container)
        self.profiles_layout.setSpacing(20)
        self.profiles_layout.setContentsMargins(20, 20, 20, 20)
        
        self.profiles_scroll.setWidget(self.profiles_container)
        
        # Store all customer profile cards for filtering
        self.customer_profile_cards = []
        
        # Traditional table view toggle
        view_toggle_layout = QHBoxLayout()
        self.view_mode_btn = ModernButton("📋 Table View", "#6c757d")
        self.view_mode_btn.setFixedWidth(150)
        self.view_mode_btn.clicked.connect(self.toggle_view_mode)
        
        view_toggle_layout.addStretch()
        view_toggle_layout.addWidget(self.view_mode_btn)
        
        # Traditional table (initially hidden)
        self.customers_table = QTableWidget()
        self.setup_table_style(self.customers_table, header_color="rgba(40, 167, 69, 0.8)")
        self.customers_table.setVisible(False)
        
        table_btn_layout = QHBoxLayout()
        edit_btn = ModernButton("✏️ Edit", "#ffc107")
        delete_btn = ModernButton("🗑️ Delete", "#dc3545")
        edit_btn.clicked.connect(self.edit_selected_customer)
        delete_btn.clicked.connect(self.delete_selected_customers)
        table_btn_layout.addStretch()
        table_btn_layout.addWidget(edit_btn)
        table_btn_layout.addWidget(delete_btn)
        
        # Add all components to main layout
        main_layout.addLayout(header_layout)
        main_layout.addLayout(search_layout)
        main_layout.addLayout(view_toggle_layout)
        main_layout.addWidget(self.profiles_scroll)
        main_layout.addWidget(self.customers_table)
        main_layout.addLayout(table_btn_layout)
        
        # Track current view mode
        self.is_table_view = False
        
        # Load customer profiles
        self.load_customer_profiles()
        return page
        
    def setup_table_style(self, table, header_color="rgba(102, 126, 234, 0.8)"):
        """Applies a consistent modern style to a QTableWidget with enhanced scrolling."""
        table.setAlternatingRowColors(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        # Enable smooth scrolling
        table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        
        # Set scroll bar policies to show when needed
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        table.setStyleSheet(f"""
            QTableWidget {{
                background: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 10px;
                color: white;
                gridline-color: #4a5568;
            }}
            QTableWidget::item {{
                background: #2d3748;
                padding: 10px;
                border-bottom: 1px solid #4a5568;
            }}
            QTableWidget::item:selected {{
                background: rgba(102, 126, 234, 0.4);
            }}
            QHeaderView::section {{
                background: {header_color};
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }}
            /* Vertical Scrollbar */
            QTableWidget QScrollBar:vertical {{
                border: none;
                background: #1a202c;
                width: 14px;
                border-radius: 7px;
            }}
            QTableWidget QScrollBar::handle:vertical {{
                background: #4a5568;
                min-height: 20px;
                border-radius: 7px;
                margin: 2px;
            }}
            QTableWidget QScrollBar::handle:vertical:hover {{
                background: #667eea;
            }}
            QTableWidget QScrollBar::handle:vertical:pressed {{
                background: #553c9a;
            }}
            QTableWidget QScrollBar::add-line:vertical,
            QTableWidget QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            QTableWidget QScrollBar::add-page:vertical,
            QTableWidget QScrollBar::sub-page:vertical {{
                background: none;
            }}
            /* Horizontal Scrollbar */
            QTableWidget QScrollBar:horizontal {{
                border: none;
                background: #1a202c;
                height: 14px;
                border-radius: 7px;
            }}
            QTableWidget QScrollBar::handle:horizontal {{
                background: #4a5568;
                min-width: 20px;
                border-radius: 7px;
                margin: 2px;
            }}
            QTableWidget QScrollBar::handle:horizontal:hover {{
                background: #667eea;
            }}
            QTableWidget QScrollBar::handle:horizontal:pressed {{
                background: #553c9a;
            }}
            QTableWidget QScrollBar::add-line:horizontal,
            QTableWidget QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
            }}
            QTableWidget QScrollBar::add-page:horizontal,
            QTableWidget QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """)

    def load_dashboard_data(self):
        try:
            response = requests.get(f"{API_BASE}/api/dashboard/stats/", timeout=5)
            if response.status_code == 200:
                stats = response.json().get('data', {})
                cards_data = [
                    ("Total Cars", str(stats.get('total_cars', 0)), "🚗"),
                    ("Available", str(stats.get('available_cars', 0)), "✅"),
                    ("Active Rentals", str(stats.get('active_rentals', 0)), "📝"),
                    ("Customers", str(stats.get('total_customers', 0)), "👥"),
                    ("Violations", str(stats.get('total_violations', 0)), "⚠️"),
                    ("Unpaid Bills", str(stats.get('unpaid_invoices', 0)), "💰")
                ]
                
                # Clear existing cards
                while self.stats_container.count():
                    child = self.stats_container.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                
                for title, value, icon in cards_data:
                    self.stats_container.addWidget(ModernCard(title, value, icon))
                self.stats_container.addStretch()
        except requests.exceptions.RequestException as e:
            print(f"Could not load dashboard stats: {e}")

    def load_cars_data(self):
        try:
            response = requests.get(f"{API_BASE}/api/cars/available/", timeout=5)
            if response.status_code == 200:
                cars = response.json().get('data', [])
                self.cars_table.setRowCount(len(cars))
                self.cars_table.setColumnCount(7)
                self.cars_table.setHorizontalHeaderLabels(["Brand", "Model", "Year", "License Plate", "Color", "Price/Day", "Status"])
                
                for row, car in enumerate(cars):
                    # Store car ID in the first item for easy access
                    brand_item = QTableWidgetItem(car.get('brand', 'N/A'))
                    brand_item.setData(Qt.UserRole, car.get('id'))
                    self.cars_table.setItem(row, 0, brand_item)
                    self.cars_table.setItem(row, 1, QTableWidgetItem(car.get('model', 'N/A')))
                    self.cars_table.setItem(row, 2, QTableWidgetItem(str(car.get('year', 'N/A'))))
                    self.cars_table.setItem(row, 3, QTableWidgetItem(car.get('license_plate', 'N/A')))
                    self.cars_table.setItem(row, 4, QTableWidgetItem(car.get('color', 'N/A')))
                    self.cars_table.setItem(row, 5, QTableWidgetItem(f"{car.get('price_per_day', 0)} AED"))
                    
                    status = "✅ Available" if car.get('available', True) else "❌ Rented"
                    status_item = QTableWidgetItem(status)
                    if car.get('available', True):
                        status_item.setForeground(QColor("#28a745"))
                    else:
                        status_item.setForeground(QColor("#dc3545"))
                    self.cars_table.setItem(row, 6, status_item)
                
                self.cars_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        except requests.exceptions.RequestException as e:
            print(f"Could not load car data: {e}")

    def load_customers_data(self):
        try:
            response = requests.get(f"{API_BASE}/api/customers/", timeout=5)
            if response.status_code == 200:
                customers = response.json().get('data', [])
                self.customers_table.setRowCount(len(customers))
                self.customers_table.setColumnCount(5)
                self.customers_table.setHorizontalHeaderLabels(["Full Name", "Email", "Phone", "National ID", "License"])
                
                for row, customer in enumerate(customers):
                    item_name = QTableWidgetItem(customer.get('full_name', 'N/A'))
                    item_name.setData(Qt.UserRole, customer.get('id'))
                    self.customers_table.setItem(row, 0, item_name)
                    self.customers_table.setItem(row, 1, QTableWidgetItem(customer.get('email', 'N/A')))
                    self.customers_table.setItem(row, 2, QTableWidgetItem(customer.get('phone_number', 'N/A')))
                    self.customers_table.setItem(row, 3, QTableWidgetItem(customer.get('National_ID', 'N/A')))
                    self.customers_table.setItem(row, 4, QTableWidgetItem(customer.get('License_Number', 'N/A')))
                
                self.customers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        except requests.exceptions.RequestException as e:
            print(f"Could not load customer data: {e}")

    def show_add_car_dialog(self):
        dialog = AddCarDialog(self)
        dialog.car_added.connect(self.load_cars_data)
        dialog.car_added.connect(self.load_dashboard_data) # Refresh stats
        dialog.exec_()

    def show_bulk_add_cars_dialog(self):
        dialog = BulkAddCarsDialog(self)
        dialog.cars_added.connect(self.load_cars_data)
        dialog.cars_added.connect(self.load_dashboard_data) # Refresh stats
        dialog.exec_()

    def show_add_customer_dialog(self):
        dialog = AddCustomerDialog(self)
        dialog.customer_added.connect(self.load_customers_data)
        dialog.customer_added.connect(self.load_customer_profiles)
        dialog.customer_added.connect(self.load_dashboard_data) # Refresh stats
        dialog.exec_()

    def logout(self):
        """Closes the dashboard and allows the application to exit."""
        self.close()

    def edit_selected_customer(self):
        selected = self.customers_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a customer to edit.")
            return
        
        row = selected[0].row()
        customer_id = self.customers_table.item(row, 0).data(Qt.UserRole)
        if not customer_id:
            QMessageBox.warning(self, "Error", "Could not determine customer ID.")
            return

        # Here you would ideally fetch the full customer details from the API
        # to pre-fill the dialog. For simplicity, we open a blank dialog.
        # response = requests.get(f"{API_BASE}/api/customers/{customer_id}/")
        # if response.status_code == 200:
        #    customer_data = response.json()
        #    dialog = AddCustomerDialog(self)
        #    dialog.prefill_data(customer_data) # You'd need to implement prefill_data
        #    ...
        
        dialog = AddCustomerDialog(self)
        # This dialog should be modified to handle updates instead of just creations.
        # This would involve changing the API endpoint and request method (e.g., PUT or PATCH).
        if dialog.exec_() == QDialog.Accepted:
            self.load_customers_data()

    def delete_selected_customers(self):
        selected_rows = set(idx.row() for idx in self.customers_table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select one or more customers to delete.")
            return
            
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete {len(selected_rows)} customer(s)?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return
            
        for row in sorted(list(selected_rows), reverse=True):
            customer_id_item = self.customers_table.item(row, 0)
            if customer_id_item is not None:
                customer_id = customer_id_item.data(Qt.UserRole)
                if customer_id:
                    try:
                        response = requests.delete(f"{API_BASE}/api/customers/{customer_id}/delete/")
                        if response.status_code != 200:
                             print(f"Failed to delete customer {customer_id}: {response.text}")
                    except Exception as e:
                        print(f"Failed to delete customer: {e}")
        
        # Refresh data after deletion
        self.load_customers_data()
        self.load_customer_profiles()
        self.load_dashboard_data()
    
    def load_customer_profiles(self):
        """Load customer data and create profile cards."""
        try:
            response = requests.get(f"{API_BASE}/api/customers/", timeout=5)
            if response.status_code == 200:
                customers = response.json().get('data', [])
                
                # Clear existing profile cards
                for card in self.customer_profile_cards:
                    card.setParent(None)
                    card.deleteLater()
                self.customer_profile_cards.clear()
                
                # Clear layout
                while self.profiles_layout.count():
                    child = self.profiles_layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                
                # Create profile cards
                row, col = 0, 0
                max_cols = 4  # Number of cards per row
                
                for customer in customers:
                    profile_card = CustomerProfileCard(customer)
                    profile_card.profile_clicked.connect(self.show_customer_profile_dialog)
                    
                    self.profiles_layout.addWidget(profile_card, row, col)
                    self.customer_profile_cards.append(profile_card)
                    
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
                
                # Add stretch to fill remaining space
                self.profiles_layout.setRowStretch(row + 1, 1)
                
        except requests.exceptions.RequestException as e:
            print(f"Could not load customer profiles: {e}")
    
    def filter_customer_profiles(self):
        """Filter customer profile cards based on search input."""
        search_text = self.customer_search_input.text().lower().strip()
        
        for card in self.customer_profile_cards:
            customer_data = card.customer_data
            
            # Check if search text matches name, email, or National ID
            matches = (
                search_text in customer_data.get('full_name', '').lower() or
                search_text in customer_data.get('email', '').lower() or
                search_text in customer_data.get('National_ID', '').lower()
            )
            
            card.setVisible(matches)
    
    def show_customer_profile_dialog(self, customer_data):
        """Show detailed customer profile dialog."""
        dialog = CustomerProfileDialog(customer_data, self)
        dialog.exec_()
    
    def toggle_view_mode(self):
        """Toggle between profile cards view and table view."""
        if self.is_table_view:
            # Switch to profile cards view
            self.profiles_scroll.setVisible(True)
            self.customers_table.setVisible(False)
            self.view_mode_btn.setText("📋 Table View")
            self.is_table_view = False
        else:
            # Switch to table view
            self.profiles_scroll.setVisible(False)
            self.customers_table.setVisible(True)
            self.view_mode_btn.setText("📇 Card View")
            self.is_table_view = True
            # Load table data if not already loaded
            self.load_customers_data()
    
    def edit_selected_car(self):
        selected = self.cars_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a car to edit.")
            return
        
        row = selected[0].row()
        car_id = self.cars_table.item(row, 0).data(Qt.UserRole)
        if not car_id:
            QMessageBox.warning(self, "Error", "Could not determine car ID.")
            return

        # For simplicity, we'll open a blank dialog. In a full implementation,
        # you would fetch the car data and pre-fill the dialog.
        dialog = AddCarDialog(self)
        # This dialog should be modified to handle updates instead of just creations.
        # This would involve changing the API endpoint and request method (e.g., PUT or PATCH).
        if dialog.exec_() == QDialog.Accepted:
            self.load_cars_data()
            self.load_dashboard_data()

    def delete_selected_cars(self):
        selected_rows = set(idx.row() for idx in self.cars_table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select one or more cars to delete.")
            return
            
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete {len(selected_rows)} car(s)?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return
            
        for row in sorted(list(selected_rows), reverse=True):
            car_id_item = self.cars_table.item(row, 0)
            if car_id_item is not None:
                car_id = car_id_item.data(Qt.UserRole)
                if car_id:
                    try:
                        response = requests.delete(f"{API_BASE}/api/cars/{car_id}/delete/")
                        if response.status_code != 200:
                            error_msg = response.json().get('message', 'Unknown error')
                            QMessageBox.warning(self, "Delete Failed", f"Failed to delete car: {error_msg}")
                    except Exception as e:
                        QMessageBox.warning(self, "Delete Failed", f"Failed to delete car: {e}")
        
        # Refresh data after deletion
        self.load_cars_data()
        self.load_dashboard_data()
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginWindow()
    login.show()

    def on_login_success(user_data):
        dashboard = DashboardWindow(user_data)
        dashboard.show()
        login.close()

    login.login_success.connect(on_login_success)
    sys.exit(app.exec_())