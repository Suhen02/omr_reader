
import cv2
import numpy as np
import json

class OMRDetector:
    def __init__(self, col_width_tolerance=250, options=None):
        self.col_width_tolerance = col_width_tolerance
        self.options = options if options else ["a", "b", "c", "d"]
    
    def process_image(self, image_input, answer_key=None,
                      output_image="detected_answers.jpg",
                      output_json="results.json"):
        
        # --- FIX: Accept image as a NumPy array or path ---
        if isinstance(image_input, str):
            image = cv2.imread(image_input)
        elif isinstance(image_input, np.ndarray):
            image = image_input
        else:
            raise ValueError("Invalid input. Expected a file path (str) or a NumPy array.")
        # --- END FIX ---

        if image is None:
            raise FileNotFoundError(f"Image could not be loaded from input.")

        # Resize (maintain ratio)
        height, width = image.shape[:2]
        scale = 1000 / width
        image = cv2.resize(image, (int(width * scale), int(height * scale)))

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Adaptive threshold
        thresh = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            9, 2
        )

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        bubbles = []
        min_dim = min(image.shape[0], image.shape[1])
        min_bubble_size = int(min_dim * 0.015)
        max_bubble_size = int(min_dim * 0.05)

        for cnt in contours:
            (x, y, w, h) = cv2.boundingRect(cnt)
            aspect_ratio = w / float(h)

            if (min_bubble_size < w < max_bubble_size and
                min_bubble_size < h < max_bubble_size and
                0.9 < aspect_ratio < 1.1):
                bubbles.append((x, y, w, h))

        # Column-wise sorting
        bubbles = sorted(bubbles, key=lambda b: (b[0] // self.col_width_tolerance, b[1]))

        # Group into 4 options
        grouped_bubbles = [bubbles[i:i + 4] for i in range(0, len(bubbles), 4)]

        detailed_results = {}
        extracted_answers = {}
        question_num = 1
        score = 0

        for row_bubbles in grouped_bubbles:
            row_bubbles = sorted(row_bubbles, key=lambda b: b[0])

            filled = None
            filled_rect = None

            fill_counts = []
            for (x, y, w, h) in row_bubbles:
                roi = thresh[y:y+h, x:x+w]
                fill_counts.append(cv2.countNonZero(roi))

            if fill_counts:
                max_fill_in_row = max(fill_counts)
                max_index = fill_counts.index(max_fill_in_row)
                other_counts = [count for i, count in enumerate(fill_counts) if i != max_index]
                avg_other_fill = np.mean(other_counts) if other_counts else 0

                min_valid_fill = 15
                if max_fill_in_row > min_valid_fill and max_fill_in_row > (avg_other_fill * 1.5):
                    filled = self.options[max_index]
                    filled_rect = row_bubbles[max_index]

            # Annotate image
            if filled_rect:
                (fx, fy, fw, fh) = filled_rect
                cv2.rectangle(image, (fx, fy), (fx + fw, fy + fh), (0, 0, 255), 2)
                cv2.putText(image, f"{question_num}:{filled}", (fx, fy - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            # --- Compare with answer key if provided ---
            if answer_key:
                # Fix: Ensure key is a string to match JSON keys
                correct_answer = answer_key.get(str(question_num))
                if filled is None:
                    status = "Not Attempted"
                    is_correct = False
                elif filled == correct_answer:
                    status = "Correct"
                    is_correct = True
                    score += 1
                else:
                    status = "Incorrect"
                    is_correct = False

                detailed_results[question_num] = {
                    "marked": filled if filled else "None",
                    "correct": correct_answer,
                    "status": status,
                    "is_correct": is_correct
                }
            else:
                detailed_results[question_num] = {
                    "marked": filled if filled else "None"
                }

            # --- Store the extracted answer here ---
            extracted_answers[question_num] = filled
            # --- End of storing extracted answer ---

            question_num += 1

        # Save annotated image
        cv2.imwrite(output_image, image)

        # Save results to JSON
        with open(output_json, "w") as f:
            json.dump(detailed_results, f, indent=2)

        # --- PRINT SCORE ONLY ---
        if answer_key:
            print(f"Total Score: {score}/{len(answer_key)}")
        
        # --- FIX: Return the required dictionary structure ---
        return {
            "total_score": score,
            "detailed_results": detailed_results,
            "extracted_answers": extracted_answers
        }
        # --- END FIX ---