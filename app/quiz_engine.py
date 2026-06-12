import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class QuizEngine:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.animals = self._load_json("animals.json")
        self.questions = self._load_json("questions.json")
        logger.info(f"✅ Загружено {len(self.animals)} животных и {len(self.questions)} вопросов")

    def _load_json(self, filename: str) -> Any:
        filepath = self.data_dir / filename
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки {filename}: {e}")
            raise

    def get_question(self, index: int) -> Optional[Dict[str, Any]]:
        if 0 <= index < len(self.questions):
            return self.questions[index]
        return None

    def get_total_questions(self) -> int:
        return len(self.questions)

    def calculate_result(self, scores: Dict[str, int], answers_history: List[Dict]) -> str:
        """Определяет победителя с учетом правила ничьей"""
        if not scores:
            return "lion"

        max_score = max(scores.values())
        # Находим всех животных, набравших максимальный балл
        top_animals = [animal for animal, score in scores.items() if score == max_score]

        # Если победитель один — возвращаем его
        if len(top_animals) == 1:
            return top_animals[0]

        # НИЧЬЯ: Приоритет у того, кто встретился в ответах раньше
        for answer_record in answers_history:
            scored_in_this_step = answer_record.get("scored_animals", [])
            for animal in top_animals:
                if animal in scored_in_this_step:
                    logger.info(f"Ничья разрешена: приоритет у {animal} (встретился раньше)")
                    return animal

        return top_animals[0]

    def get_animal_data(self, animal_key: str) -> Dict[str, Any]:
        return self.animals.get(animal_key, self.animals["lion"])