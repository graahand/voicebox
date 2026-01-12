"""
Pronunciation Dictionary module for VoiceBox project.
Maps difficult or mispronounced words to phonetically correct alternatives.
"""

from typing import Dict, Optional


class PronunciationDict:
    """
    Manages word replacements for TTS to handle difficult pronunciations.
    """
    
    # Dictionary of word replacements for better TTS pronunciation
    PRONUNCIATION_MAP: Dict[str, str] = {
        # Event-specific terms
        'Futuruma': 'Future-rama',
        'futuruma': 'future-rama',
        'FUTURUMA': 'FUTURE-RAMA',
        
        # Organization names
        'SMaRC': 'S-mark',
        'smarc': 's-mark',
        
        # Project names
        'DermaScan': 'Derma Scan',
        'dermascan': 'derma scan',
        'MeloTTS': 'Mello T T S',
        'melotts': 'mello t t s',
        
        # Technology terms
        'Mediapipe': 'Media pipe',
        'mediapipe': 'media pipe',
        'PUBG': 'pub-gee',
        'pubg': 'pub-gee',
        'FPS': 'F P S',
        'fps': 'f p s',
        'AI': 'A I',
        'LLM': 'L L M',
        'llm': 'l l m',
        'TTS': 'T T S',
        'tts': 't t s',
        'STT': 'S T T',
        'stt': 's t t',
        'API': 'A P I',
        'api': 'a p i',
        
        # Location names (Nepal specific)
        'Itahari': 'Ita-hari',
        'itahari': 'ita-hari',
        'Biratnagar': 'Birat-nagar',
        'biratnagar': 'birat-nagar',
        'Birgunj': 'Bir-gunj',
        'birgunj': 'bir-gunj',
        'Butwal': 'But-wall',
        'butwal': 'but-wall',
        'Chitwan': 'Chit-wan',
        'chitwan': 'chit-wan',
        'Kathmandu': 'Kat-man-doo',
        'kathmandu': 'kat-man-doo',
        'Pokhara': 'Poke-hara',
        'pokhara': 'poke-hara',
        
        # Game/Project names
        'Bhavisyawani': 'Bhavish-ya-wani',
        'bhavisyawani': 'bhavish-ya-wani',
        'AstroSpy': 'Astro Spy',
        'astrospy': 'astro spy',
        'Cybercentric': 'Cyber-centric',
        'cybercentric': 'cyber-centric',
    }
    
    @classmethod
    def replace_words(cls, text: str) -> str:
        """
        Replace difficult words with phonetically correct alternatives.
        
        Args:
            text: Input text with potentially difficult words.
        
        Returns:
            str: Text with replacements applied.
        """
        result = text
        
        # Apply all replacements
        for original, replacement in cls.PRONUNCIATION_MAP.items():
            result = result.replace(original, replacement)
        
        return result
    
    @classmethod
    def add_word(cls, original: str, replacement: str) -> None:
        """
        Add a new word to the pronunciation dictionary.
        
        Args:
            original: The word to replace.
            replacement: The phonetically correct version.
        """
        cls.PRONUNCIATION_MAP[original] = replacement
    
    @classmethod
    def remove_word(cls, original: str) -> bool:
        """
        Remove a word from the pronunciation dictionary.
        
        Args:
            original: The word to remove.
        
        Returns:
            bool: True if removed, False if not found.
        """
        if original in cls.PRONUNCIATION_MAP:
            del cls.PRONUNCIATION_MAP[original]
            return True
        return False
    
    @classmethod
    def get_replacement(cls, word: str) -> Optional[str]:
        """
        Get the replacement for a specific word.
        
        Args:
            word: The word to look up.
        
        Returns:
            Optional[str]: The replacement or None if not found.
        """
        return cls.PRONUNCIATION_MAP.get(word)
    
    @classmethod
    def list_words(cls) -> Dict[str, str]:
        """
        Get all word replacements.
        
        Returns:
            Dict[str, str]: Dictionary of all replacements.
        """
        return cls.PRONUNCIATION_MAP.copy()


def main() -> None:
    """
    Test pronunciation dictionary.
    """
    test_texts = [
        "Welcome to Futuruma 2026, the biggest tech fest!",
        "DermaScan uses AI and Mediapipe for analysis.",
        "Visit us in Kathmandu, Pokhara, and Biratnagar.",
        "Projects by SMaRC include Cybercentric Island and Bhavisyawani.",
        "Play PUBG-inspired Laser Tag game!"
    ]
    
    print("Pronunciation Dictionary Test\n")
    print("="*60)
    
    for text in test_texts:
        print(f"\nOriginal:  {text}")
        print(f"Replaced:  {PronunciationDict.replace_words(text)}")
    
    print(f"\n{'='*60}")
    print(f"Total words in dictionary: {len(PronunciationDict.PRONUNCIATION_MAP)}")


if __name__ == '__main__':
    main()
