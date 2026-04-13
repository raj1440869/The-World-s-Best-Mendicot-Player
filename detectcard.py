import cv2
import numpy as np
from card import Card
import torch
import os

class CNNCardDetector:
    def __init__(self, model_path='best.pt'):
        """
        Initialize CNN-based card detector using YOLOv5 model.
        
        Setup instructions:
        1. Clone the repo: git clone https://github.com/PD-Mera/Playing-Cards-Detection
        2. Install requirements: pip install -r requirements.txt
        3. Download the model weights (best.pt) from the repo
        4. Place best.pt in the same directory as this script
        
        Args:
            model_path: Path to the YOLOv5 weights file (best.pt)
        """
        self.last_card = None
        self.current_card = None
        self.stability_threshold = 5  # Number of consistent frames before accepting new card
        self.consecutive_detections = {}
        
        # Card rank and suit mappings
        self.rank_map = {
            'A': 'Ace', '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
            '7': 7, '8': 8, '9': 9, '10': 10, 'J': 'Jack', 'Q': 'Queen', 'K': 'King'
        }
        
        # Load YOLOv5 model
        try:
            print("Loading YOLOv5 playing card detection model...")
            self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=False)
            self.model.conf = 0.5  # Confidence threshold
            self.model.iou = 0.45  # NMS IOU threshold
            print("✓ Model loaded successfully!")
            self.model_loaded = True
        except Exception as e:
            print(f"⚠ Warning: Could not load model from '{model_path}'")
            print(f"Error: {e}")
            print("\nTo use the YOLOv5 model:")
            print("1. Download best.pt from: https://github.com/PD-Mera/Playing-Cards-Detection")
            print("2. Place it in the same directory as this script")
            print("3. Install: pip install torch torchvision")
            print("\nFalling back to basic detection...")
            self.model_loaded = False
        
        # Class names from the model (52 playing cards)
        # Format: "rank suit" e.g., "A clubs", "K hearts", "10 diamonds", etc.
        self.class_names = self._get_class_names()
    
    def _get_class_names(self):
        """Get the 52 playing card class names"""
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        suits = ['clubs', 'diamonds', 'hearts', 'spades']
        
        class_names = []
        for suit in suits:
            for rank in ranks:
                class_names.append(f"{rank} {suit}")
        
        return class_names
    
    def detect_newest_card_from_camera(self, camera_index=0):
        """
        Continuously monitor camera and detect the most recently placed card.
        Press 'q' to quit, 'r' to reset detection.
        """
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print("Error: Could not open camera")
            return
        
        print("\n" + "="*60)
        print("CARD DETECTION STARTED")
        print("="*60)
        print("Controls:")
        print("  Q - Quit")
        print("  R - Reset (forget current card)")
        print("  SPACE - Force detection of visible card")
        print("\nPlace cards in view to detect them automatically.")
        print("="*60 + "\n")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to read frame")
                break
            
            # Detect all cards in frame using YOLOv5
            detected_cards = self._detect_cards_in_frame(frame)
            
            # Display frame with annotations
            display_frame = self._annotate_frame(frame, detected_cards)
            
            # Track consecutive detections for stability
            if detected_cards:
                # Use the largest (closest) card
                card_info = detected_cards[0]
                card_key = f"{card_info['rank']}_{card_info['suit']}"
                self.consecutive_detections[card_key] = self.consecutive_detections.get(card_key, 0) + 1
                
                # If we've seen this card enough times consistently, it's the new card
                if self.consecutive_detections[card_key] >= self.stability_threshold:
                    # Check if this is different from the current card
                    if self._is_new_card(card_info):
                        self._update_newest_card(card_info)
                        self.consecutive_detections.clear()
            else:
                # No cards detected, slowly decay counters
                for key in list(self.consecutive_detections.keys()):
                    self.consecutive_detections[key] -= 1
                    if self.consecutive_detections[key] <= 0:
                        del self.consecutive_detections[key]
            
            # Show current and last card info
            self._display_card_info(display_frame)
            
            cv2.imshow('Playing Card Detector - Most Recent Card', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\nExiting...")
                break
            elif key == ord('r'):
                print("\n" + "="*50)
                print("RESET - All cards forgotten")
                print("="*50 + "\n")
                self.last_card = None
                self.current_card = None
                self.consecutive_detections.clear()
            elif key == ord(' '):
                if detected_cards:
                    print("\n[SPACE] Forcing detection...")
                    self._update_newest_card(detected_cards[0])
                    self.consecutive_detections.clear()
        
        cap.release()
        cv2.destroyAllWindows()
    
    def _detect_cards_in_frame(self, frame):
        """
        Detect all playing cards in the frame using YOLOv5.
        Returns list of detected cards with their positions and identities.
        """
        if not self.model_loaded:
            return self._detect_cards_fallback(frame)
        
        # Run YOLOv5 inference
        results = self.model(frame)
        
        detected_cards = []
        
        # Parse results
        for detection in results.xyxy[0]:  # xyxy format: [x1, y1, x2, y2, conf, class]
            x1, y1, x2, y2, conf, cls = detection
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            class_id = int(cls)
            confidence = float(conf)
            
            # Get card name from class
            if class_id < len(self.class_names):
                card_name = self.class_names[class_id]
                parts = card_name.split()
                
                if len(parts) >= 2:
                    rank = parts[0]
                    suit = parts[1].capitalize()  # "clubs" -> "Clubs"
                    
                    area = (x2 - x1) * (y2 - y1)
                    
                    detected_cards.append({
                        'rank': rank,
                        'suit': suit,
                        'bbox': (x1, y1, x2 - x1, y2 - y1),
                        'confidence': confidence,
                        'area': area
                    })
        
        # Sort by area (largest first) - newest card is typically largest/closest
        detected_cards.sort(key=lambda c: c['area'], reverse=True)
        
        return detected_cards
    
    def _detect_cards_fallback(self, frame):
        """Fallback detection if model isn't loaded"""
        # Simple contour-based detection (less accurate)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 11, 2)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detected_cards = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 5000:
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = h / w if w > 0 else 0
            
            if 1.2 < aspect_ratio < 1.6:
                detected_cards.append({
                    'rank': '?',
                    'suit': 'Unknown',
                    'bbox': (x, y, w, h),
                    'confidence': 0.5,
                    'area': area
                })
        
        return detected_cards
    
    def _is_new_card(self, new_card_info):
        """Check if this card is different from the current card"""
        if self.current_card is None:
            return True
        
        return (new_card_info['rank'] != self.current_card['rank'] or
                new_card_info['suit'] != self.current_card['suit'])
    
    def _update_newest_card(self, card_info):
        """Update the tracking when a new card is detected"""
        # Move current to last
        self.last_card = self.current_card
        
        # Update current
        self.current_card = card_info
        
        # Convert to Card object
        rank = card_info['rank']
        if rank in self.rank_map:
            rank = self.rank_map[rank]
        
        try:
            card_obj = Card(card_info['suit'], rank)
            value = card_obj.getValue()
        except:
            value = "?"
        
        print("\n" + "="*60)
        print("🃏 NEW CARD DETECTED!")
        print("="*60)
        print(f"  Card: {card_info['rank']} of {card_info['suit']}")
        print(f"  Value: {value}")
        if 'confidence' in card_info:
            print(f"  Confidence: {card_info['confidence']:.2%}")
        print("="*60 + "\n")
    
    def _annotate_frame(self, frame, detected_cards):
        """Draw bounding boxes and labels on detected cards"""
        output = frame.copy()
        
        for i, card in enumerate(detected_cards):
            x, y, w, h = card['bbox']
            
            # Draw bounding box
            if i == 0:
                color = (0, 255, 0)  # Green for newest/largest
                thickness = 3
            else:
                color = (255, 165, 0)  # Orange for others
                thickness = 2
            
            cv2.rectangle(output, (x, y), (x+w, y+h), color, thickness)
            
            # Draw label background
            label = f"{card['rank']} of {card['suit']}"
            if i == 0:
                label += " (ACTIVE)"
            
            if 'confidence' in card:
                label += f" {card['confidence']:.0%}"
            
            (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(output, (x, y - label_h - 10), (x + label_w, y), color, -1)
            
            # Draw label text
            cv2.putText(output, label, (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return output
    
    def _display_card_info(self, frame):
        """Display current and last card information on frame"""
        # Create semi-transparent overlay for info panel
        overlay = frame.copy()
        cv2.rectangle(overlay, (5, 5), (450, 100), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        y_offset = 30
        
        # Current card
        if self.current_card:
            rank = self.current_card['rank']
            if rank in self.rank_map:
                rank_val = self.rank_map[rank]
            else:
                rank_val = rank
            
            try:
                card_obj = Card(self.current_card['suit'], rank_val)
                value = card_obj.getValue()
            except:
                value = "?"
            
            text = f"CURRENT: {self.current_card['rank']} of {self.current_card['suit']} (Val: {value})"
            cv2.putText(frame, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            y_offset += 35
        else:
            cv2.putText(frame, "CURRENT: (none)", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 2)
            y_offset += 35
        
        # Last card
        if self.last_card:
            text = f"LAST: {self.last_card['rank']} of {self.last_card['suit']}"
            cv2.putText(frame, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 2)
        else:
            cv2.putText(frame, "LAST: (none)", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 2)
    
    def get_current_card(self):
        """Get the most recently detected card as a Card object"""
        if self.current_card:
            rank = self.current_card['rank']
            if rank in self.rank_map:
                rank = self.rank_map[rank]
            return Card(self.current_card['suit'], rank)
        return None
    
    def get_last_card(self):
        """Get the previously detected card"""
        if self.last_card:
            rank = self.last_card['rank']
            if rank in self.rank_map:
                rank = self.rank_map[rank]
            return Card(self.last_card['suit'], rank)
        return None


# Run the detector
if __name__ == "__main__":
    # Initialize detector with model path
    # Make sure best.pt is in the same directory or provide full path
    detector = CNNCardDetector(model_path='best.pt')
    detector.detect_newest_card_from_camera()