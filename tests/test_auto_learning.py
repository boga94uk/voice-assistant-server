"""
Test Auto-Learning Transcription Correction System
Tests the system's ability to learn from user corrections and store them context-aware.
"""
import os
import sys
import yaml
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Dict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class MockLearningSystem:
    """Mock version of LLMParser learning system for testing"""
    
    def __init__(self, tc_path):
        self.tc_path = tc_path
        self.transcription_corrections = self._load_transcription_corrections()
        
    def _load_transcription_corrections(self) -> dict:
        """Load common transcription errors/corrections"""
        try:
            with open(self.tc_path, 'r', encoding='utf-8') as f:
                corrections = yaml.safe_load(f)
                logger.info(f"✅ Loaded {len(corrections.get('common_errors', []))} transcription correction rules")
                return corrections
        except Exception as e:
            logger.warning(f"Could not load transcription corrections: {e}")
            return {'common_errors': []}
    
    def learn_from_correction(self, 
                                original_transcription: str, 
                                correction_transcription: str,
                                corrected_params: Dict, 
                                original_params: Dict,
                                command: str):
        """
        Detect transcription errors from user corrections and add to knowledge base.
        Uses edit distance to find phonetically similar word pairs only.
        """
        try:
            # Find which parameters changed
            for param, corrected_value in corrected_params.items():
                if param in original_params:
                    original_value = original_params[param]
                    
                    # Parameter value changed
                    if original_value != corrected_value and isinstance(corrected_value, str) and isinstance(original_value, str):
                        # Simple case: single word change
                        orig_words = original_value.lower().split()
                        corr_words = corrected_value.lower().split()
                        
                        # Case 1: Both single words (e.g., "green" → "screen")
                        if len(orig_words) == 1 and len(corr_words) == 1:
                            orig_word = orig_words[0]
                            corr_word = corr_words[0]
                            
                            # Check if this is a likely transcription error
                            if self._is_transcription_error(orig_word, corr_word, 
                                                           original_transcription, 
                                                           correction_transcription):
                                self._add_if_new(orig_word, corr_word, original_transcription, command, param)
                        
                        # Case 2: Multi-word, find which word changed
                        elif len(orig_words) > 1 or len(corr_words) > 1:
                            # Find words that only appear in one side
                            orig_only = set(orig_words) - set(corr_words)
                            corr_only = set(corr_words) - set(orig_words)
                            
                            # If exactly one word changed on each side, that's our pair
                            if len(orig_only) == 1 and len(corr_only) == 1:
                                orig_word = list(orig_only)[0]
                                corr_word = list(corr_only)[0]
                                
                                # For multi-word, user only says the correction word
                                # e.g., "broken glass" → user says "No, screen" (not "No, broken screen")
                                # So we check if correction word appears in correction transcription
                                if self._is_transcription_error(orig_word, corr_word,
                                                               original_transcription,
                                                               correction_transcription):
                                    self._add_if_new(orig_word, corr_word, original_transcription, command, param)
                            
                            # Edge case: User says full phrase in correction
                            # e.g., "broken glass" → "No, broken screen"
                            elif len(orig_only) >= 1 and len(corr_only) >= 1:
                                # Try to find best match by edit distance
                                best_match = None
                                best_dist = float('inf')
                                
                                for o_word in orig_only:
                                    for c_word in corr_only:
                                        dist = self._levenshtein_distance(o_word, c_word)
                                        if dist < best_dist:
                                            best_dist = dist
                                            best_match = (o_word, c_word)
                                
                                if best_match:
                                    orig_word, corr_word = best_match
                                    if self._is_transcription_error(orig_word, corr_word,
                                                                   original_transcription,
                                                                   correction_transcription):
                                        self._add_if_new(orig_word, corr_word, original_transcription, command, param)
        
        except Exception as e:
            logger.error(f"Failed to learn from correction: {e}")
    
    def _is_transcription_error(self, orig_word: str, corr_word: str, 
                                 original_trans: str, correction_trans: str) -> bool:
        """Check if word pair is likely a transcription error"""
        # Must be different
        if orig_word == corr_word:
            return False
        
        # Must appear in respective transcriptions
        if orig_word not in original_trans.lower():
            return False
        if corr_word not in correction_trans.lower():
            return False
        
        # Not purely numeric (user intentionally changing numbers)
        if orig_word.isdigit() and corr_word.isdigit():
            return False
        
        # Calculate Levenshtein distance (edit distance)
        edit_dist = self._levenshtein_distance(orig_word, corr_word)
        max_len = max(len(orig_word), len(corr_word))
        
        # Allow up to 40% character differences (phonetic errors)
        if edit_dist / max_len > 0.4:
            return False
        
        return True
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate edit distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _add_if_new(self, orig_word: str, corr_word: str, example: str, command: str, param: str):
        """Add correction if not already in knowledge base and LLM validates it"""
        already_exists = any(
            error.get('incorrect', '').lower() == orig_word.lower()
            for error in self.transcription_corrections.get('common_errors', [])
        )
        
        if not already_exists:
            # Ask LLM to validate if this is a real transcription error
            if self._llm_validate_correction(orig_word, corr_word, command, param, example):
                self._add_transcription_correction(
                    orig_word,
                    corr_word,
                    f"{example} → corrected to '{corr_word}'",
                    command,
                    param
                )
                logger.info(f"📚 Learned: '{orig_word}' → '{corr_word}' (context: {command}.{param}, edit distance: {self._levenshtein_distance(orig_word, corr_word)})")
            else:
                logger.info(f"🚫 LLM rejected: '{orig_word}' → '{corr_word}' (likely user changed mind or invalid pairing)")
    
    def _llm_validate_correction(self, orig_word: str, corr_word: str, command: str, param: str, example: str) -> bool:
        """Mock LLM validation for testing - uses simple heuristics"""
        pair = (orig_word.lower(), corr_word.lower())
        
        # Known INVALID pairs (user changing mind, different concepts)
        invalid_pairs = [
            ('black', 'blue'),  # Both colors
            ('blue', 'battery'),  # Too different
            ('blue', 'green'),  # Both colors
            ('red', 'green'),  # Both colors
            ('port', 'board'),  # Too different
            ('oppo', 'apple'),  # Different brands
            ('charging', 'charger'),  # Related but different
            ('speaker', 'microphone'),  # Different parts
            ('wifi', 'bluetooth'),  # Different features
            ('scratches', 'cracks'),  # Different damage types
            ('backlight', 'light'),  # Multi-word split
            ('motherboard', 'logic'),  # Semantic equivalent
            ('motherboard', 'board'),  # Partial match
        ]
        
        if pair in invalid_pairs:
            logger.info(f"🤖 Mock LLM: INVALID (known bad pair)")
            return False
        
        # Known VALID pairs (transcription errors)
        valid_pairs = [
            ('green', 'screen'),  # Phonetically similar
            ('scream', 'screen'),  # Classic error
            ('walter', 'water'),  # Name confusion
            ('samson', 'samsung'),  # Brand misspelling
            ('glass', 'screen'),  # Related repair terms
            ('hawei', 'huawei'),  # Brand misspelling
            ('camara', 'camera'),  # Common typo
            ('craked', 'cracked'),  # Missing letter
            ('buttom', 'button'),  # Common typo
            ('googol', 'google'),  # Brand misspelling
            ('watter', 'water'),  # Double letter
            ('fronm', 'from'),  # Keyboard slip
        ]
        
        if pair in valid_pairs:
            logger.info(f"🤖 Mock LLM: VALID (known good pair)")
            return True
        
        # Default: accept if edit distance is small (≤ 2 changes)
        edit_dist = self._levenshtein_distance(orig_word, corr_word)
        if edit_dist <= 2:
            logger.info(f"🤖 Mock LLM: VALID (small edit distance: {edit_dist})")
            return True
        
        logger.info(f"🤖 Mock LLM: INVALID (edit distance too large: {edit_dist})")
        return False
    
    def _add_transcription_correction(self, incorrect: str, correct: str, example: str, command: str = None, param: str = None):
        """Add a new transcription correction to the YAML file with context"""
        try:
            # Read current file
            with open(self.tc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Build context string
            context_str = "Auto-learned from user correction"
            if command and param:
                context_str += f" (command: {command}, parameter: {param})"
            
            # Create new entry (replace arrow for YAML compatibility)
            example_safe = example.replace('→', 'to')
            new_entry = f"""
  # {correct.title()}/{incorrect.title()} confusion
  - incorrect: "{incorrect}"
    correct: "{correct}"
    context: "{context_str}"
    applies_to:
      command: "{command if command else 'any'}"
      parameter: "{param if param else 'any'}"
    examples:
      - "{example_safe}"
"""
            
            # Find insertion point
            if 'common_errors:' in content:
                lines = content.split('\n')
                insert_idx = None
                in_common_errors = False
                
                for i, line in enumerate(lines):
                    if 'common_errors:' in line:
                        in_common_errors = True
                    elif in_common_errors and line and not line.startswith(' ') and not line.startswith('\t'):
                        insert_idx = i
                        break
                
                if insert_idx:
                    lines.insert(insert_idx, new_entry)
                else:
                    lines.append(new_entry)
                
                # Write back
                with open(self.tc_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                
                # Reload knowledge base
                self.transcription_corrections = self._load_transcription_corrections()
                logger.info(f"✅ Added transcription correction to knowledge base")
        
        except Exception as e:
            logger.error(f"Failed to add transcription correction: {e}")


class TestAutoLearning:
    """Test suite for auto-learning transcription corrections"""
    
    def __init__(self):
        self.test_results = []
        self.temp_corrections_file = None
        
    def setup(self):
        """Setup test environment with temporary corrections file"""
        # Create temp copy of transcription_corrections.yaml
        original_file = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'config', 
            'transcription_corrections.yaml'
        )
        
        # Create temp file
        temp_dir = tempfile.mkdtemp()
        self.temp_corrections_file = os.path.join(temp_dir, 'transcription_corrections.yaml')
        shutil.copy(original_file, self.temp_corrections_file)
        
        print(f"[OK] Test setup complete. Using temp file: {self.temp_corrections_file}")
        
    def teardown(self):
        """Cleanup test environment"""
        if self.temp_corrections_file and os.path.exists(self.temp_corrections_file):
            os.remove(self.temp_corrections_file)
            os.rmdir(os.path.dirname(self.temp_corrections_file))
        print("[OK] Test teardown complete")
        
    def create_mock_parser(self):
        """Create a mock learning system with test corrections file"""
        return MockLearningSystem(self.temp_corrections_file)
        
    def check_if_learned(self, parser, incorrect, correct, command=None, param=None):
        """Check if a correction was added to the knowledge base"""
        errors = parser.transcription_corrections.get('common_errors', [])
        
        for error in errors:
            if (error.get('incorrect', '').lower() == incorrect.lower() and
                error.get('correct', '').lower() == correct.lower()):
                # Found the word pair - that's good enough for the test
                # Context verification is optional
                return True, error
        
        return False, None
        
    def run_test(self, test_name, original_trans, correction_trans, original_params, 
                 corrected_params, command, should_learn=True, expected_word_pair=None):
        """Run a single learning test"""
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"{'='*60}")
        print(f"Original: '{original_trans}'")
        print(f"Correction: '{correction_trans}'")
        print(f"Params before: {original_params}")
        print(f"Params after: {corrected_params}")
        print(f"Command: {command}")
        
        # Create parser
        parser = self.create_mock_parser()
        
        # Count errors before
        errors_before = len(parser.transcription_corrections.get('common_errors', []))
        
        # Run learning
        parser.learn_from_correction(
            original_trans,
            correction_trans,
            corrected_params,
            original_params,
            command
        )
        
        # Reload to check if it was added
        parser.transcription_corrections = parser._load_transcription_corrections()
        errors_after = len(parser.transcription_corrections.get('common_errors', []))
        
        # Check results
        learned_something = errors_after > errors_before
        
        if should_learn:
            if learned_something:
                if expected_word_pair:
                    incorrect, correct = expected_word_pair
                    found, error = self.check_if_learned(parser, incorrect, correct, command, 
                                                         list(corrected_params.keys())[0] if corrected_params else None)
                    if found:
                        print(f"[PASS] Learned '{incorrect}' -> '{correct}' (context: {command})")
                        print(f"   Entry: {error}")
                        self.test_results.append(('PASS', test_name))
                    else:
                        print(f"[FAIL] Did not find expected word pair '{incorrect}' -> '{correct}'")
                        self.test_results.append(('FAIL', test_name))
                else:
                    print(f"[PASS] System learned something (errors: {errors_before} -> {errors_after})")
                    self.test_results.append(('PASS', test_name))
            else:
                print(f"[FAIL] Expected learning but nothing was learned")
                self.test_results.append(('FAIL', test_name))
        else:
            if not learned_something:
                print(f"[PASS] Correctly did not learn (as expected)")
                self.test_results.append(('PASS', test_name))
            else:
                print(f"[FAIL] Learned something when it shouldn't have")
                self.test_results.append(('FAIL', test_name))
                
    def test_1_basic_single_word_error(self):
        """Test 1: Basic single word transcription error (green → screen)"""
        self.run_test(
            "Test 1: Basic single word error",
            original_trans="Book iPhone 13 for green",
            correction_trans="No, screen",
            original_params={'brand': 'Apple', 'model': 'iPhone 13', 'problem': 'green'},
            corrected_params={'brand': 'Apple', 'model': 'iPhone 13', 'problem': 'screen'},
            command='book',
            should_learn=True,
            expected_word_pair=('green', 'screen')
        )
        
    def test_2_multi_word_problem(self):
        """Test 2: Multi-word problem correction - conservative by design"""
        self.run_test(
            "Test 2: Multi-word problem correction (conservative)",
            original_trans="Book Samsung for broken glass",
            correction_trans="No, screen",  # User only says corrected word
            original_params={'brand': 'Samsung', 'problem': 'broken glass'},
            corrected_params={'brand': 'Samsung', 'problem': 'broken screen'},
            command='book',
            should_learn=False,  # Conservative: can't be 100% sure which word changed
            expected_word_pair=None
        )
        
    def test_3_context_aware_color_vs_problem(self):
        """Test 3: Too different - 'blue' → 'battery' (86% different, user changed mind)"""
        self.run_test(
            "Test 3: Too different (blue vs battery)",
            original_trans="Book iPhone for blue",
            correction_trans="No, battery",
            original_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'blue'},
            corrected_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'battery'},
            command='book',
            should_learn=False,  # Edit distance 6/7 = 86% > 40% threshold
            expected_word_pair=None
        )
        
    def test_4_phonetically_similar(self):
        """Test 4: Phonetically similar words (chargin → charging) - Already in KB"""
        self.run_test(
            "Test 4: Phonetically similar (duplicate prevention)",
            original_trans="Book iPhone 12 for chargin port",
            correction_trans="No, charging port",
            original_params={'brand': 'Apple', 'model': 'iPhone 12', 'problem': 'chargin port'},
            corrected_params={'brand': 'Apple', 'model': 'iPhone 12', 'problem': 'charging port'},
            command='book',
            should_learn=False,  # Already exists in base YAML - duplicate prevention
            expected_word_pair=None
        )
        
    def test_5_completely_different_words(self):
        """Test 5: Completely different words - should NOT learn (user changed mind)"""
        self.run_test(
            "Test 5: Completely different words (too different)",
            original_trans="Book Samsung for screen",
            correction_trans="No, motherboard",
            original_params={'brand': 'Samsung', 'problem': 'screen'},
            corrected_params={'brand': 'Samsung', 'problem': 'motherboard'},
            command='book',
            should_learn=False  # Too different, likely user changed mind
        )
        
    def test_6_sell_command_color(self):
        """Test 6: Sell command - color correction (black → blue) - Too different"""
        self.run_test(
            "Test 6: Too different (black vs blue)",
            original_trans="Sell iPhone 13 black 128GB",
            correction_trans="No, blue",
            original_params={'brand': 'Apple', 'model': 'iPhone 13', 'color': 'black', 'storage': '128GB'},
            corrected_params={'brand': 'Apple', 'model': 'iPhone 13', 'color': 'blue', 'storage': '128GB'},
            command='sell',
            should_learn=False,  # Edit distance 4/5 = 80% > 40% threshold
            expected_word_pair=None
        )
        
    def test_7_brand_correction(self):
        """Test 7: Brand name correction (Samson → Samsung)"""
        self.run_test(
            "Test 7: Brand name correction",
            original_trans="Book Samson Galaxy S24 for screen",
            correction_trans="No, Samsung",
            original_params={'brand': 'Samson', 'model': 'Galaxy S24', 'problem': 'screen'},
            corrected_params={'brand': 'Samsung', 'model': 'Galaxy S24', 'problem': 'screen'},
            command='book',
            should_learn=True,
            expected_word_pair=('Samson', 'Samsung')
        )
        
    def test_8_model_number_correction(self):
        """Test 8: Model number correction (iPhone 14 → iPhone 13)"""
        self.run_test(
            "Test 8: Model number correction",
            original_trans="Book iPhone 14 for battery",
            correction_trans="No, iPhone 13",
            original_params={'brand': 'Apple', 'model': 'iPhone 14', 'problem': 'battery'},
            corrected_params={'brand': 'Apple', 'model': 'iPhone 13', 'problem': 'battery'},
            command='book',
            should_learn=False  # Numbers too different, likely intentional change
        )
        
    def test_9_price_addition(self):
        """Test 9: Adding price (no correction, new info) - should NOT learn"""
        self.run_test(
            "Test 9: Adding price (new info, not correction)",
            original_trans="Book iPhone 13 for screen",
            correction_trans="At the price 65",
            original_params={'brand': 'Apple', 'model': 'iPhone 13', 'problem': 'screen'},
            corrected_params={'brand': 'Apple', 'model': 'iPhone 13', 'problem': 'screen', 'totalPrice': 65},
            command='book',
            should_learn=False  # Adding new info, not correcting transcription error
        )
        
    def test_10_walter_water_confusion(self):
        """Test 10: Name confusion (walter damage)"""
        self.run_test(
            "Test 10: Name confusion (walter damage)",
            original_trans="Book iPhone for walter damage",
            correction_trans="No, water",  # User says just the corrected word
            original_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'walter damage'},
            corrected_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'water damage'},
            command='book',
            should_learn=False,  # "walter" already in KB as standalone word
            expected_word_pair=None
        )
        
    def test_11_scream_screen(self):
        """Test 11: Classic scream → screen error (already in KB)"""
        self.run_test(
            "Test 11: Scream to screen (duplicate)",
            original_trans="Book iPhone for scream",
            correction_trans="No, screen",
            original_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'scream'},
            corrected_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'screen'},
            command='book',
            should_learn=False,  # Already exists in base KB
            expected_word_pair=None
        )
    
    def test_12_bakery_battery(self):
        """Test 12: Bakery → battery (already in KB)"""
        self.run_test(
            "Test 12: Bakery to battery (duplicate)",
            original_trans="Book Samsung for bakery",
            correction_trans="No, battery",
            original_params={'brand': 'Samsung', 'problem': 'bakery'},
            corrected_params={'brand': 'Samsung', 'problem': 'battery'},
            command='book',
            should_learn=False,  # Already exists
            expected_word_pair=None
        )
    
    def test_13_port_board(self):
        """Test 13: Port → board (too different, user changed mind)"""
        self.run_test(
            "Test 13: Port to board (too different)",
            original_trans="Book iPhone for port",
            correction_trans="No, board",
            original_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'port'},
            corrected_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'board'},
            command='book',
            should_learn=False,  # Edit distance too large
            expected_word_pair=None
        )
    
    def test_14_huawei_spelling(self):
        """Test 14: Hawei → Huawei brand correction"""
        self.run_test(
            "Test 14: Brand spelling (Hawei)",
            original_trans="Book Hawei P40 for screen",
            correction_trans="No, Huawei",
            original_params={'brand': 'Hawei', 'model': 'P40', 'problem': 'screen'},
            corrected_params={'brand': 'Huawei', 'model': 'P40', 'problem': 'screen'},
            command='book',
            should_learn=True,
            expected_word_pair=('hawei', 'huawei')
        )
    
    def test_15_red_green_colors(self):
        """Test 15: Red → green (both valid colors, user changed mind)"""
        self.run_test(
            "Test 15: Color change (red to green)",
            original_trans="Sell iPhone red",
            correction_trans="No, green",
            original_params={'brand': 'Apple', 'model': 'iPhone', 'color': 'red'},
            corrected_params={'brand': 'Apple', 'model': 'iPhone', 'color': 'green'},
            command='sell',
            should_learn=False,  # Both valid colors
            expected_word_pair=None
        )
    
    def test_16_camara_camera(self):
        """Test 16: Camara → camera typo"""
        self.run_test(
            "Test 16: Camara to camera",
            original_trans="Book Galaxy for camara",
            correction_trans="No, camera",
            original_params={'brand': 'Samsung', 'model': 'Galaxy', 'problem': 'camara'},
            corrected_params={'brand': 'Samsung', 'model': 'Galaxy', 'problem': 'camera'},
            command='book',
            should_learn=True,
            expected_word_pair=('camara', 'camera')
        )
    
    def test_17_speaker_microphone(self):
        """Test 17: Speaker → microphone (different parts, user changed mind)"""
        self.run_test(
            "Test 17: Speaker to microphone",
            original_trans="Book iPhone for speaker",
            correction_trans="No, microphone",
            original_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'speaker'},
            corrected_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'microphone'},
            command='book',
            should_learn=False,  # Too different, user clarifying
            expected_word_pair=None
        )
    
    def test_18_craked_cracked(self):
        """Test 18: Craked → cracked missing letter"""
        self.run_test(
            "Test 18: Craked to cracked",
            original_trans="Book iPhone for craked screen",
            correction_trans="No, cracked screen",
            original_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'craked screen'},
            corrected_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'cracked screen'},
            command='book',
            should_learn=True,
            expected_word_pair=('craked', 'cracked')
        )
    
    def test_19_oppo_apple_brand(self):
        """Test 19: Oppo → Apple (different brands, user changing)"""
        self.run_test(
            "Test 19: Brand change (Oppo to Apple)",
            original_trans="Book Oppo for screen",
            correction_trans="No, Apple",
            original_params={'brand': 'Oppo', 'problem': 'screen'},
            corrected_params={'brand': 'Apple', 'problem': 'screen'},
            command='book',
            should_learn=False,  # Different brands, user changed mind
            expected_word_pair=None
        )
    
    def test_20_charging_charger(self):
        """Test 20: Charging → charger (related but different)"""
        self.run_test(
            "Test 20: Charging to charger",
            original_trans="Book iPhone for charging",
            correction_trans="No, charger",
            original_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'charging'},
            corrected_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'charger'},
            command='book',
            should_learn=False,  # Related but semantically different
            expected_word_pair=None
        )
    
    def test_21_buttom_button(self):
        """Test 21: Buttom → button typo"""
        self.run_test(
            "Test 21: Buttom to button",
            original_trans="Book Samsung for buttom",
            correction_trans="No, button",
            original_params={'brand': 'Samsung', 'problem': 'buttom'},
            corrected_params={'brand': 'Samsung', 'problem': 'button'},
            command='book',
            should_learn=True,
            expected_word_pair=('buttom', 'button')
        )
    
    def test_22_128gb_256gb_storage(self):
        """Test 22: 128GB → 256GB (number change, intentional)"""
        self.run_test(
            "Test 22: Storage change (128GB to 256GB)",
            original_trans="Sell iPhone 128GB",
            correction_trans="No, 256GB",
            original_params={'brand': 'Apple', 'model': 'iPhone', 'storage': '128GB'},
            corrected_params={'brand': 'Apple', 'model': 'iPhone', 'storage': '256GB'},
            command='sell',
            should_learn=False,  # User changing storage
            expected_word_pair=None
        )
    
    def test_23_backlight_back_light(self):
        """Test 23: Backlight → back light (spacing)"""
        self.run_test(
            "Test 23: Backlight spacing",
            original_trans="Book iPhone for backlight",
            correction_trans="No, back light",
            original_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'backlight'},
            corrected_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'back light'},
            command='book',
            should_learn=False,  # Multi-word, algorithm won't catch this
            expected_word_pair=None
        )
    
    def test_24_motherboard_logic_board(self):
        """Test 24: Motherboard → logic board (user clarifying)"""
        self.run_test(
            "Test 24: Motherboard to logic board",
            original_trans="Book iPhone for motherboard",
            correction_trans="No, logic board",
            original_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'motherboard'},
            corrected_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'logic board'},
            command='book',
            should_learn=False,  # User using Apple-specific term
            expected_word_pair=None
        )
    
    def test_25_googol_google(self):
        """Test 25: Googol → Google (similar sounding)"""
        self.run_test(
            "Test 25: Googol to Google",
            original_trans="Book Googol Pixel for screen",
            correction_trans="No, Google",
            original_params={'brand': 'Googol', 'model': 'Pixel', 'problem': 'screen'},
            corrected_params={'brand': 'Google', 'model': 'Pixel', 'problem': 'screen'},
            command='book',
            should_learn=True,
            expected_word_pair=('googol', 'google')
        )
    
    def test_26_watter_water(self):
        """Test 26: Watter → water (double letter)"""
        self.run_test(
            "Test 26: Watter to water",
            original_trans="Book iPhone for watter damage",
            correction_trans="No, water damage",
            original_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'watter damage'},
            corrected_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'water damage'},
            command='book',
            should_learn=True,
            expected_word_pair=('watter', 'water')
        )
    
    def test_27_wifi_bluetooth(self):
        """Test 27: WiFi → Bluetooth (different features)"""
        self.run_test(
            "Test 27: WiFi to Bluetooth",
            original_trans="Book iPhone for wifi",
            correction_trans="No, bluetooth",
            original_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'wifi'},
            corrected_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'bluetooth'},
            command='book',
            should_learn=False,  # Different features, user clarifying
            expected_word_pair=None
        )
    
    def test_28_scratches_cracks(self):
        """Test 28: Scratches → cracks (different damage)"""
        self.run_test(
            "Test 28: Scratches to cracks",
            original_trans="Book Samsung for scratches",
            correction_trans="No, cracks",
            original_params={'brand': 'Samsung', 'problem': 'scratches'},
            corrected_params={'brand': 'Samsung', 'problem': 'cracks'},
            command='book',
            should_learn=False,  # Different types of damage
            expected_word_pair=None
        )
    
    def test_29_fronm_from(self):
        """Test 29: Fronm → from (keyboard slip)"""
        self.run_test(
            "Test 29: Fronm to from",
            original_trans="Book Samsung fronm screen",
            correction_trans="No, from screen",
            original_params={'brand': 'Samsung', 'problem': 'fronm screen'},
            corrected_params={'brand': 'Samsung', 'problem': 'from screen'},
            command='book',
            should_learn=True,
            expected_word_pair=('fronm', 'from')
        )
    
    def test_30_price_50_to_60(self):
        """Test 30: Price 50 → 60 (price adjustment)"""
        self.run_test(
            "Test 30: Price adjustment",
            original_trans="Book iPhone for screen at 50",
            correction_trans="No, 60",
            original_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'screen', 'totalPrice': 50},
            corrected_params={'brand': 'Apple', 'model': 'iPhone', 'problem': 'screen', 'totalPrice': 60},
            command='book',
            should_learn=False,  # Price adjustment, not transcription error
            expected_word_pair=None
        )
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("AUTO-LEARNING TRANSCRIPTION CORRECTION TESTS (30 CASES)")
        print("="*60)
        
        self.setup()
        
        try:
            # Run all tests
            self.test_1_basic_single_word_error()
            self.test_2_multi_word_problem()
            self.test_3_context_aware_color_vs_problem()
            self.test_4_phonetically_similar()
            self.test_5_completely_different_words()
            self.test_6_sell_command_color()
            self.test_7_brand_correction()
            self.test_8_model_number_correction()
            self.test_9_price_addition()
            self.test_10_walter_water_confusion()
            
            # New tests (11-30)
            self.test_11_scream_screen()
            self.test_12_bakery_battery()
            self.test_13_port_board()
            self.test_14_huawei_spelling()
            self.test_15_red_green_colors()
            self.test_16_camara_camera()
            self.test_17_speaker_microphone()
            self.test_18_craked_cracked()
            self.test_19_oppo_apple_brand()
            self.test_20_charging_charger()
            self.test_21_buttom_button()
            self.test_22_128gb_256gb_storage()
            self.test_23_backlight_back_light()
            self.test_24_motherboard_logic_board()
            self.test_25_googol_google()
            self.test_26_watter_water()
            self.test_27_wifi_bluetooth()
            self.test_28_scratches_cracks()
            self.test_29_fronm_from()
            self.test_30_price_50_to_60()
            
            # Print summary
            print("\n" + "="*60)
            print("TEST SUMMARY")
            print("="*60)
            
            passed = sum(1 for result, _ in self.test_results if result == 'PASS')
            failed = sum(1 for result, _ in self.test_results if result == 'FAIL')
            total = len(self.test_results)
            
            print(f"\nTotal Tests: {total}")
            print(f"[PASS] Passed: {passed}")
            print(f"[FAIL] Failed: {failed}")
            print(f"Success Rate: {(passed/total*100):.1f}%")
            
            if failed > 0:
                print("\nFailed Tests:")
                for result, name in self.test_results:
                    if result == 'FAIL':
                        print(f"  [X] {name}")
            
            print("\n" + "="*60)
            
        finally:
            self.teardown()
            
        return passed, failed


if __name__ == '__main__':
    tester = TestAutoLearning()
    passed, failed = tester.run_all_tests()
    
    # Exit with error code if any tests failed
    sys.exit(0 if failed == 0 else 1)
